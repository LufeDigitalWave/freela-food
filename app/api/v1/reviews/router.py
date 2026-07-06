"""Endpoints /v1/contracts/{id}/reviews e /v1/me/reviews (Sprint 5)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.review import ReviewCreate, ReviewList, ReviewRead
from app.domain.services.review_service import ReviewService

router = APIRouter(tags=["reviews"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/contracts/{contract_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Avaliar contrato (após completed)",
)
async def create_review(
    contract_id: uuid.UUID,
    payload: ReviewCreate,
    user_id: UserIdDep,
    session: SessionDep,
) -> ReviewRead:
    return await ReviewService(session).create_review(
        user_id=user_id, contract_id=contract_id, payload=payload
    )


@router.get(
    "/contracts/{contract_id}/reviews",
    response_model=list[ReviewRead],
    summary="Reviews de um contrato (com visibilidade aplicada)",
)
async def list_contract_reviews(
    contract_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> list[ReviewRead]:
    return await ReviewService(session).list_for_contract(
        user_id=user_id, contract_id=contract_id
    )


@router.get(
    "/me/reviews",
    response_model=ReviewList,
    summary="Reviews recebidas pelo user autenticado",
)
async def list_my_reviews(
    user_id: UserIdDep,
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ReviewList:
    return await ReviewService(session).list_received(
        user_id=user_id, page=page, page_size=page_size
    )
