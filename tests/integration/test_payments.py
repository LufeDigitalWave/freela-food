"""Testes de pagamento — auto-create, confirm, dispute (Sprint 9)."""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.domain.models.notification import Notification
from app.domain.models.payment import Payment
from app.domain.services.payment_service import PaymentService
from tests.factories import (
    auth_header_for,
    make_application,
    make_completed_contract,
    make_establishment,
    make_freelancer,
    make_job,
    make_skill_category,
)


async def _setup_completed_with_payment() -> dict:
    """Cria contrato completed + payment pending."""
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        fl, fp = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        fp.pix_key = "fl@pix.com"
        cat = await make_skill_category(session)
        job = await make_job(
            session,
            establishment_id=est.id,
            skill_category_id=cat.id,
            status="completed",
            hourly_rate=Decimal("50.00"),
        )
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id, status="accepted"
        )
        contract = await make_completed_contract(
            session,
            freelancer_id=fl.id,
            establishment_id=est.id,
            application_id=app_.id,
            job_posting_id=job.id,
        )
        await session.flush()
        await session.commit()

    # Criar payment via service
    async with SessionLocal() as session:
        await PaymentService(session).create_for_contract(
            contract_id=contract.id, freelancer_id=fl.id
        )
        await session.commit()

    return {
        "contract_id": contract.id,
        "fl_id": fl.id,
        "fl_email": f"fl-{suffix}@test.com",
        "est_id": est.id,
        "est_email": f"est-{suffix}@test.com",
    }


async def test_create_payment_for_contract() -> None:
    ctx = await _setup_completed_with_payment()
    async with SessionLocal() as session:
        payment = await session.scalar(
            select(Payment).where(Payment.contract_id == ctx["contract_id"])
        )
    assert payment is not None
    assert payment.status == "pending"
    assert payment.pix_key == "fl@pix.com"
    assert payment.amount > Decimal("0")


async def test_create_payment_idempotent() -> None:
    ctx = await _setup_completed_with_payment()
    # Chamar de novo não deve criar duplicata
    async with SessionLocal() as session:
        await PaymentService(session).create_for_contract(
            contract_id=ctx["contract_id"], freelancer_id=ctx["fl_id"]
        )
        await session.commit()
    async with SessionLocal() as session:
        count = await session.scalar(
            select(func.count()).select_from(Payment).where(
                Payment.contract_id == ctx["contract_id"]
            )
        )
    assert count == 1


async def test_payment_notification_pending() -> None:
    ctx = await _setup_completed_with_payment()
    async with SessionLocal() as session:
        result = await session.execute(
            select(Notification).where(
                Notification.user_id == ctx["fl_id"],
                Notification.type == "payment.pending",
            )
        )
        notif = result.scalar_one_or_none()
    assert notif is not None


@pytest.mark.asyncio
async def test_get_payment_endpoint(client: AsyncClient) -> None:
    ctx = await _setup_completed_with_payment()
    headers = await auth_header_for(client, ctx["fl_email"])
    resp = await client.get(
        f"/v1/contracts/{ctx['contract_id']}/payment", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"
    assert resp.json()["pix_key"] == "fl@pix.com"


@pytest.mark.asyncio
async def test_confirm_payment(client: AsyncClient) -> None:
    ctx = await _setup_completed_with_payment()
    headers = await auth_header_for(client, ctx["est_email"])
    resp = await client.post(
        f"/v1/contracts/{ctx['contract_id']}/payment/confirm",
        json={"notes": "Pix enviado"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"
    assert resp.json()["notes"] == "Pix enviado"
    assert resp.json()["confirmed_at"] is not None


@pytest.mark.asyncio
async def test_confirm_payment_freelancer_forbidden(client: AsyncClient) -> None:
    ctx = await _setup_completed_with_payment()
    headers = await auth_header_for(client, ctx["fl_email"])
    resp = await client.post(
        f"/v1/contracts/{ctx['contract_id']}/payment/confirm",
        json={},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dispute_payment(client: AsyncClient) -> None:
    ctx = await _setup_completed_with_payment()
    headers = await auth_header_for(client, ctx["fl_email"])
    resp = await client.post(
        f"/v1/contracts/{ctx['contract_id']}/payment/dispute",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "disputed"
    assert resp.json()["disputed_at"] is not None


@pytest.mark.asyncio
async def test_dispute_payment_establishment_forbidden(client: AsyncClient) -> None:
    ctx = await _setup_completed_with_payment()
    headers = await auth_header_for(client, ctx["est_email"])
    resp = await client.post(
        f"/v1/contracts/{ctx['contract_id']}/payment/dispute",
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_confirm_already_confirmed(client: AsyncClient) -> None:
    ctx = await _setup_completed_with_payment()
    headers = await auth_header_for(client, ctx["est_email"])
    # Confirmar
    await client.post(
        f"/v1/contracts/{ctx['contract_id']}/payment/confirm",
        json={},
        headers=headers,
    )
    # Tentar confirmar de novo
    resp = await client.post(
        f"/v1/contracts/{ctx['contract_id']}/payment/confirm",
        json={},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_my_payments(client: AsyncClient) -> None:
    ctx = await _setup_completed_with_payment()
    headers = await auth_header_for(client, ctx["fl_email"])
    resp = await client.get("/v1/me/payments", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(p["contract_id"] == str(ctx["contract_id"]) for p in body["items"])


@pytest.mark.asyncio
async def test_payment_not_found_before_completion(client: AsyncClient) -> None:
    """Contrato sem payment retorna 404."""
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est.id, skill_category_id=cat.id, status="completed"
        )
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id, status="accepted"
        )
        contract = await make_completed_contract(
            session,
            freelancer_id=fl.id,
            establishment_id=est.id,
            application_id=app_.id,
            job_posting_id=job.id,
        )
        await session.commit()

    headers = await auth_header_for(client, f"fl-{suffix}@test.com")
    resp = await client.get(
        f"/v1/contracts/{contract.id}/payment", headers=headers
    )
    assert resp.status_code == 404
