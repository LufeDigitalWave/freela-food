"""Endpoint /v1/freelancers/search (estabelecimento busca freelancers)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.freelancer_search import FreelancerSearchList
from app.domain.services.freelancer_search_service import FreelancerSearchService

router = APIRouter(tags=["freelancers"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/freelancers/search",
    response_model=FreelancerSearchList,
    summary="Estabelecimento busca freelancers por proximidade + skill",
)
async def search_freelancers(
    user_id: UserIdDep,
    session: SessionDep,
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    radius_km: Annotated[float, Query(gt=0, le=500)] = 10,
    skill_category_id: Annotated[uuid.UUID | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> FreelancerSearchList:
    return await FreelancerSearchService(session).search(
        user_id=user_id,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        skill_category_id=skill_category_id,
        page=page,
        page_size=page_size,
    )
