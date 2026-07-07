"""Endpoints /v1/reports e /v1/me/reports (user-facing, Sprint 8)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.report import ReportCreate, ReportList, ReportRead
from app.domain.services.moderation_service import ModerationService

router = APIRouter(tags=["reports"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/reports",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar denúncia (qualquer user autenticado)",
)
async def create_report(
    payload: ReportCreate,
    user_id: UserIdDep,
    session: SessionDep,
) -> ReportRead:
    return await ModerationService(session).create_report(
        user_id=user_id, payload=payload
    )


@router.get(
    "/me/reports",
    response_model=ReportList,
    summary="Minhas denúncias e status",
)
async def list_my_reports(
    user_id: UserIdDep,
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ReportList:
    return await ModerationService(session).list_my_reports(
        user_id=user_id, page=page, page_size=page_size
    )
