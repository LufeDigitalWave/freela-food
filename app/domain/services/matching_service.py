"""Engine de matching/scoring de freelancers (Sprint 7).

Scoring determinístico multi-fator com pesos configuráveis.
Cada fator normalizado 0-1; score final = sum(peso * fator) * 100.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import NotFoundError, PermissionDenied
from app.domain.repositories.freelancer_repository import (
    FreelancerMatchData,
    FreelancerRepository,
)
from app.domain.repositories.profile_repository import ProfileRepository
from app.domain.schemas.matching import MatchList, ScoredFreelancerRead


def compute_score(
    data: FreelancerMatchData,
    *,
    max_distance_m: float,
    settings: Settings,
) -> float:
    """Calcula score composto 0-100 pra um candidato.

    Função pura — pode ser testada unitariamente.
    """
    profile = data.profile

    # Proximidade: mais perto = melhor
    proximity = (
        max(0.0, 1.0 - data.distance_m / max_distance_m)
        if max_distance_m > 0
        else 1.0
    )

    # Skill match: 1.0 se tem, 0.0 se não
    skill = 1.0 if data.has_skill else 0.0

    # Rating: normaliza 1-5 → 0-1; NULL (sem reviews) = 0.5 (neutro)
    if profile.average_rating is not None:
        rating = (float(profile.average_rating) - 1.0) / 4.0
    else:
        rating = 0.5

    # Confiabilidade: penaliza no-shows
    completed = max(profile.completed_contracts_count, 1)
    reliability = max(0.0, 1.0 - profile.no_show_count / completed)

    # Experiência: satura em 20 contratos
    experience = min(profile.completed_contracts_count / 20.0, 1.0)

    # Repeat hire: satura em 3 contratos com este estabelecimento
    repeat_hire = min(data.repeat_hire_count / 3.0, 1.0)

    # Score composto
    score = (
        settings.match_weight_proximity * proximity
        + settings.match_weight_skill * skill
        + settings.match_weight_rating * rating
        + settings.match_weight_reliability * reliability
        + settings.match_weight_experience * experience
        + settings.match_weight_repeat_hire * repeat_hire
    ) * 100.0

    return round(score, 2)


class MatchingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._freelancers = FreelancerRepository(session)
        self._profiles = ProfileRepository(session)

    async def matches_for_job(
        self,
        *,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        radius_km: float = 50.0,
        page: int = 1,
        page_size: int = 20,
    ) -> MatchList:
        """Retorna freelancers ranqueados por compatibilidade com a vaga."""
        settings = get_settings()

        # Validar: job existe e user é dono
        from app.domain.repositories.job_repository import JobRepository

        job_repo = JobRepository(self._session)
        job = await job_repo.get_by_id(job_id)
        if job is None:
            raise NotFoundError("Vaga não encontrada")
        if job.establishment_id != user_id:
            raise PermissionDenied()

        # Extrair localização do job
        from geoalchemy2.shape import to_shape

        job_point = to_shape(job.location)
        lat, lng = job_point.y, job_point.x

        # Busca enriquecida
        candidates, total = await self._freelancers.search_for_job_matching(
            latitude=lat,
            longitude=lng,
            radius_m=radius_km * 1000,
            skill_category_id=job.skill_category_id,
            establishment_id=user_id,
            page=page,
            page_size=page_size,
        )

        # Calcular max_distance pra normalização
        max_dist = max((c.distance_m for c in candidates), default=1.0)
        if max_dist == 0:
            max_dist = 1.0

        # Scoring + ordenação
        scored: list[ScoredFreelancerRead] = []
        for c in candidates:
            score = compute_score(c, max_distance_m=max_dist, settings=settings)
            p = c.profile
            scored.append(
                ScoredFreelancerRead(
                    user_id=p.user_id,
                    display_name=p.display_name,
                    bio=p.bio,
                    avatar_url=p.avatar_url,
                    completed_contracts_count=p.completed_contracts_count,
                    no_show_count=p.no_show_count,
                    average_rating=(
                        float(p.average_rating) if p.average_rating is not None else None
                    ),
                    total_reviews=p.total_reviews,
                    distance_m=c.distance_m,
                    match_score=score,
                )
            )

        # Ordenar por score desc
        scored.sort(key=lambda x: x.match_score, reverse=True)

        return MatchList(
            items=scored,
            total=total,
            page=page,
            page_size=page_size,
        )
