"""Schemas Pydantic para JobPosting + busca por proximidade."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.domain.schemas.profile import StateUF

JobStatus = Literal["draft", "open", "filled", "cancelled", "completed"]
CEPField = Annotated[str, StringConstraints(pattern=r"^\d{8}$")]


class JobPostingCreate(BaseModel):
    skill_category_id: uuid.UUID
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)

    # Geo: se omitido, herda do EstablishmentProfile do dono
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    # Endereço opcional — se omitido, herda do estabelecimento
    address_line: str | None = Field(default=None, max_length=500)
    neighborhood: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: StateUF | None = None
    cep: CEPField | None = None

    start_at: datetime
    end_at: datetime

    hourly_rate: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    total_pay: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)

    @model_validator(mode="after")
    def _validate(self) -> "JobPostingCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at deve ser depois de start_at")
        if self.hourly_rate is None and self.total_pay is None:
            raise ValueError("Informe hourly_rate ou total_pay")
        # Lat e lng vêm juntos ou nenhum
        if (self.latitude is None) ^ (self.longitude is None):
            raise ValueError("latitude e longitude devem ser informados juntos")
        return self


class JobPostingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    address_line: str | None = None
    neighborhood: str | None = None
    city: str | None = None
    state: StateUF | None = None
    cep: CEPField | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    hourly_rate: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    total_pay: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)

    @model_validator(mode="after")
    def _validate(self) -> "JobPostingUpdate":
        if (
            self.start_at is not None
            and self.end_at is not None
            and self.end_at <= self.start_at
        ):
            raise ValueError("end_at deve ser depois de start_at")
        if (self.latitude is None) ^ (self.longitude is None):
            raise ValueError("latitude e longitude devem ser informados juntos")
        return self


class JobPostingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    establishment_id: uuid.UUID
    skill_category_id: uuid.UUID
    title: str
    description: str | None
    latitude: float
    longitude: float
    address_line: str | None
    neighborhood: str | None
    city: str | None
    state: str | None
    cep: str | None
    start_at: datetime
    end_at: datetime
    hourly_rate: Decimal | None
    total_pay: Decimal | None
    status: JobStatus
    created_at: datetime
    updated_at: datetime


class JobPostingReadWithDistance(JobPostingRead):
    distance_m: float


class JobSearchResponse(BaseModel):
    items: list[JobPostingReadWithDistance]
    total: int
    page: int
    page_size: int
