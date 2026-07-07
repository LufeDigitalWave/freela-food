"""Service admin — dashboard + gestão de usuários (Sprint 6)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domain.repositories.admin_repository import AdminRepository
from app.domain.schemas.admin import (
    AdminUserDetail,
    AdminUserList,
    AdminUserRead,
    AuditLogList,
    AuditLogRead,
    ContractCountByStatus,
    JobCountByStatus,
    PlatformStats,
    UserCountByRole,
)
from app.utils.audit import write_audit_log


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AdminRepository(session)

    async def get_platform_stats(self) -> PlatformStats:
        users_raw = await self._repo.count_users_by_role()
        jobs_raw = await self._repo.count_jobs_by_status()
        contracts_raw = await self._repo.count_contracts_by_status()
        reviews_total = await self._repo.count_reviews()
        notifications_total = await self._repo.count_notifications()

        users = UserCountByRole(
            freelancers=users_raw.get("freelancer", 0),
            establishments=users_raw.get("establishment", 0),
            admins=users_raw.get("admin", 0),
            total=sum(users_raw.values()),
        )
        jobs = JobCountByStatus(
            **jobs_raw,
            total=sum(jobs_raw.values()),
        )
        contracts = ContractCountByStatus(
            **contracts_raw,
            total=sum(contracts_raw.values()),
        )
        return PlatformStats(
            users=users,
            jobs=jobs,
            contracts=contracts,
            reviews_total=reviews_total,
            notifications_total=notifications_total,
        )

    async def list_users(
        self,
        *,
        role: str | None = None,
        email_search: str | None = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> AdminUserList:
        items, total = await self._repo.list_users(
            role=role,
            email_search=email_search,
            include_deleted=include_deleted,
            page=page,
            page_size=page_size,
        )
        return AdminUserList(
            items=[AdminUserRead.model_validate(u) for u in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_user_detail(
        self, *, user_id: uuid.UUID
    ) -> AdminUserDetail:
        user = await self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        contracts_count = await self._repo.count_user_contracts(user_id)
        reviews_given = await self._repo.count_user_reviews_given(user_id)
        reviews_received = await self._repo.count_user_reviews_received(user_id)
        return AdminUserDetail(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            deleted_at=user.deleted_at,
            contracts_count=contracts_count,
            reviews_given=reviews_given,
            reviews_received=reviews_received,
        )

    async def deactivate_user(
        self, *, admin_id: uuid.UUID, user_id: uuid.UUID
    ) -> AdminUserRead:
        user = await self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        if user.deleted_at is not None:
            raise NotFoundError("Usuário já está desativado")
        user.deleted_at = datetime.now(UTC)
        await self._session.flush()

        await write_audit_log(
            self._session,
            actor_id=admin_id,
            action="deactivate",
            entity="user",
            entity_id=user_id,
        )
        await self._session.commit()
        await self._session.refresh(user)
        return AdminUserRead.model_validate(user)

    async def reactivate_user(
        self, *, admin_id: uuid.UUID, user_id: uuid.UUID
    ) -> AdminUserRead:
        user = await self._repo.get_user_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        if user.deleted_at is None:
            raise NotFoundError("Usuário não está desativado")
        user.deleted_at = None
        await self._session.flush()

        await write_audit_log(
            self._session,
            actor_id=admin_id,
            action="reactivate",
            entity="user",
            entity_id=user_id,
        )
        await self._session.commit()
        await self._session.refresh(user)
        return AdminUserRead.model_validate(user)

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
    ) -> AuditLogList:
        items, total = await self._repo.list_audit_log(
            action=action,
            entity=entity,
            actor_id=actor_id,
            since=since,
            until=until,
            page=page,
            page_size=page_size,
        )
        return AuditLogList(
            items=[AuditLogRead.model_validate(a) for a in items],
            total=total,
            page=page,
            page_size=page_size,
        )
