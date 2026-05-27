"""Perfil de estabelecimento — 1:1 com User. Esqueleto para Sprint 0."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, SoftDeleteMixin, TimestampMixin


class EstablishmentProfile(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "establishment_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    address_line: Mapped[str | None] = mapped_column(String(500), nullable=True)
