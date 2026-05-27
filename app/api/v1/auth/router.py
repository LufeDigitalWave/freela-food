"""Endpoints de auth: /register, /login, /me.

Exceções de domínio (DomainError) sobem até o handler central em main.py.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.auth import TokenResponse, UserCreate, UserLogin, UserRead
from app.domain.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma conta nova",
)
async def register(
    payload: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRead:
    return await AuthService(session).register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autentica e retorna access token",
)
async def login(
    payload: UserLogin,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    return await AuthService(session).login(payload)


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
