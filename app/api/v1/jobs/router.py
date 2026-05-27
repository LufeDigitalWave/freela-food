"""Endpoints /v1/jobs e /v1/jobs/search."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.job import (
    JobPostingCreate,
    JobPostingRead,
    JobPostingUpdate,
    JobSearchResponse,
)
from app.domain.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "",
    response_model=JobPostingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma vaga (apenas estabelecimentos)",
)
async def create_job(
    payload: JobPostingCreate,
    user_id: UserIdDep,
    session: SessionDep,
) -> JobPostingRead:
    return await JobService(session).create(user_id, payload)


@router.get(
    "/search",
    response_model=JobSearchResponse,
    summary="Busca vagas dentro de um raio (PostGIS ST_DWithin)",
)
async def search_jobs(
    session: SessionDep,
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    radius_km: Annotated[float, Query(gt=0, le=100)] = 10.0,
    skill_category_id: Annotated[uuid.UUID | None, Query()] = None,
    only_open: Annotated[bool, Query()] = True,
    future_only: Annotated[bool, Query()] = True,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> JobSearchResponse:
    return await JobService(session).search(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        skill_category_id=skill_category_id,
        only_open=only_open,
        future_only=future_only,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{job_id}",
    response_model=JobPostingRead,
    summary="Detalhe de uma vaga",
)
async def get_job(
    job_id: uuid.UUID,
    _user_id: UserIdDep,
    session: SessionDep,
) -> JobPostingRead:
    return await JobService(session).get_by_id(job_id)


@router.patch(
    "/{job_id}",
    response_model=JobPostingRead,
    summary="Edita uma vaga (apenas dono)",
)
async def update_job(
    job_id: uuid.UUID,
    payload: JobPostingUpdate,
    user_id: UserIdDep,
    session: SessionDep,
) -> JobPostingRead:
    return await JobService(session).update(user_id, job_id, payload)


@router.post(
    "/{job_id}/cancel",
    response_model=JobPostingRead,
    summary="Cancela uma vaga (apenas dono)",
)
async def cancel_job(
    job_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> JobPostingRead:
    return await JobService(session).cancel(user_id, job_id)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete da vaga (apenas dono)",
)
async def delete_job(
    job_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> None:
    await JobService(session).soft_delete(user_id, job_id)
