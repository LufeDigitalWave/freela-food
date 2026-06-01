"""Endpoints /v1/invitations (Fluxo B)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.invitation import InvitationCreate, InvitationList, InvitationRead
from app.domain.services.invitation_service import InvitationService

router = APIRouter(tags=["invitations"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/invitations",
    response_model=InvitationList,
    summary="Meus convites (estabelecimento vê enviados, freelancer recebidos)",
)
async def list_invitations(
    user_id: UserIdDep,
    session: SessionDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> InvitationList:
    return await InvitationService(session).list_mine(
        user_id=user_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/invitations/{invitation_id}",
    response_model=InvitationRead,
    summary="Detalhe de um convite (apenas partes)",
)
async def get_invitation(
    invitation_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> InvitationRead:
    return await InvitationService(session).get_by_id(
        user_id=user_id, invitation_id=invitation_id
    )


@router.post(
    "/invitations",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Estabelecimento convida um freelancer (Fluxo B)",
)
async def create_invitation(
    payload: InvitationCreate,
    user_id: UserIdDep,
    session: SessionDep,
) -> InvitationRead:
    return await InvitationService(session).create(
        establishment_id=user_id, payload=payload
    )
