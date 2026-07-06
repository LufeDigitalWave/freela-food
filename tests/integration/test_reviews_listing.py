"""Testes de listagem e stats de reviews (Sprint 5)."""

import uuid

import pytest

from app.core.database import SessionLocal
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


async def _setup_with_visible_reviews(*, count: int = 3) -> dict:
    """Cria N contratos completed com ambas reviews (visíveis)."""
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        fl, _ = await make_freelancer(
            session, email=f"fl-{suffix}@test.com", display_name=f"Freela {suffix}"
        )
        cat = await make_skill_category(session)
        contract_ids = []
        for i in range(count):
            job = await make_job(
                session,
                establishment_id=est.id,
                skill_category_id=cat.id,
                title=f"Vaga {suffix}-{i}",
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
            contract_ids.append(contract.id)
        await session.commit()
        return {
            "fl_id": fl.id,
            "est_id": est.id,
            "contract_ids": contract_ids,
        }


async def test_list_freelancer_reviews_public() -> None:
    ctx = await _setup_with_visible_reviews(count=2)
    # Ambos avaliam em cada contrato → reviews ficam visíveis
    for cid in ctx["contract_ids"]:
        async with SessionLocal() as session:
            await ReviewService(session).create_review(
                user_id=ctx["est_id"],
                contract_id=cid,
                payload=ReviewCreate(stars=4),
            )
        async with SessionLocal() as session:
            await ReviewService(session).create_review(
                user_id=ctx["fl_id"],
                contract_id=cid,
                payload=ReviewCreate(stars=5),
            )

    # Freelancer tem 2 reviews visíveis recebidas (do establishment)
    async with SessionLocal() as session:
        result = await ReviewService(session).list_public(
            reviewee_id=ctx["fl_id"], page=1, page_size=20
        )
    assert result.total == 2
    assert all(r.reviewee_id == ctx["fl_id"] for r in result.items)


async def test_list_establishment_reviews_public() -> None:
    ctx = await _setup_with_visible_reviews(count=2)
    for cid in ctx["contract_ids"]:
        async with SessionLocal() as session:
            await ReviewService(session).create_review(
                user_id=ctx["fl_id"],
                contract_id=cid,
                payload=ReviewCreate(stars=5),
            )
        async with SessionLocal() as session:
            await ReviewService(session).create_review(
                user_id=ctx["est_id"],
                contract_id=cid,
                payload=ReviewCreate(stars=4),
            )

    # Establishment tem 2 reviews visíveis recebidas (do freelancer)
    async with SessionLocal() as session:
        result = await ReviewService(session).list_public(
            reviewee_id=ctx["est_id"], page=1, page_size=20
        )
    assert result.total == 2
    assert all(r.reviewee_id == ctx["est_id"] for r in result.items)


async def test_stats_with_reviews() -> None:
    ctx = await _setup_with_visible_reviews(count=3)
    stars_given = [5, 4, 3]
    for i, cid in enumerate(ctx["contract_ids"]):
        async with SessionLocal() as session:
            await ReviewService(session).create_review(
                user_id=ctx["est_id"],
                contract_id=cid,
                payload=ReviewCreate(stars=stars_given[i]),
            )
        async with SessionLocal() as session:
            await ReviewService(session).create_review(
                user_id=ctx["fl_id"],
                contract_id=cid,
                payload=ReviewCreate(stars=5),
            )

    # Stats do freelancer (recebeu 5, 4, 3)
    async with SessionLocal() as session:
        stats = await ReviewService(session).get_stats(reviewee_id=ctx["fl_id"])
    assert stats.total_reviews == 3
    assert stats.average_rating == pytest.approx(4.0, abs=0.01)
    assert stats.distribution[5] == 1
    assert stats.distribution[4] == 1
    assert stats.distribution[3] == 1


async def test_stats_with_no_reviews() -> None:
    suffix = uuid.uuid4().hex[:8]
    async with SessionLocal() as session:
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        await session.commit()

    async with SessionLocal() as session:
        stats = await ReviewService(session).get_stats(reviewee_id=fl.id)
    assert stats.total_reviews == 0
    assert stats.average_rating is None
    assert stats.distribution == {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}


async def test_pagination() -> None:
    ctx = await _setup_with_visible_reviews(count=3)
    for cid in ctx["contract_ids"]:
        async with SessionLocal() as session:
            await ReviewService(session).create_review(
                user_id=ctx["est_id"],
                contract_id=cid,
                payload=ReviewCreate(stars=4),
            )
        async with SessionLocal() as session:
            await ReviewService(session).create_review(
                user_id=ctx["fl_id"],
                contract_id=cid,
                payload=ReviewCreate(stars=5),
            )

    # page_size=2 → page 1 tem 2 items, page 2 tem 1
    async with SessionLocal() as session:
        page1 = await ReviewService(session).list_public(
            reviewee_id=ctx["fl_id"], page=1, page_size=2
        )
    assert len(page1.items) == 2
    assert page1.total == 3

    async with SessionLocal() as session:
        page2 = await ReviewService(session).list_public(
            reviewee_id=ctx["fl_id"], page=2, page_size=2
        )
    assert len(page2.items) == 1


async def test_reviewer_display_name_present() -> None:
    ctx = await _setup_with_visible_reviews(count=1)
    cid = ctx["contract_ids"][0]
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["est_id"],
            contract_id=cid,
            payload=ReviewCreate(stars=4),
        )
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=cid,
            payload=ReviewCreate(stars=5),
        )

    async with SessionLocal() as session:
        result = await ReviewService(session).list_public(
            reviewee_id=ctx["fl_id"], page=1, page_size=20
        )
    # reviewer é o establishment → business_name
    assert result.items[0].reviewer_display_name is not None
    assert len(result.items[0].reviewer_display_name) > 0


async def test_reviews_from_other_user_not_shown() -> None:
    """Reviews de outro freelancer não aparecem na listagem deste."""
    ctx = await _setup_with_visible_reviews(count=1)
    cid = ctx["contract_ids"][0]
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["est_id"],
            contract_id=cid,
            payload=ReviewCreate(stars=4),
        )
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=cid,
            payload=ReviewCreate(stars=5),
        )

    # Outro freelancer não tem reviews
    other_id = uuid.uuid4()
    async with SessionLocal() as session:
        result = await ReviewService(session).list_public(
            reviewee_id=other_id, page=1, page_size=20
        )
    assert result.total == 0
