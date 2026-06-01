"""Service da busca de freelancers (Fluxo B)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDenied
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.repositories.freelancer_repository import FreelancerRepository
from app.domain.repositories.profile_repository import ProfileRepository
from app.domain.schemas.freelancer_search import (
    FreelancerSearchList,
    FreelancerSearchRead,
)


def _to_read(profile: FreelancerProfile, distance_m: float) -> FreelancerSearchRead:
    return FreelancerSearchRead(
        user_id=profile.user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        completed_contracts_count=profile.completed_contracts_count,
        no_show_count=profile.no_show_count,
        distance_m=distance_m,
    )


class FreelancerSearchService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = FreelancerRepository(session)
        self._profiles = ProfileRepository(session)

    async def search(
        self,
        *,
        user_id: uuid.UUID,
        latitude: float,
        longitude: float,
        radius_km: float,
        skill_category_id: uuid.UUID | None,
        page: int,
        page_size: int,
    ) -> FreelancerSearchList:
        # Só estabelecimento (com perfil) pode buscar freelancers
        if await self._profiles.get_establishment(user_id) is None:
            raise PermissionDenied()

        rows, total = await self._repo.search_by_proximity(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_km * 1000,
            skill_category_id=skill_category_id,
            page=page,
            page_size=page_size,
        )
        return FreelancerSearchList(
            items=[_to_read(p, d) for p, d in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
