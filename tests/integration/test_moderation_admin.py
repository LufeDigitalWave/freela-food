"""Testes de moderação admin — resolve reports + hide/unhide reviews (Sprint 8)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.notification import Notification
from app.domain.models.review import Review
from app.domain.schemas.review import ReviewCreate
from app.domain.services.review_service import ReviewService
from tests.factories import (
    auth_header_for,
    make_admin,
    make_application,
    make_completed_contract,
    make_establishment,
    make_freelancer,
    make_job,
    make_skill_category,
)


async def _admin_headers(client: AsyncClient) -> tuple[uuid.UUID, dict[str, str]]:
    suffix = uuid.uuid4().hex[:8]
    email = f"admin-{suffix}@test.com"
    async with SessionLocal() as session:
        admin = await make_admin(session, email=email)
        await session.commit()
        admin_id = admin.id
    headers = await auth_header_for(client, email)
    return admin_id, headers


async def _create_report_via_api(client: AsyncClient) -> dict:
    """Cria user + report e retorna contexto."""
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        await session.commit()

    headers = await auth_header_for(client, f"fl-{suffix}@test.com")
    resp = await client.post(
        "/v1/reports",
        json={
            "target_type": "user",
            "target_id": str(est.id),
            "reason": "spam",
            "description": "Perfil fake",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return {
        "report_id": uuid.UUID(resp.json()["id"]),
        "fl_id": fl.id,
        "est_id": est.id,
        "fl_email": f"fl-{suffix}@test.com",
    }


async def _create_visible_review() -> dict:
    """Cria contrato + review visível pra testar hide."""
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

    # Ambos avaliam → review fica visível
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=fl.id,
            contract_id=contract.id,
            payload=ReviewCreate(stars=5, comment="Ótimo!"),
        )
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=est.id,
            contract_id=contract.id,
            payload=ReviewCreate(stars=1, comment="Péssimo"),
        )

    # Pegar a review do establishment (que avaliou o freelancer)
    async with SessionLocal() as session:
        result = await session.execute(
            select(Review).where(
                Review.contract_id == contract.id,
                Review.reviewer_id == est.id,
            )
        )
        review = result.scalar_one()
        review_id = review.id

    return {
        "review_id": review_id,
        "reviewer_id": est.id,
        "fl_id": fl.id,
        "contract_id": contract.id,
    }


# ── Admin reports ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_list_reports(client: AsyncClient) -> None:
    await _create_report_via_api(client)
    _, headers = await _admin_headers(client)
    resp = await client.get("/v1/admin/reports", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_admin_list_reports_filter_status(client: AsyncClient) -> None:
    await _create_report_via_api(client)
    _, headers = await _admin_headers(client)
    resp = await client.get("/v1/admin/reports?status=pending", headers=headers)
    assert resp.status_code == 200
    assert all(r["status"] == "pending" for r in resp.json()["items"])


@pytest.mark.asyncio
async def test_admin_get_report_detail(client: AsyncClient) -> None:
    ctx = await _create_report_via_api(client)
    _, headers = await _admin_headers(client)
    resp = await client.get(f"/v1/admin/reports/{ctx['report_id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == str(ctx["report_id"])


@pytest.mark.asyncio
async def test_admin_resolve_report_action(client: AsyncClient) -> None:
    ctx = await _create_report_via_api(client)
    _, headers = await _admin_headers(client)
    resp = await client.post(
        f"/v1/admin/reports/{ctx['report_id']}/resolve",
        json={"status": "resolved_action", "resolution_note": "Usuário banido"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "resolved_action"
    assert body["resolution_note"] == "Usuário banido"
    assert body["resolved_at"] is not None


@pytest.mark.asyncio
async def test_admin_resolve_report_dismissed(client: AsyncClient) -> None:
    ctx = await _create_report_via_api(client)
    _, headers = await _admin_headers(client)
    resp = await client.post(
        f"/v1/admin/reports/{ctx['report_id']}/resolve",
        json={"status": "resolved_dismissed", "resolution_note": "Sem evidência"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved_dismissed"


@pytest.mark.asyncio
async def test_resolve_already_resolved_fails(client: AsyncClient) -> None:
    ctx = await _create_report_via_api(client)
    _, headers = await _admin_headers(client)
    # Resolver
    await client.post(
        f"/v1/admin/reports/{ctx['report_id']}/resolve",
        json={"status": "resolved_action", "resolution_note": "Done"},
        headers=headers,
    )
    # Tentar resolver de novo
    resp = await client.post(
        f"/v1/admin/reports/{ctx['report_id']}/resolve",
        json={"status": "resolved_dismissed", "resolution_note": "Retry"},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_resolve_notifies_reporter(client: AsyncClient) -> None:
    ctx = await _create_report_via_api(client)
    _, headers = await _admin_headers(client)
    await client.post(
        f"/v1/admin/reports/{ctx['report_id']}/resolve",
        json={"status": "resolved_action", "resolution_note": "Banido"},
        headers=headers,
    )
    async with SessionLocal() as session:
        result = await session.execute(
            select(Notification).where(
                Notification.user_id == ctx["fl_id"],
                Notification.type == "report.resolved",
            )
        )
        notif = result.scalar_one_or_none()
    assert notif is not None


# ── Hide/unhide review ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_hide_review(client: AsyncClient) -> None:
    ctx = await _create_visible_review()
    _, headers = await _admin_headers(client)
    resp = await client.post(
        f"/v1/admin/reviews/{ctx['review_id']}/hide", headers=headers
    )
    assert resp.status_code == 204

    # Verificar que hidden_at está preenchido
    async with SessionLocal() as session:
        review = await session.scalar(
            select(Review).where(Review.id == ctx["review_id"])
        )
    assert review is not None
    assert review.hidden_at is not None


@pytest.mark.asyncio
async def test_admin_unhide_review(client: AsyncClient) -> None:
    ctx = await _create_visible_review()
    _, headers = await _admin_headers(client)
    # Hide first
    await client.post(f"/v1/admin/reviews/{ctx['review_id']}/hide", headers=headers)
    # Then unhide
    resp = await client.post(
        f"/v1/admin/reviews/{ctx['review_id']}/unhide", headers=headers
    )
    assert resp.status_code == 204

    async with SessionLocal() as session:
        review = await session.scalar(
            select(Review).where(Review.id == ctx["review_id"])
        )
    assert review is not None
    assert review.hidden_at is None


@pytest.mark.asyncio
async def test_hidden_review_not_in_public_list(client: AsyncClient) -> None:
    ctx = await _create_visible_review()
    _, headers = await _admin_headers(client)
    # Hide the review
    await client.post(f"/v1/admin/reviews/{ctx['review_id']}/hide", headers=headers)

    # Public listing do freelancer não deve mostrar a review escondida
    async with SessionLocal() as session:
        from app.domain.services.review_service import ReviewService

        result = await ReviewService(session).list_public(
            reviewee_id=ctx["fl_id"], page=1, page_size=20
        )
    # A review que o establishment deu pro freelancer foi hidden
    hidden_ids = {i.id for i in result.items}
    assert ctx["review_id"] not in hidden_ids
