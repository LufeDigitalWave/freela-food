"""Vaga (JobPosting) — postada por estabelecimento, candidatável por freelancer."""

import uuid
from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geography, WKBElement
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class JobPosting(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "job_postings"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'open', 'filled', 'cancelled', 'completed')",
            name="job_postings_status_check",
        ),
        CheckConstraint("end_at > start_at", name="job_postings_dates_check"),
        CheckConstraint(
            "(hourly_rate IS NOT NULL) OR (total_pay IS NOT NULL)",
            name="job_postings_pay_required_check",
        ),
    )

    establishment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skill_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    location: Mapped[WKBElement] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    address_line: Mapped[str | None] = mapped_column(String(500), nullable=True)
    neighborhood: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    cep: Mapped[str | None] = mapped_column(String(8), nullable=True)

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    hourly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_pay: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default="draft", index=True
    )
