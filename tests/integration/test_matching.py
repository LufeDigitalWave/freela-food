"""Testes de integração do matching engine (Sprint 7)."""

import uuid

import pytest
from httpx import AsyncClient

from app.core.database import SessionLocal
from app.domain.services.matching_service import MatchingService
from tests.factories import (
    auth_header_for,
    make_establishment,
    make_freelancer,
    make_freelancer_skill,
    make_job,
    make_skill_category,
)


async def _setup_job_with_freelancers() -> dict:
    """Cria establishment + job + 3 freelancers com atributos variados.

    Usa coordenadas únicas (longe do default -23.55/-46.63) pra isolar do DB compartilhado.
    """
    from decimal import Decimal

    suffix = uuid.uuid4().hex[:8]
    # Coordenadas aleatórias por run pra não colidir com outros testes no DB compartilhado
    import random
    base_lat = random.uniform(30.0, 60.0)
    base_lng = random.uniform(-10.0, 30.0)
    async with SessionLocal() as session:
        est, _ = await make_establishment(
            session, email=f"est-{suffix}@test.com", lat=base_lat, lng=base_lng
        )
        cat = await make_skill_category(session, slug=f"cat-{suffix}", name=f"Cat {suffix}")
        job = await make_job(
            session,
            establishment_id=est.id,
            skill_category_id=cat.id,
            status="open",
            lat=base_lat,
            lng=base_lng,
        )

        # Freelancer 1: perto, tem skill, bom rating (deve ser #1)
        fl1, fp1 = await make_freelancer(
            session, email=f"fl1-{suffix}@test.com", lat=base_lat + 0.001, lng=base_lng + 0.001
        )
        await make_freelancer_skill(
            session, freelancer_user_id=fl1.id, skill_category_id=cat.id
        )
        fp1.average_rating = Decimal("4.50")
        fp1.total_reviews = 10
        fp1.completed_contracts_count = 15

        # Freelancer 2: perto, tem skill, sem rating
        fl2, _fp2 = await make_freelancer(
            session, email=f"fl2-{suffix}@test.com", lat=base_lat + 0.002, lng=base_lng + 0.002
        )
        await make_freelancer_skill(
            session, freelancer_user_id=fl2.id, skill_category_id=cat.id
        )

        # Freelancer 3: mais longe, sem skill, rating mediano
        fl3, fp3 = await make_freelancer(
            session, email=f"fl3-{suffix}@test.com", lat=base_lat + 0.1, lng=base_lng + 0.1
        )
        fp3.average_rating = Decimal("3.00")
        fp3.total_reviews = 3
        fp3.completed_contracts_count = 5

        await session.flush()
        await session.commit()
        return {
            "est_id": est.id,
            "est_email": f"est-{suffix}@test.com",
            "job_id": job.id,
            "fl1_id": fl1.id,
            "fl2_id": fl2.id,
            "fl3_id": fl3.id,
            "cat_id": cat.id,
        }


async def test_matches_returns_scored_list() -> None:
    ctx = await _setup_job_with_freelancers()
    async with SessionLocal() as session:
        result = await MatchingService(session).matches_for_job(
            user_id=ctx["est_id"],
            job_id=ctx["job_id"],
            radius_km=0.5,
        )
    assert result.total >= 2
    # Todos os items têm match_score
    for item in result.items:
        assert 0 <= item.match_score <= 100
    # Ordenado por score desc
    scores = [i.match_score for i in result.items]
    assert scores == sorted(scores, reverse=True)


async def test_skilled_freelancer_ranks_higher() -> None:
    ctx = await _setup_job_with_freelancers()
    # Raio de 0.5km — só pega fl1 e fl2 (a ~111-222m), não fl3 (a ~15km)
    async with SessionLocal() as session:
        result = await MatchingService(session).matches_for_job(
            user_id=ctx["est_id"],
            job_id=ctx["job_id"],
            radius_km=0.5,
        )
    # fl1 (skill + rating alto + perto) deve ter o maior score
    # Com coordenadas no oceano, só nossos freelancers próximos estão no raio
    assert result.total >= 2
    # fl1 deve estar no topo (skill + rating)
    fl1_in_results = [i for i in result.items if i.user_id == ctx["fl1_id"]]
    fl2_in_results = [i for i in result.items if i.user_id == ctx["fl2_id"]]
    assert len(fl1_in_results) == 1
    assert len(fl2_in_results) == 1
    assert fl1_in_results[0].match_score > fl2_in_results[0].match_score


async def test_permission_denied_non_owner() -> None:
    ctx = await _setup_job_with_freelancers()
    # Usar outro user que não é dono do job
    async with SessionLocal() as session:
        with pytest.raises(Exception) as exc_info:
            await MatchingService(session).matches_for_job(
                user_id=ctx["fl1_id"],  # freelancer tentando
                job_id=ctx["job_id"],
            )
    assert "Permissão" in str(exc_info.value)


async def test_job_not_found() -> None:
    ctx = await _setup_job_with_freelancers()
    fake_job = uuid.uuid4()
    async with SessionLocal() as session:
        with pytest.raises(Exception) as exc_info:
            await MatchingService(session).matches_for_job(
                user_id=ctx["est_id"],
                job_id=fake_job,
            )
    assert "não encontrada" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_endpoint_matches(client: AsyncClient) -> None:
    ctx = await _setup_job_with_freelancers()
    headers = await auth_header_for(client, ctx["est_email"])
    resp = await client.get(
        f"/v1/jobs/{ctx['job_id']}/matches?radius_km=50", headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 2
    # Primeiro item tem match_score
    assert body["items"][0]["match_score"] > 0


@pytest.mark.asyncio
async def test_endpoint_matches_non_owner_403(client: AsyncClient) -> None:
    ctx = await _setup_job_with_freelancers()
    # Registrar um user diferente
    suffix = uuid.uuid4().hex[:8]
    email = f"other-{suffix}@test.com"
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "Senha123!", "role": "establishment"},
    )
    login = await client.post(
        "/v1/auth/login", json={"email": email, "password": "Senha123!"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = await client.get(
        f"/v1/jobs/{ctx['job_id']}/matches", headers=headers
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_endpoint_pagination(client: AsyncClient) -> None:
    ctx = await _setup_job_with_freelancers()
    headers = await auth_header_for(client, ctx["est_email"])
    resp = await client.get(
        f"/v1/jobs/{ctx['job_id']}/matches?page_size=1&radius_km=50",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["page"] == 1
    assert body["page_size"] == 1


async def test_small_radius_filters_far_freelancers() -> None:
    """Raio pequeno exclui freelancers distantes."""
    ctx = await _setup_job_with_freelancers()
    # Raio de 0.5km — fl1 e fl2 (a ~111-222m do job), fl3 está a ~15km
    async with SessionLocal() as session:
        result = await MatchingService(session).matches_for_job(
            user_id=ctx["est_id"],
            job_id=ctx["job_id"],
            radius_km=0.5,
        )
    # fl3 não deve estar nos resultados (a ~15km do job)
    result_ids = {item.user_id for item in result.items}
    assert ctx["fl3_id"] not in result_ids
    # fl1 e fl2 devem estar (a <500m)
    assert ctx["fl1_id"] in result_ids
    assert ctx["fl2_id"] in result_ids
