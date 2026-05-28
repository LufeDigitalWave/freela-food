"""Service de Application.

Métodos adicionais (list, accept, reject, withdraw) entram em tasks subsequentes.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateApplication,
    JobNotOpen,
    NotFoundError,
    ProfileRequired,
    SelfApplicationForbidden,
)
from app.domain.repositories.application_repository import ApplicationRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.profile_repository import ProfileRepository
from app.domain.schemas.application import ApplicationCreate, ApplicationRead
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
