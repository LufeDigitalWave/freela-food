"""Testes de criação de review (Sprint 5)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.database import SessionLocal
from app.domain.schemas.review import ReviewCreate
from app.domain.services.review_service import ReviewService
from tests.factories import (
    make_application,
    make_completed_contract,
    make_contract,
    make_establishment,
    make_freelancer,
    make_invitation,
    make_job,
    make_skill_category,
)


async def _setup_completed_contract(
    *, via_invitation: bool = False
) -> dict:
    """Cria freelancer + establishment + contrato completed."""
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")

        if via_invitation:
            cat = await make_skill_category(session)
            inv = await make_invitation(
                session,
                establishment_id=est.id,
                freelancer_id=fl.id,
                skill_category_id=cat.id,
                status="accepted",
            )
            contract = await make_completed_contract(
                session,
                freelancer_id=fl.id,
                establishment_id=est.id,
                invitation_id=inv.id,
            )
        else:
            cat = await make_skill_category(session)
            job = await make_job(
                session,
                establishment_id=est.id,
                skill_category_id=cat.id,
                status="completed",
            )
            app_ = await make_application(
                session,
                job_posting_id=job.id,
                freelancer_id=fl.id,
                status="accepted",
            )
            contract = await make_completed_contract(
                session,
                freelancer_id=fl.id,
                establishment_id=est.id,
                application_id=app_.id,
                job_posting_id=job.id,
            )
        await session.commit()
        return {
            "contract_id": contract.id,
            "fl_id": fl.id,
            "est_id": est.id,
        }


async def test_freelancer_reviews_establishment() -> None:
    ctx = await _setup_completed_contract()
    async with SessionLocal() as session:
        result = await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5, comment="Excelente lugar!"),
        )
    assert result.stars == 5
    assert result.comment == "Excelente lugar!"
    assert result.reviewer_id == ctx["fl_id"]
    assert result.reviewee_id == ctx["est_id"]
    assert result.visible_at is None  # primeira review, invisível


async def test_establishment_reviews_freelancer() -> None:
    ctx = await _setup_completed_contract()
    async with SessionLocal() as session:
        result = await ReviewService(session).create_review(
            user_id=ctx["est_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=4),
        )
    assert result.stars == 4
    assert result.reviewer_id == ctx["est_id"]
    assert result.reviewee_id == ctx["fl_id"]


async def test_review_via_invitation_contract() -> None:
    ctx = await _setup_completed_contract(via_invitation=True)
    async with SessionLocal() as session:
        result = await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=3, comment="Ok"),
        )
    assert result.stars == 3
    assert result.contract_id == ctx["contract_id"]


async def test_review_permission_denied_non_party() -> None:
    ctx = await _setup_completed_contract()
    outsider_id = uuid.uuid4()
    async with SessionLocal() as session:
        with pytest.raises(Exception) as exc_info:
            await ReviewService(session).create_review(
                user_id=outsider_id,
                contract_id=ctx["contract_id"],
                payload=ReviewCreate(stars=4),
            )
    assert "Permissão negada" in str(exc_info.value)


async def test_review_contract_not_completed() -> None:
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est.id, skill_category_id=cat.id
        )
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id, status="accepted"
        )
        contract = await make_contract(
            session,
            application_id=app_.id,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            establishment_id=est.id,
            status="scheduled",
        )
        await session.commit()

    async with SessionLocal() as session:
        with pytest.raises(Exception) as exc_info:
            await ReviewService(session).create_review(
                user_id=fl.id,
                contract_id=contract.id,
                payload=ReviewCreate(stars=5),
            )
    assert "completed" in str(exc_info.value).lower()


async def test_review_window_closed() -> None:
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session, establishment_id=est.id, skill_category_id=cat.id
        )
        app_ = await make_application(
            session, job_posting_id=job.id, freelancer_id=fl.id, status="accepted"
        )
        # Contrato completed há 35 dias (fora da janela de 30)
        contract = await make_completed_contract(
            session,
            freelancer_id=fl.id,
            establishment_id=est.id,
            application_id=app_.id,
            job_posting_id=job.id,
            start_at=datetime.now(UTC) - timedelta(days=40),
            end_at=datetime.now(UTC) - timedelta(days=35),
        )
        # Forçar updated_at pra 35 dias atrás (simula completion antiga)
        contract.updated_at = datetime.now(UTC) - timedelta(days=35)
        await session.flush()
        await session.commit()

    async with SessionLocal() as session:
        with pytest.raises(Exception) as exc_info:
            await ReviewService(session).create_review(
                user_id=fl.id,
                contract_id=contract.id,
                payload=ReviewCreate(stars=5),
            )
    assert "30 dias" in str(exc_info.value)


async def test_review_duplicate_blocked() -> None:
    ctx = await _setup_completed_contract()
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5),
        )
    # Tentar segunda review do mesmo user
    async with SessionLocal() as session:
        with pytest.raises(Exception) as exc_info:
            await ReviewService(session).create_review(
                user_id=ctx["fl_id"],
                contract_id=ctx["contract_id"],
                payload=ReviewCreate(stars=3),
            )
    assert "já avaliou" in str(exc_info.value).lower()


async def test_reviewee_id_auto_calculated() -> None:
    ctx = await _setup_completed_contract()
    # Freelancer avalia → reviewee = establishment
    async with SessionLocal() as session:
        r1 = await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=4),
        )
    assert r1.reviewee_id == ctx["est_id"]

    # Setup novo contrato pra establishment avaliar
    ctx2 = await _setup_completed_contract()
    async with SessionLocal() as session:
        r2 = await ReviewService(session).create_review(
            user_id=ctx2["est_id"],
            contract_id=ctx2["contract_id"],
            payload=ReviewCreate(stars=3),
        )
    assert r2.reviewee_id == ctx2["fl_id"]
