"""Endpoints de auth: /register, /login, /me, /refresh, /logout.

Exceções de domínio (DomainError) sobem até o handler central em main.py.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.rate_limit import rate_limit_login, rate_limit_register
from app.core.security import get_current_user_id
from app.domain.schemas.auth import UserCreate, UserLogin, UserRead
from app.domain.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma conta nova",
)
async def register(
    payload: UserCreate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRead:
    await rate_limit_register(request)
    return await AuthService(session).register(payload)


@router.post(
    "/login",
    response_model=RefreshResponse,
    summary="Autentica e retorna access + refresh token",
)
async def login(
    payload: UserLogin,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RefreshResponse:
    await rate_limit_login(request)
    result = await AuthService(session).login_with_refresh(payload)
    return RefreshResponse(**result)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Renova access token usando refresh token",
)
async def refresh(
    payload: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RefreshResponse:
    result = await AuthService(session).refresh(payload.refresh_token)
    return RefreshResponse(**result)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoga refresh token",
)
async def logout(
    payload: RefreshRequest,
) -> None:
    from app.core.refresh_tokens import revoke_refresh_token

    await revoke_refresh_token(payload.refresh_token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Retorna o usuário autenticado",
)
async def me(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRead:
    return await AuthService(session).me(user_id)
