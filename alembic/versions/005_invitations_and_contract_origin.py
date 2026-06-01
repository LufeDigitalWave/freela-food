"""invitations + origem polimorfica do service_contract (application XOR invitation)

Revision ID: 005_invitations_origin
Revises: 004_apps_contracts_notif
Create Date: 2026-06-01 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005_invitations_origin"
down_revision: str | None = "004_apps_contracts_notif"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # invitations
    op.create_table(
        "invitations",
        sa.Column(
            "id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("establishment_id", sa.UUID(), nullable=False),
        sa.Column("freelancer_id", sa.UUID(), nullable=False),
        sa.Column("skill_category_id", sa.UUID(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("proposed_hourly_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("proposed_total_pay", sa.Numeric(10, 2), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["establishment_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["freelancer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["skill_category_id"], ["skill_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'declined', 'withdrawn', 'expired')",
            name="invitations_status_check",
        ),
        sa.CheckConstraint("end_at > start_at", name="invitations_dates_check"),
        sa.CheckConstraint(
            "message IS NULL OR length(message) <= 1000",
            name="invitations_message_length_check",
        ),
    )
    op.create_index(
        "ix_invitations_freelancer_status",
        "invitations",
        ["freelancer_id", "status"],
    )
    op.create_index(
        "ix_invitations_establishment_status",
        "invitations",
        ["establishment_id", "status"],
    )
    op.create_index("ix_invitations_expires_at", "invitations", ["expires_at"])

    # service_contracts: origem polimorfica
    op.alter_column("service_contracts", "application_id", nullable=True)
    op.alter_column("service_contracts", "job_posting_id", nullable=True)
    op.add_column(
        "service_contracts", sa.Column("invitation_id", sa.UUID(), nullable=True)
    )
    op.create_foreign_key(
        "fk_service_contracts_invitation",
        "service_contracts",
        "invitations",
        ["invitation_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_service_contracts_invitation", "service_contracts", ["invitation_id"]
    )
    op.create_check_constraint(
        "service_contracts_origin_check",
        "service_contracts",
        "(application_id IS NOT NULL AND invitation_id IS NULL) "
        "OR (application_id IS NULL AND invitation_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "service_contracts_origin_check", "service_contracts", type_="check"
    )
    op.drop_constraint(
        "uq_service_contracts_invitation", "service_contracts", type_="unique"
    )
    op.drop_constraint(
        "fk_service_contracts_invitation", "service_contracts", type_="foreignkey"
    )
    op.drop_column("service_contracts", "invitation_id")
    op.alter_column("service_contracts", "job_posting_id", nullable=False)
    op.alter_column("service_contracts", "application_id", nullable=False)

    op.drop_index("ix_invitations_expires_at", table_name="invitations")
    op.drop_index("ix_invitations_establishment_status", table_name="invitations")
    op.drop_index("ix_invitations_freelancer_status", table_name="invitations")
    op.drop_table("invitations")
