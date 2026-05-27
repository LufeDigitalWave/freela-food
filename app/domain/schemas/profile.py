"""Schemas Pydantic para perfis (freelancer + estabelecimento)."""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.utils.br_validators import (
    is_valid_cep,
    is_valid_cnpj,
    is_valid_cpf,
    normalize_cep,
    normalize_cnpj,
    normalize_cpf,
)

# Telefone E.164: +<código país><número>, total 8-15 dígitos
Phone = Annotated[str, StringConstraints(pattern=r"^\+[1-9]\d{7,14}$")]
StateUF = Annotated[
    str, StringConstraints(pattern=r"^[A-Z]{2}$", min_length=2, max_length=2)
]


# ── Freelancer ────────────────────────────────────────────────────────────────


class _FreelancerProfileBase(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    bio: str | None = Field(default=None, max_length=2000)
    phone: Phone | None = None
    cpf: str | None = None

    @field_validator("cpf", mode="before")
    @classmethod
    def _validate_cpf(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if not is_valid_cpf(v):
            raise ValueError("CPF inválido")
        return normalize_cpf(v)


class FreelancerProfileCreate(_FreelancerProfileBase):
    display_name: str = Field(min_length=2, max_length=100)


class FreelancerProfileUpdate(_FreelancerProfileBase):
    pass


class FreelancerProfileRead(BaseModel):
    """View pública — NÃO inclui CPF (apenas booleano `has_cpf`)."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    display_name: str
    bio: str | None
    phone: str | None
    avatar_url: str | None
    has_cpf: bool
    created_at: datetime
    updated_at: datetime


# ── Estabelecimento ───────────────────────────────────────────────────────────


class _EstablishmentProfileBase(BaseModel):
    business_name: str | None = Field(default=None, min_length=2, max_length=200)
    address_line: str | None = Field(default=None, max_length=500)
    neighborhood: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: StateUF | None = None
    cep: str | None = None
    phone: Phone | None = None
    cnpj: str | None = None

    @field_validator("cep", mode="before")
    @classmethod
    def _validate_cep(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if not is_valid_cep(v):
            raise ValueError("CEP inválido")
        return normalize_cep(v)

    @field_validator("cnpj", mode="before")
    @classmethod
    def _validate_cnpj(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if not is_valid_cnpj(v):
            raise ValueError("CNPJ inválido")
        return normalize_cnpj(v)


class EstablishmentProfileCreate(_EstablishmentProfileBase):
    business_name: str = Field(min_length=2, max_length=200)


class EstablishmentProfileUpdate(_EstablishmentProfileBase):
    pass


class EstablishmentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    business_name: str
    address_line: str | None
    neighborhood: str | None
    city: str | None
    state: str | None
    cep: str | None
    phone: str | None
    avatar_url: str | None
    has_cnpj: bool
    created_at: datetime
    updated_at: datetime
