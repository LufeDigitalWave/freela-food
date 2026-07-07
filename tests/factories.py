"""Helpers pra criar entidades de teste (User, profiles, jobs, applications, contracts).

Cada factory recebe `session: AsyncSession` e retorna o model criado, já com
flush() executado. Não commita — assume controle transacional do test.

Emails são únicos por default (uuid) pra evitar pollution no DB compartilhado.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from geoalchemy2.shape import from_shape
from httpx import AsyncClient
from shapely.geometry import Point
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.domain.models.application import Application
from app.domain.models.establishment_profile import EstablishmentProfile
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.freelancer_skill import FreelancerSkill
from app.domain.models.invitation import Invitation
from app.domain.models.job_posting import JobPosting
from app.domain.models.review import Review
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


async def make_admin(
    session: AsyncSession,
    *,
    email: str | None = None,
    password: str = "Senha123!",
) -> User:
    """Cria user com role='admin'."""
    return await make_user(session, email=email, role="admin", password=password)


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
    business_name: str = "Bar Test",
    lat: float = -23.55,
    lng: float = -46.63,
) -> tuple[User, EstablishmentProfile]:
    user = await make_user(session, email=email, role="establishment")
    profile = EstablishmentProfile(
        user_id=user.id,
        business_name=business_name,
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


async def make_completed_contract(
    session: AsyncSession,
    *,
    freelancer_id: uuid.UUID,
    establishment_id: uuid.UUID,
    application_id: uuid.UUID | None = None,
    invitation_id: uuid.UUID | None = None,
    job_posting_id: uuid.UUID | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> ServiceContract:
    """Cria contrato já em status 'completed' (pra testes de review)."""
    s = start_at or (datetime.now(UTC) - timedelta(days=3))
    e = end_at or (s + timedelta(hours=4))
    contract = ServiceContract(
        application_id=application_id,
        invitation_id=invitation_id,
        job_posting_id=job_posting_id,
        freelancer_id=freelancer_id,
        establishment_id=establishment_id,
        start_at=s,
        end_at=e,
        status="completed",
        agreed_hourly_rate=Decimal("30.00"),
    )
    session.add(contract)
    await session.flush()
    await session.refresh(contract)
    return contract


async def make_review(
    session: AsyncSession,
    *,
    contract_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    reviewee_id: uuid.UUID,
    stars: int = 4,
    comment: str | None = None,
    visible_at: datetime | None = None,
    created_at: datetime | None = None,
) -> Review:
    """Cria review direto no banco (pra testes de listagem/visibilidade)."""
    review = Review(
        contract_id=contract_id,
        reviewer_id=reviewer_id,
        reviewee_id=reviewee_id,
        stars=stars,
        comment=comment,
        visible_at=visible_at,
        created_at=created_at or datetime.now(UTC),
    )
    session.add(review)
    await session.flush()
    await session.refresh(review)
    return review


async def auth_header_for(
    client: AsyncClient, email: str, password: str = "Senha123!"
) -> dict[str, str]:
    """Login via API e retorna {Authorization: Bearer ...}."""
    resp = await client.post(
        "/v1/auth/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
