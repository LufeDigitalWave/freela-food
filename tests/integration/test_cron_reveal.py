"""Testes do cron reveal_reviews (Sprint 5)."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.notification import Notification
from app.domain.models.review import Review
from app.workers.tasks import reveal_reviews
from tests.factories import (
    make_application,
    make_completed_contract,
    make_establishment,
    make_freelancer,
    make_job,
    make_review,
    make_skill_category,
)


async def _create_orphan_review(
    *, days_ago: int = 8, visible_at: datetime | None = None
) -> dict:
    """Cria review órfã (só uma parte avaliou) com created_at N dias atrás."""
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
        review = await make_review(
            session,
            contract_id=contract.id,
            reviewer_id=fl.id,
            reviewee_id=est.id,
            stars=4,
            comment="Bom lugar",
            visible_at=visible_at,
            created_at=datetime.now(UTC) - timedelta(days=days_ago),
        )
        await session.commit()
        return {
            "review_id": review.id,
            "fl_id": fl.id,
            "est_id": est.id,
            "contract_id": contract.id,
        }


async def test_reveals_review_older_than_7_days() -> None:
    ctx = await _create_orphan_review(days_ago=8)

    result = await reveal_reviews({})
    assert result["revealed"] >= 1

    # Verificar visible_at preenchido
    async with SessionLocal() as session:
        review = await session.scalar(
            select(Review).where(Review.id == ctx["review_id"])
        )
    assert review is not None
    assert review.visible_at is not None


async def test_does_not_reveal_review_less_than_7_days() -> None:
    ctx = await _create_orphan_review(days_ago=3)

    await reveal_reviews({})

    async with SessionLocal() as session:
        review = await session.scalar(
            select(Review).where(Review.id == ctx["review_id"])
        )
    assert review is not None
    assert review.visible_at is None


async def test_does_not_touch_already_visible() -> None:
    """Reviews já com visible_at não são tocadas (idempotente)."""
    original_visible = datetime.now(UTC) - timedelta(days=1)
    ctx = await _create_orphan_review(days_ago=10, visible_at=original_visible)

    await reveal_reviews({})

    async with SessionLocal() as session:
        review = await session.scalar(
            select(Review).where(Review.id == ctx["review_id"])
        )
    assert review is not None
    # visible_at não mudou
    assert abs((review.visible_at - original_visible).total_seconds()) < 2


async def test_notification_review_revealed_emitted() -> None:
    ctx = await _create_orphan_review(days_ago=8)

    await reveal_reviews({})

    async with SessionLocal() as session:
        result = await session.execute(
            select(Notification).where(
                Notification.user_id == ctx["fl_id"],
                Notification.type == "review.revealed",
            )
        )
        notif = result.scalar_one_or_none()
    assert notif is not None
    assert notif.payload["review_id"] == str(ctx["review_id"])


async def test_multiple_reviews_revealed_in_batch() -> None:
    """Múltiplas reviews órfãs são reveladas em uma única execução."""
    ctx1 = await _create_orphan_review(days_ago=8)
    ctx2 = await _create_orphan_review(days_ago=10)

    result = await reveal_reviews({})
    assert result["revealed"] >= 2

    async with SessionLocal() as session:
        r1 = await session.scalar(
            select(Review).where(Review.id == ctx1["review_id"])
        )
        r2 = await session.scalar(
            select(Review).where(Review.id == ctx2["review_id"])
        )
    assert r1 is not None and r1.visible_at is not None
    assert r2 is not None and r2.visible_at is not None
