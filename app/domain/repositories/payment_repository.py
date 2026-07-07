"""Repository de Payment (Sprint 9)."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.payment import Payment
from app.domain.models.service_contract import ServiceContract


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        contract_id: uuid.UUID,
        amount: Decimal,
        pix_key: str | None = None,
    ) -> Payment:
        payment = Payment(
            contract_id=contract_id,
            amount=amount,
            pix_key=pix_key,
            created_at=datetime.now(UTC),
        )
        self._session.add(payment)
        await self._session.flush()
        await self._session.refresh(payment)
        return payment

    async def get_by_contract_id(self, contract_id: uuid.UUID) -> Payment | None:
        result = await self._session.execute(
            select(Payment).where(Payment.contract_id == contract_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        result = await self._session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Payment], int]:
        """Pagamentos onde user é freelancer ou establishment do contrato."""
        base = (
            select(Payment)
            .join(ServiceContract, Payment.contract_id == ServiceContract.id)
            .where(
                or_(
                    ServiceContract.freelancer_id == user_id,
                    ServiceContract.establishment_id == user_id,
                )
            )
        )
        if status_filter:
            base = base.where(Payment.status == status_filter)

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(Payment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def list_all(
        self,
        *,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Payment], int]:
        """Admin: todos os pagamentos."""
        base = select(Payment)
        if status_filter:
            base = base.where(Payment.status == status_filter)

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(Payment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)
