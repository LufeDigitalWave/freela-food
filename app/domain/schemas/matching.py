"""Schemas do engine de matching/scoring (Sprint 7)."""

import uuid

from pydantic import BaseModel, ConfigDict


class ScoredFreelancerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    display_name: str
    bio: str | None
    avatar_url: str | None
    completed_contracts_count: int
    no_show_count: int
    average_rating: float | None
    total_reviews: int
    distance_m: float
    match_score: float  # 0-100


class MatchList(BaseModel):
    items: list[ScoredFreelancerRead]
    total: int
    page: int
    page_size: int
