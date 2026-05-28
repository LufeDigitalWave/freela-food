"""Testes de candidatura (POST /jobs/{id}/applications)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.database import SessionLocal
from tests.factories import (
    auth_header_for,
    make_application,
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


@pytest.mark.asyncio
async def test_list_job_applications_owner_only(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl1, _ = await make_freelancer(session)
        fl2, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est.id, skill_category_id=cat.id
        )
        await session.commit()
        job_id = job.id
        est_email, fl1_email, fl2_email = est.email, fl1.email, fl2.email

    h1 = await auth_header_for(client, fl1_email)
    await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=h1)
    h2 = await auth_header_for(client, fl2_email)
    await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=h2)

    est_h = await auth_header_for(client, est_email)
    resp = await client.get(f"/v1/jobs/{job_id}/applications", headers=est_h)
    assert resp.status_code == 200
    assert resp.json()["total"] == 2

    # freelancer (não dono da vaga) não pode listar
    resp2 = await client.get(f"/v1/jobs/{job_id}/applications", headers=h1)
    assert resp2.status_code == 403


@pytest.mark.asyncio
async def test_list_my_applications(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        j1 = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        j2 = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        await session.commit()
        ids = (j1.id, j2.id)
        fl_email = fl.email

    h = await auth_header_for(client, fl_email)
    for jid in ids:
        await client.post(f"/v1/jobs/{jid}/applications", json={}, headers=h)

    resp = await client.get("/v1/me/applications", headers=h)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2


@pytest.mark.asyncio
async def test_get_application_only_parties(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        outro, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        await session.commit()
        job_id = job.id
        est_email, fl_email, outro_email = est.email, fl.email, outro.email

    h_fl = await auth_header_for(client, fl_email)
    r = await client.post(f"/v1/jobs/{job_id}/applications", json={}, headers=h_fl)
    aid = r.json()["id"]

    # Freelancer dono vê
    r1 = await client.get(f"/v1/applications/{aid}", headers=h_fl)
    assert r1.status_code == 200

    # Estabelecimento dono da vaga vê
    h_est = await auth_header_for(client, est_email)
    r2 = await client.get(f"/v1/applications/{aid}", headers=h_est)
    assert r2.status_code == 200

    # Outro freelancer não vê
    h_out = await auth_header_for(client, outro_email)
    r3 = await client.get(f"/v1/applications/{aid}", headers=h_out)
    assert r3.status_code == 403


@pytest.mark.asyncio
async def test_list_applications_status_filter(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id, status="pending"
        )
        await session.commit()
        job_id = job.id
        est_email = est.email

    est_h = await auth_header_for(client, est_email)
    r = await client.get(
        f"/v1/jobs/{job_id}/applications?status=pending", headers=est_h
    )
    assert r.status_code == 200
    assert r.json()["total"] == 1

    r2 = await client.get(
        f"/v1/jobs/{job_id}/applications?status=rejected", headers=est_h
    )
    assert r2.json()["total"] == 0


@pytest.mark.asyncio
async def test_reject_application_by_establishment(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = app_.id
        est_email = est.email

    h = await auth_header_for(client, est_email)
    r = await client.post(f"/v1/applications/{aid}/reject", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    assert r.json()["decided_at"] is not None


@pytest.mark.asyncio
async def test_reject_by_non_owner_returns_403(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        outro, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = app_.id
        outro_email = outro.email

    h = await auth_header_for(client, outro_email)
    r = await client.post(f"/v1/applications/{aid}/reject", headers=h)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_reject_non_pending_returns_409(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        app_ = await make_application(
            session,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            status="rejected",
        )
        await session.commit()
        aid = app_.id
        est_email = est.email

    h = await auth_header_for(client, est_email)
    r = await client.post(f"/v1/applications/{aid}/reject", headers=h)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_withdraw_application_by_freelancer(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = app_.id
        fl_email = fl.email

    h = await auth_header_for(client, fl_email)
    r = await client.post(f"/v1/applications/{aid}/withdraw", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "withdrawn"


@pytest.mark.asyncio
async def test_withdraw_by_non_owner_returns_403(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        outro, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = app_.id
        outro_email = outro.email

    h = await auth_header_for(client, outro_email)
    r = await client.post(f"/v1/applications/{aid}/withdraw", headers=h)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_reject_emits_notification(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(session, establishment_id=est.id, skill_category_id=cat.id)
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = app_.id
        est_email, fl_email = est.email, fl.email

    h = await auth_header_for(client, est_email)
    await client.post(f"/v1/applications/{aid}/reject", headers=h)

    h_fl = await auth_header_for(client, fl_email)
    notif = await client.get("/v1/me/notifications", headers=h_fl)
    types = [n["type"] for n in notif.json()["items"]]
    assert "application.rejected" in types
