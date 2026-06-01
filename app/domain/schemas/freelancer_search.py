"""Schemas da busca de freelancers (Fluxo B)."""

import uuid

from pydantic import BaseModel, ConfigDict


class FreelancerSearchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    display_name: str
    bio: str | None
    avatar_url: str | None
    completed_contracts_count: int
    no_show_count: int
    distance_m: float


class FreelancerSearchList(BaseModel):
    items: list[FreelancerSearchRead]
    total: int
    page: int
    page_size: int
