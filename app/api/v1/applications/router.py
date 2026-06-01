"""Endpoints /v1/applications, /v1/jobs/{id}/applications, /v1/me/applications.

Métodos adicionais serão acrescentados em tasks subsequentes.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.application import (
    ApplicationCreate,
    ApplicationList,
    ApplicationRead,
)
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


@router.get(
    "/jobs/{job_id}/applications",
    response_model=ApplicationList,
    summary="Lista candidaturas de uma vaga (apenas dono)",
)
async def list_job_applications(
    job_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApplicationList:
    return await ApplicationService(session).list_for_job(
        user_id=user_id,
        job_id=job_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/me/applications",
    response_model=ApplicationList,
    summary="Minhas candidaturas (freelancer)",
)
async def list_my_applications(
    user_id: UserIdDep,
    session: SessionDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApplicationList:
    return await ApplicationService(session).list_mine(
        user_id=user_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationRead,
    summary="Detalhe de uma candidatura (freelancer ou estabelecimento partes)",
)
async def get_application(
    application_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> ApplicationRead:
    return await ApplicationService(session).get_by_id(
        user_id=user_id, app_id=application_id
    )


@router.post(
    "/applications/{application_id}/reject",
    response_model=ApplicationRead,
    summary="Estabelecimento rejeita uma candidatura",
)
async def reject_application(
    application_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> ApplicationRead:
    return await ApplicationService(session).reject(
        user_id=user_id, app_id=application_id
    )


@router.post(
    "/applications/{application_id}/withdraw",
    response_model=ApplicationRead,
    summary="Freelancer retira a própria candidatura",
)
async def withdraw_application(
    application_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> ApplicationRead:
    return await ApplicationService(session).withdraw(
        user_id=user_id, app_id=application_id
    )


@router.post(
    "/applications/{application_id}/accept",
    response_model=ApplicationRead,
    summary="Estabelecimento aceita uma candidatura (cria contrato)",
)
async def accept_application(
    application_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> ApplicationRead:
    return await ApplicationService(session).accept(
        user_id=user_id, app_id=application_id
    )
