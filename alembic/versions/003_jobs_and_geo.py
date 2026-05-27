"""jobs and geo

Revision ID: 003_jobs_and_geo
Revises: 1baf1247a1bf
Create Date: 2026-05-27 17:30:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from geoalchemy2 import Geography

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '003_jobs_and_geo'
down_revision: str | None = '1baf1247a1bf'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Geo nos profiles ─────────────────────────────────────────────────────
    op.add_column(
        'freelancer_profiles',
        sa.Column(
            'location',
            Geography(geometry_type='POINT', srid=4326, spatial_index=False),
            nullable=True,
        ),
    )
    op.add_column(
        'freelancer_profiles',
        sa.Column('service_radius_km', sa.Integer(), nullable=True),
    )
    op.add_column(
        'establishment_profiles',
        sa.Column(
            'location',
            Geography(geometry_type='POINT', srid=4326, spatial_index=False),
            nullable=True,
        ),
    )
    op.create_index(
        'idx_freelancer_profiles_location',
        'freelancer_profiles',
        ['location'],
        postgresql_using='gist',
    )
    op.create_index(
        'idx_establishment_profiles_location',
        'establishment_profiles',
        ['location'],
        postgresql_using='gist',
    )

    # ── job_postings ─────────────────────────────────────────────────────────
    op.create_table(
        'job_postings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('establishment_id', sa.UUID(), nullable=False),
        sa.Column('skill_category_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'location',
            Geography(geometry_type='POINT', srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column('address_line', sa.String(length=500), nullable=True),
        sa.Column('neighborhood', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=2), nullable=True),
        sa.Column('cep', sa.String(length=8), nullable=True),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('total_pay', sa.Numeric(10, 2), nullable=True),
        sa.Column(
            'status', sa.String(length=20), nullable=False, server_default='draft'
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ['establishment_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['skill_category_id'], ['skill_categories.id'], ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status IN ('draft', 'open', 'filled', 'cancelled', 'completed')",
            name='job_postings_status_check',
        ),
        sa.CheckConstraint(
            'end_at > start_at', name='job_postings_dates_check'
        ),
        sa.CheckConstraint(
            '(hourly_rate IS NOT NULL) OR (total_pay IS NOT NULL)',
            name='job_postings_pay_required_check',
        ),
    )
    op.create_index(
        'ix_job_postings_establishment_id', 'job_postings', ['establishment_id']
    )
    op.create_index(
        'ix_job_postings_skill_category_id', 'job_postings', ['skill_category_id']
    )
    op.create_index('ix_job_postings_status', 'job_postings', ['status'])
    op.create_index(
        'idx_job_postings_location',
        'job_postings',
        ['location'],
        postgresql_using='gist',
    )

    # ── Seed inicial de skill_categories ─────────────────────────────────────
    op.execute(
        """
        INSERT INTO skill_categories (id, slug, name, created_at, updated_at) VALUES
          (gen_random_uuid(), 'garcom', 'Garçom/Garçonete', now(), now()),
          (gen_random_uuid(), 'barman', 'Barman/Barwoman', now(), now()),
          (gen_random_uuid(), 'cozinheiro', 'Cozinheiro', now(), now()),
          (gen_random_uuid(), 'auxiliar_cozinha', 'Auxiliar de Cozinha', now(), now()),
          (gen_random_uuid(), 'chapeiro', 'Chapeiro', now(), now()),
          (gen_random_uuid(), 'sushiman', 'Sushiman', now(), now()),
          (gen_random_uuid(), 'pizzaiolo', 'Pizzaiolo', now(), now()),
          (gen_random_uuid(), 'copeiro', 'Copeiro', now(), now()),
          (gen_random_uuid(), 'recepcionista', 'Recepcionista', now(), now()),
          (gen_random_uuid(), 'seguranca', 'Segurança', now(), now()),
          (gen_random_uuid(), 'limpeza', 'Limpeza', now(), now()),
          (gen_random_uuid(), 'entregador', 'Entregador', now(), now()),
          (gen_random_uuid(), 'promoter', 'Promoter/Hostess', now(), now())
        ON CONFLICT (slug) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM skill_categories WHERE slug IN (
          'garcom', 'barman', 'cozinheiro', 'auxiliar_cozinha', 'chapeiro',
          'sushiman', 'pizzaiolo', 'copeiro', 'recepcionista', 'seguranca',
          'limpeza', 'entregador', 'promoter'
        )
        """
    )
    op.drop_index('idx_job_postings_location', table_name='job_postings')
    op.drop_index('ix_job_postings_status', table_name='job_postings')
    op.drop_index(
        'ix_job_postings_skill_category_id', table_name='job_postings'
    )
    op.drop_index(
        'ix_job_postings_establishment_id', table_name='job_postings'
    )
    op.drop_table('job_postings')
    op.drop_index(
        'idx_establishment_profiles_location', table_name='establishment_profiles'
    )
    op.drop_column('establishment_profiles', 'location')
    op.drop_index(
        'idx_freelancer_profiles_location', table_name='freelancer_profiles'
    )
    op.drop_column('freelancer_profiles', 'service_radius_km')
    op.drop_column('freelancer_profiles', 'location')
