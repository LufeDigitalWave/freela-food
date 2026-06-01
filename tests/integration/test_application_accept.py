"""Testes do accept de application — caso crítico transacional do Fluxo A."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.application import Application
from app.domain.models.job_posting import JobPosting
from app.domain.models.service_contract import ServiceContract
from tests.factories import (
    auth_header_for,
    make_application,
    make_contract,
    make_establishment,
    make_freelancer,
    make_job,
    make_skill_category,
)


async def _three_freelancers_apply() -> dict:
    """Setup: 1 estabelecimento, 3 freelancers, 1 job open, 3 applications pending."""
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fls = []
        for _ in range(3):
            u, _ = await make_freelancer(session)
            fls.append(u)
        cat = await make_skill_category(session)
        start = datetime.now(UTC) + timedelta(days=2)
        job = await make_job(
            session,
            establishment_id=est.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start,
            end_at=start + timedelta(hours=5),
            hourly_rate=Decimal("40.00"),
        )
        apps = []
        for fl in fls:
            a = await make_application(
                session, job_posting_id=job.id, freelancer_id=fl.id
            )
            apps.append(a)
        await session.commit()
        return {
            "est_email": est.email,
            "fl_emails": [u.email for u in fls],
            "job_id": job.id,
            "app_ids": [a.id for a in apps],
        }


@pytest.mark.asyncio
async def test_accept_happy_path_creates_contract(client: AsyncClient) -> None:
    ctx = await _three_freelancers_apply()
    h = await auth_header_for(client, ctx["est_email"])
    r = await client.post(f"/v1/applications/{ctx['app_ids'][0]}/accept", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"

    async with SessionLocal() as session:
        # Job → filled
        job = (
            await session.execute(
                select(JobPosting).where(JobPosting.id == ctx["job_id"])
            )
        ).scalar_one()
        assert job.status == "filled"
        # Outras 2 applications → rejected
        rows = (
            (
                await session.execute(
                    select(Application).where(
                        Application.job_posting_id == ctx["job_id"]
                    )
                )
            )
            .scalars()
            .all()
        )
        statuses = sorted([a.status for a in rows])
        assert statuses == ["accepted", "rejected", "rejected"]
        # ServiceContract criado
        contract = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.application_id == ctx["app_ids"][0]
                )
            )
        ).scalar_one()
        assert contract.status == "scheduled"
        assert contract.agreed_hourly_rate == Decimal("40.00")


@pytest.mark.asyncio
async def test_accept_with_single_pending_no_cascade(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est.id, skill_category_id=cat.id, status="open"
        )
        a = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = a.id
        est_email = est.email

    h = await auth_header_for(client, est_email)
    r = await client.post(f"/v1/applications/{aid}/accept", headers=h)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_accept_non_pending_returns_409(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est.id, skill_category_id=cat.id, status="open"
        )
        a = await make_application(
            session,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            status="rejected",
        )
        await session.commit()
        aid = a.id
        est_email = est.email

    h = await auth_header_for(client, est_email)
    r = await client.post(f"/v1/applications/{aid}/accept", headers=h)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_accept_by_non_owner_returns_403(client: AsyncClient) -> None:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        outro, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est.id, skill_category_id=cat.id, status="open"
        )
        a = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = a.id
        outro_email = outro.email

    h = await auth_header_for(client, outro_email)
    r = await client.post(f"/v1/applications/{aid}/accept", headers=h)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_accept_blocked_by_overlap_scheduled(client: AsyncClient) -> None:
    """Freelancer já tem contrato scheduled no mesmo intervalo → 409."""
    async with SessionLocal() as session:
        est_a, _ = await make_establishment(session)
        est_b, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        start = datetime.now(UTC) + timedelta(days=3)
        end = start + timedelta(hours=4)

        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start,
            end_at=end,
        )
        app_a = await make_application(
            session,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            status="accepted",
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start,
            end_at=end,
            status="scheduled",
        )

        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start,
            end_at=end,
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        b_id = app_b.id
        est_b_email = est_b.email

    h = await auth_header_for(client, est_b_email)
    r = await client.post(f"/v1/applications/{b_id}/accept", headers=h)
    assert r.status_code == 409
    assert "sobreposto" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_accept_blocked_by_overlap_in_progress(client: AsyncClient) -> None:
    """Contrato in_progress também bloqueia accept."""
    async with SessionLocal() as session:
        est_a, _ = await make_establishment(session)
        est_b, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        start_a = datetime.now(UTC) - timedelta(hours=1)
        end_a = start_a + timedelta(hours=4)
        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start_a,
            end_at=end_a,
        )
        app_a = await make_application(
            session, job_posting_id=job_a.id, freelancer_id=fl.id, status="accepted"
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start_a,
            end_at=end_a,
            status="in_progress",
        )
        # Job B sobrepondo
        start_b = start_a + timedelta(hours=1)
        end_b = start_b + timedelta(hours=2)
        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start_b,
            end_at=end_b,
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        bid = app_b.id
        est_b_email = est_b.email

    h = await auth_header_for(client, est_b_email)
    r = await client.post(f"/v1/applications/{bid}/accept", headers=h)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_accept_allows_overlap_with_cancelled_contract(
    client: AsyncClient,
) -> None:
    """Contrato cancelled no intervalo NÃO bloqueia."""
    async with SessionLocal() as session:
        est_a, _ = await make_establishment(session)
        est_b, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        start = datetime.now(UTC) + timedelta(days=3)
        end = start + timedelta(hours=4)
        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="cancelled",
            start_at=start,
            end_at=end,
        )
        app_a = await make_application(
            session, job_posting_id=job_a.id, freelancer_id=fl.id, status="accepted"
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start,
            end_at=end,
            status="cancelled",
        )
        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start,
            end_at=end,
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        bid = app_b.id
        est_b_email = est_b.email

    h = await auth_header_for(client, est_b_email)
    r = await client.post(f"/v1/applications/{bid}/accept", headers=h)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_accept_allows_overlap_with_completed_contract(
    client: AsyncClient,
) -> None:
    """Contrato completed no intervalo NÃO bloqueia (raro, mas válido)."""
    async with SessionLocal() as session:
        est_a, _ = await make_establishment(session)
        est_b, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        start = datetime.now(UTC) + timedelta(days=3)
        end = start + timedelta(hours=4)
        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="completed",
            start_at=start,
            end_at=end,
        )
        app_a = await make_application(
            session, job_posting_id=job_a.id, freelancer_id=fl.id, status="accepted"
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start,
            end_at=end,
            status="completed",
        )
        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start,
            end_at=end,
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        bid = app_b.id
        est_b_email = est_b.email

    h = await auth_header_for(client, est_b_email)
    r = await client.post(f"/v1/applications/{bid}/accept", headers=h)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_accept_partial_overlap_borders(client: AsyncClient) -> None:
    """Job B começa antes do A terminar → overlap detectado."""
    async with SessionLocal() as session:
        est_a, _ = await make_establishment(session)
        est_b, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        start_a = datetime.now(UTC) + timedelta(days=3)
        end_a = start_a + timedelta(hours=4)
        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start_a,
            end_at=end_a,
        )
        app_a = await make_application(
            session, job_posting_id=job_a.id, freelancer_id=fl.id, status="accepted"
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start_a,
            end_at=end_a,
            status="scheduled",
        )
        # B começa 1h antes de A terminar → 1h de overlap
        start_b = end_a - timedelta(hours=1)
        end_b = start_b + timedelta(hours=3)
        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=start_b,
            end_at=end_b,
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        bid = app_b.id
        est_b_email = est_b.email

    h = await auth_header_for(client, est_b_email)
    r = await client.post(f"/v1/applications/{bid}/accept", headers=h)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_accept_no_overlap_adjacent(client: AsyncClient) -> None:
    """Job B começa exatamente quando A termina → SEM overlap (intervalo half-open)."""
    async with SessionLocal() as session:
        est_a, _ = await make_establishment(session)
        est_b, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        start_a = datetime.now(UTC) + timedelta(days=3)
        end_a = start_a + timedelta(hours=4)
        job_a = await make_job(
            session,
            establishment_id=est_a.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start_a,
            end_at=end_a,
        )
        app_a = await make_application(
            session, job_posting_id=job_a.id, freelancer_id=fl.id, status="accepted"
        )
        await make_contract(
            session,
            application_id=app_a.id,
            job_posting_id=job_a.id,
            freelancer_id=fl.id,
            establishment_id=est_a.id,
            start_at=start_a,
            end_at=end_a,
            status="scheduled",
        )
        # B começa exatamente em end_a — sem overlap
        job_b = await make_job(
            session,
            establishment_id=est_b.id,
            skill_category_id=cat.id,
            status="open",
            start_at=end_a,
            end_at=end_a + timedelta(hours=3),
        )
        app_b = await make_application(
            session, job_posting_id=job_b.id, freelancer_id=fl.id
        )
        await session.commit()
        bid = app_b.id
        est_b_email = est_b.email

    h = await auth_header_for(client, est_b_email)
    r = await client.post(f"/v1/applications/{bid}/accept", headers=h)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_accept_emits_notifications(client: AsyncClient) -> None:
    """Accept gera 1 application.accepted + N application.rejected."""
    ctx = await _three_freelancers_apply()
    h_est = await auth_header_for(client, ctx["est_email"])
    await client.post(f"/v1/applications/{ctx['app_ids'][0]}/accept", headers=h_est)

    # Vencedor
    h_w = await auth_header_for(client, ctx["fl_emails"][0])
    r_w = await client.get("/v1/me/notifications", headers=h_w)
    types_w = [n["type"] for n in r_w.json()["items"]]
    assert "application.accepted" in types_w

    # Perdedores
    for email in ctx["fl_emails"][1:]:
        h_l = await auth_header_for(client, email)
        r_l = await client.get("/v1/me/notifications", headers=h_l)
        types_l = [n["type"] for n in r_l.json()["items"]]
        assert "application.rejected" in types_l


@pytest.mark.asyncio
async def test_accept_copies_pay_from_job(client: AsyncClient) -> None:
    """Contract.agreed_hourly_rate e agreed_total_pay vêm do job."""
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        job = await make_job(
            session,
            establishment_id=est.id,
            skill_category_id=cat.id,
            status="open",
            hourly_rate=None,
            total_pay=Decimal("250.00"),
        )
        a = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id
        )
        await session.commit()
        aid = a.id
        est_email = est.email

    h = await auth_header_for(client, est_email)
    r = await client.post(f"/v1/applications/{aid}/accept", headers=h)
    assert r.status_code == 200

    async with SessionLocal() as session:
        c = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.application_id == aid
                )
            )
        ).scalar_one()
        assert c.agreed_total_pay == Decimal("250.00")
        assert c.agreed_hourly_rate is None
