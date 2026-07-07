"""Endpoints /v1/me/notifications e /v1/notifications/*."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.domain.schemas.notification import (
    NotificationList,
    NotificationRead,
    ReadAllResponse,
    UnreadCountResponse,
)
from app.domain.services.notification_service import NotificationService

router = APIRouter(tags=["notifications"])

UserIdDep = Annotated[uuid.UUID, Depends(get_current_user_id)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/me/notifications",
    response_model=NotificationList,
    summary="Lista notificações do user logado",
)
async def list_my_notifications(
    user_id: UserIdDep,
    session: SessionDep,
    unread_only: Annotated[bool, Query()] = False,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> NotificationList:
    return await NotificationService(session).list_for_user(
        user_id=user_id,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/notifications/{notif_id}/read",
    response_model=NotificationRead,
    summary="Marca uma notificação como lida",
)
async def mark_read(
    notif_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> NotificationRead:
    return await NotificationService(session).mark_read(
        user_id=user_id, notif_id=notif_id
    )


@router.post(
    "/me/notifications/read-all",
    response_model=ReadAllResponse,
    status_code=status.HTTP_200_OK,
    summary="Marca todas as não-lidas como lidas",
)
async def mark_all_read(
    user_id: UserIdDep,
    session: SessionDep,
) -> ReadAllResponse:
    return await NotificationService(session).mark_all_read(user_id=user_id)


@router.delete(
    "/notifications/{notif_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deleta uma notificação (ownership check)",
)
async def delete_notification(
    notif_id: uuid.UUID,
    user_id: UserIdDep,
    session: SessionDep,
) -> None:
    await NotificationService(session).delete(user_id=user_id, notif_id=notif_id)
    await session.commit()


@router.get(
    "/me/notifications/count",
    response_model=UnreadCountResponse,
    summary="Contagem de notificações não-lidas (pra badge/polling)",
)
async def count_unread(
    user_id: UserIdDep,
    session: SessionDep,
) -> UnreadCountResponse:
    return await NotificationService(session).count_unread(user_id=user_id)
