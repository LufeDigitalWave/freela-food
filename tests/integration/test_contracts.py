"""Testes de listagem, detalhe e cancelamento de ServiceContract."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from freezegun import freeze_time
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.job_posting import JobPosting
from tests.factories import (
    auth_header_for,
    make_application,
    make_contract,
    make_establishment,
    make_freelancer,
    make_job,
    make_skill_category,
)


async def _setup_contract_scenario(
    *, days_until_start: int = 5, status: str = "scheduled"
) -> dict:
    async with SessionLocal() as session:
        est, _ = await make_establishment(session)
        fl, _ = await make_freelancer(session)
        cat = await make_skill_category(session)
        start = datetime.now(UTC) + timedelta(days=days_until_start)
        job = await make_job(
            session,
            establishment_id=est.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start,
            end_at=start + timedelta(hours=4),
        )
        app_ = await make_application(
            session,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            status="accepted",
        )
        contract = await make_contract(
            session,
            application_id=app_.id,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            establishment_id=est.id,
            start_at=start,
            end_at=start + timedelta(hours=4),
            status=status,
        )
        await session.commit()
        return {
            "est_email": est.email,
            "fl_email": fl.email,
            "fl_id": fl.id,
            "contract_id": contract.id,
            "job_id": job.id,
        }


@pytest.mark.asyncio
async def test_list_my_contracts_as_freelancer(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario()
    h = await auth_header_for(client, ctx["fl_email"])
    r = await client.get("/v1/me/contracts", headers=h)
    assert r.status_code == 200
    assert r.json()["total"] == 1


@pytest.mark.asyncio
async def test_list_my_contracts_as_establishment(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario()
    h = await auth_header_for(client, ctx["est_email"])
    r = await client.get("/v1/me/contracts", headers=h)
    assert r.status_code == 200
    assert r.json()["total"] == 1


@pytest.mark.asyncio
async def test_get_contract_third_party_403(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario()
    async with SessionLocal() as session:
        third, _ = await make_freelancer(session)
        await session.commit()
        third_email = third.email
    h = await auth_header_for(client, third_email)
    r = await client.get(f"/v1/contracts/{ctx['contract_id']}", headers=h)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_cancel_by_freelancer_far_from_start_no_no_show(
    client: AsyncClient,
) -> None:
    """Cancel pelo freelancer com >24h até start_at → no_show=false, counter intacto."""
    ctx = await _setup_contract_scenario(days_until_start=5)
    h = await auth_header_for(client, ctx["fl_email"])
    r = await client.post(
        f"/v1/contracts/{ctx['contract_id']}/cancel",
        json={"reason": "imprevisto"},
        headers=h,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "cancelled"
    assert body["cancelled_by"] == "freelancer"
    assert body["no_show"] is False

    async with SessionLocal() as session:
        row = await session.execute(
            select(FreelancerProfile).where(
                FreelancerProfile.user_id == ctx["fl_id"]
            )
        )
        profile = row.scalar_one()
        assert profile.no_show_count == 0


@pytest.mark.asyncio
async def test_cancel_by_freelancer_under_24h_marks_no_show(
    client: AsyncClient,
) -> None:
    """Cancel <24h pelo freelancer → no_show=true, counter++."""
    # Setup com start em 5 dias, depois congela o tempo a 23h antes do start.
    ctx = await _setup_contract_scenario(days_until_start=5)
    real_start = datetime.now(UTC) + timedelta(days=5)
    frozen_now = real_start - timedelta(hours=23)
    with freeze_time(frozen_now):
        h = await auth_header_for(client, ctx["fl_email"])
        r = await client.post(
            f"/v1/contracts/{ctx['contract_id']}/cancel",
            json={"reason": "doente"},
            headers=h,
        )
    assert r.status_code == 200
    body = r.json()
    assert body["no_show"] is True

    async with SessionLocal() as session:
        row = await session.execute(
            select(FreelancerProfile).where(
                FreelancerProfile.user_id == ctx["fl_id"]
            )
        )
        profile = row.scalar_one()
        assert profile.no_show_count == 1


@pytest.mark.asyncio
async def test_cancel_by_establishment_no_no_show(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario(days_until_start=5)
    h = await auth_header_for(client, ctx["est_email"])
    r = await client.post(
        f"/v1/contracts/{ctx['contract_id']}/cancel",
        json={"reason": "evento adiado"},
        headers=h,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["cancelled_by"] == "establishment"
    assert body["no_show"] is False


@pytest.mark.asyncio
async def test_cancel_far_from_start_reopens_job(client: AsyncClient) -> None:
    """Cancel com >2h até start_at → job volta a open."""
    ctx = await _setup_contract_scenario(days_until_start=5)
    h = await auth_header_for(client, ctx["fl_email"])
    await client.post(
        f"/v1/contracts/{ctx['contract_id']}/cancel",
        json={},
        headers=h,
    )
    async with SessionLocal() as session:
        row = await session.execute(
            select(JobPosting).where(JobPosting.id == ctx["job_id"])
        )
        job = row.scalar_one()
        assert job.status == "open"


@pytest.mark.asyncio
async def test_cancel_close_to_start_cancels_job(client: AsyncClient) -> None:
    """Cancel com ≤2h até start_at → job vira cancelled."""
    ctx = await _setup_contract_scenario(days_until_start=5)
    real_start = datetime.now(UTC) + timedelta(days=5)
    frozen_now = real_start - timedelta(hours=1)
    with freeze_time(frozen_now):
        h = await auth_header_for(client, ctx["fl_email"])
        await client.post(
            f"/v1/contracts/{ctx['contract_id']}/cancel",
            json={},
            headers=h,
        )
    async with SessionLocal() as session:
        row = await session.execute(
            select(JobPosting).where(JobPosting.id == ctx["job_id"])
        )
        job = row.scalar_one()
        assert job.status == "cancelled"


@pytest.mark.asyncio
async def test_cancel_terminal_returns_409(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario(status="completed")
    h = await auth_header_for(client, ctx["fl_email"])
    r = await client.post(
        f"/v1/contracts/{ctx['contract_id']}/cancel", json={}, headers=h
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_cancel_emits_notification_to_other_party(client: AsyncClient) -> None:
    ctx = await _setup_contract_scenario(days_until_start=5)
    h = await auth_header_for(client, ctx["fl_email"])
    await client.post(
        f"/v1/contracts/{ctx['contract_id']}/cancel", json={}, headers=h
    )
    # Establishment recebe notification
    h_est = await auth_header_for(client, ctx["est_email"])
    r = await client.get("/v1/me/notifications", headers=h_est)
    types = [n["type"] for n in r.json()["items"]]
    assert "contract.cancelled_by_other_party" in types
