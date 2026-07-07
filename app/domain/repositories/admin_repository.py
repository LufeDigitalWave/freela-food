"""Repository admin — queries agregadas pra dashboard (Sprint 6)."""

import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.audit_log import AuditLog
from app.domain.models.job_posting import JobPosting
from app.domain.models.notification import Notification
from app.domain.models.review import Review
from app.domain.models.service_contract import ServiceContract
from app.domain.models.user import User


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Stats ─────────────────────────────────────────────────────────────────

    async def count_users_by_role(self) -> dict[str, int]:
        result = await self._session.execute(
            select(User.role, func.count()).group_by(User.role)
        )
        counts: dict[str, int] = {"freelancer": 0, "establishment": 0, "admin": 0}
        for role, count in result.all():
            counts[role] = int(count)
        return counts

    async def count_jobs_by_status(self) -> dict[str, int]:
        result = await self._session.execute(
            select(JobPosting.status, func.count()).group_by(JobPosting.status)
        )
        counts: dict[str, int] = {}
        for status, count in result.all():
            counts[status] = int(count)
        return counts

    async def count_contracts_by_status(self) -> dict[str, int]:
        result = await self._session.execute(
            select(ServiceContract.status, func.count())
            .group_by(ServiceContract.status)
        )
        counts: dict[str, int] = {}
        for status, count in result.all():
            counts[status] = int(count)
        return counts

    async def count_reviews(self) -> int:
        result = await self._session.scalar(
            select(func.count()).select_from(Review)
        )
        return int(result or 0)

    async def count_notifications(self) -> int:
        result = await self._session.scalar(
            select(func.count()).select_from(Notification)
        )
        return int(result or 0)

    # ── Users ─────────────────────────────────────────────────────────────────

    async def list_users(
        self,
        *,
        role: str | None = None,
        email_search: str | None = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        base = select(User)
        if not include_deleted:
            base = base.where(User.deleted_at.is_(None))
        if role is not None:
            base = base.where(User.role == role)
        if email_search:
            base = base.where(User.email.ilike(f"%{email_search}%"))

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def count_user_contracts(self, user_id: uuid.UUID) -> int:
        result = await self._session.scalar(
            select(func.count())
            .select_from(ServiceContract)
            .where(
                or_(
                    ServiceContract.freelancer_id == user_id,
                    ServiceContract.establishment_id == user_id,
                )
            )
        )
        return int(result or 0)

    async def count_user_reviews_given(self, user_id: uuid.UUID) -> int:
        result = await self._session.scalar(
            select(func.count())
            .select_from(Review)
            .where(Review.reviewer_id == user_id)
        )
        return int(result or 0)

    async def count_user_reviews_received(self, user_id: uuid.UUID) -> int:
        result = await self._session.scalar(
            select(func.count())
            .select_from(Review)
            .where(Review.reviewee_id == user_id)
        )
        return int(result or 0)

    # ── Audit log ─────────────────────────────────────────────────────────────

    async def list_audit_log(
        self,
        *,
        action: str | None = None,
        entity: str | None = None,
        actor_id: uuid.UUID | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        base = select(AuditLog)
        if action:
            base = base.where(AuditLog.action == action)
        if entity:
            base = base.where(AuditLog.entity == entity)
        if actor_id:
            base = base.where(AuditLog.actor_id == actor_id)
        if since:
            base = base.where(AuditLog.created_at >= since)
        if until:
            base = base.where(AuditLog.created_at <= until)

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)
