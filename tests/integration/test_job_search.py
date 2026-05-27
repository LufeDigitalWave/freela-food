"""Busca de vagas por proximidade (PostGIS ST_DWithin)."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.skill_category import SkillCategory

# Pontos de São Paulo
PAULISTA = (-23.561, -46.656)  # Av Paulista
PINHEIROS = (-23.564, -46.694)  # Pinheiros (~4 km de Paulista)
GUARULHOS = (-23.463, -46.533)  # Guarulhos (~20 km de Paulista)


def _email() -> str:
    return f"search-{uuid.uuid4()}@example.com"


async def _setup_estab_with_job(
    client: AsyncClient, lat: float, lng: float, skill_slug: str = "garcom"
) -> str:
    pwd = "supersecret123"
    email = _email()
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": pwd, "role": "establishment"},
    )
    login = await client.post(
        "/v1/auth/login", json={"email": email, "password": pwd}
    )
    token: str = login.json()["access_token"]

    await client.post(
        "/v1/me/establishment-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "business_name": f"Place at {lat},{lng}",
            "latitude": lat,
            "longitude": lng,
        },
    )

    async with SessionLocal() as session:
        result = await session.execute(
            select(SkillCategory.id).where(SkillCategory.slug == skill_slug)
        )
        skill_id = result.scalar_one()

    start = datetime.now(UTC) + timedelta(days=5)
    end = start + timedelta(hours=4)
    created = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "skill_category_id": str(skill_id),
            "title": f"Vaga em ({lat},{lng})",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "hourly_rate": "40.00",
        },
    )
    return created.json()["id"]  # type: ignore[no-any-return]


async def _freelancer_token(client: AsyncClient) -> str:
    email = _email()
    pwd = "supersecret123"
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": pwd, "role": "freelancer"},
    )
    login = await client.post(
        "/v1/auth/login", json={"email": email, "password": pwd}
    )
    return login.json()["access_token"]  # type: ignore[no-any-return]


async def test_search_returns_jobs_within_radius(client: AsyncClient) -> None:
    # 2 jobs próximos, 1 distante
    paulista_job = await _setup_estab_with_job(client, *PAULISTA)
    pinheiros_job = await _setup_estab_with_job(client, *PINHEIROS)
    await _setup_estab_with_job(client, *GUARULHOS)

    token = await _freelancer_token(client)
    response = await client.get(
        "/v1/jobs/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"latitude": PAULISTA[0], "longitude": PAULISTA[1], "radius_km": 10},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    job_ids = {item["id"] for item in data["items"]}
    assert paulista_job in job_ids
    assert pinheiros_job in job_ids
    # Guarulhos (>10km) deve estar fora
    distances = [item["distance_m"] for item in data["items"]]
    assert all(d <= 10_000 for d in distances)


async def test_search_orders_by_distance_ascending(client: AsyncClient) -> None:
    await _setup_estab_with_job(client, *PINHEIROS)
    await _setup_estab_with_job(client, *PAULISTA)

    token = await _freelancer_token(client)
    response = await client.get(
        "/v1/jobs/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"latitude": PAULISTA[0], "longitude": PAULISTA[1], "radius_km": 20},
    )
    items = response.json()["items"]
    distances = [item["distance_m"] for item in items]
    assert distances == sorted(distances)


async def test_search_filters_by_skill(client: AsyncClient) -> None:
    await _setup_estab_with_job(client, *PAULISTA, skill_slug="garcom")
    await _setup_estab_with_job(client, *PAULISTA, skill_slug="barman")

    async with SessionLocal() as session:
        result = await session.execute(
            select(SkillCategory.id).where(SkillCategory.slug == "garcom")
        )
        garcom_id = result.scalar_one()

    token = await _freelancer_token(client)
    response = await client.get(
        "/v1/jobs/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "latitude": PAULISTA[0],
            "longitude": PAULISTA[1],
            "radius_km": 5,
            "skill_category_id": str(garcom_id),
        },
    )
    items = response.json()["items"]
    assert len(items) >= 1
    assert all(item["skill_category_id"] == str(garcom_id) for item in items)


async def test_search_pagination(client: AsyncClient) -> None:
    # Cria múltiplas vagas no mesmo lugar
    for _ in range(5):
        await _setup_estab_with_job(client, *PAULISTA)

    token = await _freelancer_token(client)
    response = await client.get(
        "/v1/jobs/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "latitude": PAULISTA[0],
            "longitude": PAULISTA[1],
            "radius_km": 1,
            "page_size": 3,
            "page": 1,
        },
    )
    data = response.json()
    assert len(data["items"]) <= 3
    assert data["page_size"] == 3
    assert data["page"] == 1
    assert data["total"] >= 5


async def test_search_excludes_cancelled_jobs_by_default(client: AsyncClient) -> None:
    pwd = "supersecret123"
    email = _email()
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": pwd, "role": "establishment"},
    )
    login = await client.post(
        "/v1/auth/login", json={"email": email, "password": pwd}
    )
    token = login.json()["access_token"]

    await client.post(
        "/v1/me/establishment-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "business_name": "Cancelled Test",
            "latitude": PAULISTA[0],
            "longitude": PAULISTA[1],
        },
    )

    async with SessionLocal() as session:
        result = await session.execute(
            select(SkillCategory.id).where(SkillCategory.slug == "barman")
        )
        skill_id = result.scalar_one()

    start = datetime.now(UTC) + timedelta(days=5)
    created = await client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "skill_category_id": str(skill_id),
            "title": "Vaga a ser cancelada",
            "start_at": start.isoformat(),
            "end_at": (start + timedelta(hours=4)).isoformat(),
            "hourly_rate": "50.00",
        },
    )
    job_id = created.json()["id"]
    await client.post(
        f"/v1/jobs/{job_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    freelancer_tok = await _freelancer_token(client)
    response = await client.get(
        "/v1/jobs/search",
        headers={"Authorization": f"Bearer {freelancer_tok}"},
        params={
            "latitude": PAULISTA[0],
            "longitude": PAULISTA[1],
            "radius_km": 2,
            "skill_category_id": str(skill_id),
        },
    )
    job_ids = {item["id"] for item in response.json()["items"]}
    assert job_id not in job_ids
