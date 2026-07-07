"""Repository de busca de freelancers por proximidade (PostGIS)."""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.freelancer_skill import FreelancerSkill
from app.domain.models.service_contract import ServiceContract


@dataclass
class FreelancerMatchData:
    """Dados enriquecidos de freelancer pra scoring."""

    profile: FreelancerProfile
    distance_m: float
    has_skill: bool
    repeat_hire_count: int


class FreelancerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search_by_proximity(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_m: float,
        skill_category_id: uuid.UUID | None,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[FreelancerProfile, float]], int]:
        point_expr = func.ST_SetSRID(
            func.ST_MakePoint(longitude, latitude), 4326
        ).cast(FreelancerProfile.location.type)

        conditions = [
            FreelancerProfile.deleted_at.is_(None),
            FreelancerProfile.location.is_not(None),
            func.ST_DWithin(FreelancerProfile.location, point_expr, radius_m),
        ]
        if skill_category_id is not None:
            conditions.append(
                FreelancerProfile.user_id.in_(
                    select(FreelancerSkill.freelancer_user_id).where(
                        FreelancerSkill.skill_category_id == skill_category_id
                    )
                )
            )

        distance_col = func.ST_Distance(
            FreelancerProfile.location, point_expr
        ).label("distance_m")

        base = select(FreelancerProfile, distance_col).where(*conditions)

        total = await self._session.scalar(
            select(func.count()).select_from(
                select(FreelancerProfile.user_id).where(*conditions).subquery()
            )
        )

        result = await self._session.execute(
            base.order_by(
                distance_col.asc(),
                FreelancerProfile.completed_contracts_count.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows: list[tuple[FreelancerProfile, float]] = [
            (row[0], float(row[1])) for row in result.all()
        ]
        return rows, int(total or 0)

    async def search_for_job_matching(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_m: float,
        skill_category_id: uuid.UUID,
        establishment_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[FreelancerMatchData], int]:
        """Busca enriquecida pra matching: retorna perfis + dados de scoring."""
        point_expr = func.ST_SetSRID(
            func.ST_MakePoint(longitude, latitude), 4326
        ).cast(FreelancerProfile.location.type)

        conditions = [
            FreelancerProfile.deleted_at.is_(None),
            FreelancerProfile.location.is_not(None),
            func.ST_DWithin(FreelancerProfile.location, point_expr, radius_m),
        ]

        distance_col = func.ST_Distance(
            FreelancerProfile.location, point_expr
        ).label("distance_m")

        # Subquery: tem a skill?
        has_skill_subq = (
            select(FreelancerSkill.freelancer_user_id)
            .where(FreelancerSkill.skill_category_id == skill_category_id)
        ).correlate(FreelancerProfile)

        has_skill_col = FreelancerProfile.user_id.in_(has_skill_subq).label("has_skill")

        # Subquery: repeat hire count
        repeat_hire_subq = (
            select(func.count())
            .select_from(ServiceContract)
            .where(
                ServiceContract.freelancer_id == FreelancerProfile.user_id,
                ServiceContract.establishment_id == establishment_id,
                ServiceContract.status == "completed",
            )
        ).correlate(FreelancerProfile).scalar_subquery().label("repeat_hire_count")

        base = select(
            FreelancerProfile, distance_col, has_skill_col, repeat_hire_subq
        ).where(*conditions)

        total = await self._session.scalar(
            select(func.count()).select_from(
                select(FreelancerProfile.user_id).where(*conditions).subquery()
            )
        )

        # Busca sem ORDER BY — scoring é feito no service
        result = await self._session.execute(
            base.offset((page - 1) * page_size).limit(page_size)
        )

        items: list[FreelancerMatchData] = [
            FreelancerMatchData(
                profile=row[0],
                distance_m=float(row[1]),
                has_skill=bool(row[2]),
                repeat_hire_count=int(row[3] or 0),
            )
            for row in result.all()
        ]
        return items, int(total or 0)
