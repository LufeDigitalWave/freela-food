"""Testes unitários do engine de scoring (Sprint 7).

Testa a função compute_score isoladamente com dados mockados.
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.core.config import Settings
from app.domain.repositories.freelancer_repository import FreelancerMatchData
from app.domain.services.matching_service import compute_score


def _make_settings(**overrides: float) -> Settings:
    """Settings com pesos default (ou override)."""
    defaults = {
        "database_url": "postgresql+asyncpg://x:x@localhost/x",
        "redis_url": "redis://localhost",
        "jwt_secret": "a" * 64,
        "db_encryption_key": "b" * 64,
        "s3_endpoint_url": "http://localhost:9000",
        "s3_bucket": "test",
        "s3_public_base_url": "http://localhost:9000/test",
        "s3_access_key": "key",
        "s3_secret_key": "secret",
    }
    return Settings(**defaults, **overrides)  # type: ignore[arg-type]


def _make_profile(
    *,
    average_rating: Decimal | None = Decimal("4.00"),
    total_reviews: int = 5,
    completed_contracts_count: int = 10,
    no_show_count: int = 0,
) -> MagicMock:
    p = MagicMock()
    p.average_rating = average_rating
    p.total_reviews = total_reviews
    p.completed_contracts_count = completed_contracts_count
    p.no_show_count = no_show_count
    return p


def _make_data(
    *,
    distance_m: float = 1000.0,
    has_skill: bool = True,
    repeat_hire_count: int = 0,
    profile: MagicMock | None = None,
) -> FreelancerMatchData:
    return FreelancerMatchData(
        profile=profile or _make_profile(),
        distance_m=distance_m,
        has_skill=has_skill,
        repeat_hire_count=repeat_hire_count,
    )


def test_perfect_candidate_scores_high() -> None:
    """Candidato com todos os fatores no máximo."""
    data = _make_data(
        distance_m=0.0,
        has_skill=True,
        repeat_hire_count=5,
        profile=_make_profile(
            average_rating=Decimal("5.00"),
            completed_contracts_count=20,
            no_show_count=0,
        ),
    )
    score = compute_score(data, max_distance_m=10000.0, settings=_make_settings())
    assert score >= 95.0  # quase 100


def test_worst_candidate_scores_low() -> None:
    """Candidato longe, sem skill, rating ruim, unreliable."""
    data = _make_data(
        distance_m=10000.0,  # = max_distance → proximity = 0
        has_skill=False,
        repeat_hire_count=0,
        profile=_make_profile(
            average_rating=Decimal("1.00"),
            completed_contracts_count=5,
            no_show_count=5,  # reliability = 0
        ),
    )
    score = compute_score(data, max_distance_m=10000.0, settings=_make_settings())
    assert score < 15.0


def test_proximity_factor() -> None:
    """Mais perto = score maior."""
    settings = _make_settings()
    close = _make_data(distance_m=100.0)
    far = _make_data(distance_m=9000.0)
    score_close = compute_score(close, max_distance_m=10000.0, settings=settings)
    score_far = compute_score(far, max_distance_m=10000.0, settings=settings)
    assert score_close > score_far


def test_skill_match_bonus() -> None:
    """Ter a skill aumenta o score."""
    settings = _make_settings()
    with_skill = _make_data(has_skill=True)
    without_skill = _make_data(has_skill=False)
    s1 = compute_score(with_skill, max_distance_m=10000.0, settings=settings)
    s2 = compute_score(without_skill, max_distance_m=10000.0, settings=settings)
    assert s1 > s2
    # Diferença deve ser ~20% do score total (peso 0.20 * 100)
    assert (s1 - s2) == pytest.approx(20.0, abs=1.0)


def test_no_show_penalty() -> None:
    """No-shows reduzem o score."""
    settings = _make_settings()
    reliable = _make_data(profile=_make_profile(no_show_count=0, completed_contracts_count=10))
    unreliable = _make_data(profile=_make_profile(no_show_count=5, completed_contracts_count=10))
    s1 = compute_score(reliable, max_distance_m=10000.0, settings=settings)
    s2 = compute_score(unreliable, max_distance_m=10000.0, settings=settings)
    assert s1 > s2


def test_repeat_hire_bonus() -> None:
    """Repeat hire com o mesmo estabelecimento aumenta score."""
    settings = _make_settings()
    first_time = _make_data(repeat_hire_count=0)
    repeat = _make_data(repeat_hire_count=3)
    s1 = compute_score(first_time, max_distance_m=10000.0, settings=settings)
    s2 = compute_score(repeat, max_distance_m=10000.0, settings=settings)
    assert s2 > s1
    # Diferença deve ser ~10% (peso 0.10 * 100)
    assert (s2 - s1) == pytest.approx(10.0, abs=1.0)


def test_null_rating_is_neutral() -> None:
    """Freelancer sem rating (NULL) recebe 0.5 (neutro, não penaliza)."""
    settings = _make_settings()
    no_rating = _make_data(profile=_make_profile(average_rating=None))
    mid_rating = _make_data(profile=_make_profile(average_rating=Decimal("3.00")))
    s1 = compute_score(no_rating, max_distance_m=10000.0, settings=settings)
    s2 = compute_score(mid_rating, max_distance_m=10000.0, settings=settings)
    assert s1 == s2  # 3.00 normaliza pra 0.5, igual ao default NULL
