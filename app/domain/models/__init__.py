"""Re-export de todos os modelos — Alembic detecta tudo via Base.metadata."""

from app.domain.models.application import Application
from app.domain.models.audit_log import AuditLog
from app.domain.models.base import Base
from app.domain.models.establishment_profile import EstablishmentProfile
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.freelancer_skill import FreelancerSkill
from app.domain.models.job_posting import JobPosting
from app.domain.models.notification import Notification
from app.domain.models.service_contract import ServiceContract
from app.domain.models.skill_category import SkillCategory
from app.domain.models.user import User

__all__ = [
    "Application",
    "AuditLog",
    "Base",
    "EstablishmentProfile",
    "FreelancerProfile",
    "FreelancerSkill",
    "JobPosting",
    "Notification",
    "ServiceContract",
    "SkillCategory",
    "User",
]
