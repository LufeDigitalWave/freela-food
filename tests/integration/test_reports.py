"""Testes de reports user-facing (Sprint 8)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.notification import Notification
from tests.factories import (
    auth_header_for,
    make_establishment,
    make_freelancer,
)


async def _setup_users() -> dict:
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        await session.commit()
        return {
            "fl_id": fl.id,
            "fl_email": f"fl-{suffix}@test.com",
            "est_id": est.id,
            "est_email": f"est-{suffix}@test.com",
        }


@pytest.mark.asyncio
async def test_create_report(client: AsyncClient) -> None:
    ctx = await _setup_users()
    headers = await auth_header_for(client, ctx["fl_email"])
    resp = await client.post(
        "/v1/reports",
        json={
            "target_type": "user",
            "target_id": str(ctx["est_id"]),
            "reason": "spam",
            "description": "Perfil falso",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["reporter_id"] == str(ctx["fl_id"])
    assert body["target_type"] == "user"
    assert body["status"] == "pending"


@pytest.mark.asyncio
async def test_create_report_self_forbidden(client: AsyncClient) -> None:
    ctx = await _setup_users()
    headers = await auth_header_for(client, ctx["fl_email"])
    resp = await client.post(
        "/v1/reports",
        json={
            "target_type": "user",
            "target_id": str(ctx["fl_id"]),  # reportando a si mesmo
            "reason": "fake",
        },
        headers=headers,
    )
    assert resp.status_code == 403
    assert "si mesmo" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_report_duplicate_pending(client: AsyncClient) -> None:
    ctx = await _setup_users()
    headers = await auth_header_for(client, ctx["fl_email"])
    payload = {
        "target_type": "user",
        "target_id": str(ctx["est_id"]),
        "reason": "offensive",
    }
    # Primeiro report
    resp1 = await client.post("/v1/reports", json=payload, headers=headers)
    assert resp1.status_code == 201
    # Segundo report duplicado
    resp2 = await client.post("/v1/reports", json=payload, headers=headers)
    assert resp2.status_code == 409
    assert "pendente" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_my_reports(client: AsyncClient) -> None:
    ctx = await _setup_users()
    headers = await auth_header_for(client, ctx["fl_email"])
    # Criar um report
    await client.post(
        "/v1/reports",
        json={
            "target_type": "user",
            "target_id": str(ctx["est_id"]),
            "reason": "harassment",
        },
        headers=headers,
    )
    # Listar
    resp = await client.get("/v1/me/reports", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert body["items"][0]["reporter_id"] == str(ctx["fl_id"])


@pytest.mark.asyncio
async def test_report_notification_emitted(client: AsyncClient) -> None:
    ctx = await _setup_users()
    headers = await auth_header_for(client, ctx["fl_email"])
    await client.post(
        "/v1/reports",
        json={
            "target_type": "user",
            "target_id": str(ctx["est_id"]),
            "reason": "spam",
        },
        headers=headers,
    )
    # Confirmar notificação report.submitted
    async with SessionLocal() as session:
        result = await session.execute(
            select(Notification).where(
                Notification.user_id == ctx["fl_id"],
                Notification.type == "report.submitted",
            )
        )
        notif = result.scalar_one_or_none()
    assert notif is not None


@pytest.mark.asyncio
async def test_create_report_review_target(client: AsyncClient) -> None:
    ctx = await _setup_users()
    headers = await auth_header_for(client, ctx["fl_email"])
    fake_review_id = uuid.uuid4()
    resp = await client.post(
        "/v1/reports",
        json={
            "target_type": "review",
            "target_id": str(fake_review_id),
            "reason": "offensive",
            "description": "Contém linguagem inapropriada",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["target_type"] == "review"


@pytest.mark.asyncio
async def test_report_unauthenticated(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/reports",
        json={
            "target_type": "user",
            "target_id": str(uuid.uuid4()),
            "reason": "spam",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_my_reports_empty(client: AsyncClient) -> None:
    ctx = await _setup_users()
    headers = await auth_header_for(client, ctx["est_email"])
    resp = await client.get("/v1/me/reports", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
