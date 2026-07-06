"""Schemas Pydantic de Review (Sprint 5)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    stars: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contract_id: uuid.UUID
    reviewer_id: uuid.UUID
    reviewee_id: uuid.UUID
    stars: int
    comment: str | None
    visible_at: datetime | None
    created_at: datetime
    reviewer_display_name: str | None = None


class ReviewList(BaseModel):
    items: list[ReviewRead]
    total: int
    page: int
    page_size: int


class ReviewStats(BaseModel):
    average_rating: float | None
    total_reviews: int
    distribution: dict[int, int] = Field(
        default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    )
