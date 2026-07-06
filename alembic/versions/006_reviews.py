"""reviews + rating agregado nos perfis

Revision ID: 006_reviews
Revises: 005_invitations_origin
Create Date: 2026-07-06 10:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

revision: str = "006_reviews"
down_revision: str | None = "005_invitations_origin"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Tabela reviews ---
    op.create_table(
        "reviews",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contract_id", PG_UUID(as_uuid=True), sa.ForeignKey("service_contracts.id"), nullable=False),
        sa.Column("reviewer_id", PG_UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reviewee_id", PG_UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stars", sa.SmallInteger, nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("visible_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        # Constraints
        sa.UniqueConstraint("contract_id", "reviewer_id", name="uq_reviews_contract_reviewer"),
        sa.CheckConstraint("stars >= 1 AND stars <= 5", name="reviews_stars_check"),
        sa.CheckConstraint("comment IS NULL OR length(comment) <= 2000", name="reviews_comment_length_check"),
        sa.CheckConstraint("reviewer_id != reviewee_id", name="reviews_no_self_review_check"),
    )

    # Índices
    op.create_index("ix_reviews_reviewee_visible", "reviews", ["reviewee_id", "visible_at"])
    op.create_index("ix_reviews_contract", "reviews", ["contract_id"])

    # --- Rating agregado em freelancer_profiles ---
    op.add_column(
        "freelancer_profiles",
        sa.Column("average_rating", sa.Numeric(3, 2), nullable=True),
    )
    op.add_column(
        "freelancer_profiles",
        sa.Column("total_reviews", sa.Integer, nullable=False, server_default="0"),
    )

    # --- Rating agregado em establishment_profiles ---
    op.add_column(
        "establishment_profiles",
        sa.Column("average_rating", sa.Numeric(3, 2), nullable=True),
    )
    op.add_column(
        "establishment_profiles",
        sa.Column("total_reviews", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("establishment_profiles", "total_reviews")
    op.drop_column("establishment_profiles", "average_rating")
    op.drop_column("freelancer_profiles", "total_reviews")
    op.drop_column("freelancer_profiles", "average_rating")
    op.drop_index("ix_reviews_contract", table_name="reviews")
    op.drop_index("ix_reviews_reviewee_visible", table_name="reviews")
    op.drop_table("reviews")
