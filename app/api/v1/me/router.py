"""Endpoints do próprio usuário (/v1/me)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.core.storage import ALLOWED_AVATAR_TYPES, MAX_AVATAR_BYTES, upload_avatar
from app.domain.schemas.me import DeleteMeResponse, MeExport, MeRead
from app.domain.schemas.profile import (
    EstablishmentProfileCreate,
    EstablishmentProfileRead,
    EstablishmentProfileUpdate,
    FreelancerProfileCreate,
    FreelancerProfileRead,
    FreelancerProfileUpdate,
)
from app.domain.services.me_service import MeService
from app.domain.services.profile_service import ProfileService

router = APIRouter(prefix="/me", tags=["me"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=MeRead, summary="User + perfil")
async def get_me(user_id: UserIdDep, session: SessionDep) -> MeRead:
    return await MeService(session).get_me(user_id)


@router.get("/export", response_model=MeExport, summary="LGPD: dump completo do usuário")
async def export_me(user_id: UserIdDep, session: SessionDep) -> MeExport:
    return await MeService(session).export_me(user_id)


@router.delete(
    "",
    response_model=DeleteMeResponse,
    summary="LGPD: soft delete + purge em N dias",
)
async def delete_me(user_id: UserIdDep, session: SessionDep) -> DeleteMeResponse:
    return await MeService(session).soft_delete_me(user_id)


# ── Profile (role-specific) ───────────────────────────────────────────────────


@router.post(
    "/freelancer-profile",
    response_model=FreelancerProfileRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_freelancer_profile(
    payload: FreelancerProfileCreate,
    user_id: UserIdDep,
    session: SessionDep,
) -> FreelancerProfileRead:
    return await ProfileService(session).create_freelancer(user_id, payload)


@router.patch("/freelancer-profile", response_model=FreelancerProfileRead)
async def update_freelancer_profile(
    payload: FreelancerProfileUpdate,
    user_id: UserIdDep,
    session: SessionDep,
) -> FreelancerProfileRead:
    return await ProfileService(session).update_freelancer(user_id, payload)


@router.post(
    "/establishment-profile",
    response_model=EstablishmentProfileRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_establishment_profile(
    payload: EstablishmentProfileCreate,
    user_id: UserIdDep,
    session: SessionDep,
) -> EstablishmentProfileRead:
    return await ProfileService(session).create_establishment(user_id, payload)


@router.patch("/establishment-profile", response_model=EstablishmentProfileRead)
async def update_establishment_profile(
    payload: EstablishmentProfileUpdate,
    user_id: UserIdDep,
    session: SessionDep,
) -> EstablishmentProfileRead:
    return await ProfileService(session).update_establishment(user_id, payload)


# ── Avatar upload ─────────────────────────────────────────────────────────────


@router.post("/avatar", summary="Upload do avatar (jpeg/png/webp, max 5MB)")
async def upload_avatar_endpoint(
    file: Annotated[UploadFile, File()],
    user_id: UserIdDep,
    session: SessionDep,
) -> dict[str, str]:
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo não permitido. Aceitos: {sorted(ALLOWED_AVATAR_TYPES)}",
        )
    body = await file.read()
    if len(body) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Avatar excede {MAX_AVATAR_BYTES // (1024 * 1024)} MB",
        )

    url = await upload_avatar(str(user_id), file.content_type, body)
    await ProfileService(session).set_avatar_url(user_id, url)
    return {"avatar_url": url}
