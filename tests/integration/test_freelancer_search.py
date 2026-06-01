"""Busca de freelancers por proximidade (Fluxo B)."""

import uuid

from httpx import AsyncClient

from app.core.database import SessionLocal
from tests.factories import (
    auth_header_for,
    make_establishment,
    make_freelancer,
    make_freelancer_skill,
    make_skill_category,
)

PWD = "Senha123!"


def _anchor() -> tuple[float, float]:
    # Âncora única por execução — DB da VPS é compartilhado.
    seed = uuid.uuid4().int
    lat = -23.5 - (seed % 500) / 1000.0
    lng = -47.5 - ((seed >> 32) % 500) / 1000.0
    return (lat, lng)


async def _establishment_token(client: AsyncClient, lat: float, lng: float) -> str:
    email = f"est-{uuid.uuid4().hex[:8]}@test.com"
    async with SessionLocal() as session:
        await make_establishment(session, email=email, lat=lat, lng=lng)
        await session.commit()
    return (await auth_header_for(client, email, PWD))["Authorization"].split()[1]


async def _make_freelancer_at(
    lat: float, lng: float, skill_id: uuid.UUID | None = None
) -> uuid.UUID:
    email = f"fl-{uuid.uuid4().hex[:8]}@test.com"
    async with SessionLocal() as session:
        user, _ = await make_freelancer(session, email=email, lat=lat, lng=lng)
        if skill_id is not None:
            await make_freelancer_skill(
                session, freelancer_user_id=user.id, skill_category_id=skill_id
            )
        await session.commit()
        return user.id


async def test_search_returns_nearby_freelancer(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    fl_id = await _make_freelancer_at(anchor_lat, anchor_lng)
    token = await _establishment_token(client, anchor_lat, anchor_lng)

    resp = await client.get(
        "/v1/freelancers/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"latitude": anchor_lat, "longitude": anchor_lng, "radius_km": 10},
    )
    assert resp.status_code == 200, resp.text
    ids = {item["user_id"] for item in resp.json()["items"]}
    assert str(fl_id) in ids


async def test_search_excludes_far_freelancer(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    far_id = await _make_freelancer_at(anchor_lat + 0.18, anchor_lng)  # ~20 km
    token = await _establishment_token(client, anchor_lat, anchor_lng)

    resp = await client.get(
        "/v1/freelancers/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"latitude": anchor_lat, "longitude": anchor_lng, "radius_km": 10},
    )
    ids = {item["user_id"] for item in resp.json()["items"]}
    assert str(far_id) not in ids


async def test_search_orders_by_distance_ascending(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    await _make_freelancer_at(anchor_lat + 0.04, anchor_lng)  # ~4 km
    await _make_freelancer_at(anchor_lat, anchor_lng)  # ~0 km
    token = await _establishment_token(client, anchor_lat, anchor_lng)

    resp = await client.get(
        "/v1/freelancers/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"latitude": anchor_lat, "longitude": anchor_lng, "radius_km": 10},
    )
    distances = [item["distance_m"] for item in resp.json()["items"]]
    assert distances == sorted(distances)


async def test_search_filters_by_skill(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    async with SessionLocal() as session:
        cat = await make_skill_category(session)
        await session.commit()
        skill_id = cat.id
    with_skill = await _make_freelancer_at(anchor_lat, anchor_lng, skill_id=skill_id)
    without_skill = await _make_freelancer_at(anchor_lat, anchor_lng)
    token = await _establishment_token(client, anchor_lat, anchor_lng)

    resp = await client.get(
        "/v1/freelancers/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "latitude": anchor_lat,
            "longitude": anchor_lng,
            "radius_km": 10,
            "skill_category_id": str(skill_id),
        },
    )
    ids = {item["user_id"] for item in resp.json()["items"]}
    assert str(with_skill) in ids
    assert str(without_skill) not in ids


async def test_search_does_not_leak_pii(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    await _make_freelancer_at(anchor_lat, anchor_lng)
    token = await _establishment_token(client, anchor_lat, anchor_lng)

    resp = await client.get(
        "/v1/freelancers/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"latitude": anchor_lat, "longitude": anchor_lng, "radius_km": 10},
    )
    for item in resp.json()["items"]:
        assert "cpf" not in item
        assert "phone" not in item


async def test_search_forbidden_for_freelancer(client: AsyncClient) -> None:
    anchor_lat, anchor_lng = _anchor()
    email = f"fl-{uuid.uuid4().hex[:8]}@test.com"
    async with SessionLocal() as session:
        await make_freelancer(session, email=email, lat=anchor_lat, lng=anchor_lng)
        await session.commit()
    headers = await auth_header_for(client, email, PWD)

    resp = await client.get(
        "/v1/freelancers/search",
        headers=headers,
        params={"latitude": anchor_lat, "longitude": anchor_lng, "radius_km": 10},
    )
    assert resp.status_code == 403
