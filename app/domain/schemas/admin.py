"""Schemas Pydantic do dashboard admin (Sprint 6)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

# ── Platform Stats ────────────────────────────────────────────────────────────


class UserCountByRole(BaseModel):
    freelancers: int
    establishments: int
    admins: int
    total: int


class JobCountByStatus(BaseModel):
    draft: int = 0
    open: int = 0
    filled: int = 0
    cancelled: int = 0
    completed: int = 0
    total: int = 0


class ContractCountByStatus(BaseModel):
    scheduled: int = 0
    in_progress: int = 0
    completed: int = 0
    cancelled: int = 0
    total: int = 0


class PlatformStats(BaseModel):
    users: UserCountByRole
    jobs: JobCountByStatus
    contracts: ContractCountByStatus
    reviews_total: int
    notifications_total: int


# ── User management ──────────────────────────────────────────────────────────


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: str
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class AdminUserDetail(AdminUserRead):
    contracts_count: int = 0
    reviews_given: int = 0
    reviews_received: int = 0


class AdminUserList(BaseModel):
    items: list[AdminUserRead]
    total: int
    page: int
    page_size: int


# ── Audit log ────────────────────────────────────────────────────────────────


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID | None
    action: str
    entity: str
    entity_id: uuid.UUID | None
    diff: dict[str, Any]
    ip: str | None
    user_agent: str | None
    created_at: datetime


class AuditLogList(BaseModel):
    items: list[AuditLogRead]
    total: int
    page: int
    page_size: int
