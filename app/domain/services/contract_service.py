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
from app.utils.audit import write_audit_log


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

        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="cancel",
            entity="service_contract",
            entity_id=contract.id,
            diff={"cancelled_by": cancelled_by, "no_show": no_show},
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

        await self._session.commit()
        return ServiceContractRead.model_validate(contract)
