"""Service de Notification. Utilizado pelos outros services pra emitir eventos."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotificationNotFound, PermissionDenied
from app.domain.models.notification import Notification
from app.domain.repositories.notification_repository import NotificationRepository
from app.domain.schemas.notification import (
    NotificationList,
    NotificationRead,
    ReadAllResponse,
    UnreadCountResponse,
)


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = NotificationRepository(session)

    async def emit(
        self, *, user_id: uuid.UUID, type: str, payload: dict[str, Any]
    ) -> Notification:
        """Cria notification. Chamado por outros services dentro da própria tx."""
        return await self._repo.create(user_id=user_id, type=type, payload=payload)

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        unread_only: bool,
        page: int,
        page_size: int,
    ) -> NotificationList:
        items, total, unread = await self._repo.list_for_user(
            user_id=user_id,
            unread_only=unread_only,
            page=page,
            page_size=page_size,
        )
        return NotificationList(
            items=[NotificationRead.model_validate(n) for n in items],
            total=total,
            unread_count=unread,
            page=page,
            page_size=page_size,
        )

    async def mark_read(
        self, *, user_id: uuid.UUID, notif_id: uuid.UUID
    ) -> NotificationRead:
        notif = await self._repo.get_by_id(notif_id)
        if notif is None:
            raise NotificationNotFound()
        if notif.user_id != user_id:
            raise PermissionDenied()
        if notif.read_at is None:
            notif = await self._repo.mark_read(notif)
        return NotificationRead.model_validate(notif)

    async def mark_all_read(self, *, user_id: uuid.UUID) -> ReadAllResponse:
        n = await self._repo.mark_all_read(user_id)
        return ReadAllResponse(updated=n)

    async def delete(
        self, *, user_id: uuid.UUID, notif_id: uuid.UUID
    ) -> None:
        notif = await self._repo.get_by_id(notif_id)
        if notif is None:
            raise NotificationNotFound()
        if notif.user_id != user_id:
            raise PermissionDenied()
        await self._repo.delete(notif)

    async def count_unread(self, *, user_id: uuid.UUID) -> UnreadCountResponse:
        n = await self._repo.count_unread(user_id)
        return UnreadCountResponse(unread=n)
