"""Service de auth — orquestra hash, validação, JWT e refresh tokens."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, ConflictError, DomainError
from app.core.refresh_tokens import (
    generate_refresh_token,
    revoke_refresh_token,
    store_refresh_token,
    validate_refresh_token,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.repositories.user_repository import UserRepository
from app.domain.schemas.auth import TokenResponse, UserCreate, UserLogin, UserRead


class PasswordTooWeak(DomainError):
    status_code = 422
    detail = "Senha muito fraca. Mínimo 8 caracteres, incluindo ao menos 1 número."


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._repo = UserRepository(session)
        self._session = session
        self._settings = settings or get_settings()

    def _validate_password(self, password: str) -> None:
        if len(password) < self._settings.password_min_length:
            raise PasswordTooWeak()
        if not any(c.isdigit() for c in password):
            raise PasswordTooWeak()

    async def register(self, payload: UserCreate) -> UserRead:
        self._validate_password(payload.password)

        existing = await self._repo.get_by_email(payload.email)
        if existing is not None:
            raise ConflictError("E-mail já cadastrado")

        user = await self._repo.create(
            email=payload.email,
            password_hash=hash_password(payload.password, settings=self._settings),
            role=payload.role,
        )
        await self._session.commit()
        return UserRead.model_validate(user)

    async def login(self, payload: UserLogin) -> TokenResponse:
        user = await self._repo.get_by_email(payload.email)
        if user is None or not verify_password(
            payload.password, user.password_hash, settings=self._settings
        ):
            raise AuthenticationError("E-mail ou senha incorretos")

        token = create_access_token(user.id, settings=self._settings)
        return TokenResponse(
            access_token=token,
            expires_in=self._settings.jwt_expires_minutes * 60,
        )

    async def login_with_refresh(self, payload: UserLogin) -> dict[str, str]:
        user = await self._repo.get_by_email(payload.email)
        if user is None or not verify_password(
            payload.password, user.password_hash, settings=self._settings
        ):
            raise AuthenticationError("E-mail ou senha incorretos")

        access = create_access_token(user.id, settings=self._settings)
        refresh = generate_refresh_token()
        await store_refresh_token(user.id, refresh)

        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
        }

    async def refresh(self, refresh_token: str) -> dict[str, str]:
        user_id = await validate_refresh_token(refresh_token)
        if user_id is None:
            raise AuthenticationError("Refresh token inválido ou expirado")

        await revoke_refresh_token(refresh_token)

        new_access = create_access_token(user_id, settings=self._settings)
        new_refresh = generate_refresh_token()
        await store_refresh_token(user_id, new_refresh)

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        }

    async def me(self, user_id: uuid.UUID) -> UserRead:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("Usuário inativo ou inexistente")
        return UserRead.model_validate(user)
