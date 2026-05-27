"""Service de auth — orquestra hash, validação e emissão de JWT."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.repositories.user_repository import UserRepository
from app.domain.schemas.auth import TokenResponse, UserCreate, UserLogin, UserRead


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._repo = UserRepository(session)
        self._session = session
        self._settings = settings or get_settings()

    async def register(self, payload: UserCreate) -> UserRead:
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

    async def me(self, user_id: uuid.UUID) -> UserRead:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("Usuário inativo ou inexistente")
        return UserRead.model_validate(user)
