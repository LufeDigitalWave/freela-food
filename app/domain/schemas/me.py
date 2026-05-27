"""Schemas agregados do próprio usuário (/v1/me)."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr

from app.domain.schemas.auth import Role
from app.domain.schemas.profile import EstablishmentProfileRead, FreelancerProfileRead


class MeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    role: Role
    created_at: datetime
    freelancer_profile: FreelancerProfileRead | None = None
    establishment_profile: EstablishmentProfileRead | None = None


class _AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    action: str
    entity: str
    entity_id: uuid.UUID | None
    diff: dict[str, object]
    created_at: datetime


class MeExport(BaseModel):
    """Dump LGPD: tudo do usuário, incluindo CPF/CNPJ decriptados."""

    user_id: uuid.UUID
    email: EmailStr
    role: Role
    created_at: datetime
    cpf: str | None = None
    cnpj: str | None = None
    freelancer_profile: FreelancerProfileRead | None = None
    establishment_profile: EstablishmentProfileRead | None = None
    audit_log: list[_AuditLogEntry] = []


class DeleteMeResponse(BaseModel):
    status: Literal["scheduled_for_deletion"] = "scheduled_for_deletion"
    purge_at: datetime
