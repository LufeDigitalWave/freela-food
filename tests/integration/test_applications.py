"""Testes de candidatura (POST /jobs/{id}/applications)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.database import SessionLocal
from tests.factories import (
    auth_header_for,
    make_establishment,
    make_freelancer,
    make_job,
    make_skill_category,
    make_user,
)


@pytest.mark.asyncio
async def test_freelancer_creates_application_happy_path(client: AsyncClient) -> None:
    """Freelancer com profile candidata em vaga open → 201, status=pending."""
    async with SessionLocal() as session:
        est_user, _ = await make_establishment(session)
        freela_user, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(
            session,
            establishment_id=est_user.id,
            skill_category_id=cat.id,
            status="open",
        )
        await session.commit()
        job_id = job.id
        fl_email = freela_user.email

    headers = await auth_header_for(client, fl_email)
    resp = await client.post(
        f"/v1/jobs/{job_id}/applications",
        json={"message": "Tenho 5 anos de experiência"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["message"] == "Tenho 5 anos de experiência"
    assert body["decided_at"] is None


@pytest.mark.asyncio
async def test_duplicate_application_returns_409(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est_user, _ = await make_establishment(session)
        freela_user, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est_user.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id
        fl_email = freela_user.email

    headers = await auth_header_for(client, fl_email)
    r1 = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=headers)
    assert r1.status_code == 201
    r2 = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=headers)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_application_without_profile_returns_409(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est_user, _ = await make_establishment(session)
        # User freelancer SEM profile
        freela_user = await make_user(session, role="freelancer")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est_user.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id
        fl_email = freela_user.email

    headers = await auth_header_for(client, fl_email)
    resp = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=headers)
    assert resp.status_code == 409
    assert "perfil" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_self_application_returns_403(client: AsyncClient) -> None:
    """Dono da vaga tentando candidatar na própria → 403."""
    async with SessionLocal() as session:
        est_user, _ = await make_establishment(session)
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est_user.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id
        est_email = est_user.email

    headers = await auth_header_for(client, est_email)
    resp = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_application_on_non_open_job_returns_409(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est_user, _ = await make_establishment(session)
        freela_user, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        # Vaga em draft
        job_draft = await make_job(
            session,
            establishment_id=est_user.id,
            skill_category_id=cat.id,
            status="draft",
        )
        await session.commit()
        job_id = job_draft.id
        fl_email = freela_user.email

    headers = await auth_header_for(client, fl_email)
    resp = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_message_too_long_returns_422(client: AsyncClient) -> None:
    """Message > 500 chars rejeitada pelo Pydantic."""
    async with SessionLocal() as session:
        est_user, _ = await make_establishment(session)
        freela_user, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est_user.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id
        fl_email = freela_user.email

    headers = await auth_header_for(client, fl_email)
    resp = await client.post(
        f"/v1/jobs/{job_id}/applications",
        json={"message": "x" * 501},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_application_creates_notification(client: AsyncClient) -> None:
    """Após candidatura, notification.received aparece pro estabelecimento."""
    async with SessionLocal() as session:
        est_user, _ = await make_establishment(session)
        freela_user, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est_user.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id
        fl_email = freela_user.email
        est_email = est_user.email

    fl_headers = await auth_header_for(client, fl_email)
    await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=fl_headers)

    est_headers = await auth_header_for(client, est_email)
    resp = await client.get("/v1/me/notifications", headers=est_headers)
    body = resp.json()
    assert body["total"] >= 1
    types = [n["type"] for n in body["items"]]
    assert "application.received" in types
