"""Categoria de skill — referenciada por freelancers e (futuramente) job postings."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin, UUIDPKMixin


class SkillCategory(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "skill_categories"

    slug: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
