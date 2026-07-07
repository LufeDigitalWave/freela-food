"""Report — denúncia de conteúdo inapropriado (Sprint 8)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, UUIDPKMixin


class Report(Base, UUIDPKMixin):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint(
            "target_type IN ('user', 'review')",
            name="reports_target_type_check",
        ),
        CheckConstraint(
            "reason IN ('spam', 'offensive', 'fake', 'harassment', 'other')",
            name="reports_reason_check",
        ),
        CheckConstraint(
            "status IN ('pending', 'resolved_action', 'resolved_dismissed')",
            name="reports_status_check",
        ),
        CheckConstraint(
            "description IS NULL OR length(description) <= 1000",
            name="reports_description_length_check",
        ),
    )

    reporter_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
