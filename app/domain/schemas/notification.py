"""Schemas Pydantic de Notification."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    payload: dict[str, Any]
    read_at: datetime | None
    created_at: datetime


class NotificationList(BaseModel):
    items: list[NotificationRead]
    total: int
    unread_count: int
    page: int
    page_size: int


class ReadAllResponse(BaseModel):
    updated: int
