# Sprint 4 — Fluxo B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que um estabelecimento busque freelancers por proximidade/skill e os convide diretamente; o aceite do convite gera um `ServiceContract` sem vaga pública, convergindo no mesmo modelo de contrato do Fluxo A.

**Architecture:** Nova entidade `Invitation` (convite freeform com termos propostos e TTL). `ServiceContract` ganha origem polimórfica (`application_id` XOR `invitation_id`) via migration que torna `application_id`/`job_posting_id` nullable e adiciona `invitation_id`. Busca de freelancers via PostGIS `ST_DWithin`. Aceite transacional reaproveita `has_overlap` + `ContractRepository.create` (assinatura generalizada) e faz cascade auto-decline de convites sobrepostos. Cron ARQ de 5 min expira convites pendentes vencidos.

**Tech Stack:** Python 3.12 + uv, FastAPI, SQLAlchemy 2.x async, Alembic, Postgres 15 + PostGIS (geoalchemy2/shapely), ARQ, pytest-asyncio. DB de teste = DB da VPS (porta 5435).

**Spec:** `docs/superpowers/specs/2026-06-01-sprint-4-fluxo-b-design.md`

---

## File structure

**Criar:**
- `app/domain/models/invitation.py` — model `Invitation`
- `app/domain/schemas/invitation.py` — `InvitationCreate`, `InvitationRead`, `InvitationList`
- `app/domain/schemas/freelancer_search.py` — `FreelancerSearchRead`, `FreelancerSearchList`
- `app/domain/repositories/invitation_repository.py` — CRUD + queries de convite
- `app/domain/repositories/freelancer_repository.py` — busca PostGIS de freelancers
- `app/domain/services/invitation_service.py` — regras de negócio de convite
- `app/domain/services/freelancer_search_service.py` — orquestra busca
- `app/api/v1/invitations/__init__.py`, `app/api/v1/invitations/router.py`
- `app/api/v1/freelancers/__init__.py`, `app/api/v1/freelancers/router.py`
- `alembic/versions/005_invitations_and_contract_origin.py`
- `tests/integration/test_freelancer_search.py`
- `tests/integration/test_invitations.py`
- `tests/integration/test_invitation_accept.py`
- `tests/integration/test_cron_invitation_expiry.py`

**Modificar:**
- `app/domain/models/service_contract.py` — `invitation_id` + FKs nullable
- `app/domain/models/__init__.py` — exportar `Invitation`
- `app/domain/repositories/contract_repository.py` — `create(...)` aceita origem por convite
- `app/core/exceptions.py` — exceções novas
- `app/core/config.py` — `invitation_ttl_hours`
- `app/workers/tasks.py` — `expire_invitations`
- `app/workers/arq_worker.py` — registrar cron
- `app/main.py` — incluir routers `invitations` e `freelancers`
- `tests/factories.py` — `make_invitation`, `make_freelancer_skill`

---

## Task 1: Bootstrap — branch + factories skeleton

**Files:**
- Test: `tests/factories.py`

- [ ] **Step 1: Criar branch a partir de main atualizada**

Run:
```bash
git checkout main && git pull --ff-only origin main
git checkout -b feat/sprint-4-flow-b
```

- [ ] **Step 2: Adicionar factory `make_freelancer_skill` em tests/factories.py**

Adicionar import no topo (junto aos outros models) e a função ao final do arquivo:

```python
from app.domain.models.freelancer_skill import FreelancerSkill
```

```python
async def make_freelancer_skill(
    session: AsyncSession,
    *,
    freelancer_user_id: uuid.UUID,
    skill_category_id: uuid.UUID,
) -> FreelancerSkill:
    link = FreelancerSkill(
        freelancer_user_id=freelancer_user_id,
        skill_category_id=skill_category_id,
    )
    session.add(link)
    await session.flush()
    await session.refresh(link)
    return link
```

- [ ] **Step 3: Smoke — pytest collect ainda funciona**

Run: `uv run pytest --collect-only -q 2>&1 | tail -3`
Expected: coleta sem erros (mesma contagem de antes + 0 testes novos).

- [ ] **Step 4: Commit**

```bash
git add tests/factories.py
git commit -m "chore(sprint-4): bootstrap branch + make_freelancer_skill factory"
```

---

## Task 2: Migration 005 — invitations + origem polimórfica do contrato

**Files:**
- Create: `alembic/versions/005_invitations_and_contract_origin.py`

- [ ] **Step 1: Escrever a migration**

Criar `alembic/versions/005_invitations_and_contract_origin.py`:

```python
"""invitations + origem polimorfica do service_contract (application XOR invitation)

Revision ID: 005_invitations_origin
Revises: 004_apps_contracts_notif
Create Date: 2026-06-01 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005_invitations_origin"
down_revision: str | None = "004_apps_contracts_notif"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── invitations ──────────────────────────────────────────────────────────
    op.create_table(
        "invitations",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("establishment_id", sa.UUID(), nullable=False),
        sa.Column("freelancer_id", sa.UUID(), nullable=False),
        sa.Column("skill_category_id", sa.UUID(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("proposed_hourly_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("proposed_total_pay", sa.Numeric(10, 2), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["establishment_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["freelancer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["skill_category_id"], ["skill_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'declined', 'withdrawn', 'expired')",
            name="invitations_status_check",
        ),
        sa.CheckConstraint("end_at > start_at", name="invitations_dates_check"),
        sa.CheckConstraint(
            "message IS NULL OR length(message) <= 1000",
            name="invitations_message_length_check",
        ),
    )
    op.create_index(
        "ix_invitations_freelancer_status",
        "invitations",
        ["freelancer_id", "status"],
    )
    op.create_index(
        "ix_invitations_establishment_status",
        "invitations",
        ["establishment_id", "status"],
    )
    op.create_index("ix_invitations_expires_at", "invitations", ["expires_at"])

    # ── service_contracts: origem polimorfica ─────────────────────────────────
    op.alter_column("service_contracts", "application_id", nullable=True)
    op.alter_column("service_contracts", "job_posting_id", nullable=True)
    op.add_column(
        "service_contracts", sa.Column("invitation_id", sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        "fk_service_contracts_invitation",
        "service_contracts",
        "invitations",
        ["invitation_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_service_contracts_invitation", "service_contracts", ["invitation_id"]
    )
    op.create_check_constraint(
        "service_contracts_origin_check",
        "service_contracts",
        "(application_id IS NOT NULL AND invitation_id IS NULL) "
        "OR (application_id IS NULL AND invitation_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "service_contracts_origin_check", "service_contracts", type_="check"
    )
    op.drop_constraint(
        "uq_service_contracts_invitation", "service_contracts", type_="unique"
    )
    op.drop_constraint(
        "fk_service_contracts_invitation", "service_contracts", type_="foreignkey"
    )
    op.drop_column("service_contracts", "invitation_id")
    op.alter_column("service_contracts", "job_posting_id", nullable=False)
    op.alter_column("service_contracts", "application_id", nullable=False)

    op.drop_index("ix_invitations_expires_at", table_name="invitations")
    op.drop_index("ix_invitations_establishment_status", table_name="invitations")
    op.drop_index("ix_invitations_freelancer_status", table_name="invitations")
    op.drop_table("invitations")
```

- [ ] **Step 2: Verificar sintaxe**

Run: `uv run python -c "import ast; ast.parse(open('alembic/versions/005_invitations_and_contract_origin.py').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Aplicar a migration (DB da VPS via .env)**

Run: `uv run alembic upgrade head`
Expected: `Running upgrade 004_apps_contracts_notif -> 005_invitations_origin`

- [ ] **Step 4: Verificar tabela e constraint de origem**

Run:
```bash
uv run python -c "import asyncio; from sqlalchemy import text; from app.core.database import SessionLocal; \
asyncio.run((lambda: None)()) if False else None"
```
Em vez disso, verificar via psql na VPS:
```bash
ssh root@93.127.211.7 "docker exec \$(docker ps -qf name=freela_food_postgres | head -1) psql -U freela -d freela_food -tAc \"SELECT conname FROM pg_constraint WHERE conname='service_contracts_origin_check';\""
```
Expected: `service_contracts_origin_check`

- [ ] **Step 5: Testar downgrade reversível**

Run: `uv run alembic downgrade -1 && uv run alembic upgrade head`
Expected: downgrade volta pra `004_apps_contracts_notif` (sem erro), upgrade reaplica `005_invitations_origin`.

- [ ] **Step 6: Commit**

```bash
git add alembic/versions/005_invitations_and_contract_origin.py
git commit -m "feat(sprint-4): migration 005 - invitations + origem polimorfica do contrato"
```

---

## Task 3: Models — Invitation + ServiceContract (origem)

**Files:**
- Create: `app/domain/models/invitation.py`
- Modify: `app/domain/models/service_contract.py`
- Modify: `app/domain/models/__init__.py`

- [ ] **Step 1: Escrever app/domain/models/invitation.py**

```python
"""Invitation — convite direto do estabelecimento ao freelancer (Fluxo B)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin, UUIDPKMixin


class Invitation(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "invitations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'declined', 'withdrawn', 'expired')",
            name="invitations_status_check",
        ),
        CheckConstraint("end_at > start_at", name="invitations_dates_check"),
        CheckConstraint(
            "message IS NULL OR length(message) <= 1000",
            name="invitations_message_length_check",
        ),
        Index("ix_invitations_freelancer_status", "freelancer_id", "status"),
        Index("ix_invitations_establishment_status", "establishment_id", "status"),
        Index("ix_invitations_expires_at", "expires_at"),
    )

    establishment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    skill_category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("skill_categories.id"), nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    proposed_hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    proposed_total_pay: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

- [ ] **Step 2: Alterar app/domain/models/service_contract.py — origem polimórfica**

Tornar `application_id` e `job_posting_id` nullable e adicionar `invitation_id`. Substituir o bloco das colunas `application_id` e `job_posting_id` por:

```python
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=True,
    )
    invitation_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("invitations.id"),
        nullable=True,
    )
    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("job_postings.id"),
        nullable=True,
    )
```

E adicionar ao `__table_args__` (depois do `UniqueConstraint` de application) estas duas constraints:

```python
        UniqueConstraint("invitation_id", name="uq_service_contracts_invitation"),
        CheckConstraint(
            "(application_id IS NOT NULL AND invitation_id IS NULL) "
            "OR (application_id IS NULL AND invitation_id IS NOT NULL)",
            name="service_contracts_origin_check",
        ),
```

- [ ] **Step 3: Exportar Invitation em app/domain/models/__init__.py**

Adicionar (seguindo o padrão dos imports/`__all__` existentes):

```python
from app.domain.models.invitation import Invitation
```

E incluir `"Invitation"` na lista `__all__`.

- [ ] **Step 4: Smoke — imports + metadata batem com o DB**

Run: `uv run python -c "from app.domain.models import Invitation, ServiceContract; print(Invitation.__tablename__, ServiceContract.invitation_id)"`
Expected: imprime `invitations` + a coluna sem erro.

- [ ] **Step 5: mypy strict nos models novos/alterados**

Run: `uv run mypy app/domain/models/invitation.py app/domain/models/service_contract.py`
Expected: `Success`

- [ ] **Step 6: Commit**

```bash
git add app/domain/models/
git commit -m "feat(sprint-4): model Invitation + origem polimorfica no ServiceContract"
```

---

## Task 4: Exceções + Settings

**Files:**
- Modify: `app/core/exceptions.py`
- Modify: `app/core/config.py`

- [ ] **Step 1: Adicionar exceções em app/core/exceptions.py**

Acrescentar ao final do arquivo:

```python
# ── Sprint 4 (Fluxo B) ───────────────────────────────────────────────────────


class EstablishmentProfileRequired(ConflictError):
    detail = "É necessário ter perfil de estabelecimento para esta ação"


class InvalidInvitationTarget(DomainError):
    detail = "Convidado precisa ser um freelancer ativo"


class InvalidInvitationWindow(DomainError):
    detail = "Janela do convite inválida (início no futuro e fim após início)"


class DuplicateInvitation(ConflictError):
    detail = "Já existe convite pendente sobreposto para este freelancer"


class InvitationNotPending(ConflictError):
    detail = "Convite já foi decidido"


class InvitationExpired(ConflictError):
    detail = "Convite expirou"
```

- [ ] **Step 2: Adicionar invitation_ttl_hours em app/core/config.py**

Adicionar dentro da classe `Settings`, logo após `delete_grace_period_days`:

```python
    # Fluxo B: validade default de um convite (limitada também pelo start_at)
    invitation_ttl_hours: int = Field(default=72, ge=1)
```

- [ ] **Step 3: Smoke**

Run: `uv run python -c "from app.core.config import get_settings; from app.core.exceptions import InvitationExpired; print(get_settings().invitation_ttl_hours, InvitationExpired().status_code)"`
Expected: `72 409`

- [ ] **Step 4: Commit**

```bash
git add app/core/exceptions.py app/core/config.py
git commit -m "feat(sprint-4): excecoes do Fluxo B + invitation_ttl_hours"
```

---

## Task 5: Busca de freelancers — repo + service + schema + endpoint

**Files:**
- Create: `app/domain/schemas/freelancer_search.py`
- Create: `app/domain/repositories/freelancer_repository.py`
- Create: `app/domain/services/freelancer_search_service.py`
- Create: `app/api/v1/freelancers/__init__.py`, `app/api/v1/freelancers/router.py`
- Modify: `app/main.py`
- Test: `tests/integration/test_freelancer_search.py`

- [ ] **Step 1: Escrever app/domain/schemas/freelancer_search.py**

```python
"""Schemas da busca de freelancers (Fluxo B)."""

import uuid

from pydantic import BaseModel, ConfigDict


class FreelancerSearchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    display_name: str
    bio: str | None
    avatar_url: str | None
    completed_contracts_count: int
    no_show_count: int
    distance_m: float


class FreelancerSearchList(BaseModel):
    items: list[FreelancerSearchRead]
    total: int
    page: int
    page_size: int
```

- [ ] **Step 2: Escrever app/domain/repositories/freelancer_repository.py**

```python
"""Repository de busca de freelancers por proximidade (PostGIS)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.freelancer_skill import FreelancerSkill


class FreelancerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search_by_proximity(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_m: float,
        skill_category_id: uuid.UUID | None,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[FreelancerProfile, float]], int]:
        point_expr = func.ST_SetSRID(
            func.ST_MakePoint(longitude, latitude), 4326
        ).cast(FreelancerProfile.location.type)

        conditions = [
            FreelancerProfile.deleted_at.is_(None),
            FreelancerProfile.location.is_not(None),
            func.ST_DWithin(FreelancerProfile.location, point_expr, radius_m),
        ]
        if skill_category_id is not None:
            conditions.append(
                FreelancerProfile.user_id.in_(
                    select(FreelancerSkill.freelancer_user_id).where(
                        FreelancerSkill.skill_category_id == skill_category_id
                    )
                )
            )

        distance_col = func.ST_Distance(
            FreelancerProfile.location, point_expr
        ).label("distance_m")

        base = select(FreelancerProfile, distance_col).where(*conditions)

        total = await self._session.scalar(
            select(func.count()).select_from(
                select(FreelancerProfile.user_id).where(*conditions).subquery()
            )
        )

        result = await self._session.execute(
            base.order_by(
                distance_col.asc(),
                FreelancerProfile.completed_contracts_count.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows: list[tuple[FreelancerProfile, float]] = [
            (row[0], float(row[1])) for row in result.all()
        ]
        return rows, int(total or 0)
```

- [ ] **Step 3: Escrever app/domain/services/freelancer_search_service.py**

```python
"""Service da busca de freelancers (Fluxo B)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDenied
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.repositories.freelancer_repository import FreelancerRepository
from app.domain.repositories.profile_repository import ProfileRepository
from app.domain.schemas.freelancer_search import (
    FreelancerSearchList,
    FreelancerSearchRead,
)


def _to_read(profile: FreelancerProfile, distance_m: float) -> FreelancerSearchRead:
    return FreelancerSearchRead(
        user_id=profile.user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        completed_contracts_count=profile.completed_contracts_count,
        no_show_count=profile.no_show_count,
        distance_m=distance_m,
    )


class FreelancerSearchService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = FreelancerRepository(session)
        self._profiles = ProfileRepository(session)

    async def search(
        self,
        *,
        user_id: uuid.UUID,
        latitude: float,
        longitude: float,
        radius_km: float,
        skill_category_id: uuid.UUID | None,
        page: int,
        page_size: int,
    ) -> FreelancerSearchList:
        # Só estabelecimento (com perfil) pode buscar freelancers
        if await self._profiles.get_establishment(user_id) is None:
            raise PermissionDenied()

        rows, total = await self._repo.search_by_proximity(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_km * 1000,
            skill_category_id=skill_category_id,
            page=page,
            page_size=page_size,
        )
        return FreelancerSearchList(
            items=[_to_read(p, d) for p, d in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
```

- [ ] **Step 4: Escrever app/api/v1/freelancers/__init__.py**

```python
```
(arquivo vazio)

- [ ] **Step 5: Escrever app/api/v1/freelancers/router.py**

```python
"""Endpoint /v1/freelancers/search (estabelecimento busca freelancers)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.freelancer_search import FreelancerSearchList
from app.domain.services.freelancer_search_service import FreelancerSearchService

router = APIRouter(tags=["freelancers"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/freelancers/search",
    response_model=FreelancerSearchList,
    summary="Estabelecimento busca freelancers por proximidade + skill",
)
async def search_freelancers(
    user_id: UserIdDep,
    session: SessionDep,
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    radius_km: Annotated[float, Query(gt=0, le=500)] = 10,
    skill_category_id: Annotated[uuid.UUID | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> FreelancerSearchList:
    return await FreelancerSearchService(session).search(
        user_id=user_id,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        skill_category_id=skill_category_id,
        page=page,
        page_size=page_size,
    )
```

- [ ] **Step 6: Incluir router em app/main.py**

Seguindo o padrão dos outros `include_router`, adicionar o import e o registro do router de freelancers com prefixo `/v1` (igual aos demais). Exemplo do registro:

```python
from app.api.v1.freelancers.router import router as freelancers_router
# ...
app.include_router(freelancers_router, prefix="/v1")
```

- [ ] **Step 7: Escrever testes em tests/integration/test_freelancer_search.py**

```python
"""Busca de freelancers por proximidade (Fluxo B)."""

import uuid

from httpx import AsyncClient

from app.core.database import SessionLocal
from tests.factories import (
    auth_header_for,
    make_establishment,
    make_freelancer,
    make_freelancer_skill,
    make_skill_category,
)

PWD = "Senha123!"


def _anchor() -> tuple[float, float]:
    # Âncora única por execução — DB da VPS é compartilhado.
    seed = uuid.uuid4().int
    lat = -23.5 - (seed % 500) / 1000.0
    lng = -47.5 - ((seed >> 32) % 500) / 1000.0
    return (lat, lng)


async def _establishment_token(client: AsyncClient, lat: float, lng: float) -> str:
    email = f"est-{uuid.uuid4().hex[:8]}@test.com"
    async with SessionLocal() as session:
        await make_establishment(session, email=email, lat=lat, lng=lng)
        await session.commit()
    return (await auth_header_for(client, email, PWD))["Authorization"].split()[1]


async def _make_freelancer_at(
    lat: float, lng: float, skill_id: uuid.UUID | None = None
) -> uuid.UUID:
    email = f"fl-{uuid.uuid4().hex[:8]}@test.com"
    async with SessionLocal() as session:
        user, _ = await make_freelancer(session, email=email, lat=lat, lng=lng)
        if skill_id is not None:
            await make_freelancer_skill(
                session, freelancer_user_id=user.id, skill_category_id=skill_id
            )
        await session.commit()
        return user.id


async def test_search_returns_nearby_freelancer(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    fl_id = await _make_freelancer_at(anchor_lat, anchor_lng)
    token = await _establishment_token(client, anchor_lat, anchor_lng)

    resp = await client.get(
        "/v1/freelancers/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"latitude": anchor_lat, "longitude": anchor_lng, "radius_km": 10},
    )
    assert resp.status_code == 200, resp.text
    ids = {item["user_id"] for item in resp.json()["items"]}
    assert str(fl_id) in ids


async def test_search_excludes_far_freelancer(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    far_id = await _make_freelancer_at(anchor_lat + 0.18, anchor_lng)  # ~20 km
    token = await _establishment_token(client, anchor_lat, anchor_lng)

    resp = await client.get(
        "/v1/freelancers/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"latitude": anchor_lat, "longitude": anchor_lng, "radius_km": 10},
    )
    ids = {item["user_id"] for item in resp.json()["items"]}
    assert str(far_id) not in ids


async def test_search_orders_by_distance_ascending(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    await _make_freelancer_at(anchor_lat + 0.04, anchor_lng)  # ~4 km
    await _make_freelancer_at(anchor_lat, anchor_lng)  # ~0 km
    token = await _establishment_token(client, anchor_lat, anchor_lng)

    resp = await client.get(
        "/v1/freelancers/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"latitude": anchor_lat, "longitude": anchor_lng, "radius_km": 10},
    )
    distances = [item["distance_m"] for item in resp.json()["items"]]
    assert distances == sorted(distances)


async def test_search_filters_by_skill(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    async with SessionLocal() as session:
        cat = await make_skill_category(session)
        await session.commit()
        skill_id = cat.id
    with_skill = await _make_freelancer_at(anchor_lat, anchor_lng, skill_id=skill_id)
    without_skill = await _make_freelancer_at(anchor_lat, anchor_lng)
    token = await _establishment_token(client, anchor_lat, anchor_lng)

    resp = await client.get(
        "/v1/freelancers/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "latitude": anchor_lat,
            "longitude": anchor_lng,
            "radius_km": 10,
            "skill_category_id": str(skill_id),
        },
    )
    ids = {item["user_id"] for item in resp.json()["items"]}
    assert str(with_skill) in ids
    assert str(without_skill) not in ids


async def test_search_does_not_leak_pii(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    await _make_freelancer_at(anchor_lat, anchor_lng)
    token = await _establishment_token(client, anchor_lat, anchor_lng)

    resp = await client.get(
        "/v1/freelancers/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"latitude": anchor_lat, "longitude": anchor_lng, "radius_km": 10},
    )
    for item in resp.json()["items"]:
        assert "cpf" not in item
        assert "phone" not in item


async def test_search_forbidden_for_freelancer(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    email = f"fl-{uuid.uuid4().hex[:8]}@test.com"
    async with SessionLocal() as session:
        await make_freelancer(session, email=email, lat=anchor_lat, lng=anchor_lng)
        await session.commit()
    headers = await auth_header_for(client, email, PWD)

    resp = await client.get(
        "/v1/freelancers/search",
        headers=headers,
        params={"latitude": anchor_lat, "longitude": anchor_lng, "radius_km": 10},
    )
    assert resp.status_code == 403
```

- [ ] **Step 8: Rodar testes da busca**

Run: `uv run pytest tests/integration/test_freelancer_search.py -v`
Expected: 6 passed.

- [ ] **Step 9: Lint + mypy**

Run:
```bash
uv run ruff check app/domain/repositories/freelancer_repository.py app/domain/services/freelancer_search_service.py app/domain/schemas/freelancer_search.py app/api/v1/freelancers/ tests/integration/test_freelancer_search.py
uv run mypy app/domain/repositories/freelancer_repository.py app/domain/services/freelancer_search_service.py app/api/v1/freelancers/router.py
```
Expected: verdes.

- [ ] **Step 10: Commit**

```bash
git add app/domain/schemas/freelancer_search.py app/domain/repositories/freelancer_repository.py app/domain/services/freelancer_search_service.py app/api/v1/freelancers/ app/main.py tests/integration/test_freelancer_search.py
git commit -m "feat(sprint-4): busca de freelancers por proximidade + skill (PostGIS) + 6 tests"
```

---

## Task 6: Invitation schemas + repository

**Files:**
- Create: `app/domain/schemas/invitation.py`
- Create: `app/domain/repositories/invitation_repository.py`

- [ ] **Step 1: Escrever app/domain/schemas/invitation.py**

```python
"""Schemas Pydantic de Invitation."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InvitationCreate(BaseModel):
    freelancer_id: uuid.UUID
    skill_category_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    proposed_hourly_rate: Decimal | None = Field(default=None, ge=0)
    proposed_total_pay: Decimal | None = Field(default=None, ge=0)
    message: str | None = Field(default=None, max_length=1000)


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    establishment_id: uuid.UUID
    freelancer_id: uuid.UUID
    skill_category_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    proposed_hourly_rate: Decimal | None
    proposed_total_pay: Decimal | None
    message: str | None
    status: str
    expires_at: datetime
    decided_at: datetime | None
    created_at: datetime


class InvitationList(BaseModel):
    items: list[InvitationRead]
    total: int
    page: int
    page_size: int
```

- [ ] **Step 2: Escrever app/domain/repositories/invitation_repository.py**

```python
"""Repository de Invitation."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.invitation import Invitation


class InvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        establishment_id: uuid.UUID,
        freelancer_id: uuid.UUID,
        skill_category_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
        proposed_hourly_rate: Decimal | None,
        proposed_total_pay: Decimal | None,
        message: str | None,
        expires_at: datetime,
    ) -> Invitation:
        inv = Invitation(
            establishment_id=establishment_id,
            freelancer_id=freelancer_id,
            skill_category_id=skill_category_id,
            start_at=start_at,
            end_at=end_at,
            proposed_hourly_rate=proposed_hourly_rate,
            proposed_total_pay=proposed_total_pay,
            message=message,
            expires_at=expires_at,
            status="pending",
        )
        self._session.add(inv)
        await self._session.flush()
        await self._session.refresh(inv)
        return inv

    async def get_by_id(self, invitation_id: uuid.UUID) -> Invitation | None:
        result = await self._session.execute(
            select(Invitation).where(Invitation.id == invitation_id)
        )
        return result.scalar_one_or_none()

    async def has_pending_overlap(
        self,
        *,
        establishment_id: uuid.UUID,
        freelancer_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
    ) -> bool:
        """True se já há convite pending desse par com janela sobreposta."""
        result = await self._session.execute(
            select(Invitation.id)
            .where(
                Invitation.establishment_id == establishment_id,
                Invitation.freelancer_id == freelancer_id,
                Invitation.status == "pending",
                Invitation.start_at < end_at,
                Invitation.end_at > start_at,
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def list_pending_overlapping_for_freelancer(
        self,
        *,
        freelancer_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
        except_id: uuid.UUID,
    ) -> list[Invitation]:
        """Convites pending do freelancer que se sobrepõem (exceto o aceito)."""
        result = await self._session.execute(
            select(Invitation).where(
                Invitation.freelancer_id == freelancer_id,
                Invitation.status == "pending",
                Invitation.id != except_id,
                Invitation.start_at < end_at,
                Invitation.end_at > start_at,
            )
        )
        return list(result.scalars().all())

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        as_role: str,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Invitation], int]:
        col = (
            Invitation.establishment_id
            if as_role == "establishment"
            else Invitation.freelancer_id
        )
        conditions = [col == user_id]
        if status_filter is not None:
            conditions.append(Invitation.status == status_filter)
        base = select(Invitation).where(and_(*conditions))
        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(Invitation.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def update_status(
        self, inv: Invitation, *, new_status: str, decided_at: datetime
    ) -> Invitation:
        inv.status = new_status
        inv.decided_at = decided_at
        await self._session.flush()
        await self._session.refresh(inv)
        return inv
```

- [ ] **Step 3: Smoke**

Run: `uv run python -c "from app.domain.repositories.invitation_repository import InvitationRepository; from app.domain.schemas.invitation import InvitationCreate; print('OK')"`
Expected: `OK`

- [ ] **Step 4: mypy strict**

Run: `uv run mypy app/domain/repositories/invitation_repository.py app/domain/schemas/invitation.py`
Expected: `Success`

- [ ] **Step 5: Commit**

```bash
git add app/domain/schemas/invitation.py app/domain/repositories/invitation_repository.py
git commit -m "feat(sprint-4): schemas + repository de Invitation"
```

---

## Task 7: Invitation create — service + endpoint

**Files:**
- Create: `app/domain/services/invitation_service.py`
- Create: `app/api/v1/invitations/__init__.py`, `app/api/v1/invitations/router.py`
- Modify: `app/main.py`
- Modify: `tests/factories.py` (make_invitation)
- Test: `tests/integration/test_invitations.py`

- [ ] **Step 1: Adicionar make_invitation em tests/factories.py**

Adicionar import e função:

```python
from app.domain.models.invitation import Invitation
```

```python
async def make_invitation(
    session: AsyncSession,
    *,
    establishment_id: uuid.UUID,
    freelancer_id: uuid.UUID,
    skill_category_id: uuid.UUID,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    status: str = "pending",
    expires_at: datetime | None = None,
    proposed_hourly_rate: Decimal | None = Decimal("30.00"),
) -> Invitation:
    s = start_at or (datetime.now(UTC) + timedelta(days=1))
    e = end_at or (s + timedelta(hours=4))
    inv = Invitation(
        establishment_id=establishment_id,
        freelancer_id=freelancer_id,
        skill_category_id=skill_category_id,
        start_at=s,
        end_at=e,
        proposed_hourly_rate=proposed_hourly_rate,
        status=status,
        expires_at=expires_at or (s),
    )
    session.add(inv)
    await session.flush()
    await session.refresh(inv)
    return inv
```

- [ ] **Step 2: Escrever app/domain/services/invitation_service.py (apenas create por enquanto)**

```python
"""Service de Invitation (Fluxo B)."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    DuplicateInvitation,
    EstablishmentProfileRequired,
    InvalidInvitationTarget,
    InvalidInvitationWindow,
)
from app.domain.repositories.invitation_repository import InvitationRepository
from app.domain.repositories.profile_repository import ProfileRepository
from app.domain.schemas.invitation import InvitationCreate, InvitationRead
from app.domain.services.notification_service import NotificationService
from app.utils.audit import write_audit_log


class InvitationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvitationRepository(session)
        self._profiles = ProfileRepository(session)
        self._notifications = NotificationService(session)

    async def create(
        self, *, establishment_id: uuid.UUID, payload: InvitationCreate
    ) -> InvitationRead:
        if await self._profiles.get_establishment(establishment_id) is None:
            raise EstablishmentProfileRequired()

        # Convidado precisa ser freelancer ativo (perfil não soft-deleted)
        if await self._profiles.get_freelancer(payload.freelancer_id) is None:
            raise InvalidInvitationTarget()

        now = datetime.now(UTC)
        if payload.start_at <= now or payload.end_at <= payload.start_at:
            raise InvalidInvitationWindow()

        if await self._repo.has_pending_overlap(
            establishment_id=establishment_id,
            freelancer_id=payload.freelancer_id,
            start_at=payload.start_at,
            end_at=payload.end_at,
        ):
            raise DuplicateInvitation()

        ttl_hours = get_settings().invitation_ttl_hours
        expires_at = min(now + timedelta(hours=ttl_hours), payload.start_at)

        inv = await self._repo.create(
            establishment_id=establishment_id,
            freelancer_id=payload.freelancer_id,
            skill_category_id=payload.skill_category_id,
            start_at=payload.start_at,
            end_at=payload.end_at,
            proposed_hourly_rate=payload.proposed_hourly_rate,
            proposed_total_pay=payload.proposed_total_pay,
            message=payload.message,
            expires_at=expires_at,
        )

        await write_audit_log(
            self._session,
            actor_id=establishment_id,
            action="create",
            entity="invitation",
            entity_id=inv.id,
            diff={"freelancer_id": str(payload.freelancer_id)},
        )
        await self._notifications.emit(
            user_id=payload.freelancer_id,
            type="invitation.received",
            payload={
                "invitation_id": str(inv.id),
                "establishment_id": str(establishment_id),
            },
        )
        await self._session.commit()
        return InvitationRead.model_validate(inv)
```

- [ ] **Step 2b: Escrever app/api/v1/invitations/__init__.py**

```python
```
(arquivo vazio)

- [ ] **Step 3: Escrever app/api/v1/invitations/router.py (apenas create por enquanto)**

```python
"""Endpoints /v1/invitations (Fluxo B)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.invitation import InvitationCreate, InvitationRead
from app.domain.services.invitation_service import InvitationService

router = APIRouter(tags=["invitations"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/invitations",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Estabelecimento convida um freelancer (Fluxo B)",
)
async def create_invitation(
    payload: InvitationCreate,
    user_id: UserIdDep,
    session: SessionDep,
) -> InvitationRead:
    return await InvitationService(session).create(
        establishment_id=user_id, payload=payload
    )
```

- [ ] **Step 4: Incluir router em app/main.py**

Adicionar import e registro (igual aos demais, prefixo `/v1`):

```python
from app.api.v1.invitations.router import router as invitations_router
# ...
app.include_router(invitations_router, prefix="/v1")
```

- [ ] **Step 5: Escrever testes de create em tests/integration/test_invitations.py**

```python
"""Convites — create + validações (Fluxo B)."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.core.database import SessionLocal
from tests.factories import (
    auth_header_for,
    make_establishment,
    make_freelancer,
    make_skill_category,
)

PWD = "Senha123!"


async def _seed_pair() -> dict[str, uuid.UUID | str]:
    est_email = f"est-{uuid.uuid4().hex[:8]}@test.com"
    fl_email = f"fl-{uuid.uuid4().hex[:8]}@test.com"
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=est_email)
        fl, _ = await make_freelancer(session, email=fl_email)
        cat = await make_skill_category(session)
        await session.commit()
        return {
            "est_id": est.id,
            "fl_id": fl.id,
            "skill_id": cat.id,
            "est_email": est_email,
            "fl_email": fl_email,
        }


def _future_window() -> tuple[str, str]:
    start = datetime.now(UTC) + timedelta(days=2)
    end = start + timedelta(hours=4)
    return start.isoformat(), end.isoformat()


async def test_create_invitation_happy(client: AsyncClient) -> None:
    s = await _seed_pair()
    headers = await auth_header_for(client, str(s["est_email"]), PWD)
    start, end = _future_window()
    resp = await client.post(
        "/v1/invitations",
        headers=headers,
        json={
            "freelancer_id": str(s["fl_id"]),
            "skill_category_id": str(s["skill_id"]),
            "start_at": start,
            "end_at": end,
            "proposed_hourly_rate": "45.00",
            "message": "Topa um plantão?",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["freelancer_id"] == str(s["fl_id"])
    assert body["expires_at"] is not None


async def test_create_forbidden_for_freelancer(client: AsyncClient) -> None:
    s = await _seed_pair()
    headers = await auth_header_for(client, str(s["fl_email"]), PWD)
    start, end = _future_window()
    resp = await client.post(
        "/v1/invitations",
        headers=headers,
        json={
            "freelancer_id": str(s["fl_id"]),
            "skill_category_id": str(s["skill_id"]),
            "start_at": start,
            "end_at": end,
        },
    )
    assert resp.status_code == 409  # EstablishmentProfileRequired


async def test_create_invalid_target(client: AsyncClient) -> None:
    s = await _seed_pair()
    headers = await auth_header_for(client, str(s["est_email"]), PWD)
    start, end = _future_window()
    resp = await client.post(
        "/v1/invitations",
        headers=headers,
        json={
            "freelancer_id": str(uuid.uuid4()),  # não existe
            "skill_category_id": str(s["skill_id"]),
            "start_at": start,
            "end_at": end,
        },
    )
    assert resp.status_code == 400


async def test_create_invalid_window_past(client: AsyncClient) -> None:
    s = await _seed_pair()
    headers = await auth_header_for(client, str(s["est_email"]), PWD)
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    end = (datetime.now(UTC) + timedelta(hours=3)).isoformat()
    resp = await client.post(
        "/v1/invitations",
        headers=headers,
        json={
            "freelancer_id": str(s["fl_id"]),
            "skill_category_id": str(s["skill_id"]),
            "start_at": past,
            "end_at": end,
        },
    )
    assert resp.status_code == 400


async def test_create_duplicate_overlapping(client: AsyncClient) -> None:
    s = await _seed_pair()
    headers = await auth_header_for(client, str(s["est_email"]), PWD)
    start, end = _future_window()
    payload = {
        "freelancer_id": str(s["fl_id"]),
        "skill_category_id": str(s["skill_id"]),
        "start_at": start,
        "end_at": end,
    }
    first = await client.post("/v1/invitations", headers=headers, json=payload)
    assert first.status_code == 201
    second = await client.post("/v1/invitations", headers=headers, json=payload)
    assert second.status_code == 409
```

- [ ] **Step 6: Rodar testes de create**

Run: `uv run pytest tests/integration/test_invitations.py -v`
Expected: 5 passed.

- [ ] **Step 7: Lint + mypy**

Run:
```bash
uv run ruff check app/domain/services/invitation_service.py app/api/v1/invitations/ tests/integration/test_invitations.py tests/factories.py
uv run mypy app/domain/services/invitation_service.py app/api/v1/invitations/router.py
```
Expected: verdes.

- [ ] **Step 8: Commit**

```bash
git add app/domain/services/invitation_service.py app/api/v1/invitations/ app/main.py tests/factories.py tests/integration/test_invitations.py
git commit -m "feat(sprint-4): POST /v1/invitations + notification.received + 5 tests"
```

---

## Task 8: Invitation list + get

**Files:**
- Modify: `app/domain/services/invitation_service.py`
- Modify: `app/api/v1/invitations/router.py`
- Test: `tests/integration/test_invitations.py`

- [ ] **Step 1: Adicionar list_mine + get_by_id no invitation_service.py**

Adicionar imports no topo:

```python
from app.core.exceptions import NotFoundError, PermissionDenied
from app.domain.schemas.invitation import InvitationList
```

Adicionar métodos à classe:

```python
    async def list_mine(
        self,
        *,
        user_id: uuid.UUID,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> InvitationList:
        # Determina papel: estabelecimento vê enviados; freelancer vê recebidos
        as_role = (
            "establishment"
            if await self._profiles.get_establishment(user_id) is not None
            else "freelancer"
        )
        items, total = await self._repo.list_for_user(
            user_id=user_id,
            as_role=as_role,
            status_filter=status_filter,
            page=page,
            page_size=page_size,
        )
        return InvitationList(
            items=[InvitationRead.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_by_id(
        self, *, user_id: uuid.UUID, invitation_id: uuid.UUID
    ) -> InvitationRead:
        inv = await self._repo.get_by_id(invitation_id)
        if inv is None:
            raise NotFoundError("Convite não encontrado")
        if user_id not in (inv.establishment_id, inv.freelancer_id):
            raise PermissionDenied()
        return InvitationRead.model_validate(inv)
```

- [ ] **Step 2: Adicionar endpoints no router.py**

Adicionar import de `Query` e `InvitationList`:

```python
from fastapi import APIRouter, Depends, Query, status
from app.domain.schemas.invitation import InvitationCreate, InvitationList, InvitationRead
```

Adicionar endpoints:

```python
@router.get(
    "/invitations",
    response_model=InvitationList,
    summary="Meus convites (estabelecimento vê enviados, freelancer recebidos)",
)
async def list_invitations(
    user_id: UserIdDep,
    session: SessionDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> InvitationList:
    return await InvitationService(session).list_mine(
        user_id=user_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/invitations/{invitation_id}",
    response_model=InvitationRead,
    summary="Detalhe de um convite (apenas partes)",
)
async def get_invitation(
    invitation_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> InvitationRead:
    return await InvitationService(session).get_by_id(
        user_id=user_id, invitation_id=invitation_id
    )
```

- [ ] **Step 3: Adicionar testes em tests/integration/test_invitations.py**

```python
async def test_list_establishment_sees_sent(client: AsyncClient) -> None:
    s = await _seed_pair()
    est_headers = await auth_header_for(client, str(s["est_email"]), PWD)
    start, end = _future_window()
    created = await client.post(
        "/v1/invitations",
        headers=est_headers,
        json={
            "freelancer_id": str(s["fl_id"]),
            "skill_category_id": str(s["skill_id"]),
            "start_at": start,
            "end_at": end,
        },
    )
    inv_id = created.json()["id"]
    resp = await client.get("/v1/invitations", headers=est_headers)
    ids = {item["id"] for item in resp.json()["items"]}
    assert inv_id in ids


async def test_list_freelancer_sees_received(client: AsyncClient) -> None:
    s = await _seed_pair()
    est_headers = await auth_header_for(client, str(s["est_email"]), PWD)
    fl_headers = await auth_header_for(client, str(s["fl_email"]), PWD)
    start, end = _future_window()
    created = await client.post(
        "/v1/invitations",
        headers=est_headers,
        json={
            "freelancer_id": str(s["fl_id"]),
            "skill_category_id": str(s["skill_id"]),
            "start_at": start,
            "end_at": end,
        },
    )
    inv_id = created.json()["id"]
    resp = await client.get("/v1/invitations", headers=fl_headers)
    ids = {item["id"] for item in resp.json()["items"]}
    assert inv_id in ids


async def test_get_invitation_by_party(client: AsyncClient) -> None:
    s = await _seed_pair()
    est_headers = await auth_header_for(client, str(s["est_email"]), PWD)
    start, end = _future_window()
    created = await client.post(
        "/v1/invitations",
        headers=est_headers,
        json={
            "freelancer_id": str(s["fl_id"]),
            "skill_category_id": str(s["skill_id"]),
            "start_at": start,
            "end_at": end,
        },
    )
    inv_id = created.json()["id"]
    resp = await client.get(f"/v1/invitations/{inv_id}", headers=est_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == inv_id


async def test_get_invitation_forbidden_for_stranger(client: AsyncClient) -> None:
    s = await _seed_pair()
    est_headers = await auth_header_for(client, str(s["est_email"]), PWD)
    start, end = _future_window()
    created = await client.post(
        "/v1/invitations",
        headers=est_headers,
        json={
            "freelancer_id": str(s["fl_id"]),
            "skill_category_id": str(s["skill_id"]),
            "start_at": start,
            "end_at": end,
        },
    )
    inv_id = created.json()["id"]
    # terceiro sem relação
    other_email = f"est-{uuid.uuid4().hex[:8]}@test.com"
    async with SessionLocal() as session:
        await make_establishment(session, email=other_email)
        await session.commit()
    other_headers = await auth_header_for(client, other_email, PWD)
    resp = await client.get(f"/v1/invitations/{inv_id}", headers=other_headers)
    assert resp.status_code == 403


async def test_get_invitation_not_found(client: AsyncClient) -> None:
    s = await _seed_pair()
    headers = await auth_header_for(client, str(s["est_email"]), PWD)
    resp = await client.get(f"/v1/invitations/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404
```

- [ ] **Step 4: Rodar testes**

Run: `uv run pytest tests/integration/test_invitations.py -v`
Expected: 10 passed (5 anteriores + 5 novos).

- [ ] **Step 5: Lint + mypy**

Run:
```bash
uv run ruff check app/domain/services/invitation_service.py app/api/v1/invitations/router.py tests/integration/test_invitations.py
uv run mypy app/domain/services/invitation_service.py app/api/v1/invitations/router.py
```
Expected: verdes.

- [ ] **Step 6: Commit**

```bash
git add app/domain/services/invitation_service.py app/api/v1/invitations/router.py tests/integration/test_invitations.py
git commit -m "feat(sprint-4): GET /v1/invitations (list role-aware) + GET /v1/invitations/{id} + 5 tests"
```

---

## Task 9: Invitation decline + withdraw

**Files:**
- Modify: `app/domain/services/invitation_service.py`
- Modify: `app/api/v1/invitations/router.py`
- Test: `tests/integration/test_invitations.py`

- [ ] **Step 1: Adicionar decline + withdraw no invitation_service.py**

Adicionar import:

```python
from app.core.exceptions import InvitationNotPending
```

Adicionar métodos:

```python
    async def decline(
        self, *, user_id: uuid.UUID, invitation_id: uuid.UUID
    ) -> InvitationRead:
        inv = await self._repo.get_by_id(invitation_id)
        if inv is None:
            raise NotFoundError("Convite não encontrado")
        if inv.freelancer_id != user_id:
            raise PermissionDenied()
        if inv.status != "pending":
            raise InvitationNotPending()

        now = datetime.now(UTC)
        inv = await self._repo.update_status(
            inv, new_status="declined", decided_at=now
        )
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="decline",
            entity="invitation",
            entity_id=inv.id,
            diff={},
        )
        await self._notifications.emit(
            user_id=inv.establishment_id,
            type="invitation.declined",
            payload={"invitation_id": str(inv.id), "auto": False},
        )
        await self._session.commit()
        return InvitationRead.model_validate(inv)

    async def withdraw(
        self, *, user_id: uuid.UUID, invitation_id: uuid.UUID
    ) -> InvitationRead:
        inv = await self._repo.get_by_id(invitation_id)
        if inv is None:
            raise NotFoundError("Convite não encontrado")
        if inv.establishment_id != user_id:
            raise PermissionDenied()
        if inv.status != "pending":
            raise InvitationNotPending()

        now = datetime.now(UTC)
        inv = await self._repo.update_status(
            inv, new_status="withdrawn", decided_at=now
        )
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="withdraw",
            entity="invitation",
            entity_id=inv.id,
            diff={},
        )
        await self._notifications.emit(
            user_id=inv.freelancer_id,
            type="invitation.withdrawn",
            payload={"invitation_id": str(inv.id)},
        )
        await self._session.commit()
        return InvitationRead.model_validate(inv)
```

- [ ] **Step 2: Adicionar endpoints no router.py**

```python
@router.post(
    "/invitations/{invitation_id}/decline",
    response_model=InvitationRead,
    summary="Freelancer recusa um convite",
)
async def decline_invitation(
    invitation_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> InvitationRead:
    return await InvitationService(session).decline(
        user_id=user_id, invitation_id=invitation_id
    )


@router.post(
    "/invitations/{invitation_id}/withdraw",
    response_model=InvitationRead,
    summary="Estabelecimento retira um convite",
)
async def withdraw_invitation(
    invitation_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> InvitationRead:
    return await InvitationService(session).withdraw(
        user_id=user_id, invitation_id=invitation_id
    )
```

- [ ] **Step 3: Adicionar testes em tests/integration/test_invitations.py**

```python
async def _create_invitation(client: AsyncClient, s: dict) -> tuple[str, dict, dict]:
    est_headers = await auth_header_for(client, str(s["est_email"]), PWD)
    fl_headers = await auth_header_for(client, str(s["fl_email"]), PWD)
    start, end = _future_window()
    created = await client.post(
        "/v1/invitations",
        headers=est_headers,
        json={
            "freelancer_id": str(s["fl_id"]),
            "skill_category_id": str(s["skill_id"]),
            "start_at": start,
            "end_at": end,
        },
    )
    return created.json()["id"], est_headers, fl_headers


async def test_decline_by_freelancer(client: AsyncClient) -> None:
    s = await _seed_pair()
    inv_id, _, fl_headers = await _create_invitation(client, s)
    resp = await client.post(f"/v1/invitations/{inv_id}/decline", headers=fl_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "declined"


async def test_decline_forbidden_for_establishment(client: AsyncClient) -> None:
    s = await _seed_pair()
    inv_id, est_headers, _ = await _create_invitation(client, s)
    resp = await client.post(f"/v1/invitations/{inv_id}/decline", headers=est_headers)
    assert resp.status_code == 403


async def test_withdraw_by_establishment(client: AsyncClient) -> None:
    s = await _seed_pair()
    inv_id, est_headers, _ = await _create_invitation(client, s)
    resp = await client.post(f"/v1/invitations/{inv_id}/withdraw", headers=est_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "withdrawn"


async def test_withdraw_forbidden_for_freelancer(client: AsyncClient) -> None:
    s = await _seed_pair()
    inv_id, _, fl_headers = await _create_invitation(client, s)
    resp = await client.post(f"/v1/invitations/{inv_id}/withdraw", headers=fl_headers)
    assert resp.status_code == 403


async def test_decline_already_decided(client: AsyncClient) -> None:
    s = await _seed_pair()
    inv_id, _, fl_headers = await _create_invitation(client, s)
    await client.post(f"/v1/invitations/{inv_id}/decline", headers=fl_headers)
    again = await client.post(f"/v1/invitations/{inv_id}/decline", headers=fl_headers)
    assert again.status_code == 409
```

- [ ] **Step 4: Rodar testes**

Run: `uv run pytest tests/integration/test_invitations.py -v`
Expected: 15 passed.

- [ ] **Step 5: Lint + mypy**

Run:
```bash
uv run ruff check app/domain/services/invitation_service.py app/api/v1/invitations/router.py tests/integration/test_invitations.py
uv run mypy app/domain/services/invitation_service.py app/api/v1/invitations/router.py
```
Expected: verdes.

- [ ] **Step 6: Commit**

```bash
git add app/domain/services/invitation_service.py app/api/v1/invitations/router.py tests/integration/test_invitations.py
git commit -m "feat(sprint-4): decline + withdraw de convites (com notifications) + 5 tests"
```

---

## Task 10: Invitation ACCEPT — transação + cascade + contrato

**Files:**
- Modify: `app/domain/repositories/contract_repository.py` (generaliza `create`)
- Modify: `app/domain/services/invitation_service.py`
- Modify: `app/api/v1/invitations/router.py`
- Test: `tests/integration/test_invitation_accept.py`

- [ ] **Step 1: Generalizar ContractRepository.create para aceitar origem por convite**

Em `app/domain/repositories/contract_repository.py`, substituir a assinatura e o corpo de `create` por:

```python
    async def create(
        self,
        *,
        freelancer_id: uuid.UUID,
        establishment_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
        agreed_hourly_rate: Decimal | None,
        agreed_total_pay: Decimal | None,
        application_id: uuid.UUID | None = None,
        invitation_id: uuid.UUID | None = None,
        job_posting_id: uuid.UUID | None = None,
    ) -> ServiceContract:
        contract = ServiceContract(
            application_id=application_id,
            invitation_id=invitation_id,
            job_posting_id=job_posting_id,
            freelancer_id=freelancer_id,
            establishment_id=establishment_id,
            start_at=start_at,
            end_at=end_at,
            agreed_hourly_rate=agreed_hourly_rate,
            agreed_total_pay=agreed_total_pay,
            status="scheduled",
        )
        self._session.add(contract)
        await self._session.flush()
        await self._session.refresh(contract)
        return contract
```

> A chamada existente em `application_service.accept` passa `application_id=` e `job_posting_id=` como keyword — continua válida (novos params têm default `None`). Não alterar `application_service.py`.

- [ ] **Step 2: Verificar que o Fluxo A continua verde após a mudança de assinatura**

Run: `uv run pytest tests/integration/test_application_accept.py -q`
Expected: 12 passed (nenhuma regressão).

- [ ] **Step 3: Adicionar accept no invitation_service.py**

Adicionar imports:

```python
from app.core.exceptions import FreelancerOverlap, InvitationExpired
from app.domain.repositories.contract_repository import ContractRepository
```

Adicionar método:

```python
    async def accept(
        self, *, user_id: uuid.UUID, invitation_id: uuid.UUID
    ) -> InvitationRead:
        contracts_repo = ContractRepository(self._session)

        inv = await self._repo.get_by_id(invitation_id)
        if inv is None:
            raise NotFoundError("Convite não encontrado")
        if inv.freelancer_id != user_id:
            raise PermissionDenied()
        if inv.status != "pending":
            raise InvitationNotPending()

        now = datetime.now(UTC)
        if inv.expires_at <= now:
            raise InvitationExpired()

        if await contracts_repo.has_overlap(
            freelancer_id=inv.freelancer_id,
            start_at=inv.start_at,
            end_at=inv.end_at,
        ):
            raise FreelancerOverlap()

        # 1) Convite aceito
        inv = await self._repo.update_status(
            inv, new_status="accepted", decided_at=now
        )

        # 2) Cria contrato (origem invitation, sem job)
        contract = await contracts_repo.create(
            invitation_id=inv.id,
            freelancer_id=inv.freelancer_id,
            establishment_id=inv.establishment_id,
            start_at=inv.start_at,
            end_at=inv.end_at,
            agreed_hourly_rate=inv.proposed_hourly_rate,
            agreed_total_pay=inv.proposed_total_pay,
        )

        # 3) Cascade: auto-decline dos convites pending sobrepostos
        overlapping = await self._repo.list_pending_overlapping_for_freelancer(
            freelancer_id=inv.freelancer_id,
            start_at=inv.start_at,
            end_at=inv.end_at,
            except_id=inv.id,
        )
        for other in overlapping:
            await self._repo.update_status(
                other, new_status="declined", decided_at=now
            )
            await self._notifications.emit(
                user_id=other.establishment_id,
                type="invitation.declined",
                payload={"invitation_id": str(other.id), "auto": True},
            )

        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="accept",
            entity="invitation",
            entity_id=inv.id,
            diff={"contract_id": str(contract.id)},
        )
        await self._notifications.emit(
            user_id=inv.establishment_id,
            type="invitation.accepted",
            payload={
                "invitation_id": str(inv.id),
                "contract_id": str(contract.id),
            },
        )
        await self._session.commit()
        return InvitationRead.model_validate(inv)
```

- [ ] **Step 4: Adicionar endpoint accept no router.py**

```python
@router.post(
    "/invitations/{invitation_id}/accept",
    response_model=InvitationRead,
    summary="Freelancer aceita um convite (cria contrato)",
)
async def accept_invitation(
    invitation_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> InvitationRead:
    return await InvitationService(session).accept(
        user_id=user_id, invitation_id=invitation_id
    )
```

- [ ] **Step 5: Escrever tests/integration/test_invitation_accept.py**

```python
"""Aceite de convite (Fluxo B) — contrato + cascade."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.service_contract import ServiceContract
from app.domain.services.invitation_service import InvitationService
from tests.factories import (
    make_establishment,
    make_freelancer,
    make_invitation,
    make_skill_category,
)


async def _setup(
    *,
    start_offset_h: float = 48,
    end_offset_h: float = 52,
    status: str = "pending",
    expires_offset_h: float = 24,
) -> dict:
    suffix = uuid.uuid4().hex[:8]
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        cat = await make_skill_category(session)
        inv = await make_invitation(
            session,
            establishment_id=est.id,
            freelancer_id=fl.id,
            skill_category_id=cat.id,
            start_at=now + timedelta(hours=start_offset_h),
            end_at=now + timedelta(hours=end_offset_h),
            status=status,
            expires_at=now + timedelta(hours=expires_offset_h),
        )
        await session.commit()
        return {"inv_id": inv.id, "est_id": est.id, "fl_id": fl.id, "cat_id": cat.id}


async def test_accept_creates_contract() -> None:
    ctx = await _setup()
    async with SessionLocal() as session:
        result = await InvitationService(session).accept(
            user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
        )
        assert result.status == "accepted"
    async with SessionLocal() as session:
        contract = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.invitation_id == ctx["inv_id"]
                )
            )
        ).scalar_one()
        assert contract.application_id is None
        assert contract.job_posting_id is None
        assert contract.status == "scheduled"
        assert contract.freelancer_id == ctx["fl_id"]


async def test_accept_copies_terms() -> None:
    ctx = await _setup()
    async with SessionLocal() as session:
        await InvitationService(session).accept(
            user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
        )
    async with SessionLocal() as session:
        contract = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.invitation_id == ctx["inv_id"]
                )
            )
        ).scalar_one()
        assert contract.agreed_hourly_rate is not None


async def test_accept_cascade_declines_overlapping() -> None:
    ctx = await _setup()
    now = datetime.now(UTC)
    # outro convite pending sobreposto pro mesmo freelancer
    async with SessionLocal() as session:
        est2, _ = await make_establishment(
            session, email=f"est2-{uuid.uuid4().hex[:8]}@test.com"
        )
        cat = await make_skill_category(session)
        other = await make_invitation(
            session,
            establishment_id=est2.id,
            freelancer_id=ctx["fl_id"],
            skill_category_id=cat.id,
            start_at=now + timedelta(hours=49),
            end_at=now + timedelta(hours=51),
            status="pending",
            expires_at=now + timedelta(hours=24),
        )
        await session.commit()
        other_id = other.id

    async with SessionLocal() as session:
        await InvitationService(session).accept(
            user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
        )
    async with SessionLocal() as session:
        from app.domain.models.invitation import Invitation

        refreshed = (
            await session.execute(
                select(Invitation).where(Invitation.id == other_id)
            )
        ).scalar_one()
        assert refreshed.status == "declined"


async def test_accept_does_not_touch_nonoverlapping() -> None:
    ctx = await _setup()
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        est2, _ = await make_establishment(
            session, email=f"est2-{uuid.uuid4().hex[:8]}@test.com"
        )
        cat = await make_skill_category(session)
        other = await make_invitation(
            session,
            establishment_id=est2.id,
            freelancer_id=ctx["fl_id"],
            skill_category_id=cat.id,
            start_at=now + timedelta(hours=100),  # sem sobreposição
            end_at=now + timedelta(hours=104),
            status="pending",
            expires_at=now + timedelta(hours=80),
        )
        await session.commit()
        other_id = other.id

    async with SessionLocal() as session:
        await InvitationService(session).accept(
            user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
        )
    async with SessionLocal() as session:
        from app.domain.models.invitation import Invitation

        refreshed = (
            await session.execute(
                select(Invitation).where(Invitation.id == other_id)
            )
        ).scalar_one()
        assert refreshed.status == "pending"


async def test_accept_blocked_by_overlap() -> None:
    """Freelancer já tem contrato sobreposto → FreelancerOverlap."""
    from app.core.exceptions import FreelancerOverlap

    ctx = await _setup()
    # aceita o primeiro (cria contrato)
    async with SessionLocal() as session:
        await InvitationService(session).accept(
            user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
        )
    # segundo convite sobreposto
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        est2, _ = await make_establishment(
            session, email=f"est2-{uuid.uuid4().hex[:8]}@test.com"
        )
        cat = await make_skill_category(session)
        inv2 = await make_invitation(
            session,
            establishment_id=est2.id,
            freelancer_id=ctx["fl_id"],
            skill_category_id=cat.id,
            start_at=now + timedelta(hours=49),
            end_at=now + timedelta(hours=51),
            status="pending",
            expires_at=now + timedelta(hours=24),
        )
        await session.commit()
        inv2_id = inv2.id

    async with SessionLocal() as session:
        try:
            await InvitationService(session).accept(
                user_id=ctx["fl_id"], invitation_id=inv2_id
            )
            raise AssertionError("esperava FreelancerOverlap")
        except FreelancerOverlap:
            pass


async def test_accept_blocked_when_expired() -> None:
    from app.core.exceptions import InvitationExpired

    ctx = await _setup(expires_offset_h=-1)  # já expirado
    async with SessionLocal() as session:
        try:
            await InvitationService(session).accept(
                user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
            )
            raise AssertionError("esperava InvitationExpired")
        except InvitationExpired:
            pass


async def test_accept_blocked_when_not_pending() -> None:
    from app.core.exceptions import InvitationNotPending

    ctx = await _setup(status="declined")
    async with SessionLocal() as session:
        try:
            await InvitationService(session).accept(
                user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
            )
            raise AssertionError("esperava InvitationNotPending")
        except InvitationNotPending:
            pass


async def test_accept_forbidden_for_non_invitee() -> None:
    from app.core.exceptions import PermissionDenied

    ctx = await _setup()
    async with SessionLocal() as session:
        try:
            await InvitationService(session).accept(
                user_id=ctx["est_id"], invitation_id=ctx["inv_id"]
            )
            raise AssertionError("esperava PermissionDenied")
        except PermissionDenied:
            pass
```

> Nota: estes testes chamam o service direto (não via HTTP) para exercitar a transação e o cascade sem depender de tokens — mesmo padrão usado em `test_cron_lifecycle.py`. São `async def` sem parâmetros (asyncio_mode=auto cuida do loop; sem fixtures a resolver).

- [ ] **Step 6: Rodar testes do accept**

Run: `uv run pytest tests/integration/test_invitation_accept.py -v`
Expected: 8 passed.

- [ ] **Step 7: Lint + mypy**

Run:
```bash
uv run ruff check app/domain/repositories/contract_repository.py app/domain/services/invitation_service.py app/api/v1/invitations/router.py tests/integration/test_invitation_accept.py
uv run mypy app/domain/repositories/contract_repository.py app/domain/services/invitation_service.py app/api/v1/invitations/router.py
```
Expected: verdes.

- [ ] **Step 8: Commit**

```bash
git add app/domain/repositories/contract_repository.py app/domain/services/invitation_service.py app/api/v1/invitations/router.py tests/integration/test_invitation_accept.py
git commit -m "feat(sprint-4): aceite de convite transacional + cascade auto-decline + contrato + 8 tests"
```

---

## Task 11: Cron ARQ — expire_invitations

**Files:**
- Modify: `app/workers/tasks.py`
- Modify: `app/workers/arq_worker.py`
- Test: `tests/integration/test_cron_invitation_expiry.py`

- [ ] **Step 1: Adicionar expire_invitations em app/workers/tasks.py**

Adicionar import do model (junto aos demais imports de model):

```python
from app.domain.models.invitation import Invitation
```

Adicionar função ao final do arquivo:

```python
async def expire_invitations(_ctx: dict[str, Any]) -> dict[str, int]:
    """Cron 5min — marca convites pending vencidos como expired.

    Idempotente. Usa func.now() do DB.
    """
    log = get_logger("arq.invitation_lifecycle")
    async with SessionLocal() as session, session.begin():
        result = await session.execute(
            update(Invitation)
            .where(
                Invitation.status == "pending",
                Invitation.expires_at <= func.now(),
            )
            .values(status="expired", updated_at=func.now())
            .returning(Invitation.id)
        )
        expired = len(result.all())
    log.info("invitation_lifecycle.tick", expired=expired)
    return {"expired": expired}
```

> `update` e `func` já são importados no topo de `tasks.py` (usados por `advance_contract_lifecycle`).

- [ ] **Step 2: Registrar cron em app/workers/arq_worker.py**

Atualizar o import:

```python
from app.workers.tasks import (
    advance_contract_lifecycle,
    expire_invitations,
    purge_inactive_users,
)
```

Adicionar `expire_invitations` à lista `functions` e um `cron(...)` de 5 min em `cron_jobs`:

```python
    functions: ClassVar[list[Any]] = [
        purge_inactive_users,
        advance_contract_lifecycle,
        expire_invitations,
    ]
    cron_jobs: ClassVar[list[Any]] = [
        cron(purge_inactive_users, hour={2}, minute={0}),  # type: ignore[arg-type]
        cron(
            advance_contract_lifecycle,  # type: ignore[arg-type]
            minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55},
        ),
        cron(
            expire_invitations,  # type: ignore[arg-type]
            minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55},
        ),
    ]
```

- [ ] **Step 3: Escrever tests/integration/test_cron_invitation_expiry.py**

```python
"""Cron expire_invitations (Fluxo B)."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.invitation import Invitation
from app.workers.tasks import expire_invitations
from tests.factories import (
    make_establishment,
    make_freelancer,
    make_invitation,
    make_skill_category,
)


async def _make_invitation(*, status: str, expires_offset_h: float) -> uuid.UUID:
    suffix = uuid.uuid4().hex[:8]
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        cat = await make_skill_category(session)
        inv = await make_invitation(
            session,
            establishment_id=est.id,
            freelancer_id=fl.id,
            skill_category_id=cat.id,
            start_at=now + timedelta(hours=100),
            end_at=now + timedelta(hours=104),
            status=status,
            expires_at=now + timedelta(hours=expires_offset_h),
        )
        await session.commit()
        return inv.id


async def _status(inv_id: uuid.UUID) -> str:
    async with SessionLocal() as session:
        inv = (
            await session.execute(select(Invitation).where(Invitation.id == inv_id))
        ).scalar_one()
        return inv.status


async def test_expires_pending_past_due() -> None:
    inv_id = await _make_invitation(status="pending", expires_offset_h=-1)
    res = await expire_invitations({})
    assert res["expired"] >= 1
    assert await _status(inv_id) == "expired"


async def test_ignores_pending_not_due() -> None:
    inv_id = await _make_invitation(status="pending", expires_offset_h=10)
    await expire_invitations({})
    assert await _status(inv_id) == "pending"


async def test_ignores_non_pending() -> None:
    inv_id = await _make_invitation(status="accepted", expires_offset_h=-1)
    await expire_invitations({})
    assert await _status(inv_id) == "accepted"


async def test_idempotent() -> None:
    inv_id = await _make_invitation(status="pending", expires_offset_h=-1)
    await expire_invitations({})
    res2 = await expire_invitations({})
    # nosso convite já expirou no 1º run; 2º não o reconta
    assert await _status(inv_id) == "expired"
    assert isinstance(res2["expired"], int)


async def test_accept_blocked_after_expiry() -> None:
    from app.core.exceptions import InvitationExpired
    from app.domain.services.invitation_service import InvitationService

    suffix = uuid.uuid4().hex[:8]
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        cat = await make_skill_category(session)
        inv = await make_invitation(
            session,
            establishment_id=est.id,
            freelancer_id=fl.id,
            skill_category_id=cat.id,
            start_at=now + timedelta(hours=100),
            end_at=now + timedelta(hours=104),
            status="pending",
            expires_at=now - timedelta(hours=1),
        )
        await session.commit()
        inv_id, fl_id = inv.id, fl.id

    await expire_invitations({})
    async with SessionLocal() as session:
        try:
            await InvitationService(session).accept(
                user_id=fl_id, invitation_id=inv_id
            )
            raise AssertionError("esperava InvitationExpired")
        except InvitationExpired:
            pass
```

- [ ] **Step 4: Rodar testes do cron**

Run: `uv run pytest tests/integration/test_cron_invitation_expiry.py -v`
Expected: 5 passed.

- [ ] **Step 5: Lint + mypy**

Run:
```bash
uv run ruff check app/workers/ tests/integration/test_cron_invitation_expiry.py
uv run mypy app/workers/tasks.py app/workers/arq_worker.py
```
Expected: verdes.

- [ ] **Step 6: Commit**

```bash
git add app/workers/ tests/integration/test_cron_invitation_expiry.py
git commit -m "feat(sprint-4): cron expire_invitations (5min) + 5 tests"
```

---

## Task 12: Verificação final + CLAUDE.md + deploy + merge

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Rodar suíte completa + lint + mypy do projeto**

Run:
```bash
uv run ruff check app tests
uv run mypy app
uv run pytest -q
```
Expected: tudo verde. ~99 (Sprint 3) + ~39 (Sprint 4) = ~138 testes passando.

- [ ] **Step 2: Confirmar migration aplicada na VPS**

Run:
```bash
ssh root@93.127.211.7 "docker exec \$(docker ps -qf name=freela_food_postgres | head -1) psql -U freela -d freela_food -tAc \"SELECT version_num FROM alembic_version;\""
```
Expected: `005_invitations_origin` (já aplicada na Task 2; reconfirmar).

- [ ] **Step 3: Atualizar Roadmap no CLAUDE.md (seção 11)**

Marcar Sprint 4 como concluída e mover o ponteiro pra Sprint 5:

```markdown
- **Sprint 4**: Fluxo B (busca de freelancers → convite direto → aceite → contrato). ✅ (~39 testes)
- **Sprint 5**: Contratos + avaliações com regra de visibilidade. ← *você está aqui*
```

- [ ] **Step 4: Commit do CLAUDE.md**

```bash
git add CLAUDE.md
git commit -m "docs: marcar Sprint 4 (Fluxo B) como concluida no roadmap"
```

- [ ] **Step 5: Push da branch**

```bash
git push -u origin feat/sprint-4-flow-b
```

- [ ] **Step 6: Merge em main + push**

```bash
git checkout main
git merge feat/sprint-4-flow-b -m "merge: sprint 4 - Fluxo B (busca + convite + aceite + cron, ~39 testes verdes)"
git push origin main
```

> Não há worker ARQ deployado na VPS (só infra de dados). O cron `expire_invitations` roda quando o worker for iniciado; registrar em `WorkerSettings` é suficiente neste momento.

---

## Self-review checklist (executado durante a escrita)

**Spec coverage:**
- [x] Migration 005 (invitations + origem XOR) → Task 2
- [x] Models Invitation + ServiceContract origem → Task 3
- [x] Exceções + Settings TTL → Task 4
- [x] Busca de freelancers (PostGIS) → Task 5
- [x] Schemas + repository Invitation → Task 6
- [x] Create invitation → Task 7
- [x] List + get → Task 8
- [x] Decline + withdraw → Task 9
- [x] Accept transacional + cascade → Task 10
- [x] Cron expire_invitations → Task 11
- [x] Deploy/merge/CLAUDE.md → Task 12

**Consistência de tipos/nomes:**
- [x] `ContractRepository.create` generalizado (origem por keyword default None) usado por Fluxo A (intacto) e Fluxo B.
- [x] `has_overlap` reaproveitado tal qual.
- [x] `InvitationCreate/Read/List` consistentes em schema/service/router.
- [x] Exceções `EstablishmentProfileRequired`, `InvalidInvitationTarget`, `InvalidInvitationWindow`, `DuplicateInvitation`, `InvitationNotPending`, `InvitationExpired` definidas em Task 4 e usadas em 7/9/10.
- [x] `expire_invitations(ctx)` assinatura igual em tasks.py, arq_worker.py e tests.
- [x] Factories `make_invitation`, `make_freelancer_skill` definidas em Tasks 1/7 e usadas em 5/10/11.

**Placeholders:** sem TBD/TODO; cada step de código mostra o código completo.

**Padrões anti-poluição:** todos os testes usam emails/identificadores únicos (uuid); busca usa âncora geográfica única por execução.

---

## Execution Handoff

Plano salvo em `docs/superpowers/plans/2026-06-01-sprint-4-fluxo-b.md`.
