"""Tabela de junção M:N entre FreelancerProfile e SkillCategory."""

import uuid

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin


class FreelancerSkill(Base, TimestampMixin):
    __tablename__ = "freelancer_skills"
    __table_args__ = (
        PrimaryKeyConstraint("freelancer_user_id", "skill_category_id"),
    )

    freelancer_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("freelancer_profiles.user_id", ondelete="CASCADE"),
    )
    skill_category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skill_categories.id", ondelete="CASCADE"),
    )
