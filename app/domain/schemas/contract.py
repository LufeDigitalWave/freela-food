"""Schemas Pydantic de ServiceContract."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServiceContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID | None
    job_posting_id: uuid.UUID | None
    invitation_id: uuid.UUID | None = None
    freelancer_id: uuid.UUID
    establishment_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    agreed_hourly_rate: Decimal | None
    agreed_total_pay: Decimal | None
    status: str
    cancelled_by: str | None
    cancelled_at: datetime | None
    cancel_reason: str | None
    no_show: bool
    created_at: datetime


class ServiceContractList(BaseModel):
    items: list[ServiceContractRead]
    total: int
    page: int
    page_size: int


class ContractCancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)
