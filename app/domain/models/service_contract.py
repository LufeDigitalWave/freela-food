"""ServiceContract — contrato gerado pelo aceite (Fluxo A) ou convite (Fluxo B futuro)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin, UUIDPKMixin


class ServiceContract(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "service_contracts"
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_service_contracts_application"),
        CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')",
            name="service_contracts_status_check",
        ),
        CheckConstraint(
            "cancelled_by IS NULL OR cancelled_by IN "
            "('freelancer', 'establishment', 'system')",
            name="service_contracts_cancelled_by_check",
        ),
        CheckConstraint("end_at > start_at", name="service_contracts_dates_check"),
        CheckConstraint(
            "(cancelled_at IS NULL AND cancelled_by IS NULL) "
            "OR (cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL)",
            name="service_contracts_cancel_consistency_check",
        ),
        CheckConstraint(
            "cancel_reason IS NULL OR length(cancel_reason) <= 1000",
            name="service_contracts_reason_length_check",
        ),
        UniqueConstraint("invitation_id", name="uq_service_contracts_invitation"),
        CheckConstraint(
            "(application_id IS NOT NULL AND invitation_id IS NULL) "
            "OR (application_id IS NULL AND invitation_id IS NOT NULL)",
            name="service_contracts_origin_check",
        ),
    )

    application_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=True,
    )
    invitation_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("invitations.id"),
        nullable=True,
    )
    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("job_postings.id"),
        nullable=True,
    )
    freelancer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    establishment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    agreed_hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    agreed_total_pay: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="scheduled", server_default="scheduled"
    )
    cancelled_by: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    no_show: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
