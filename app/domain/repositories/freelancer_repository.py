"""Repository de busca de freelancers por proximidade (PostGIS)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.freelancer_skill import FreelancerSkill


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
