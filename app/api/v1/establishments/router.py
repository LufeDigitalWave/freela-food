"""Endpoints /v1/establishments/{id}/reviews e /v1/establishments/{id}/stats (Sprint 5)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.review import ReviewList, ReviewStats
from app.domain.services.review_service import ReviewService

router = APIRouter(tags=["establishments"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/establishments/{user_id}/reviews",
    response_model=ReviewList,
    summary="Reviews visíveis recebidas por um estabelecimento (público)",
)
async def list_establishment_reviews(
    user_id: uuid.UUID,
    _caller: UserIdDep,
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ReviewList:
    return await ReviewService(session).list_public(
        reviewee_id=user_id, page=page, page_size=page_size
    )


@router.get(
    "/establishments/{user_id}/stats",
    response_model=ReviewStats,
    summary="Rating agregado de um estabelecimento (público)",
)
async def get_establishment_stats(
    user_id: uuid.UUID,
    _caller: UserIdDep,
    session: SessionDep,
) -> ReviewStats:
    return await ReviewService(session).get_stats(reviewee_id=user_id)
