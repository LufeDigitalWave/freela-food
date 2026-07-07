"""payments + pix_key em freelancer_profiles

Revision ID: 008_payments
Revises: 007_reports_moderation
Create Date: 2026-07-07 14:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

revision: str = "008_payments"
down_revision: str | None = "007_reports_moderation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Tabela payments ---
    op.create_table(
        "payments",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contract_id", PG_UUID(as_uuid=True), sa.ForeignKey("service_contracts.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("pix_key", sa.String(100), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_by", PG_UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("disputed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        # Constraints
        sa.UniqueConstraint("contract_id", name="uq_payments_contract"),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'disputed')",
            name="payments_status_check",
        ),
    )
    op.create_index("ix_payments_status", "payments", ["status"])

    # --- pix_key em freelancer_profiles ---
    op.add_column(
        "freelancer_profiles",
        sa.Column("pix_key", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("freelancer_profiles", "pix_key")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_table("payments")
