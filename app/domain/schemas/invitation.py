"""Schemas Pydantic de Invitation."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InvitationCreate(BaseModel):
    freelancer_id: uuid.UUID
    skill_category_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    proposed_hourly_rate: Decimal | None = Field(default=None, ge=0)
    proposed_total_pay: Decimal | None = Field(default=None, ge=0)
    message: str | None = Field(default=None, max_length=1000)


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    establishment_id: uuid.UUID
    freelancer_id: uuid.UUID
    skill_category_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    proposed_hourly_rate: Decimal | None
    proposed_total_pay: Decimal | None
    message: str | None
    status: str
    expires_at: datetime
    decided_at: datetime | None
    created_at: datetime


class InvitationList(BaseModel):
    items: list[InvitationRead]
    total: int
    page: int
    page_size: int
