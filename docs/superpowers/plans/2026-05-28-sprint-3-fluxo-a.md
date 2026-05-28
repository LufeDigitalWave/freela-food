# Sprint 3 — Fluxo A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o Fluxo A do marketplace (candidatura → aceite → contrato com ciclo de vida via cron ARQ), incluindo notifications in-app persistidas e regras de overlap/no-show/auto-reopen.

**Architecture:** Três módulos paralelos (`applications/`, `contracts/`, `notifications/`) seguindo o padrão de `app/api/v1/jobs/` da Sprint 2. NotificationService é serviço infra invocado dentro da transação dos services de application/contract. Operação `accept` usa `REPEATABLE READ` + `SELECT FOR UPDATE` para serialização. Cron ARQ a cada 5min avança contratos `scheduled→in_progress→completed`.

**Tech Stack:** Python 3.12 + uv, FastAPI + Pydantic v2, SQLAlchemy 2.x async + Alembic, Postgres 15 + PostGIS, asyncpg, ARQ (Redis), pytest-asyncio + httpx + **freezegun** (novo).

**Spec:** `docs/superpowers/specs/2026-05-28-sprint-3-fluxo-a-design.md`

---

## File structure

**Novos:**
```
alembic/versions/004_applications_contracts_notifications.py
app/api/v1/applications/__init__.py
app/api/v1/applications/router.py
app/api/v1/contracts/__init__.py
app/api/v1/contracts/router.py
app/api/v1/notifications/__init__.py
app/api/v1/notifications/router.py
app/domain/models/application.py
app/domain/models/service_contract.py
app/domain/models/notification.py
app/domain/repositories/application_repository.py
app/domain/repositories/contract_repository.py
app/domain/repositories/notification_repository.py
app/domain/schemas/application.py
app/domain/schemas/contract.py
app/domain/schemas/notification.py
app/domain/services/application_service.py
app/domain/services/contract_service.py
app/domain/services/notification_service.py
tests/factories.py
tests/integration/test_applications.py
tests/integration/test_application_accept.py
tests/integration/test_contracts.py
tests/integration/test_cron_lifecycle.py
tests/integration/test_notifications.py
```

**Modificados:**
```
app/core/exceptions.py            (novas subclasses de domínio)
app/domain/models/__init__.py     (exports)
app/domain/models/freelancer_profile.py (no_show_count, completed_contracts_count)
app/main.py                       (include_router das 3 novas rotas)
app/workers/tasks.py              (advance_contract_lifecycle)
app/workers/arq_worker.py         (cron 5min)
pyproject.toml                    (freezegun em dev-deps)
```

---

## Task 1: Bootstrap — branch, freezegun, factories scaffold

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/factories.py`

- [ ] **Step 1: Criar branch a partir de main**

```bash
git checkout main
git pull origin main
git checkout -b feat/sprint-3-flow-a
```

- [ ] **Step 2: Adicionar freezegun a dev-deps**

Editar `pyproject.toml` na seção de dev-deps (encontrar a chave `dev` em `[tool.uv]` ou `[project.optional-dependencies]` — usar a que já existe no projeto). Adicionar `"freezegun>=1.5.1"` à lista.

- [ ] **Step 3: Rodar uv sync**

```bash
uv sync
```

Expected: instala freezegun. Se falhar (lock do Windows Defender), tentar com `--frozen=false` ou rebuild da .venv.

- [ ] **Step 4: Criar tests/factories.py com skeleton (apenas imports + docstring)**

```python
"""Helpers pra criar entidades de teste (User, profiles, jobs, applications, contracts).

Cada factory recebe `session: AsyncSession` e retorna o model criado, já com
flush() executado. Não commita — assume controle transacional do test.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

# Factories serão preenchidas conforme as tasks adicionam os models.
```

- [ ] **Step 5: Smoke test do skeleton — pytest collect**

```bash
uv run pytest --collect-only -q tests/factories.py 2>&1 | tail -5
```

Expected: nenhum erro de import.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock tests/factories.py
git commit -m "chore(sprint-3): bootstrap branch + freezegun + factories skeleton"
```

---

## Task 2: Migration 004 — schema completo

**Files:**
- Create: `alembic/versions/004_applications_contracts_notifications.py`

- [ ] **Step 1: Escrever a migration**

```python
"""applications, service_contracts, notifications + counters em freelancer_profiles

Revision ID: 004_apps_contracts_notif
Revises: 003_jobs_and_geo
Create Date: 2026-05-28 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004_apps_contracts_notif"
down_revision: str | None = "003_jobs_and_geo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── applications ─────────────────────────────────────────────────────────
    op.create_table(
        "applications",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("job_posting_id", sa.UUID(), nullable=False),
        sa.Column("freelancer_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("message", sa.Text(), nullable=True),
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
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["job_posting_id"], ["job_postings.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["freelancer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "job_posting_id", "freelancer_id", name="uq_applications_job_freelancer"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'withdrawn')",
            name="applications_status_check",
        ),
        sa.CheckConstraint(
            "message IS NULL OR length(message) <= 500",
            name="applications_message_length_check",
        ),
    )
    op.create_index(
        "ix_applications_job_posting_status",
        "applications",
        ["job_posting_id", "status"],
    )
    op.create_index(
        "ix_applications_freelancer_status",
        "applications",
        ["freelancer_id", "status"],
    )

    # ── service_contracts ────────────────────────────────────────────────────
    op.create_table(
        "service_contracts",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("job_posting_id", sa.UUID(), nullable=False),
        sa.Column("freelancer_id", sa.UUID(), nullable=False),
        sa.Column("establishment_id", sa.UUID(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("agreed_hourly_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("agreed_total_pay", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("cancelled_by", sa.String(length=20), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column(
            "no_show",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
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
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["job_posting_id"], ["job_postings.id"]),
        sa.ForeignKeyConstraint(["freelancer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["establishment_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id", name="uq_service_contracts_application"),
        sa.CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')",
            name="service_contracts_status_check",
        ),
        sa.CheckConstraint(
            "cancelled_by IS NULL OR cancelled_by IN ('freelancer', 'establishment', 'system')",
            name="service_contracts_cancelled_by_check",
        ),
        sa.CheckConstraint(
            "end_at > start_at", name="service_contracts_dates_check"
        ),
        sa.CheckConstraint(
            "(cancelled_at IS NULL AND cancelled_by IS NULL) "
            "OR (cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL)",
            name="service_contracts_cancel_consistency_check",
        ),
        sa.CheckConstraint(
            "cancel_reason IS NULL OR length(cancel_reason) <= 1000",
            name="service_contracts_reason_length_check",
        ),
    )
    op.create_index(
        "ix_service_contracts_freelancer_status_dates",
        "service_contracts",
        ["freelancer_id", "status", "start_at", "end_at"],
    )
    op.create_index(
        "ix_service_contracts_status_start_at",
        "service_contracts",
        ["status", "start_at"],
    )
    op.create_index(
        "ix_service_contracts_status_end_at",
        "service_contracts",
        ["status", "end_at"],
    )
    op.create_index(
        "ix_service_contracts_job_posting",
        "service_contracts",
        ["job_posting_id"],
    )

    # ── notifications ────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column(
            "payload",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_user_read_created",
        "notifications",
        ["user_id", "read_at", sa.text("created_at DESC")],
    )

    # ── freelancer_profiles counters ────────────────────────────────────────
    op.add_column(
        "freelancer_profiles",
        sa.Column(
            "no_show_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "freelancer_profiles",
        sa.Column(
            "completed_contracts_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("freelancer_profiles", "completed_contracts_count")
    op.drop_column("freelancer_profiles", "no_show_count")
    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(
        "ix_service_contracts_job_posting", table_name="service_contracts"
    )
    op.drop_index(
        "ix_service_contracts_status_end_at", table_name="service_contracts"
    )
    op.drop_index(
        "ix_service_contracts_status_start_at", table_name="service_contracts"
    )
    op.drop_index(
        "ix_service_contracts_freelancer_status_dates", table_name="service_contracts"
    )
    op.drop_table("service_contracts")
    op.drop_index(
        "ix_applications_freelancer_status", table_name="applications"
    )
    op.drop_index(
        "ix_applications_job_posting_status", table_name="applications"
    )
    op.drop_table("applications")
```

- [ ] **Step 2: Verificar migration sintaticamente**

```bash
uv run python -c "from alembic.config import Config; from alembic.script import ScriptDirectory; sd = ScriptDirectory.from_config(Config('alembic.ini')); print(sd.get_revision('004_apps_contracts_notif'))"
```

Expected: imprime objeto Revision sem erro.

- [ ] **Step 3: Aplicar a migration localmente**

```bash
uv run alembic upgrade head
```

Expected: `Running upgrade 003_jobs_and_geo -> 004_apps_contracts_notif`.

- [ ] **Step 4: Verificar tabelas no DB**

```bash
uv run python -c "import asyncio; from sqlalchemy import text; from app.core.database import engine; \
async def go():
    async with engine.connect() as c:
        r = await c.execute(text(\"SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('applications','service_contracts','notifications') ORDER BY tablename\"))
        print([row[0] for row in r])
asyncio.run(go())"
```

Expected: `['applications', 'notifications', 'service_contracts']`.

- [ ] **Step 5: Testar downgrade reversível**

```bash
uv run alembic downgrade -1
uv run alembic upgrade head
```

Expected: ambos passam sem erro.

- [ ] **Step 6: Commit**

```bash
git add alembic/versions/004_applications_contracts_notifications.py
git commit -m "feat(sprint-3): migration 004 - applications + service_contracts + notifications"
```

---

## Task 3: Models SQLAlchemy + alteração no FreelancerProfile

**Files:**
- Create: `app/domain/models/application.py`
- Create: `app/domain/models/service_contract.py`
- Create: `app/domain/models/notification.py`
- Modify: `app/domain/models/freelancer_profile.py`
- Modify: `app/domain/models/__init__.py`

- [ ] **Step 1: Escrever app/domain/models/application.py**

```python
"""Application — candidatura de freelancer numa vaga."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin, UUIDPKMixin


class Application(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "job_posting_id", "freelancer_id", name="uq_applications_job_freelancer"
        ),
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'withdrawn')",
            name="applications_status_check",
        ),
        CheckConstraint(
            "message IS NULL OR length(message) <= 500",
            name="applications_message_length_check",
        ),
    )

    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        nullable=False,
    )
    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(nullable=True)
```

- [ ] **Step 2: Escrever app/domain/models/service_contract.py**

```python
"""ServiceContract — contrato gerado pelo aceite (Fluxo A) ou convite (Fluxo B futuro)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin, UUIDPKMixin


class ServiceContract(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "service_contracts"
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_service_contracts_application"),
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')",
            name="service_contracts_status_check",
        ),
        CheckConstraint(
            "cancelled_by IS NULL OR cancelled_by IN "
            "('freelancer', 'establishment', 'system')",
            name="service_contracts_cancelled_by_check",
        ),
        CheckConstraint("end_at > start_at", name="service_contracts_dates_check"),
        CheckConstraint(
            "(cancelled_at IS NULL AND cancelled_by IS NULL) "
            "OR (cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL)",
            name="service_contracts_cancel_consistency_check",
        ),
        CheckConstraint(
            "cancel_reason IS NULL OR length(cancel_reason) <= 1000",
            name="service_contracts_reason_length_check",
        ),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=False,
    )
    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("job_postings.id"),
        nullable=False,
    )
    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    establishment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    agreed_hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    agreed_total_pay: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="scheduled", server_default="scheduled"
    )
    cancelled_by: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    no_show: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
```

- [ ] **Step 3: Escrever app/domain/models/notification.py**

```python
"""Notification — log in-app de eventos pro user (Sprint 6 expande)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, UUIDPKMixin


class Notification(Base, UUIDPKMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
```

- [ ] **Step 4: Alterar app/domain/models/freelancer_profile.py**

Adicionar `Integer` ao import (já está) e dois novos campos abaixo de `service_radius_km`:

```python
    no_show_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    completed_contracts_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
```

- [ ] **Step 5: Atualizar app/domain/models/__init__.py**

Substituir todo o conteúdo por:

```python
"""Re-export de todos os modelos — Alembic detecta tudo via Base.metadata."""

from app.domain.models.application import Application
from app.domain.models.audit_log import AuditLog
from app.domain.models.base import Base
from app.domain.models.establishment_profile import EstablishmentProfile
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.freelancer_skill import FreelancerSkill
from app.domain.models.job_posting import JobPosting
from app.domain.models.notification import Notification
from app.domain.models.service_contract import ServiceContract
from app.domain.models.skill_category import SkillCategory
from app.domain.models.user import User

__all__ = [
    "Application",
    "AuditLog",
    "Base",
    "EstablishmentProfile",
    "FreelancerProfile",
    "FreelancerSkill",
    "JobPosting",
    "Notification",
    "ServiceContract",
    "SkillCategory",
    "User",
]
```

- [ ] **Step 6: Smoke test — imports**

```bash
uv run python -c "from app.domain.models import Application, ServiceContract, Notification, FreelancerProfile; print('ok', Application.__tablename__, ServiceContract.__tablename__, Notification.__tablename__, FreelancerProfile.no_show_count)"
```

Expected: `ok applications service_contracts notifications ...`

- [ ] **Step 7: Rodar mypy strict só nos arquivos novos**

```bash
uv run mypy app/domain/models/application.py app/domain/models/service_contract.py app/domain/models/notification.py app/domain/models/freelancer_profile.py
```

Expected: `Success: no issues found in 4 source files`.

- [ ] **Step 8: Commit**

```bash
git add app/domain/models/
git commit -m "feat(sprint-3): models Application, ServiceContract, Notification + counters em FreelancerProfile"
```

---

## Task 4: Exceções de domínio + Notification module completo

**Files:**
- Modify: `app/core/exceptions.py`
- Create: `app/domain/schemas/notification.py`
- Create: `app/domain/repositories/notification_repository.py`
- Create: `app/domain/services/notification_service.py`
- Create: `app/api/v1/notifications/__init__.py`
- Create: `app/api/v1/notifications/router.py`
- Modify: `app/main.py`
- Modify: `tests/factories.py`
- Create: `tests/integration/test_notifications.py`

- [ ] **Step 1: Adicionar exceções novas em app/core/exceptions.py**

Adicionar ao final do arquivo:

```python
# ── Sprint 3 ────────────────────────────────────────────────────────────────


class JobNotOpen(ConflictError):
    detail = "Vaga não está aberta para candidaturas"


class SelfApplicationForbidden(PermissionDenied):
    detail = "Estabelecimento não pode se candidatar à própria vaga"


class ProfileRequired(ConflictError):
    detail = "É necessário ter perfil de freelancer para candidatar-se"


class DuplicateApplication(ConflictError):
    detail = "Já existe candidatura sua nesta vaga"


class ApplicationNotPending(ConflictError):
    detail = "Candidatura já foi decidida"


class FreelancerOverlap(ConflictError):
    detail = "Freelancer já tem contrato sobreposto no horário"


class ContractAlreadyTerminal(ConflictError):
    detail = "Contrato já está em estado final (completed ou cancelled)"


class NotificationNotFound(NotFoundError):
    detail = "Notificação não encontrada"
```

- [ ] **Step 2: Escrever test FAILING em tests/integration/test_notifications.py**

```python
"""Testes do endpoint /v1/notifications."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_my_notifications_empty(client: AsyncClient) -> None:
    """User novo não tem notifications, lista retorna vazia."""
    # Registrar + login
    await client.post(
        "/v1/auth/register",
        json={"email": "n1@test.com", "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": "n1@test.com", "password": "Senha123!"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/v1/me/notifications", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["unread_count"] == 0
```

- [ ] **Step 3: Rodar — vai falhar (404)**

```bash
uv run pytest tests/integration/test_notifications.py::test_list_my_notifications_empty -v
```

Expected: FAIL com status_code 404 (rota não existe).

- [ ] **Step 4: Escrever app/domain/schemas/notification.py**

```python
"""Schemas Pydantic de Notification."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    payload: dict[str, Any]
    read_at: datetime | None
    created_at: datetime


class NotificationList(BaseModel):
    items: list[NotificationRead]
    total: int
    unread_count: int
    page: int
    page_size: int


class ReadAllResponse(BaseModel):
    updated: int
```

- [ ] **Step 5: Escrever app/domain/repositories/notification_repository.py**

```python
"""Repository de Notification."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, user_id: uuid.UUID, type: str, payload: dict[str, Any]
    ) -> Notification:
        notif = Notification(user_id=user_id, type=type, payload=payload)
        self._session.add(notif)
        await self._session.flush()
        await self._session.refresh(notif)
        return notif

    async def get_by_id(self, notif_id: uuid.UUID) -> Notification | None:
        result = await self._session.execute(
            select(Notification).where(Notification.id == notif_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        unread_only: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Notification], int, int]:
        base = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            base = base.where(Notification.read_at.is_(None))

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        unread = await self._session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
        )

        result = await self._session.execute(
            base.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0), int(unread or 0)

    async def mark_read(self, notif: Notification) -> Notification:
        notif.read_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(notif)
        return notif

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(UTC))
        )
        await self._session.flush()
        return int(result.rowcount or 0)
```

- [ ] **Step 6: Escrever app/domain/services/notification_service.py**

```python
"""Service de Notification. Utilizado pelos outros services pra emitir eventos."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotificationNotFound, PermissionDenied
from app.domain.models.notification import Notification
from app.domain.repositories.notification_repository import NotificationRepository
from app.domain.schemas.notification import (
    NotificationList,
    NotificationRead,
    ReadAllResponse,
)


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = NotificationRepository(session)

    async def emit(
        self, *, user_id: uuid.UUID, type: str, payload: dict[str, Any]
    ) -> Notification:
        """Cria notification. Chamado por outros services dentro da própria tx."""
        return await self._repo.create(user_id=user_id, type=type, payload=payload)

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        unread_only: bool,
        page: int,
        page_size: int,
    ) -> NotificationList:
        items, total, unread = await self._repo.list_for_user(
            user_id=user_id,
            unread_only=unread_only,
            page=page,
            page_size=page_size,
        )
        return NotificationList(
            items=[NotificationRead.model_validate(n) for n in items],
            total=total,
            unread_count=unread,
            page=page,
            page_size=page_size,
        )

    async def mark_read(
        self, *, user_id: uuid.UUID, notif_id: uuid.UUID
    ) -> NotificationRead:
        notif = await self._repo.get_by_id(notif_id)
        if notif is None:
            raise NotificationNotFound()
        if notif.user_id != user_id:
            raise PermissionDenied()
        if notif.read_at is None:
            notif = await self._repo.mark_read(notif)
        return NotificationRead.model_validate(notif)

    async def mark_all_read(self, *, user_id: uuid.UUID) -> ReadAllResponse:
        n = await self._repo.mark_all_read(user_id)
        return ReadAllResponse(updated=n)
```

- [ ] **Step 7: Escrever app/api/v1/notifications/__init__.py (vazio)**

```python
```

- [ ] **Step 8: Escrever app/api/v1/notifications/router.py**

```python
"""Endpoints /v1/me/notifications e /v1/notifications/*."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.notification import (
    NotificationList,
    NotificationRead,
    ReadAllResponse,
)
from app.domain.services.notification_service import NotificationService

router = APIRouter(tags=["notifications"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/me/notifications",
    response_model=NotificationList,
    summary="Lista notificações do user logado",
)
async def list_my_notifications(
    user_id: UserIdDep,
    session: SessionDep,
    unread_only: Annotated[bool, Query()] = False,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> NotificationList:
    return await NotificationService(session).list_for_user(
        user_id=user_id,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/notifications/{notif_id}/read",
    response_model=NotificationRead,
    summary="Marca uma notificação como lida",
)
async def mark_read(
    notif_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> NotificationRead:
    return await NotificationService(session).mark_read(
        user_id=user_id, notif_id=notif_id
    )


@router.post(
    "/me/notifications/read-all",
    response_model=ReadAllResponse,
    status_code=status.HTTP_200_OK,
    summary="Marca todas as não-lidas como lidas",
)
async def mark_all_read(
    user_id: UserIdDep,
    session: SessionDep,
) -> ReadAllResponse:
    return await NotificationService(session).mark_all_read(user_id=user_id)
```

- [ ] **Step 9: Incluir router em app/main.py**

Adicionar import abaixo de `jobs_router`:

```python
from app.api.v1.notifications.router import router as notifications_router
```

E include_router antes do `return app`:

```python
    app.include_router(notifications_router, prefix="/v1")
```

- [ ] **Step 10: Rodar test do step 2 — agora passa**

```bash
uv run pytest tests/integration/test_notifications.py::test_list_my_notifications_empty -v
```

Expected: PASS.

- [ ] **Step 11: Adicionar testes restantes em tests/integration/test_notifications.py**

Adicionar ao mesmo arquivo:

```python
@pytest.mark.asyncio
async def test_emit_and_list_notification(client: AsyncClient) -> None:
    """Notification persistida via service direto aparece na listagem."""
    from app.core.database import async_session_factory
    from app.domain.services.notification_service import NotificationService
    from app.domain.repositories.user_repository import UserRepository

    await client.post(
        "/v1/auth/register",
        json={"email": "n2@test.com", "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": "n2@test.com", "password": "Senha123!"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    async with async_session_factory() as session:
        user = await UserRepository(session).get_by_email("n2@test.com")
        assert user is not None
        await NotificationService(session).emit(
            user_id=user.id,
            type="application.received",
            payload={"job_posting_id": "fake"},
        )
        await session.commit()

    resp = await client.get("/v1/me/notifications", headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["unread_count"] == 1
    assert body["items"][0]["type"] == "application.received"


@pytest.mark.asyncio
async def test_unread_only_filter(client: AsyncClient) -> None:
    """Filtro unread_only=true só retorna não-lidas."""
    from app.core.database import async_session_factory
    from app.domain.services.notification_service import NotificationService
    from app.domain.repositories.user_repository import UserRepository

    await client.post(
        "/v1/auth/register",
        json={"email": "n3@test.com", "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": "n3@test.com", "password": "Senha123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    async with async_session_factory() as session:
        user = await UserRepository(session).get_by_email("n3@test.com")
        assert user is not None
        await NotificationService(session).emit(
            user_id=user.id, type="a", payload={}
        )
        n = await NotificationService(session).emit(
            user_id=user.id, type="b", payload={}
        )
        await NotificationService(session).mark_read(user_id=user.id, notif_id=n.id)
        await session.commit()

    resp = await client.get(
        "/v1/me/notifications?unread_only=true", headers=headers
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "a"


@pytest.mark.asyncio
async def test_mark_read_single(client: AsyncClient) -> None:
    from app.core.database import async_session_factory
    from app.domain.services.notification_service import NotificationService
    from app.domain.repositories.user_repository import UserRepository

    await client.post(
        "/v1/auth/register",
        json={"email": "n4@test.com", "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": "n4@test.com", "password": "Senha123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    async with async_session_factory() as session:
        user = await UserRepository(session).get_by_email("n4@test.com")
        assert user is not None
        n = await NotificationService(session).emit(
            user_id=user.id, type="x", payload={}
        )
        await session.commit()
        nid = n.id

    resp = await client.post(f"/v1/notifications/{nid}/read", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["read_at"] is not None


@pytest.mark.asyncio
async def test_mark_read_not_owner(client: AsyncClient) -> None:
    """User B não pode marcar como lida notification do A."""
    from app.core.database import async_session_factory
    from app.domain.services.notification_service import NotificationService
    from app.domain.repositories.user_repository import UserRepository

    for email in ["n5a@test.com", "n5b@test.com"]:
        await client.post(
            "/v1/auth/register",
            json={"email": email, "password": "Senha123!", "role": "freelancer"},
        )

    async with async_session_factory() as session:
        user_a = await UserRepository(session).get_by_email("n5a@test.com")
        assert user_a is not None
        n = await NotificationService(session).emit(
            user_id=user_a.id, type="x", payload={}
        )
        await session.commit()
        nid = n.id

    login_b = await client.post(
        "/v1/auth/login",
        json={"email": "n5b@test.com", "password": "Senha123!"},
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}
    resp = await client.post(f"/v1/notifications/{nid}/read", headers=headers_b)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient) -> None:
    from app.core.database import async_session_factory
    from app.domain.services.notification_service import NotificationService
    from app.domain.repositories.user_repository import UserRepository

    await client.post(
        "/v1/auth/register",
        json={"email": "n6@test.com", "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": "n6@test.com", "password": "Senha123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    async with async_session_factory() as session:
        user = await UserRepository(session).get_by_email("n6@test.com")
        assert user is not None
        for t in ("a", "b", "c"):
            await NotificationService(session).emit(
                user_id=user.id, type=t, payload={}
            )
        await session.commit()

    resp = await client.post("/v1/me/notifications/read-all", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["updated"] == 3


@pytest.mark.asyncio
async def test_pagination_order_desc(client: AsyncClient) -> None:
    from app.core.database import async_session_factory
    from app.domain.services.notification_service import NotificationService
    from app.domain.repositories.user_repository import UserRepository

    await client.post(
        "/v1/auth/register",
        json={"email": "n7@test.com", "password": "Senha123!", "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login",
        json={"email": "n7@test.com", "password": "Senha123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    async with async_session_factory() as session:
        user = await UserRepository(session).get_by_email("n7@test.com")
        assert user is not None
        for t in ("first", "second", "third"):
            await NotificationService(session).emit(
                user_id=user.id, type=t, payload={}
            )
        await session.commit()

    resp = await client.get(
        "/v1/me/notifications?page=1&page_size=2", headers=headers
    )
    body = resp.json()
    assert body["total"] == 3
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    # ordem desc por created_at: 'third' antes
    assert body["items"][0]["type"] == "third"
```

- [ ] **Step 12: Rodar todos os tests de notifications**

```bash
uv run pytest tests/integration/test_notifications.py -v
```

Expected: 6 passed (incluindo o do step 2).

- [ ] **Step 13: Lint + mypy**

```bash
uv run ruff check app/api/v1/notifications app/domain/schemas/notification.py app/domain/repositories/notification_repository.py app/domain/services/notification_service.py
uv run mypy app/api/v1/notifications app/domain/schemas/notification.py app/domain/repositories/notification_repository.py app/domain/services/notification_service.py
```

Expected: ambos verdes.

- [ ] **Step 14: Commit**

```bash
git add app/core/exceptions.py app/domain/schemas/notification.py app/domain/repositories/notification_repository.py app/domain/services/notification_service.py app/api/v1/notifications/ app/main.py tests/integration/test_notifications.py
git commit -m "feat(sprint-3): notifications module - schemas + repo + service + endpoints + 6 tests"
```

---

## Task 5: Application module — create endpoint (POST /jobs/{id}/applications)

**Files:**
- Create: `app/domain/schemas/application.py`
- Create: `app/domain/repositories/application_repository.py`
- Create: `app/domain/services/application_service.py`
- Create: `app/api/v1/applications/__init__.py`
- Create: `app/api/v1/applications/router.py`
- Modify: `app/main.py`
- Modify: `tests/factories.py`
- Create: `tests/integration/test_applications.py`

- [ ] **Step 1: Adicionar factories de user/profile em tests/factories.py**

Substituir o conteúdo por:

```python
"""Helpers pra criar entidades de teste.

Cada factory recebe `session: AsyncSession` e retorna o model criado, já com
flush() executado. Não commita — assume controle transacional do test.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.domain.models.application import Application
from app.domain.models.establishment_profile import EstablishmentProfile
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.job_posting import JobPosting
from app.domain.models.service_contract import ServiceContract
from app.domain.models.skill_category import SkillCategory
from app.domain.models.user import User


async def make_user(
    session: AsyncSession,
    *,
    email: str | None = None,
    role: str = "freelancer",
    password: str = "Senha123!",
) -> User:
    user = User(
        email=email or f"u-{uuid.uuid4().hex[:8]}@test.com",
        password_hash=hash_password(password),
        role=role,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def make_freelancer(
    session: AsyncSession,
    *,
    email: str | None = None,
    display_name: str = "Freela Test",
    lat: float = -23.55,
    lng: float = -46.63,
) -> tuple[User, FreelancerProfile]:
    user = await make_user(session, email=email, role="freelancer")
    profile = FreelancerProfile(
        user_id=user.id,
        display_name=display_name,
        location=from_shape(Point(lng, lat), srid=4326),
        service_radius_km=10,
    )
    session.add(profile)
    await session.flush()
    await session.refresh(profile)
    return user, profile


async def make_establishment(
    session: AsyncSession,
    *,
    email: str | None = None,
    display_name: str = "Bar Test",
    lat: float = -23.55,
    lng: float = -46.63,
) -> tuple[User, EstablishmentProfile]:
    user = await make_user(session, email=email, role="establishment")
    profile = EstablishmentProfile(
        user_id=user.id,
        display_name=display_name,
        location=from_shape(Point(lng, lat), srid=4326),
    )
    session.add(profile)
    await session.flush()
    await session.refresh(profile)
    return user, profile


async def make_skill_category(
    session: AsyncSession, *, slug: str = "garcom", name: str = "Garçom"
) -> SkillCategory:
    """Retorna a SkillCategory com esse slug; cria se não existir."""
    from sqlalchemy import select

    result = await session.execute(
        select(SkillCategory).where(SkillCategory.slug == slug)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing
    cat = SkillCategory(slug=slug, name=name)
    session.add(cat)
    await session.flush()
    await session.refresh(cat)
    return cat


async def make_job(
    session: AsyncSession,
    *,
    establishment_id: uuid.UUID,
    skill_category_id: uuid.UUID,
    title: str = "Vaga teste",
    status: str = "open",
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    hourly_rate: Decimal | None = Decimal("30.00"),
    total_pay: Decimal | None = None,
    lat: float = -23.55,
    lng: float = -46.63,
) -> JobPosting:
    s = start_at or (datetime.now(UTC) + timedelta(days=1))
    e = end_at or (s + timedelta(hours=4))
    job = JobPosting(
        establishment_id=establishment_id,
        skill_category_id=skill_category_id,
        title=title,
        location=from_shape(Point(lng, lat), srid=4326),
        start_at=s,
        end_at=e,
        hourly_rate=hourly_rate,
        total_pay=total_pay,
        status=status,
    )
    session.add(job)
    await session.flush()
    await session.refresh(job)
    return job


async def make_application(
    session: AsyncSession,
    *,
    job_posting_id: uuid.UUID,
    freelancer_id: uuid.UUID,
    status: str = "pending",
    message: str | None = None,
) -> Application:
    app_ = Application(
        job_posting_id=job_posting_id,
        freelancer_id=freelancer_id,
        status=status,
        message=message,
    )
    session.add(app_)
    await session.flush()
    await session.refresh(app_)
    return app_


async def make_contract(
    session: AsyncSession,
    *,
    application_id: uuid.UUID,
    job_posting_id: uuid.UUID,
    freelancer_id: uuid.UUID,
    establishment_id: uuid.UUID,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    status: str = "scheduled",
    agreed_hourly_rate: Decimal | None = Decimal("30.00"),
) -> ServiceContract:
    s = start_at or (datetime.now(UTC) + timedelta(days=1))
    e = end_at or (s + timedelta(hours=4))
    contract = ServiceContract(
        application_id=application_id,
        job_posting_id=job_posting_id,
        freelancer_id=freelancer_id,
        establishment_id=establishment_id,
        start_at=s,
        end_at=e,
        status=status,
        agreed_hourly_rate=agreed_hourly_rate,
    )
    session.add(contract)
    await session.flush()
    await session.refresh(contract)
    return contract


async def auth_header_for(client, email: str, password: str = "Senha123!") -> dict[str, str]:
    """Login via API e retorna {Authorization: Bearer ...}."""
    resp = await client.post(
        "/v1/auth/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
```

- [ ] **Step 2: Escrever app/domain/schemas/application.py**

```python
"""Schemas Pydantic de Application."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApplicationCreate(BaseModel):
    message: str | None = Field(default=None, max_length=500)


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_posting_id: uuid.UUID
    freelancer_id: uuid.UUID
    status: str
    message: str | None
    created_at: datetime
    decided_at: datetime | None


class ApplicationList(BaseModel):
    items: list[ApplicationRead]
    total: int
    page: int
    page_size: int
```

- [ ] **Step 3: Escrever app/domain/repositories/application_repository.py (apenas create + get_by_id pra esta task)**

```python
"""Repository de Application. Outros métodos serão adicionados em tasks subsequentes."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.application import Application


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        job_posting_id: uuid.UUID,
        freelancer_id: uuid.UUID,
        message: str | None,
    ) -> Application:
        app_ = Application(
            job_posting_id=job_posting_id,
            freelancer_id=freelancer_id,
            message=message,
            status="pending",
        )
        self._session.add(app_)
        await self._session.flush()
        await self._session.refresh(app_)
        return app_

    async def get_by_id(self, app_id: uuid.UUID) -> Application | None:
        result = await self._session.execute(
            select(Application).where(Application.id == app_id)
        )
        return result.scalar_one_or_none()
```

- [ ] **Step 4: Escrever app/domain/services/application_service.py (apenas create)**

```python
"""Service de Application. Métodos adicionais (list, accept, reject, withdraw) entram em tasks subsequentes."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateApplication,
    JobNotOpen,
    NotFoundError,
    ProfileRequired,
    SelfApplicationForbidden,
)
from app.domain.repositories.application_repository import ApplicationRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.profile_repository import ProfileRepository
from app.domain.schemas.application import ApplicationCreate, ApplicationRead
from app.domain.services.notification_service import NotificationService


class ApplicationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ApplicationRepository(session)
        self._jobs = JobRepository(session)
        self._profiles = ProfileRepository(session)
        self._notifications = NotificationService(session)

    async def create(
        self,
        *,
        freelancer_id: uuid.UUID,
        job_id: uuid.UUID,
        payload: ApplicationCreate,
    ) -> ApplicationRead:
        job = await self._jobs.get_by_id(job_id)
        if job is None:
            raise NotFoundError("Vaga não encontrada")
        if job.establishment_id == freelancer_id:
            raise SelfApplicationForbidden()
        if job.status != "open":
            raise JobNotOpen()

        profile = await self._profiles.get_freelancer(freelancer_id)
        if profile is None:
            raise ProfileRequired()

        try:
            app_ = await self._repo.create(
                job_posting_id=job_id,
                freelancer_id=freelancer_id,
                message=payload.message,
            )
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateApplication() from exc

        # Notification pro estabelecimento
        await self._notifications.emit(
            user_id=job.establishment_id,
            type="application.received",
            payload={
                "application_id": str(app_.id),
                "job_posting_id": str(job_id),
                "freelancer_id": str(freelancer_id),
            },
        )

        return ApplicationRead.model_validate(app_)
```

- [ ] **Step 5: Escrever app/api/v1/applications/__init__.py (vazio)**

```python
```

- [ ] **Step 6: Escrever app/api/v1/applications/router.py (apenas create por enquanto)**

```python
"""Endpoints /v1/applications, /v1/jobs/{id}/applications, /v1/me/applications.

Métodos adicionais serão acrescentados em tasks subsequentes.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.application import ApplicationCreate, ApplicationRead
from app.domain.services.application_service import ApplicationService

router = APIRouter(tags=["applications"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/jobs/{job_id}/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Freelancer candidata-se a uma vaga",
)
async def create_application(
    job_id: uuid.UUID,
    payload: ApplicationCreate,
    user_id: UserIdDep,
    session: SessionDep,
) -> ApplicationRead:
    return await ApplicationService(session).create(
        freelancer_id=user_id, job_id=job_id, payload=payload
    )
```

- [ ] **Step 7: Incluir router em app/main.py**

Adicionar import:

```python
from app.api.v1.applications.router import router as applications_router
```

E include_router:

```python
    app.include_router(applications_router, prefix="/v1")
```

- [ ] **Step 8: Escrever testes de create em tests/integration/test_applications.py**

```python
"""Testes de candidatura (POST /jobs/{id}/applications)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.database import async_session_factory
from tests.factories import (
    auth_header_for,
    make_establishment,
    make_freelancer,
    make_job,
    make_skill_category,
)


@pytest.mark.asyncio
async def test_freelancer_creates_application_happy_path(client: AsyncClient) -> None:
    """Freelancer com profile candidata em vaga open → 201, status=pending."""
    async with async_session_factory() as session:
        est_user, _ = await make_establishment(
            session, email="t1-est@test.com"
        )
        freela_user, _ = await make_freelancer(
            session, email="t1-fl@test.com"
        )
        cat = await make_skill_category(session)
        job = await make_job(
            session,
            establishment_id=est_user.id,
            skill_category_id=cat.id,
            status="open",
        )
        await session.commit()
        job_id = job.id

    headers = await auth_header_for(client, "t1-fl@test.com")
    resp = await client.post(
        f"/v1/jobs/{job_id}/applications",
        json={"message": "Tenho 5 anos de experiência"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["message"] == "Tenho 5 anos de experiência"
    assert body["decided_at"] is None


@pytest.mark.asyncio
async def test_duplicate_application_returns_409(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est_user, _ = await make_establishment(session, email="t2-est@test.com")
        freela_user, _ = await make_freelancer(session, email="t2-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est_user.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id

    headers = await auth_header_for(client, "t2-fl@test.com")
    r1 = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=headers)
    assert r1.status_code == 201
    r2 = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=headers)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_application_without_profile_returns_409(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est_user, _ = await make_establishment(session, email="t3-est@test.com")
        # User freelancer SEM profile
        from tests.factories import make_user
        await make_user(session, email="t3-fl@test.com", role="freelancer")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est_user.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id

    headers = await auth_header_for(client, "t3-fl@test.com")
    resp = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=headers)
    assert resp.status_code == 409
    assert "perfil" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_self_application_returns_403(client: AsyncClient) -> None:
    """Dono da vaga tentando candidatar na própria → 403."""
    async with async_session_factory() as session:
        est_user, _ = await make_establishment(session, email="t4-est@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est_user.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id

    headers = await auth_header_for(client, "t4-est@test.com")
    resp = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_application_on_non_open_job_returns_409(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est_user, _ = await make_establishment(session, email="t5-est@test.com")
        await make_freelancer(session, email="t5-fl@test.com")
        cat = await make_skill_category(session)
        # Vaga em draft
        job_draft = await make_job(
            session,
            establishment_id=est_user.id,
            skill_category_id=cat.id,
            status="draft",
        )
        await session.commit()
        job_id = job_draft.id

    headers = await auth_header_for(client, "t5-fl@test.com")
    resp = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_message_too_long_returns_422(client: AsyncClient) -> None:
    """Message > 500 chars rejeitada pelo Pydantic."""
    async with async_session_factory() as session:
        est_user, _ = await make_establishment(session, email="t6-est@test.com")
        await make_freelancer(session, email="t6-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est_user.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id

    headers = await auth_header_for(client, "t6-fl@test.com")
    resp = await client.post(
        f"/v1/jobs/{job_id}/applications",
        json={"message": "x" * 501},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_application_creates_notification(client: AsyncClient) -> None:
    """Após candidatura, notification.received aparece pro estabelecimento."""
    async with async_session_factory() as session:
        est_user, _ = await make_establishment(session, email="t7-est@test.com")
        await make_freelancer(session, email="t7-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est_user.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id

    fl_headers = await auth_header_for(client, "t7-fl@test.com")
    await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=fl_headers)

    est_headers = await auth_header_for(client, "t7-est@test.com")
    resp = await client.get("/v1/me/notifications", headers=est_headers)
    body = resp.json()
    assert body["total"] >= 1
    types = [n["type"] for n in body["items"]]
    assert "application.received" in types
```

- [ ] **Step 9: Rodar testes — 7 passam**

```bash
uv run pytest tests/integration/test_applications.py -v
```

Expected: 7 passed.

- [ ] **Step 10: Lint + mypy**

```bash
uv run ruff check app/api/v1/applications app/domain/schemas/application.py app/domain/repositories/application_repository.py app/domain/services/application_service.py tests/factories.py
uv run mypy app/api/v1/applications app/domain/schemas/application.py app/domain/repositories/application_repository.py app/domain/services/application_service.py
```

Expected: ambos verdes.

- [ ] **Step 11: Commit**

```bash
git add app/ tests/
git commit -m "feat(sprint-3): POST /v1/jobs/{id}/applications + notification.received + 7 tests"
```

---

## Task 6: Application list + get endpoints

**Files:**
- Modify: `app/domain/repositories/application_repository.py`
- Modify: `app/domain/services/application_service.py`
- Modify: `app/api/v1/applications/router.py`
- Modify: `tests/integration/test_applications.py`

- [ ] **Step 1: Adicionar métodos no application_repository.py**

Adicionar ao final da classe `ApplicationRepository`:

```python
    async def list_for_job(
        self,
        *,
        job_posting_id: uuid.UUID,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Application], int]:
        from sqlalchemy import func, select

        base = select(Application).where(
            Application.job_posting_id == job_posting_id
        )
        if status_filter is not None:
            base = base.where(Application.status == status_filter)

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(Application.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def list_for_freelancer(
        self,
        *,
        freelancer_id: uuid.UUID,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Application], int]:
        from sqlalchemy import func, select

        base = select(Application).where(Application.freelancer_id == freelancer_id)
        if status_filter is not None:
            base = base.where(Application.status == status_filter)

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(Application.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)
```

- [ ] **Step 2: Adicionar métodos no application_service.py**

Adicionar ao final da classe `ApplicationService`:

```python
    async def get_by_id(
        self, *, user_id: uuid.UUID, app_id: uuid.UUID
    ) -> ApplicationRead:
        from app.core.exceptions import NotFoundError, PermissionDenied

        app_ = await self._repo.get_by_id(app_id)
        if app_ is None:
            raise NotFoundError("Candidatura não encontrada")
        job = await self._jobs.get_by_id(app_.job_posting_id)
        is_freelancer = app_.freelancer_id == user_id
        is_establishment = job is not None and job.establishment_id == user_id
        if not (is_freelancer or is_establishment):
            raise PermissionDenied()
        return ApplicationRead.model_validate(app_)

    async def list_for_job(
        self,
        *,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> "ApplicationList":
        from app.core.exceptions import NotFoundError, PermissionDenied
        from app.domain.schemas.application import ApplicationList

        job = await self._jobs.get_by_id(job_id)
        if job is None:
            raise NotFoundError("Vaga não encontrada")
        if job.establishment_id != user_id:
            raise PermissionDenied()

        items, total = await self._repo.list_for_job(
            job_posting_id=job_id,
            status_filter=status_filter,
            page=page,
            page_size=page_size,
        )
        return ApplicationList(
            items=[ApplicationRead.model_validate(a) for a in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def list_mine(
        self,
        *,
        user_id: uuid.UUID,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> "ApplicationList":
        from app.domain.schemas.application import ApplicationList

        items, total = await self._repo.list_for_freelancer(
            freelancer_id=user_id,
            status_filter=status_filter,
            page=page,
            page_size=page_size,
        )
        return ApplicationList(
            items=[ApplicationRead.model_validate(a) for a in items],
            total=total,
            page=page,
            page_size=page_size,
        )
```

- [ ] **Step 3: Adicionar endpoints no router.py**

Adicionar `Query` e `ApplicationList` aos imports e os endpoints abaixo de `create_application`:

```python
from fastapi import APIRouter, Depends, Query, status
from app.domain.schemas.application import ApplicationCreate, ApplicationList, ApplicationRead


@router.get(
    "/jobs/{job_id}/applications",
    response_model=ApplicationList,
    summary="Lista candidaturas de uma vaga (apenas dono)",
)
async def list_job_applications(
    job_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApplicationList:
    return await ApplicationService(session).list_for_job(
        user_id=user_id,
        job_id=job_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/me/applications",
    response_model=ApplicationList,
    summary="Minhas candidaturas (freelancer)",
)
async def list_my_applications(
    user_id: UserIdDep,
    session: SessionDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApplicationList:
    return await ApplicationService(session).list_mine(
        user_id=user_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationRead,
    summary="Detalhe de uma candidatura (freelancer ou estabelecimento partes)",
)
async def get_application(
    application_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> ApplicationRead:
    return await ApplicationService(session).get_by_id(
        user_id=user_id, app_id=application_id
    )
```

- [ ] **Step 4: Adicionar tests em tests/integration/test_applications.py**

```python
@pytest.mark.asyncio
async def test_list_job_applications_owner_only(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="t8-est@test.com")
        fl1, _ = await make_freelancer(session, email="t8-f1@test.com")
        fl2, _ = await make_freelancer(session, email="t8-f2@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id

    h1 = await auth_header_for(client, "t8-f1@test.com")
    await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=h1)
    h2 = await auth_header_for(client, "t8-f2@test.com")
    await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=h2)

    est_h = await auth_header_for(client, "t8-est@test.com")
    resp = await client.get(f"/v1/jobs/{job_id}/applications", headers=est_h)
    assert resp.status_code == 200
    assert resp.json()["total"] == 2

    # outro user não pode listar
    other_h = await auth_header_for(client, "t8-f1@test.com")
    resp2 = await client.get(f"/v1/jobs/{job_id}/applications", headers=other_h)
    assert resp2.status_code == 403


@pytest.mark.asyncio
async def test_list_my_applications(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="t9-est@test.com")
        await make_freelancer(session, email="t9-fl@test.com")
        cat = await make_skill_category(session)
        j1 = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        j2 = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        await session.commit()
        ids = (j1.id, j2.id)

    h = await auth_header_for(client, "t9-fl@test.com")
    for jid in ids:
        await client.post(f"/v1/jobs/{jid}/applications", json={}, headers=h)

    resp = await client.get("/v1/me/applications", headers=h)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2


@pytest.mark.asyncio
async def test_get_application_only_parties(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="t10-est@test.com")
        await make_freelancer(session, email="t10-fl@test.com")
        await make_freelancer(session, email="t10-outro@test.com")
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        await session.commit()
        job_id = job.id

    h_fl = await auth_header_for(client, "t10-fl@test.com")
    r = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=h_fl)
    aid = r.json()["id"]

    # Freelancer dono vê
    r1 = await client.get(f"/v1/applications/{aid}", headers=h_fl)
    assert r1.status_code == 200

    # Estabelecimento dono da vaga vê
    h_est = await auth_header_for(client, "t10-est@test.com")
    r2 = await client.get(f"/v1/applications/{aid}", headers=h_est)
    assert r2.status_code == 200

    # Outro freelancer não vê
    h_out = await auth_header_for(client, "t10-outro@test.com")
    r3 = await client.get(f"/v1/applications/{aid}", headers=h_out)
    assert r3.status_code == 403


@pytest.mark.asyncio
async def test_list_applications_status_filter(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="t11-est@test.com")
        fl, _ = await make_freelancer(session, email="t11-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        from tests.factories import make_application

        await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id, status="pending"
        )
        await session.commit()
        job_id = job.id

    est_h = await auth_header_for(client, "t11-est@test.com")
    r = await client.get(
        f"/v1/jobs/{job_id}/applications?status=pending", headers=est_h
    )
    assert r.status_code == 200
    assert r.json()["total"] == 1

    r2 = await client.get(
        f"/v1/jobs/{job_id}/applications?status=rejected", headers=est_h
    )
    assert r2.json()["total"] == 0
```

- [ ] **Step 5: Rodar testes (espera 11 totais no test_applications.py agora)**

```bash
uv run pytest tests/integration/test_applications.py -v
```

Expected: 11 passed.

- [ ] **Step 6: Lint + mypy**

```bash
uv run ruff check app/api/v1/applications app/domain/services/application_service.py app/domain/repositories/application_repository.py
uv run mypy app/api/v1/applications app/domain/services/application_service.py app/domain/repositories/application_repository.py
```

Expected: verdes.

- [ ] **Step 7: Commit**

```bash
git add app/api/v1/applications app/domain/services/application_service.py app/domain/repositories/application_repository.py tests/integration/test_applications.py
git commit -m "feat(sprint-3): list + get de applications (jobs/{id}/applications, me/applications, applications/{id})"
```

---

## Task 7: Application reject + withdraw

**Files:**
- Modify: `app/domain/repositories/application_repository.py`
- Modify: `app/domain/services/application_service.py`
- Modify: `app/api/v1/applications/router.py`
- Modify: `tests/integration/test_applications.py`

- [ ] **Step 1: Adicionar método de update no application_repository.py**

```python
    async def update_status(
        self,
        app_: Application,
        *,
        new_status: str,
        decided_at: "datetime | None" = None,
    ) -> Application:
        from datetime import UTC, datetime

        app_.status = new_status
        app_.decided_at = decided_at if decided_at is not None else datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(app_)
        return app_
```

Adicionar `from datetime import datetime` no topo do arquivo se ainda não tiver.

- [ ] **Step 2: Adicionar reject + withdraw em application_service.py**

```python
    async def reject(
        self, *, user_id: uuid.UUID, app_id: uuid.UUID
    ) -> ApplicationRead:
        from app.core.exceptions import (
            ApplicationNotPending,
            NotFoundError,
            PermissionDenied,
        )

        app_ = await self._repo.get_by_id(app_id)
        if app_ is None:
            raise NotFoundError("Candidatura não encontrada")
        job = await self._jobs.get_by_id(app_.job_posting_id)
        if job is None or job.establishment_id != user_id:
            raise PermissionDenied()
        if app_.status != "pending":
            raise ApplicationNotPending()

        app_ = await self._repo.update_status(app_, new_status="rejected")
        await self._notifications.emit(
            user_id=app_.freelancer_id,
            type="application.rejected",
            payload={
                "application_id": str(app_.id),
                "job_posting_id": str(app_.job_posting_id),
            },
        )
        return ApplicationRead.model_validate(app_)

    async def withdraw(
        self, *, user_id: uuid.UUID, app_id: uuid.UUID
    ) -> ApplicationRead:
        from app.core.exceptions import (
            ApplicationNotPending,
            NotFoundError,
            PermissionDenied,
        )

        app_ = await self._repo.get_by_id(app_id)
        if app_ is None:
            raise NotFoundError("Candidatura não encontrada")
        if app_.freelancer_id != user_id:
            raise PermissionDenied()
        if app_.status != "pending":
            raise ApplicationNotPending()

        app_ = await self._repo.update_status(app_, new_status="withdrawn")
        return ApplicationRead.model_validate(app_)
```

- [ ] **Step 3: Adicionar endpoints em router.py**

```python
@router.post(
    "/applications/{application_id}/reject",
    response_model=ApplicationRead,
    summary="Estabelecimento rejeita uma candidatura",
)
async def reject_application(
    application_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> ApplicationRead:
    return await ApplicationService(session).reject(
        user_id=user_id, app_id=application_id
    )


@router.post(
    "/applications/{application_id}/withdraw",
    response_model=ApplicationRead,
    summary="Freelancer retira a própria candidatura",
)
async def withdraw_application(
    application_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> ApplicationRead:
    return await ApplicationService(session).withdraw(
        user_id=user_id, app_id=application_id
    )
```

- [ ] **Step 4: Adicionar tests em tests/integration/test_applications.py**

```python
@pytest.mark.asyncio
async def test_reject_application_by_establishment(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="t12-est@test.com")
        fl, _ = await make_freelancer(session, email="t12-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        from tests.factories import make_application

        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = app_.id

    h = await auth_header_for(client, "t12-est@test.com")
    r = await client.post(f"/v1/applications/{aid}/reject", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    assert r.json()["decided_at"] is not None


@pytest.mark.asyncio
async def test_reject_by_non_owner_returns_403(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="t13-est@test.com")
        fl, _ = await make_freelancer(session, email="t13-fl@test.com")
        await make_freelancer(session, email="t13-outro@test.com")
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        from tests.factories import make_application
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = app_.id

    h = await auth_header_for(client, "t13-outro@test.com")
    r = await client.post(f"/v1/applications/{aid}/reject", headers=h)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_reject_non_pending_returns_409(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="t14-est@test.com")
        fl, _ = await make_freelancer(session, email="t14-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        from tests.factories import make_application
        app_ = await make_application(
            session,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            status="rejected",
        )
        await session.commit()
        aid = app_.id

    h = await auth_header_for(client, "t14-est@test.com")
    r = await client.post(f"/v1/applications/{aid}/reject", headers=h)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_withdraw_application_by_freelancer(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="t15-est@test.com")
        fl, _ = await make_freelancer(session, email="t15-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        from tests.factories import make_application
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = app_.id

    h = await auth_header_for(client, "t15-fl@test.com")
    r = await client.post(f"/v1/applications/{aid}/withdraw", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "withdrawn"


@pytest.mark.asyncio
async def test_withdraw_by_non_owner_returns_403(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="t16-est@test.com")
        fl, _ = await make_freelancer(session, email="t16-fl@test.com")
        await make_freelancer(session, email="t16-out@test.com")
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        from tests.factories import make_application
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = app_.id

    h = await auth_header_for(client, "t16-out@test.com")
    r = await client.post(f"/v1/applications/{aid}/withdraw", headers=h)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_reject_emits_notification(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="t17-est@test.com")
        fl, _ = await make_freelancer(session, email="t17-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        from tests.factories import make_application
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = app_.id

    h = await auth_header_for(client, "t17-est@test.com")
    await client.post(f"/v1/applications/{aid}/reject", headers=h)

    h_fl = await auth_header_for(client, "t17-fl@test.com")
    notif = await client.get("/v1/me/notifications", headers=h_fl)
    types = [n["type"] for n in notif.json()["items"]]
    assert "application.rejected" in types
```

- [ ] **Step 5: Rodar testes**

```bash
uv run pytest tests/integration/test_applications.py -v
```

Expected: 17 passed.

- [ ] **Step 6: Lint + mypy**

```bash
uv run ruff check app/api/v1/applications app/domain/services/application_service.py app/domain/repositories/application_repository.py
uv run mypy app/api/v1/applications app/domain/services/application_service.py app/domain/repositories/application_repository.py
```

Expected: verdes.

- [ ] **Step 7: Commit**

```bash
git add app/ tests/integration/test_applications.py
git commit -m "feat(sprint-3): reject + withdraw applications (com notification.rejected)"
```

---

## Task 8: Contracts module — list/get/cancel (sem accept)

**Files:**
- Create: `app/domain/schemas/contract.py`
- Create: `app/domain/repositories/contract_repository.py`
- Create: `app/domain/services/contract_service.py`
- Create: `app/api/v1/contracts/__init__.py`
- Create: `app/api/v1/contracts/router.py`
- Modify: `app/main.py`
- Create: `tests/integration/test_contracts.py`

- [ ] **Step 1: Escrever app/domain/schemas/contract.py**

```python
"""Schemas Pydantic de ServiceContract."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServiceContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    job_posting_id: uuid.UUID
    freelancer_id: uuid.UUID
    establishment_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    agreed_hourly_rate: Decimal | None
    agreed_total_pay: Decimal | None
    status: str
    cancelled_by: str | None
    cancelled_at: datetime | None
    cancel_reason: str | None
    no_show: bool
    created_at: datetime


class ServiceContractList(BaseModel):
    items: list[ServiceContractRead]
    total: int
    page: int
    page_size: int


class ContractCancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)
```

- [ ] **Step 2: Escrever app/domain/repositories/contract_repository.py**

```python
"""Repository de ServiceContract."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.service_contract import ServiceContract


class ContractRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        application_id: uuid.UUID,
        job_posting_id: uuid.UUID,
        freelancer_id: uuid.UUID,
        establishment_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
        agreed_hourly_rate,
        agreed_total_pay,
    ) -> ServiceContract:
        contract = ServiceContract(
            application_id=application_id,
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

    async def get_by_id(self, contract_id: uuid.UUID) -> ServiceContract | None:
        result = await self._session.execute(
            select(ServiceContract).where(ServiceContract.id == contract_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[ServiceContract], int]:
        base = select(ServiceContract).where(
            or_(
                ServiceContract.freelancer_id == user_id,
                ServiceContract.establishment_id == user_id,
            )
        )
        if status_filter is not None:
            base = base.where(ServiceContract.status == status_filter)
        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(ServiceContract.start_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def has_overlap(
        self,
        *,
        freelancer_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
        exclude_contract_id: uuid.UUID | None = None,
    ) -> bool:
        """True se freelancer já tem contrato (scheduled OU in_progress) sobreposto."""
        conditions = [
            ServiceContract.freelancer_id == freelancer_id,
            ServiceContract.status.in_(["scheduled", "in_progress"]),
            # Overlap: A.start < B.end AND A.end > B.start
            ServiceContract.start_at < end_at,
            ServiceContract.end_at > start_at,
        ]
        if exclude_contract_id is not None:
            conditions.append(ServiceContract.id != exclude_contract_id)
        result = await self._session.execute(
            select(ServiceContract.id).where(and_(*conditions)).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def cancel(
        self,
        contract: ServiceContract,
        *,
        cancelled_by: str,
        reason: str | None,
        no_show: bool,
    ) -> ServiceContract:
        contract.status = "cancelled"
        contract.cancelled_by = cancelled_by
        contract.cancelled_at = datetime.now(UTC)
        contract.cancel_reason = reason
        contract.no_show = no_show
        await self._session.flush()
        await self._session.refresh(contract)
        return contract
```

- [ ] **Step 3: Escrever app/domain/services/contract_service.py**

```python
"""Service de ServiceContract — list, get, cancel."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ContractAlreadyTerminal,
    NotFoundError,
    PermissionDenied,
)
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.job_posting import JobPosting
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.schemas.contract import (
    ContractCancelRequest,
    ServiceContractList,
    ServiceContractRead,
)
from app.domain.services.notification_service import NotificationService


class ContractService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ContractRepository(session)
        self._notifications = NotificationService(session)

    async def list_mine(
        self,
        *,
        user_id: uuid.UUID,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> ServiceContractList:
        items, total = await self._repo.list_for_user(
            user_id=user_id,
            status_filter=status_filter,
            page=page,
            page_size=page_size,
        )
        return ServiceContractList(
            items=[ServiceContractRead.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_by_id(
        self, *, user_id: uuid.UUID, contract_id: uuid.UUID
    ) -> ServiceContractRead:
        contract = await self._repo.get_by_id(contract_id)
        if contract is None:
            raise NotFoundError("Contrato não encontrado")
        if user_id not in (contract.freelancer_id, contract.establishment_id):
            raise PermissionDenied()
        return ServiceContractRead.model_validate(contract)

    async def cancel(
        self,
        *,
        user_id: uuid.UUID,
        contract_id: uuid.UUID,
        payload: ContractCancelRequest,
    ) -> ServiceContractRead:
        contract = await self._repo.get_by_id(contract_id)
        if contract is None:
            raise NotFoundError("Contrato não encontrado")
        if user_id not in (contract.freelancer_id, contract.establishment_id):
            raise PermissionDenied()
        if contract.status not in ("scheduled", "in_progress"):
            raise ContractAlreadyTerminal()

        is_freelancer = user_id == contract.freelancer_id
        cancelled_by = "freelancer" if is_freelancer else "establishment"

        now = datetime.now(UTC)
        # no_show só quando freelancer cancela <24h antes de start_at
        no_show = is_freelancer and (contract.start_at - now < timedelta(hours=24))

        contract = await self._repo.cancel(
            contract,
            cancelled_by=cancelled_by,
            reason=payload.reason,
            no_show=no_show,
        )

        # Penalidade no_show no profile do freelancer
        if no_show:
            await self._session.execute(
                update(FreelancerProfile)
                .where(FreelancerProfile.user_id == contract.freelancer_id)
                .values(no_show_count=FreelancerProfile.no_show_count + 1)
            )

        # Auto-reopen do job se faltar >2h pra start_at; senão job vira cancelled
        new_job_status = (
            "open" if (contract.start_at - now > timedelta(hours=2)) else "cancelled"
        )
        await self._session.execute(
            update(JobPosting)
            .where(
                JobPosting.id == contract.job_posting_id,
                JobPosting.status == "filled",
            )
            .values(status=new_job_status, updated_at=now)
        )

        # Notification pra outra parte
        other_party_id = (
            contract.establishment_id if is_freelancer else contract.freelancer_id
        )
        await self._notifications.emit(
            user_id=other_party_id,
            type="contract.cancelled_by_other_party",
            payload={
                "contract_id": str(contract.id),
                "job_posting_id": str(contract.job_posting_id),
                "cancelled_by": cancelled_by,
                "no_show": no_show,
            },
        )

        return ServiceContractRead.model_validate(contract)
```

- [ ] **Step 4: Escrever app/api/v1/contracts/__init__.py (vazio)**

```python
```

- [ ] **Step 5: Escrever app/api/v1/contracts/router.py**

```python
"""Endpoints /v1/me/contracts, /v1/contracts/{id}, /v1/contracts/{id}/cancel."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.contract import (
    ContractCancelRequest,
    ServiceContractList,
    ServiceContractRead,
)
from app.domain.services.contract_service import ContractService

router = APIRouter(tags=["contracts"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/me/contracts",
    response_model=ServiceContractList,
    summary="Lista contratos do user (como freelancer ou estabelecimento)",
)
async def list_my_contracts(
    user_id: UserIdDep,
    session: SessionDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ServiceContractList:
    return await ContractService(session).list_mine(
        user_id=user_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/contracts/{contract_id}",
    response_model=ServiceContractRead,
    summary="Detalhe de um contrato (apenas partes)",
)
async def get_contract(
    contract_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> ServiceContractRead:
    return await ContractService(session).get_by_id(
        user_id=user_id, contract_id=contract_id
    )


@router.post(
    "/contracts/{contract_id}/cancel",
    response_model=ServiceContractRead,
    summary="Cancela contrato (freelancer ou estabelecimento parte)",
)
async def cancel_contract(
    contract_id: uuid.UUID,
    payload: ContractCancelRequest,
    user_id: UserIdDep,
    session: SessionDep,
) -> ServiceContractRead:
    return await ContractService(session).cancel(
        user_id=user_id, contract_id=contract_id, payload=payload
    )
```

- [ ] **Step 6: Incluir router em app/main.py**

```python
from app.api.v1.contracts.router import router as contracts_router
# ...
    app.include_router(contracts_router, prefix="/v1")
```

- [ ] **Step 7: Escrever tests/integration/test_contracts.py**

```python
"""Testes de listagem, detalhe e cancelamento de ServiceContract."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from freezegun import freeze_time
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import async_session_factory
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.job_posting import JobPosting
from tests.factories import (
    auth_header_for,
    make_application,
    make_contract,
    make_establishment,
    make_freelancer,
    make_job,
    make_skill_category,
)


async def _setup_contract_scenario(*, days_until_start: int = 5, status: str = "scheduled"):
    async with async_session_factory() as session:
        est, _ = await make_establishment(
            session, email=f"c-est-{days_until_start}-{status}@test.com"
        )
        fl, _ = await make_freelancer(
            session, email=f"c-fl-{days_until_start}-{status}@test.com"
        )
        cat = await make_skill_category(session)
        start = datetime.now(UTC) + timedelta(days=days_until_start)
        job = await make_job(
            session,
            establishment_id=est.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start,
            end_at=start + timedelta(hours=4),
        )
        app_ = await make_application(
            session,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            status="accepted",
        )
        contract = await make_contract(
            session,
            application_id=app_.id,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            establishment_id=est.id,
            start_at=start,
            end_at=start + timedelta(hours=4),
            status=status,
        )
        await session.commit()
        return {
            "est_email": est.email,
            "fl_email": fl.email,
            "contract_id": contract.id,
            "job_id": job.id,
        }


@pytest.mark.asyncio
async def test_list_my_contracts_as_freelancer(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario()
    h = await auth_header_for(client, ctx["fl_email"])
    r = await client.get("/v1/me/contracts", headers=h)
    assert r.status_code == 200
    assert r.json()["total"] == 1


@pytest.mark.asyncio
async def test_list_my_contracts_as_establishment(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario()
    h = await auth_header_for(client, ctx["est_email"])
    r = await client.get("/v1/me/contracts", headers=h)
    assert r.status_code == 200
    assert r.json()["total"] == 1


@pytest.mark.asyncio
async def test_get_contract_third_party_403(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario()
    async with async_session_factory() as session:
        await make_freelancer(session, email="c-third@test.com")
        await session.commit()
    h = await auth_header_for(client, "c-third@test.com")
    r = await client.get(f"/v1/contracts/{ctx['contract_id']}", headers=h)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_cancel_by_freelancer_far_from_start_no_no_show(client: AsyncClient) -> None:
    """Cancel pelo freelancer com >24h até start_at → no_show=false, counter intacto."""
    ctx = await _setup_contract_scenario(days_until_start=5)
    h = await auth_header_for(client, ctx["fl_email"])
    r = await client.post(
        f"/v1/contracts/{ctx['contract_id']}/cancel",
        json={"reason": "imprevisto"},
        headers=h,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "cancelled"
    assert body["cancelled_by"] == "freelancer"
    assert body["no_show"] is False

    async with async_session_factory() as session:
        from app.domain.repositories.user_repository import UserRepository
        fl_user = await UserRepository(session).get_by_email(ctx["fl_email"])
        assert fl_user is not None
        row = await session.execute(
            select(FreelancerProfile).where(FreelancerProfile.user_id == fl_user.id)
        )
        profile = row.scalar_one()
        assert profile.no_show_count == 0


@pytest.mark.asyncio
async def test_cancel_by_freelancer_under_24h_marks_no_show(client: AsyncClient) -> None:
    """Cancel <24h pelo freelancer → no_show=true, counter++."""
    # Setup com start em 5 dias, depois congela o tempo a 23h antes do start.
    ctx = await _setup_contract_scenario(days_until_start=5)
    real_start = datetime.now(UTC) + timedelta(days=5)
    frozen_now = real_start - timedelta(hours=23)
    with freeze_time(frozen_now):
        h = await auth_header_for(client, ctx["fl_email"])
        r = await client.post(
            f"/v1/contracts/{ctx['contract_id']}/cancel",
            json={"reason": "doente"},
            headers=h,
        )
    assert r.status_code == 200
    body = r.json()
    assert body["no_show"] is True

    async with async_session_factory() as session:
        from app.domain.repositories.user_repository import UserRepository
        fl_user = await UserRepository(session).get_by_email(ctx["fl_email"])
        assert fl_user is not None
        row = await session.execute(
            select(FreelancerProfile).where(FreelancerProfile.user_id == fl_user.id)
        )
        profile = row.scalar_one()
        assert profile.no_show_count == 1


@pytest.mark.asyncio
async def test_cancel_by_establishment_no_no_show(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario(days_until_start=5)
    h = await auth_header_for(client, ctx["est_email"])
    r = await client.post(
        f"/v1/contracts/{ctx['contract_id']}/cancel",
        json={"reason": "evento adiado"},
        headers=h,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["cancelled_by"] == "establishment"
    assert body["no_show"] is False


@pytest.mark.asyncio
async def test_cancel_far_from_start_reopens_job(client: AsyncClient) -> None:
    """Cancel com >2h até start_at → job volta a open."""
    ctx = await _setup_contract_scenario(days_until_start=5)
    h = await auth_header_for(client, ctx["fl_email"])
    await client.post(
        f"/v1/contracts/{ctx['contract_id']}/cancel",
        json={},
        headers=h,
    )
    async with async_session_factory() as session:
        row = await session.execute(
            select(JobPosting).where(JobPosting.id == ctx["job_id"])
        )
        job = row.scalar_one()
        assert job.status == "open"


@pytest.mark.asyncio
async def test_cancel_close_to_start_cancels_job(client: AsyncClient) -> None:
    """Cancel com ≤2h até start_at → job vira cancelled."""
    ctx = await _setup_contract_scenario(days_until_start=5)
    real_start = datetime.now(UTC) + timedelta(days=5)
    frozen_now = real_start - timedelta(hours=1)
    with freeze_time(frozen_now):
        h = await auth_header_for(client, ctx["fl_email"])
        await client.post(
            f"/v1/contracts/{ctx['contract_id']}/cancel",
            json={},
            headers=h,
        )
    async with async_session_factory() as session:
        row = await session.execute(
            select(JobPosting).where(JobPosting.id == ctx["job_id"])
        )
        job = row.scalar_one()
        assert job.status == "cancelled"


@pytest.mark.asyncio
async def test_cancel_terminal_returns_409(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario(status="completed")
    h = await auth_header_for(client, ctx["fl_email"])
    r = await client.post(
        f"/v1/contracts/{ctx['contract_id']}/cancel", json={}, headers=h
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_cancel_emits_notification_to_other_party(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario(days_until_start=5)
    h = await auth_header_for(client, ctx["fl_email"])
    await client.post(
        f"/v1/contracts/{ctx['contract_id']}/cancel", json={}, headers=h
    )
    # Establishment recebe notification
    h_est = await auth_header_for(client, ctx["est_email"])
    r = await client.get("/v1/me/notifications", headers=h_est)
    types = [n["type"] for n in r.json()["items"]]
    assert "contract.cancelled_by_other_party" in types
```

- [ ] **Step 8: Rodar testes**

```bash
uv run pytest tests/integration/test_contracts.py -v
```

Expected: 10 passed.

- [ ] **Step 9: Lint + mypy**

```bash
uv run ruff check app/api/v1/contracts app/domain/schemas/contract.py app/domain/repositories/contract_repository.py app/domain/services/contract_service.py
uv run mypy app/api/v1/contracts app/domain/schemas/contract.py app/domain/repositories/contract_repository.py app/domain/services/contract_service.py
```

Expected: verdes.

- [ ] **Step 10: Commit**

```bash
git add app/ tests/integration/test_contracts.py
git commit -m "feat(sprint-3): contracts module - list/get/cancel com no-show + auto-reopen"
```

---

## Task 9: Application ACCEPT — transação completa

**Files:**
- Modify: `app/domain/services/application_service.py`
- Modify: `app/domain/repositories/application_repository.py` (helper queries)
- Modify: `app/api/v1/applications/router.py`
- Modify: `app/core/database.py` (talvez `session_factory_repeatable_read` helper — verificar antes; provavelmente set isolation a nível de session)
- Create: `tests/integration/test_application_accept.py`

- [ ] **Step 1: Adicionar query helper em application_repository.py**

```python
    async def list_pending_for_job_except(
        self, *, job_posting_id: uuid.UUID, except_id: uuid.UUID
    ) -> "list[Application]":
        from sqlalchemy import select

        result = await self._session.execute(
            select(Application).where(
                Application.job_posting_id == job_posting_id,
                Application.status == "pending",
                Application.id != except_id,
            )
        )
        return list(result.scalars().all())
```

- [ ] **Step 2: Adicionar método `accept` em application_service.py**

```python
    async def accept(
        self, *, user_id: uuid.UUID, app_id: uuid.UUID
    ) -> ApplicationRead:
        from datetime import UTC, datetime

        from sqlalchemy import update

        from app.core.exceptions import (
            ApplicationNotPending,
            FreelancerOverlap,
            JobNotOpen,
            NotFoundError,
            PermissionDenied,
        )
        from app.domain.models.application import Application
        from app.domain.models.job_posting import JobPosting
        from app.domain.repositories.contract_repository import ContractRepository

        contracts_repo = ContractRepository(self._session)

        # Lock da application
        app_ = await self._repo.get_by_id(app_id)
        if app_ is None:
            raise NotFoundError("Candidatura não encontrada")

        job = await self._jobs.get_by_id(app_.job_posting_id)
        if job is None:
            raise NotFoundError("Vaga não encontrada")
        if job.establishment_id != user_id:
            raise PermissionDenied()
        if app_.status != "pending":
            raise ApplicationNotPending()
        if job.status != "open":
            raise JobNotOpen()

        # Overlap check
        has = await contracts_repo.has_overlap(
            freelancer_id=app_.freelancer_id,
            start_at=job.start_at,
            end_at=job.end_at,
        )
        if has:
            raise FreelancerOverlap()

        now = datetime.now(UTC)

        # 1) Marca esta application como accepted
        app_ = await self._repo.update_status(
            app_, new_status="accepted", decided_at=now
        )

        # 2) Cascade-reject das demais pending da mesma vaga
        pending_others = await self._repo.list_pending_for_job_except(
            job_posting_id=job.id, except_id=app_.id
        )
        for other in pending_others:
            await self._repo.update_status(
                other, new_status="rejected", decided_at=now
            )

        # 3) Job → filled
        await self._session.execute(
            update(JobPosting)
            .where(JobPosting.id == job.id)
            .values(status="filled", updated_at=now)
        )

        # 4) Cria ServiceContract
        contract = await contracts_repo.create(
            application_id=app_.id,
            job_posting_id=job.id,
            freelancer_id=app_.freelancer_id,
            establishment_id=job.establishment_id,
            start_at=job.start_at,
            end_at=job.end_at,
            agreed_hourly_rate=job.hourly_rate,
            agreed_total_pay=job.total_pay,
        )

        # 5) Notifications
        await self._notifications.emit(
            user_id=app_.freelancer_id,
            type="application.accepted",
            payload={
                "application_id": str(app_.id),
                "job_posting_id": str(job.id),
                "contract_id": str(contract.id),
            },
        )
        for other in pending_others:
            await self._notifications.emit(
                user_id=other.freelancer_id,
                type="application.rejected",
                payload={
                    "application_id": str(other.id),
                    "job_posting_id": str(job.id),
                },
            )

        return ApplicationRead.model_validate(app_)
```

- [ ] **Step 3: Adicionar endpoint accept em router.py**

```python
@router.post(
    "/applications/{application_id}/accept",
    response_model=ApplicationRead,
    summary="Estabelecimento aceita uma candidatura (cria contrato)",
)
async def accept_application(
    application_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> ApplicationRead:
    return await ApplicationService(session).accept(
        user_id=user_id, app_id=application_id
    )
```

- [ ] **Step 4: Escrever tests/integration/test_application_accept.py**

```python
"""Testes do accept de application — caso crítico transacional do Fluxo A."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import async_session_factory
from app.domain.models.application import Application
from app.domain.models.job_posting import JobPosting
from app.domain.models.service_contract import ServiceContract
from tests.factories import (
    auth_header_for,
    make_application,
    make_contract,
    make_establishment,
    make_freelancer,
    make_job,
    make_skill_category,
)


async def _three_freelancers_apply(prefix: str):
    """Setup: 1 estabelecimento, 3 freelancers, 1 job open, 3 applications pending."""
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email=f"{prefix}-est@test.com")
        fls = []
        for i in range(3):
            u, _ = await make_freelancer(session, email=f"{prefix}-f{i}@test.com")
            fls.append(u)
        cat = await make_skill_category(session)
        start = datetime.now(UTC) + timedelta(days=2)
        job = await make_job(
            session,
            establishment_id=est.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start,
            end_at=start + timedelta(hours=5),
            hourly_rate=Decimal("40.00"),
        )
        apps = []
        for fl in fls:
            a = await make_application(
                session, job_posting_id=job.id, freelancer_id=fl.id
            )
            apps.append(a)
        await session.commit()
        return {
            "est_email": est.email,
            "fl_emails": [u.email for u in fls],
            "job_id": job.id,
            "app_ids": [a.id for a in apps],
        }


@pytest.mark.asyncio
async def test_accept_happy_path_creates_contract(client: AsyncClient) -> None:
    ctx = await _three_freelancers_apply("acc1")
    h = await auth_header_for(client, ctx["est_email"])
    r = await client.post(
        f"/v1/applications/{ctx['app_ids'][0]}/accept", headers=h
    )
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"

    async with async_session_factory() as session:
        # Job → filled
        job = (
            await session.execute(select(JobPosting).where(JobPosting.id == ctx["job_id"]))
        ).scalar_one()
        assert job.status == "filled"
        # Outras 2 applications → rejected
        rows = (
            await session.execute(select(Application).where(Application.job_posting_id == ctx["job_id"]))
        ).scalars().all()
        statuses = sorted([a.status for a in rows])
        assert statuses == ["accepted", "rejected", "rejected"]
        # ServiceContract criado
        contract = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.application_id == ctx["app_ids"][0]
                )
            )
        ).scalar_one()
        assert contract.status == "scheduled"
        assert contract.agreed_hourly_rate == Decimal("40.00")


@pytest.mark.asyncio
async def test_accept_with_single_pending_no_cascade(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="acc2-est@test.com")
        fl, _ = await make_freelancer(session, email="acc2-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est.id, skill_category_id=cat.id, status="open"
        )
        a = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = a.id

    h = await auth_header_for(client, "acc2-est@test.com")
    r = await client.post(f"/v1/applications/{aid}/accept", headers=h)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_accept_non_pending_returns_409(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="acc3-est@test.com")
        fl, _ = await make_freelancer(session, email="acc3-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est.id, skill_category_id=cat.id, status="open"
        )
        a = await make_application(
            session,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            status="rejected",
        )
        await session.commit()
        aid = a.id

    h = await auth_header_for(client, "acc3-est@test.com")
    r = await client.post(f"/v1/applications/{aid}/accept", headers=h)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_accept_by_non_owner_returns_403(client: AsyncClient) -> None:
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="acc4-est@test.com")
        await make_establishment(session, email="acc4-out@test.com")
        fl, _ = await make_freelancer(session, email="acc4-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est.id, skill_category_id=cat.id, status="open"
        )
        a = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = a.id

    h = await auth_header_for(client, "acc4-out@test.com")
    r = await client.post(f"/v1/applications/{aid}/accept", headers=h)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_accept_blocked_by_overlap_scheduled(client: AsyncClient) -> None:
    """Freelancer já tem contrato scheduled no mesmo intervalo → 409."""
    async with async_session_factory() as session:
        est_a, _ = await make_establishment(session, email="acc5-esta@test.com")
        est_b, _ = await make_establishment(session, email="acc5-estb@test.com")
        fl, _ = await make_freelancer(session, email="acc5-fl@test.com")
        cat = await make_skill_category(session)
        start = datetime.now(UTC) + timedelta(days=3)
        end = start + timedelta(hours=4)

        # Job A (já tem contrato scheduled)
        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start,
            end_at=end,
        )
        app_a = await make_application(
            session,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            status="accepted",
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start,
            end_at=end,
            status="scheduled",
        )

        # Job B (mesma janela, accept vai falhar)
        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start,
            end_at=end,
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        b_id = app_b.id

    h = await auth_header_for(client, "acc5-estb@test.com")
    r = await client.post(f"/v1/applications/{b_id}/accept", headers=h)
    assert r.status_code == 409
    assert "sobreposto" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_accept_blocked_by_overlap_in_progress(client: AsyncClient) -> None:
    """Contrato in_progress também bloqueia accept."""
    async with async_session_factory() as session:
        est_a, _ = await make_establishment(session, email="acc6-esta@test.com")
        est_b, _ = await make_establishment(session, email="acc6-estb@test.com")
        fl, _ = await make_freelancer(session, email="acc6-fl@test.com")
        cat = await make_skill_category(session)
        start_a = datetime.now(UTC) - timedelta(hours=1)
        end_a = start_a + timedelta(hours=4)
        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start_a,
            end_at=end_a,
        )
        app_a = await make_application(
            session, job_posting_id=job_a.id, freelancer_id=fl.id, status="accepted"
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start_a,
            end_at=end_a,
            status="in_progress",
        )
        # Job B sobrepondo
        start_b = start_a + timedelta(hours=1)
        end_b = start_b + timedelta(hours=2)
        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start_b,
            end_at=end_b,
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        bid = app_b.id

    h = await auth_header_for(client, "acc6-estb@test.com")
    r = await client.post(f"/v1/applications/{bid}/accept", headers=h)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_accept_allows_overlap_with_cancelled_contract(client: AsyncClient) -> None:
    """Contrato cancelled no intervalo NÃO bloqueia."""
    async with async_session_factory() as session:
        est_a, _ = await make_establishment(session, email="acc7-esta@test.com")
        est_b, _ = await make_establishment(session, email="acc7-estb@test.com")
        fl, _ = await make_freelancer(session, email="acc7-fl@test.com")
        cat = await make_skill_category(session)
        start = datetime.now(UTC) + timedelta(days=3)
        end = start + timedelta(hours=4)
        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="cancelled",
            start_at=start,
            end_at=end,
        )
        app_a = await make_application(
            session, job_posting_id=job_a.id, freelancer_id=fl.id, status="accepted"
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start,
            end_at=end,
            status="cancelled",
        )
        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start,
            end_at=end,
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        bid = app_b.id

    h = await auth_header_for(client, "acc7-estb@test.com")
    r = await client.post(f"/v1/applications/{bid}/accept", headers=h)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_accept_allows_overlap_with_completed_contract(client: AsyncClient) -> None:
    """Contrato completed no intervalo NÃO bloqueia (raro, mas válido)."""
    async with async_session_factory() as session:
        est_a, _ = await make_establishment(session, email="acc8-esta@test.com")
        est_b, _ = await make_establishment(session, email="acc8-estb@test.com")
        fl, _ = await make_freelancer(session, email="acc8-fl@test.com")
        cat = await make_skill_category(session)
        start = datetime.now(UTC) + timedelta(days=3)
        end = start + timedelta(hours=4)
        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="completed",
            start_at=start,
            end_at=end,
        )
        app_a = await make_application(
            session, job_posting_id=job_a.id, freelancer_id=fl.id, status="accepted"
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start,
            end_at=end,
            status="completed",
        )
        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start,
            end_at=end,
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        bid = app_b.id

    h = await auth_header_for(client, "acc8-estb@test.com")
    r = await client.post(f"/v1/applications/{bid}/accept", headers=h)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_accept_partial_overlap_borders(client: AsyncClient) -> None:
    """Job B começa antes do A terminar → overlap detectado."""
    async with async_session_factory() as session:
        est_a, _ = await make_establishment(session, email="acc9-esta@test.com")
        est_b, _ = await make_establishment(session, email="acc9-estb@test.com")
        fl, _ = await make_freelancer(session, email="acc9-fl@test.com")
        cat = await make_skill_category(session)
        start_a = datetime.now(UTC) + timedelta(days=3)
        end_a = start_a + timedelta(hours=4)
        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start_a,
            end_at=end_a,
        )
        app_a = await make_application(
            session, job_posting_id=job_a.id, freelancer_id=fl.id, status="accepted"
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start_a,
            end_at=end_a,
            status="scheduled",
        )
        # B começa 1h antes de A terminar → 1h de overlap
        start_b = end_a - timedelta(hours=1)
        end_b = start_b + timedelta(hours=3)
        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start_b,
            end_at=end_b,
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        bid = app_b.id

    h = await auth_header_for(client, "acc9-estb@test.com")
    r = await client.post(f"/v1/applications/{bid}/accept", headers=h)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_accept_no_overlap_adjacent(client: AsyncClient) -> None:
    """Job B começa exatamente quando A termina → SEM overlap (intervalo half-open)."""
    async with async_session_factory() as session:
        est_a, _ = await make_establishment(session, email="acc10-esta@test.com")
        est_b, _ = await make_establishment(session, email="acc10-estb@test.com")
        fl, _ = await make_freelancer(session, email="acc10-fl@test.com")
        cat = await make_skill_category(session)
        start_a = datetime.now(UTC) + timedelta(days=3)
        end_a = start_a + timedelta(hours=4)
        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start_a,
            end_at=end_a,
        )
        app_a = await make_application(
            session, job_posting_id=job_a.id, freelancer_id=fl.id, status="accepted"
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start_a,
            end_at=end_a,
            status="scheduled",
        )
        # B começa exatamente em end_a — sem overlap
        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=end_a,
            end_at=end_a + timedelta(hours=3),
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        bid = app_b.id

    h = await auth_header_for(client, "acc10-estb@test.com")
    r = await client.post(f"/v1/applications/{bid}/accept", headers=h)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_accept_emits_notifications(client: AsyncClient) -> None:
    """Accept gera 1 application.accepted + N application.rejected."""
    ctx = await _three_freelancers_apply("acc11")
    h_est = await auth_header_for(client, ctx["est_email"])
    await client.post(f"/v1/applications/{ctx['app_ids'][0]}/accept", headers=h_est)

    # Vencedor
    h_w = await auth_header_for(client, ctx["fl_emails"][0])
    r_w = await client.get("/v1/me/notifications", headers=h_w)
    types_w = [n["type"] for n in r_w.json()["items"]]
    assert "application.accepted" in types_w

    # Perdedores
    for email in ctx["fl_emails"][1:]:
        h_l = await auth_header_for(client, email)
        r_l = await client.get("/v1/me/notifications", headers=h_l)
        types_l = [n["type"] for n in r_l.json()["items"]]
        assert "application.rejected" in types_l


@pytest.mark.asyncio
async def test_accept_copies_pay_from_job(client: AsyncClient) -> None:
    """Contract.agreed_hourly_rate e agreed_total_pay vêm do job."""
    async with async_session_factory() as session:
        est, _ = await make_establishment(session, email="acc12-est@test.com")
        fl, _ = await make_freelancer(session, email="acc12-fl@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session,
            establishment_id=est.id,
            skill_category_id=cat.id,
            status="open",
            hourly_rate=None,
            total_pay=Decimal("250.00"),
        )
        a = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = a.id

    h = await auth_header_for(client, "acc12-est@test.com")
    r = await client.post(f"/v1/applications/{aid}/accept", headers=h)
    assert r.status_code == 200

    async with async_session_factory() as session:
        c = (
            await session.execute(
                select(ServiceContract).where(ServiceContract.application_id == aid)
            )
        ).scalar_one()
        assert c.agreed_total_pay == Decimal("250.00")
        assert c.agreed_hourly_rate is None
```

- [ ] **Step 5: Rodar testes do accept**

```bash
uv run pytest tests/integration/test_application_accept.py -v
```

Expected: 12 passed.

- [ ] **Step 6: Lint + mypy**

```bash
uv run ruff check app/domain/services/application_service.py app/domain/repositories/application_repository.py
uv run mypy app/domain/services/application_service.py app/domain/repositories/application_repository.py
```

Expected: verdes.

- [ ] **Step 7: Commit**

```bash
git add app/ tests/integration/test_application_accept.py
git commit -m "feat(sprint-3): application accept (transacao com cascade reject + overlap + contract + notifications)"
```

---

## Task 10: Cron ARQ `advance_contract_lifecycle`

**Files:**
- Modify: `app/workers/tasks.py`
- Modify: `app/workers/arq_worker.py`
- Create: `tests/integration/test_cron_lifecycle.py`

- [ ] **Step 1: Adicionar `advance_contract_lifecycle` em app/workers/tasks.py**

Adicionar ao arquivo existente:

```python
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update

from app.core.database import async_session_factory
from app.core.logging import get_logger
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.job_posting import JobPosting
from app.domain.models.service_contract import ServiceContract


async def advance_contract_lifecycle(_ctx: dict[str, Any]) -> dict[str, int]:
    """Cron 5min — avança contratos scheduled→in_progress→completed.

    Idempotente. Usa now() do DB para evitar drift entre app e DB.
    Side effects do completed:
      - FreelancerProfile.completed_contracts_count++
      - JobPosting filled → completed
    """
    log = get_logger("arq.contract_lifecycle")
    started = 0
    completed_ids: list[tuple[str, str]] = []
    async with async_session_factory() as session:
        async with session.begin():
            # scheduled → in_progress (start_at <= now < end_at)
            r1 = await session.execute(
                update(ServiceContract)
                .where(
                    ServiceContract.status == "scheduled",
                    ServiceContract.start_at <= func.now(),
                    ServiceContract.end_at > func.now(),
                )
                .values(status="in_progress", updated_at=func.now())
                .returning(ServiceContract.id)
            )
            started = len(r1.all())

            # qualquer scheduled/in_progress com end_at <= now → completed
            r2 = await session.execute(
                update(ServiceContract)
                .where(
                    ServiceContract.status.in_(["scheduled", "in_progress"]),
                    ServiceContract.end_at <= func.now(),
                )
                .values(status="completed", updated_at=func.now())
                .returning(
                    ServiceContract.id,
                    ServiceContract.freelancer_id,
                    ServiceContract.job_posting_id,
                )
            )
            for row in r2.all():
                completed_ids.append((str(row[0]), str(row[2])))
                # FreelancerProfile counter
                await session.execute(
                    update(FreelancerProfile)
                    .where(FreelancerProfile.user_id == row[1])
                    .values(
                        completed_contracts_count=(
                            FreelancerProfile.completed_contracts_count + 1
                        )
                    )
                )
                # Job filled → completed
                await session.execute(
                    update(JobPosting)
                    .where(
                        JobPosting.id == row[2],
                        JobPosting.status == "filled",
                    )
                    .values(status="completed", updated_at=func.now())
                )

    log.info(
        "contract_lifecycle.tick", started=started, completed=len(completed_ids)
    )
    return {"started": started, "completed": len(completed_ids)}
```

- [ ] **Step 2: Registrar cron em app/workers/arq_worker.py**

Modificar `arq_worker.py`:

```python
from app.workers.tasks import advance_contract_lifecycle, purge_inactive_users

# ...

class WorkerSettings:
    functions: ClassVar[list[Any]] = [purge_inactive_users, advance_contract_lifecycle]
    cron_jobs: ClassVar[list[Any]] = [
        cron(purge_inactive_users, hour={2}, minute={0}),  # type: ignore[arg-type]
        cron(  # a cada 5min
            advance_contract_lifecycle,
            minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55},
        ),  # type: ignore[arg-type]
    ]
    redis_settings = _redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 300
    max_jobs = 10
```

- [ ] **Step 3: Escrever tests/integration/test_cron_lifecycle.py**

```python
"""Testes do cron advance_contract_lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.database import async_session_factory
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.job_posting import JobPosting
from app.domain.models.service_contract import ServiceContract
from app.workers.tasks import advance_contract_lifecycle
from tests.factories import (
    make_application,
    make_contract,
    make_establishment,
    make_freelancer,
    make_job,
    make_skill_category,
)


async def _setup_contract(*, start_offset_hours: float, end_offset_hours: float, status: str = "scheduled"):
    now = datetime.now(UTC)
    start = now + timedelta(hours=start_offset_hours)
    end = now + timedelta(hours=end_offset_hours)
    async with async_session_factory() as session:
        suffix = f"{start_offset_hours}-{end_offset_hours}-{status}"
        est, _ = await make_establishment(session, email=f"cron-est-{suffix}@test.com")
        fl, _ = await make_freelancer(session, email=f"cron-fl-{suffix}@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session,
            establishment_id=est.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start,
            end_at=end,
        )
        a = await make_application(
            session,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            status="accepted",
        )
        c = await make_contract(
            session,
            application_id=a.id,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            establishment_id=est.id,
            start_at=start,
            end_at=end,
            status=status,
        )
        await session.commit()
        return {
            "contract_id": c.id,
            "job_id": job.id,
            "fl_id": fl.id,
        }


@pytest.mark.asyncio
async def test_scheduled_to_in_progress():
    """Contrato com start_at no passado e end_at no futuro → in_progress."""
    ctx = await _setup_contract(start_offset_hours=-1, end_offset_hours=3)
    res = await advance_contract_lifecycle({})
    assert res["started"] >= 1
    async with async_session_factory() as session:
        c = (
            await session.execute(select(ServiceContract).where(ServiceContract.id == ctx["contract_id"]))
        ).scalar_one()
        assert c.status == "in_progress"


@pytest.mark.asyncio
async def test_in_progress_to_completed():
    ctx = await _setup_contract(
        start_offset_hours=-5, end_offset_hours=-1, status="in_progress"
    )
    res = await advance_contract_lifecycle({})
    assert res["completed"] >= 1
    async with async_session_factory() as session:
        c = (
            await session.execute(select(ServiceContract).where(ServiceContract.id == ctx["contract_id"]))
        ).scalar_one()
        assert c.status == "completed"


@pytest.mark.asyncio
async def test_scheduled_skips_directly_to_completed_when_recovery():
    """Cron parou; contrato scheduled com end_at já passado → vai direto pra completed."""
    ctx = await _setup_contract(start_offset_hours=-10, end_offset_hours=-5)
    await advance_contract_lifecycle({})
    async with async_session_factory() as session:
        c = (
            await session.execute(select(ServiceContract).where(ServiceContract.id == ctx["contract_id"]))
        ).scalar_one()
        assert c.status == "completed"


@pytest.mark.asyncio
async def test_completed_increments_counter():
    ctx = await _setup_contract(
        start_offset_hours=-5, end_offset_hours=-1, status="in_progress"
    )
    await advance_contract_lifecycle({})
    async with async_session_factory() as session:
        prof = (
            await session.execute(select(FreelancerProfile).where(FreelancerProfile.user_id == ctx["fl_id"]))
        ).scalar_one()
        assert prof.completed_contracts_count == 1


@pytest.mark.asyncio
async def test_completed_marks_job_completed():
    ctx = await _setup_contract(
        start_offset_hours=-5, end_offset_hours=-1, status="in_progress"
    )
    await advance_contract_lifecycle({})
    async with async_session_factory() as session:
        job = (
            await session.execute(select(JobPosting).where(JobPosting.id == ctx["job_id"]))
        ).scalar_one()
        assert job.status == "completed"


@pytest.mark.asyncio
async def test_idempotent_run_twice():
    """2 execuções seguidas — segunda não duplica side-effects."""
    ctx = await _setup_contract(
        start_offset_hours=-5, end_offset_hours=-1, status="in_progress"
    )
    await advance_contract_lifecycle({})
    res2 = await advance_contract_lifecycle({})
    assert res2["completed"] == 0
    async with async_session_factory() as session:
        prof = (
            await session.execute(select(FreelancerProfile).where(FreelancerProfile.user_id == ctx["fl_id"]))
        ).scalar_one()
        assert prof.completed_contracts_count == 1


@pytest.mark.asyncio
async def test_cancelled_ignored():
    """Contrato cancelled NÃO é tocado pelo cron."""
    ctx = await _setup_contract(
        start_offset_hours=-5, end_offset_hours=-1, status="scheduled"
    )
    # Marca como cancelled manualmente antes do cron
    async with async_session_factory() as session:
        c = (
            await session.execute(select(ServiceContract).where(ServiceContract.id == ctx["contract_id"]))
        ).scalar_one()
        c.status = "cancelled"
        c.cancelled_by = "establishment"
        c.cancelled_at = datetime.now(UTC)
        await session.commit()

    await advance_contract_lifecycle({})

    async with async_session_factory() as session:
        c2 = (
            await session.execute(select(ServiceContract).where(ServiceContract.id == ctx["contract_id"]))
        ).scalar_one()
        assert c2.status == "cancelled"
```

- [ ] **Step 4: Rodar testes do cron**

```bash
uv run pytest tests/integration/test_cron_lifecycle.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Lint + mypy**

```bash
uv run ruff check app/workers/tasks.py app/workers/arq_worker.py
uv run mypy app/workers/tasks.py app/workers/arq_worker.py
```

Expected: verdes.

- [ ] **Step 6: Commit**

```bash
git add app/workers/ tests/integration/test_cron_lifecycle.py
git commit -m "feat(sprint-3): cron ARQ advance_contract_lifecycle (5min) + 7 tests"
```

---

## Task 11: Verificação final + CLAUDE.md + deploy + merge

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Rodar suite completa**

```bash
uv run ruff check app tests
uv run mypy app
uv run pytest -v
```

Expected: tudo verde. ~100 tests passando (46 antigos + 17 + 10 + 12 + 7 + 6 = ~98 novos no Sprint 3).

- [ ] **Step 2: Aplicar migration na VPS**

```bash
ssh root@93.127.211.7 -t "docker exec -i $(docker ps -qf name=freela_food_postgres | head -1) psql -U freela -d freela_food" < alembic/versions/004_applications_contracts_notifications.py
```

OU, se a API estiver containerizada com Alembic instalado:

```bash
ssh root@93.127.211.7 -t "docker exec freela-food-api uv run alembic upgrade head"
```

Verificar manualmente quais tabelas e qual abordagem aplica (igual fizemos na Sprint 2).

Expected: `Running upgrade 003_jobs_and_geo -> 004_apps_contracts_notif`.

- [ ] **Step 3: Reiniciar ARQ worker na VPS (pra cron novo entrar)**

```bash
ssh root@93.127.211.7 docker service update --force freela_food_arq_worker
```

Verificar nome real do service (ajustar se diferente). Conferir logs:

```bash
ssh root@93.127.211.7 docker service logs --tail 20 freela_food_arq_worker
```

Expected: `worker.startup` recente.

- [ ] **Step 4: Atualizar seção 11 do CLAUDE.md**

Marcar Sprint 3 como concluída na seção Roadmap macro. Editar o item correspondente:

```markdown
- **Sprint 3**: Fluxo A end-to-end. ✅ (commit `<hash do merge>`, ~52+ tests)
```

E mudar o "← *você está aqui*" pra Sprint 4.

- [ ] **Step 5: Commit final + push**

```bash
git add CLAUDE.md
git commit -m "docs: marcar Sprint 3 como concluida no roadmap"
git push -u origin feat/sprint-3-flow-a
```

- [ ] **Step 6: Merge em main (estratégia Sprint 2 — merge commit)**

```bash
git checkout main
git merge feat/sprint-3-flow-a -m "merge: sprint 3 - Fluxo A (applications + contracts + cron + notifications, ~52 testes verdes)"
git push origin main
```

- [ ] **Step 7: Smoke E2E mínimo na VPS (manual, opcional)**

Sequência via curl/httpie pra ter confiança que o fluxo está vivo:

```bash
# registra freelancer + estabelecimento, cria perfis, cria vaga,
# candidata, aceita, checa contrato e notifications, cancela
```

Documentar em comentário no commit se rodar.

---

## Self-review checklist (já executado durante a escrita)

**Spec coverage:**
- [x] Migration 004 → Task 2
- [x] Models → Task 3
- [x] Notifications → Task 4
- [x] Applications create → Task 5
- [x] Applications list/get → Task 6
- [x] Applications reject/withdraw → Task 7
- [x] Contracts list/get/cancel + no-show + auto-reopen → Task 8
- [x] Application accept (transacional) → Task 9
- [x] Cron ARQ → Task 10
- [x] Deploy/merge/CLAUDE.md → Task 11
- [x] Audit log: NOTA — usar o decorator/helper de `app/utils/audit.py` em cada mutação dos services. Pelo padrão da Sprint 2, isso já é responsabilidade da utility e a chamada explícita pode ou não ser necessária; o agente executando deve verificar como Sprint 1/2 fez (provavelmente decorator) e replicar nas mutações novas.

**Placeholders:**
- [x] Sem TBDs, TODOs, "implement later", ou steps sem código.
- [x] Cada step que muda código mostra o código completo.

**Type consistency:**
- [x] `ApplicationRead`, `ApplicationList`, `ApplicationCreate` consistentes em schemas + services + router.
- [x] `ServiceContractRead`, `ServiceContractList`, `ContractCancelRequest` idem.
- [x] `NotificationRead`, `NotificationList`, `ReadAllResponse` idem.
- [x] Exceções `JobNotOpen`, `FreelancerOverlap`, `ApplicationNotPending`, `ContractAlreadyTerminal`, `DuplicateApplication`, `ProfileRequired`, `SelfApplicationForbidden`, `NotificationNotFound` definidas em Task 4 e usadas em Tasks 5-9.
- [x] `advance_contract_lifecycle(ctx)` assinatura igual em tasks.py, arq_worker.py e tests.
- [x] Factories `make_user/freelancer/establishment/skill_category/job/application/contract` definidas em Task 5 e usadas em Tasks 6-10.
