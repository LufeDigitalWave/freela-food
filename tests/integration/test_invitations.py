"""Convites — create + validações (Fluxo B)."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.core.database import SessionLocal
from tests.factories import (
    auth_header_for,
    make_establishment,
    make_freelancer,
    make_skill_category,
)

PWD = "Senha123!"


async def _seed_pair() -> dict[str, uuid.UUID | str]:
    est_email = f"est-{uuid.uuid4().hex[:8]}@test.com"
    fl_email = f"fl-{uuid.uuid4().hex[:8]}@test.com"
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=est_email)
        fl, _ = await make_freelancer(session, email=fl_email)
        cat = await make_skill_category(session)
        await session.commit()
        return {
            "est_id": est.id,
            "fl_id": fl.id,
            "skill_id": cat.id,
            "est_email": est_email,
            "fl_email": fl_email,
        }


def _future_window() -> tuple[str, str]:
    start = datetime.now(UTC) + timedelta(days=2)
    end = start + timedelta(hours=4)
    return start.isoformat(), end.isoformat()


async def test_create_invitation_happy(client: AsyncClient) -> None:
    s = await _seed_pair()
    headers = await auth_header_for(client, str(s["est_email"]), PWD)
    start, end = _future_window()
    resp = await client.post(
        "/v1/invitations",
        headers=headers,
        json={
            "freelancer_id": str(s["fl_id"]),
            "skill_category_id": str(s["skill_id"]),
            "start_at": start,
            "end_at": end,
            "proposed_hourly_rate": "45.00",
            "message": "Topa um plantão?",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["freelancer_id"] == str(s["fl_id"])
    assert body["expires_at"] is not None


async def test_create_forbidden_for_freelancer(client: AsyncClient) -> None:
    s = await _seed_pair()
    headers = await auth_header_for(client, str(s["fl_email"]), PWD)
    start, end = _future_window()
    resp = await client.post(
        "/v1/invitations",
        headers=headers,
        json={
            "freelancer_id": str(s["fl_id"]),
            "skill_category_id": str(s["skill_id"]),
            "start_at": start,
            "end_at": end,
        },
    )
    assert resp.status_code == 409  # EstablishmentProfileRequired


async def test_create_invalid_target(client: AsyncClient) -> None:
    s = await _seed_pair()
    headers = await auth_header_for(client, str(s["est_email"]), PWD)
    start, end = _future_window()
    resp = await client.post(
        "/v1/invitations",
        headers=headers,
        json={
            "freelancer_id": str(uuid.uuid4()),  # não existe
            "skill_category_id": str(s["skill_id"]),
            "start_at": start,
            "end_at": end,
        },
    )
    assert resp.status_code == 400


async def test_create_invalid_window_past(client: AsyncClient) -> None:
    s = await _seed_pair()
    headers = await auth_header_for(client, str(s["est_email"]), PWD)
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    end = (datetime.now(UTC) + timedelta(hours=3)).isoformat()
    resp = await client.post(
        "/v1/invitations",
        headers=headers,
        json={
            "freelancer_id": str(s["fl_id"]),
            "skill_category_id": str(s["skill_id"]),
            "start_at": past,
            "end_at": end,
        },
    )
    assert resp.status_code == 400


async def test_create_duplicate_overlapping(client: AsyncClient) -> None:
    s = await _seed_pair()
    headers = await auth_header_for(client, str(s["est_email"]), PWD)
    start, end = _future_window()
    payload = {
        "freelancer_id": str(s["fl_id"]),
        "skill_category_id": str(s["skill_id"]),
        "start_at": start,
        "end_at": end,
    }
    first = await client.post("/v1/invitations", headers=headers, json=payload)
    assert first.status_code == 201
    second = await client.post("/v1/invitations", headers=headers, json=payload)
    assert second.status_code == 409
