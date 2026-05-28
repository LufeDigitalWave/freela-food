"""Endpoints /v1/applications, /v1/jobs/{id}/applications, /v1/me/applications.

Métodos adicionais serão acrescentados em tasks subsequentes.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.application import ApplicationCreate, ApplicationRead
from app.domain.services.application_service import ApplicationService

router = APIRouter(tags=["applications"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/jobs/{job_id}/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Freelancer candidata-se a uma vaga",
)
async def create_application(
    job_id: uuid.UUID,
    payload: ApplicationCreate,
    user_id: UserIdDep,
    session: SessionDep,
) -> ApplicationRead:
    return await ApplicationService(session).create(
        freelancer_id=user_id, job_id=job_id, payload=payload
    )
