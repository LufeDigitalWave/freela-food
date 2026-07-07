"""reports + moderation fields em reviews

Revision ID: 007_reports_moderation
Revises: 006_reviews
Create Date: 2026-07-07 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

revision: str = "007_reports_moderation"
down_revision: str | None = "006_reviews"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Tabela reports ---
    op.create_table(
        "reports",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("reporter_id", PG_UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("resolved_by", PG_UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        # Constraints
        sa.CheckConstraint(
            "target_type IN ('user', 'review')",
            name="reports_target_type_check",
        ),
        sa.CheckConstraint(
            "reason IN ('spam', 'offensive', 'fake', 'harassment', 'other')",
            name="reports_reason_check",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'resolved_action', 'resolved_dismissed')",
            name="reports_status_check",
        ),
        sa.CheckConstraint(
            "description IS NULL OR length(description) <= 1000",
            name="reports_description_length_check",
        ),
    )

    # Índices
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_target", "reports", ["target_type", "target_id"])
    op.create_index("ix_reports_reporter", "reports", ["reporter_id"])

    # --- Campos de moderação em reviews ---
    op.add_column(
        "reviews",
        sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "reviews",
        sa.Column("hidden_by", PG_UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reviews", "hidden_by")
    op.drop_column("reviews", "hidden_at")
    op.drop_index("ix_reports_reporter", table_name="reports")
    op.drop_index("ix_reports_target", table_name="reports")
    op.drop_index("ix_reports_status", table_name="reports")
    op.drop_table("reports")
