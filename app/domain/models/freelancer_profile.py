"""Perfil de freelancer — 1:1 com User."""

import uuid

from geoalchemy2 import Geography, WKBElement
from sqlalchemy import ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, SoftDeleteMixin, TimestampMixin


class FreelancerProfile(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "freelancer_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cpf_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # Geo: ponto base do freelancer + raio de atuação
    location: Mapped[WKBElement | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )
    service_radius_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
