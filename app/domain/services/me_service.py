"""Service /v1/me — agrega user + profile, LGPD export + soft delete."""

import contextlib
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.storage import delete_avatar
from app.domain.models.audit_log import AuditLog
from app.domain.repositories.profile_repository import ProfileRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.schemas.me import DeleteMeResponse, MeExport, MeRead, _AuditLogEntry
from app.domain.services.profile_service import (
    _establishment_to_read,
    _freelancer_to_read,
)
from app.utils.audit import write_audit_log


class MeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._profile_repo = ProfileRepository(session)

    async def get_me(self, user_id: uuid.UUID) -> MeRead:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")

        freelancer = (
            await self._profile_repo.get_freelancer(user_id)
            if user.role == "freelancer"
            else None
        )
        establishment = (
            await self._profile_repo.get_establishment(user_id)
            if user.role == "establishment"
            else None
        )

        return MeRead(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            freelancer_profile=(
                _freelancer_to_read(freelancer) if freelancer is not None else None
            ),
            establishment_profile=(
                _establishment_to_read(establishment)
                if establishment is not None
                else None
            ),
        )

    async def export_me(self, user_id: uuid.UUID) -> MeExport:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")

        cpf: str | None = None
        cnpj: str | None = None
        freelancer_read = None
        establishment_read = None

        if user.role == "freelancer":
            freelancer = await self._profile_repo.get_freelancer(user_id)
            if freelancer is not None:
                cpf = await self._profile_repo.decrypt_freelancer_cpf(freelancer)
                freelancer_read = _freelancer_to_read(freelancer)
        elif user.role == "establishment":
            establishment = await self._profile_repo.get_establishment(user_id)
            if establishment is not None:
                cnpj = await self._profile_repo.decrypt_establishment_cnpj(establishment)
                establishment_read = _establishment_to_read(establishment)

        # Grava log do export ANTES de ler audit_log, pra incluir a entrada no dump
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="export",
            entity="user",
            entity_id=user_id,
        )

        audit_result = await self._session.execute(
            select(AuditLog)
            .where(AuditLog.actor_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(1000)
        )
        audit_rows = audit_result.scalars().all()

        await self._session.commit()

        return MeExport(
            user_id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            cpf=cpf,
            cnpj=cnpj,
            freelancer_profile=freelancer_read,
            establishment_profile=establishment_read,
            audit_log=[_AuditLogEntry.model_validate(a) for a in audit_rows],
        )

    async def soft_delete_me(self, user_id: uuid.UUID) -> DeleteMeResponse:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")

        now = datetime.now(UTC)
        user.deleted_at = now

        # Tenta limpar avatar do storage (best-effort; falha não bloqueia)
        with contextlib.suppress(Exception):
            await delete_avatar(str(user_id))

        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="delete",
            entity="user",
            entity_id=user_id,
        )
        await self._session.commit()

        purge_at = now + timedelta(days=get_settings().delete_grace_period_days)
        return DeleteMeResponse(purge_at=purge_at)
