"""Schemas Pydantic de Application."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApplicationCreate(BaseModel):
    message: str | None = Field(default=None, max_length=500)


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_posting_id: uuid.UUID
    freelancer_id: uuid.UUID
    status: str
    message: str | None
    created_at: datetime
    decided_at: datetime | None


class ApplicationList(BaseModel):
    items: list[ApplicationRead]
    total: int
    page: int
    page_size: int
