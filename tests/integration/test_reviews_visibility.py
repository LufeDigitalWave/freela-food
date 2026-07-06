"""Testes de visibilidade anti-retaliação de reviews (Sprint 5)."""

import uuid

from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.notification import Notification
from app.domain.models.review import Review
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


async def _setup() -> dict:
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
        }


async def test_first_review_invisible() -> None:
    ctx = await _setup()
    async with SessionLocal() as session:
        r = await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5),
        )
    assert r.visible_at is None


async def test_second_review_makes_both_visible() -> None:
    ctx = await _setup()
    # Primeira review (freelancer)
    async with SessionLocal() as session:
        r1 = await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5, comment="Ótimo!"),
        )
    assert r1.visible_at is None

    # Segunda review (establishment)
    async with SessionLocal() as session:
        r2 = await ReviewService(session).create_review(
            user_id=ctx["est_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=4, comment="Bom freelancer"),
        )
    assert r2.visible_at is not None

    # Verificar que a primeira review também ficou visível
    async with SessionLocal() as session:
        result = await session.execute(
            select(Review).where(Review.id == r1.id)
        )
        r1_updated = result.scalar_one()
    assert r1_updated.visible_at is not None


async def test_public_endpoint_filters_invisible() -> None:
    ctx = await _setup()
    # Criar review sem visible_at (primeira review)
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5),
        )

    # Listar reviews públicas do establishment — deve ser vazio
    async with SessionLocal() as session:
        public_list = await ReviewService(session).list_public(
            reviewee_id=ctx["est_id"], page=1, page_size=20
        )
    assert public_list.total == 0
    assert len(public_list.items) == 0


async def test_public_endpoint_shows_visible() -> None:
    ctx = await _setup()
    # Ambos avaliam → ficam visíveis
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5),
        )
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["est_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=4),
        )

    # Agora endpoint público mostra a review recebida pelo establishment
    async with SessionLocal() as session:
        public_list = await ReviewService(session).list_public(
            reviewee_id=ctx["est_id"], page=1, page_size=20
        )
    assert public_list.total == 1
    assert public_list.items[0].stars == 5


async def test_contract_reviews_own_visible_peer_hidden() -> None:
    ctx = await _setup()
    # Só freelancer avaliou
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5),
        )

    # Freelancer vê sua própria review
    async with SessionLocal() as session:
        reviews = await ReviewService(session).list_for_contract(
            user_id=ctx["fl_id"], contract_id=ctx["contract_id"]
        )
    assert len(reviews) == 1
    assert reviews[0].reviewer_id == ctx["fl_id"]

    # Establishment não vê nada (review do freelancer está invisível)
    async with SessionLocal() as session:
        reviews = await ReviewService(session).list_for_contract(
            user_id=ctx["est_id"], contract_id=ctx["contract_id"]
        )
    assert len(reviews) == 0


async def test_contract_reviews_both_visible_after_second() -> None:
    ctx = await _setup()
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5),
        )
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["est_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=3),
        )

    # Ambos veem ambas
    async with SessionLocal() as session:
        fl_reviews = await ReviewService(session).list_for_contract(
            user_id=ctx["fl_id"], contract_id=ctx["contract_id"]
        )
    assert len(fl_reviews) == 2

    async with SessionLocal() as session:
        est_reviews = await ReviewService(session).list_for_contract(
            user_id=ctx["est_id"], contract_id=ctx["contract_id"]
        )
    assert len(est_reviews) == 2


async def test_me_reviews_shows_all_received() -> None:
    ctx = await _setup()
    # Establishment avalia freelancer (review invisível)
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["est_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=4),
        )

    # /me/reviews do freelancer — deve ver a review mesmo invisível
    async with SessionLocal() as session:
        my_reviews = await ReviewService(session).list_received(
            user_id=ctx["fl_id"], page=1, page_size=20
        )
    assert my_reviews.total == 1
    assert my_reviews.items[0].stars == 4


async def test_notification_peer_submitted_on_first_review() -> None:
    ctx = await _setup()
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5),
        )

    async with SessionLocal() as session:
        result = await session.execute(
            select(Notification).where(
                Notification.user_id == ctx["est_id"],
                Notification.type == "review.peer_submitted",
            )
        )
        notif = result.scalar_one_or_none()
    assert notif is not None
    assert str(ctx["contract_id"]) in notif.payload.get("contract_id", "")


async def test_notification_both_visible_on_second_review() -> None:
    ctx = await _setup()
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["fl_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=5),
        )
    async with SessionLocal() as session:
        await ReviewService(session).create_review(
            user_id=ctx["est_id"],
            contract_id=ctx["contract_id"],
            payload=ReviewCreate(stars=4),
        )

    # Ambos devem ter notificação both_visible
    async with SessionLocal() as session:
        result = await session.execute(
            select(Notification).where(
                Notification.type == "review.both_visible",
                Notification.payload["contract_id"].astext == str(ctx["contract_id"]),
            )
        )
        notifs = result.scalars().all()
    assert len(notifs) == 2
    user_ids = {n.user_id for n in notifs}
    assert ctx["fl_id"] in user_ids
    assert ctx["est_id"] in user_ids
