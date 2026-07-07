"""Repository de Notification."""

import uuid
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, user_id: uuid.UUID, type: str, payload: dict[str, Any]
    ) -> Notification:
        # Setamos created_at explicitamente em Python pra garantir timestamps
        # distintos entre emissões dentro da mesma transação (now() do PG é
        # transaction_timestamp(), o que quebra ordenação por created_at quando
        # múltiplas notifications são emitidas na mesma tx).
        notif = Notification(
            user_id=user_id,
            type=type,
            payload=payload,
            created_at=datetime.now(UTC),
        )
        self._session.add(notif)
        await self._session.flush()
        await self._session.refresh(notif)
        return notif

    async def get_by_id(self, notif_id: uuid.UUID) -> Notification | None:
        result = await self._session.execute(
            select(Notification).where(Notification.id == notif_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        unread_only: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Notification], int, int]:
        base = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            base = base.where(Notification.read_at.is_(None))

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        unread = await self._session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
        )

        result = await self._session.execute(
            base.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0), int(unread or 0)

    async def mark_read(self, notif: Notification) -> Notification:
        notif.read_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(notif)
        return notif

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        # session.execute() retorna Result[Any] no stub, mas em runtime é
        # CursorResult para UPDATE/DELETE. Cast pra acessar .rowcount.
        result = cast(
            CursorResult[Any],
            await self._session.execute(
                update(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None),
                )
                .values(read_at=datetime.now(UTC))
            ),
        )
        await self._session.flush()
        return int(result.rowcount or 0)

    async def delete(self, notif: Notification) -> None:
        await self._session.execute(
            delete(Notification).where(Notification.id == notif.id)
        )
        await self._session.flush()

    async def count_unread(self, user_id: uuid.UUID) -> int:
        result = await self._session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
        )
        return int(result or 0)
