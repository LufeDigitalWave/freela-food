"""Perfil de estabelecimento — 1:1 com User."""

import uuid
from decimal import Decimal

from geoalchemy2 import Geography, WKBElement
from sqlalchemy import ForeignKey, Integer, LargeBinary, Numeric, String
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
    neighborhood: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    cep: Mapped[str | None] = mapped_column(String(8), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cnpj_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    location: Mapped[WKBElement | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # Rating agregado (Sprint 5)
    average_rating: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    total_reviews: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
