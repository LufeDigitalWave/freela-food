"""Schemas Pydantic de Payment (Sprint 9)."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_id: uuid.UUID
    amount: Decimal
    status: str
    pix_key: str | None
    confirmed_at: datetime | None
    confirmed_by: uuid.UUID | None
    disputed_at: datetime | None
    notes: str | None
    created_at: datetime


class PaymentList(BaseModel):
    items: list[PaymentRead]
    total: int
    page: int
    page_size: int


class ConfirmPaymentRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)
