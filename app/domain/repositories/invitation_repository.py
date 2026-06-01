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
