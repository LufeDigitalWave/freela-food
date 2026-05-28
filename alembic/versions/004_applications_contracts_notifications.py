"""applications, service_contracts, notifications + counters em freelancer_profiles

Revision ID: 004_apps_contracts_notif
Revises: 003_jobs_and_geo
Create Date: 2026-05-28 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "004_apps_contracts_notif"
down_revision: str | None = "003_jobs_and_geo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── applications ─────────────────────────────────────────────────────────
    op.create_table(
        "applications",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("job_posting_id", sa.UUID(), nullable=False),
        sa.Column("freelancer_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["job_posting_id"], ["job_postings.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["freelancer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "job_posting_id", "freelancer_id", name="uq_applications_job_freelancer"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'withdrawn')",
            name="applications_status_check",
        ),
        sa.CheckConstraint(
            "message IS NULL OR length(message) <= 500",
            name="applications_message_length_check",
        ),
    )
    op.create_index(
        "ix_applications_job_posting_status",
        "applications",
        ["job_posting_id", "status"],
    )
    op.create_index(
        "ix_applications_freelancer_status",
        "applications",
        ["freelancer_id", "status"],
    )

    # ── service_contracts ────────────────────────────────────────────────────
    op.create_table(
        "service_contracts",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("job_posting_id", sa.UUID(), nullable=False),
        sa.Column("freelancer_id", sa.UUID(), nullable=False),
        sa.Column("establishment_id", sa.UUID(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("agreed_hourly_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("agreed_total_pay", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("cancelled_by", sa.String(length=20), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column(
            "no_show",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["job_posting_id"], ["job_postings.id"]),
        sa.ForeignKeyConstraint(["freelancer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["establishment_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id", name="uq_service_contracts_application"),
        sa.CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')",
            name="service_contracts_status_check",
        ),
        sa.CheckConstraint(
            "cancelled_by IS NULL OR cancelled_by IN ('freelancer', 'establishment', 'system')",
            name="service_contracts_cancelled_by_check",
        ),
        sa.CheckConstraint(
            "end_at > start_at", name="service_contracts_dates_check"
        ),
        sa.CheckConstraint(
            "(cancelled_at IS NULL AND cancelled_by IS NULL) "
            "OR (cancelled_at IS NOT NULL AND cancelled_by IS NOT NULL)",
            name="service_contracts_cancel_consistency_check",
        ),
        sa.CheckConstraint(
            "cancel_reason IS NULL OR length(cancel_reason) <= 1000",
            name="service_contracts_reason_length_check",
        ),
    )
    op.create_index(
        "ix_service_contracts_freelancer_status_dates",
        "service_contracts",
        ["freelancer_id", "status", "start_at", "end_at"],
    )
    op.create_index(
        "ix_service_contracts_status_start_at",
        "service_contracts",
        ["status", "start_at"],
    )
    op.create_index(
        "ix_service_contracts_status_end_at",
        "service_contracts",
        ["status", "end_at"],
    )
    op.create_index(
        "ix_service_contracts_job_posting",
        "service_contracts",
        ["job_posting_id"],
    )

    # ── notifications ────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column(
            "payload",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_user_read_created",
        "notifications",
        ["user_id", "read_at", sa.text("created_at DESC")],
    )

    # ── freelancer_profiles counters ────────────────────────────────────────
    op.add_column(
        "freelancer_profiles",
        sa.Column(
            "no_show_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "freelancer_profiles",
        sa.Column(
            "completed_contracts_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("freelancer_profiles", "completed_contracts_count")
    op.drop_column("freelancer_profiles", "no_show_count")
    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(
        "ix_service_contracts_job_posting", table_name="service_contracts"
    )
    op.drop_index(
        "ix_service_contracts_status_end_at", table_name="service_contracts"
    )
    op.drop_index(
        "ix_service_contracts_status_start_at", table_name="service_contracts"
    )
    op.drop_index(
        "ix_service_contracts_freelancer_status_dates", table_name="service_contracts"
    )
    op.drop_table("service_contracts")
    op.drop_index(
        "ix_applications_freelancer_status", table_name="applications"
    )
    op.drop_index(
        "ix_applications_job_posting_status", table_name="applications"
    )
    op.drop_table("applications")
