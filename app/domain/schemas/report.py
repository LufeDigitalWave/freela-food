"""Schemas Pydantic de Report/Moderação (Sprint 8)."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    target_type: Literal["user", "review"]
    target_id: uuid.UUID
    reason: Literal["spam", "offensive", "fake", "harassment", "other"]
    description: str | None = Field(default=None, max_length=1000)


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reporter_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    reason: str
    description: str | None
    status: str
    resolved_by: uuid.UUID | None
    resolved_at: datetime | None
    resolution_note: str | None
    created_at: datetime


class ReportList(BaseModel):
    items: list[ReportRead]
    total: int
    page: int
    page_size: int


class ResolveRequest(BaseModel):
    status: Literal["resolved_action", "resolved_dismissed"]
    resolution_note: str = Field(min_length=1, max_length=2000)
