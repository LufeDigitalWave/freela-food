"""Testes de rating agregado nos perfis (Sprint 5)."""

import uuid

import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.establishment_profile import EstablishmentProfile
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.schemas.review import ReviewCreate
from app.domain.services.review_service import ReviewService
from tests.factories import (
    make_application,
    make_completed_contract,
    make_establishment,
    make_freelancer,
    make_job,
    make_skill_category,
)


async def _setup_contract() -> dict:
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
        return {
            "contract_id": contract.id,
            "fl_id": fl.id,
            "est_id": est.id,
            "fl_email": f"fl-{suffix}@test.com",
            "cat_id": cat.id,
        }


async def test_first_review_sets_rating() -> None:
    ctx = await _setup_contract()
    # Establishment avalia freelancer com 4 estrelas
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["est_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=4),
        )

    # Profile do freelancer deve ter average_rating=4.00, total_reviews=1
    async with SessionLocal() as session:
        fp = await session.scalar(
            select(FreelancerProfile).where(
                FreelancerProfile.user_id == ctx["fl_id"]
            )
        )
    assert fp is not None
    assert fp.total_reviews == 1
    assert float(fp.average_rating) == pytest.approx(4.0, abs=0.01)


async def test_second_review_recalculates_average() -> None:
    ctx1 = await _setup_contract()
    # Primeira review: 4 estrelas pro freelancer
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx1["est_id"],
            contract_id=ctx1["contract_id"],
            payload=ReviewCreate(stars=4),
        )

    # Criar segundo contrato pro mesmo freelancer com outro establishment
    suffix2 = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        est2, _ = await make_establishment(session, email=f"est2-{suffix2}@test.com")
        cat = await make_skill_category(session)
        job2 = await make_job(
            session, establishment_id=est2.id, skill_category_id=cat.id,
            title=f"Vaga {suffix2}", status="completed",
        )
        app2 = await make_application(
            session, job_posting_id=job2.id, freelancer_id=ctx1["fl_id"], status="accepted"
        )
        contract2 = await make_completed_contract(
            session,
            freelancer_id=ctx1["fl_id"],
            establishment_id=est2.id,
            application_id=app2.id,
            job_posting_id=job2.id,
        )
        await session.commit()

    # Segunda review: 2 estrelas
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=est2.id,
            contract_id=contract2.id,
            payload=ReviewCreate(stars=2),
        )

    # Média = (4+2)/2 = 3.00
    async with SessionLocal() as session:
        fp = await session.scalar(
            select(FreelancerProfile).where(
                FreelancerProfile.user_id == ctx1["fl_id"]
            )
        )
    assert fp is not None
    assert fp.total_reviews == 2
    assert float(fp.average_rating) == pytest.approx(3.0, abs=0.01)


async def test_rating_updates_establishment_profile() -> None:
    ctx = await _setup_contract()
    # Freelancer avalia establishment com 5 estrelas
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5),
        )

    async with SessionLocal() as session:
        ep = await session.scalar(
            select(EstablishmentProfile).where(
                EstablishmentProfile.user_id == ctx["est_id"]
            )
        )
    assert ep is not None
    assert ep.total_reviews == 1
    assert float(ep.average_rating) == pytest.approx(5.0, abs=0.01)


async def test_reviewer_rating_unchanged() -> None:
    """Quem avalia NÃO ganha rating — só o reviewee."""
    ctx = await _setup_contract()
    # Freelancer avalia establishment
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5),
        )

    # Freelancer (reviewer) não deve ter rating alterado
    async with SessionLocal() as session:
        fp = await session.scalar(
            select(FreelancerProfile).where(
                FreelancerProfile.user_id == ctx["fl_id"]
            )
        )
    assert fp is not None
    assert fp.total_reviews == 0
    assert fp.average_rating is None


async def test_five_reviews_average_precision() -> None:
    """5 reviews com notas variadas — verifica precisão do arredondamento."""
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        cat = await make_skill_category(session)
        await session.commit()

    stars_list = [5, 4, 3, 5, 4]  # média = 21/5 = 4.20
    for stars in stars_list:
        s = uuid.uuid4().hex[:8]
        async with SessionLocal() as session:
            est_i, _ = await make_establishment(session, email=f"est-{s}@test.com")
            job_i = await make_job(
                session, establishment_id=est_i.id, skill_category_id=cat.id,
                title=f"Vaga {s}", status="completed",
            )
            app_i = await make_application(
                session, job_posting_id=job_i.id, freelancer_id=fl.id, status="accepted"
            )
            c_i = await make_completed_contract(
                session,
                freelancer_id=fl.id,
                establishment_id=est_i.id,
                application_id=app_i.id,
                job_posting_id=job_i.id,
            )
            await session.commit()

        async with SessionLocal() as session:
            await ReviewService(session).create_review(
                user_id=est_i.id,
                contract_id=c_i.id,
                payload=ReviewCreate(stars=stars),
            )

    async with SessionLocal() as session:
        fp = await session.scalar(
            select(FreelancerProfile).where(FreelancerProfile.user_id == fl.id)
        )
    assert fp is not None
    assert fp.total_reviews == 5
    assert float(fp.average_rating) == pytest.approx(4.2, abs=0.02)
