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
    NotFoundError,
    PermissionDenied,
)
from app.domain.repositories.invitation_repository import InvitationRepository
from app.domain.repositories.profile_repository import ProfileRepository
from app.domain.schemas.invitation import InvitationCreate, InvitationList, InvitationRead
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
