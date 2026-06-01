"""Service de Application.

Métodos adicionais (list, accept, reject, withdraw) entram em tasks subsequentes.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ApplicationNotPending,
    DuplicateApplication,
    FreelancerOverlap,
    JobNotOpen,
    NotFoundError,
    PermissionDenied,
    ProfileRequired,
    SelfApplicationForbidden,
)
from app.domain.models.job_posting import JobPosting
from app.domain.repositories.application_repository import ApplicationRepository
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.profile_repository import ProfileRepository
from app.domain.schemas.application import (
    ApplicationCreate,
    ApplicationList,
    ApplicationRead,
)
from app.domain.services.notification_service import NotificationService
from app.utils.audit import write_audit_log


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

        await write_audit_log(
            self._session,
            actor_id=freelancer_id,
            action="create",
            entity="application",
            entity_id=app_.id,
            diff={"job_posting_id": str(job_id)},
        )

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

        await self._session.commit()
        return ApplicationRead.model_validate(app_)

    async def get_by_id(
        self, *, user_id: uuid.UUID, app_id: uuid.UUID
    ) -> ApplicationRead:
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
    ) -> ApplicationList:
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

    async def reject(
        self, *, user_id: uuid.UUID, app_id: uuid.UUID
    ) -> ApplicationRead:
        app_ = await self._repo.get_by_id(app_id)
        if app_ is None:
            raise NotFoundError("Candidatura não encontrada")
        job = await self._jobs.get_by_id(app_.job_posting_id)
        if job is None or job.establishment_id != user_id:
            raise PermissionDenied()
        if app_.status != "pending":
            raise ApplicationNotPending()

        app_ = await self._repo.update_status(app_, new_status="rejected")
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="reject",
            entity="application",
            entity_id=app_.id,
        )
        await self._notifications.emit(
            user_id=app_.freelancer_id,
            type="application.rejected",
            payload={
                "application_id": str(app_.id),
                "job_posting_id": str(app_.job_posting_id),
            },
        )
        await self._session.commit()
        return ApplicationRead.model_validate(app_)

    async def withdraw(
        self, *, user_id: uuid.UUID, app_id: uuid.UUID
    ) -> ApplicationRead:
        app_ = await self._repo.get_by_id(app_id)
        if app_ is None:
            raise NotFoundError("Candidatura não encontrada")
        if app_.freelancer_id != user_id:
            raise PermissionDenied()
        if app_.status != "pending":
            raise ApplicationNotPending()

        app_ = await self._repo.update_status(app_, new_status="withdrawn")
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="withdraw",
            entity="application",
            entity_id=app_.id,
        )
        await self._session.commit()
        return ApplicationRead.model_validate(app_)

    async def accept(
        self, *, user_id: uuid.UUID, app_id: uuid.UUID
    ) -> ApplicationRead:
        contracts_repo = ContractRepository(self._session)

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

        # Overlap check — freelancer não pode ter contrato sobreposto
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

        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="accept",
            entity="application",
            entity_id=app_.id,
            diff={"contract_id": str(contract.id)},
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

        await self._session.commit()
        return ApplicationRead.model_validate(app_)

    async def list_mine(
        self,
        *,
        user_id: uuid.UUID,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> ApplicationList:
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
