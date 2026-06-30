"""Invitation — convite direto do estabelecimento ao freelancer (Fluxo B)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin, UUIDPKMixin


class Invitation(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "invitations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'declined', 'withdrawn', 'expired')",
            name="invitations_status_check",
        ),
        CheckConstraint("end_at > start_at", name="invitations_dates_check"),
        CheckConstraint(
            "message IS NULL OR length(message) <= 1000",
            name="invitations_message_length_check",
        ),
        Index("ix_invitations_freelancer_status", "freelancer_id", "status"),
        Index("ix_invitations_establishment_status", "establishment_id", "status"),
        Index("ix_invitations_expires_at", "expires_at"),
    )

    establishment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    skill_category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("skill_categories.id"), nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    proposed_hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    proposed_total_pay: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
