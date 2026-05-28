"""Repository de ServiceContract."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

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
        agreed_hourly_rate: Decimal | None,
        agreed_total_pay: Decimal | None,
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
            # Overlap (half-open): A.start < B.end AND A.end > B.start
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
