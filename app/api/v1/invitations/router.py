"""Endpoints /v1/invitations (Fluxo B)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.invitation import InvitationCreate, InvitationRead
from app.domain.services.invitation_service import InvitationService

router = APIRouter(tags=["invitations"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


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
