"""Repository de Review (Sprint 5)."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import CursorResult, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.review import Review


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        contract_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        reviewee_id: uuid.UUID,
        stars: int,
        comment: str | None,
    ) -> Review:
        review = Review(
            contract_id=contract_id,
            reviewer_id=reviewer_id,
            reviewee_id=reviewee_id,
            stars=stars,
            comment=comment,
            created_at=datetime.now(UTC),
        )
        self._session.add(review)
        await self._session.flush()
        await self._session.refresh(review)
        return review

    async def get_by_contract_and_reviewer(
        self, contract_id: uuid.UUID, reviewer_id: uuid.UUID
    ) -> Review | None:
        result = await self._session.execute(
            select(Review).where(
                Review.contract_id == contract_id,
                Review.reviewer_id == reviewer_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_peer_review(
        self, contract_id: uuid.UUID, reviewer_id: uuid.UUID
    ) -> Review | None:
        """Retorna a review que a OUTRA parte escreveu (onde reviewer_id é o peer)."""
        result = await self._session.execute(
            select(Review).where(
                Review.contract_id == contract_id,
                Review.reviewer_id != reviewer_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_visible_for_user(
        self, reviewee_id: uuid.UUID, *, page: int, page_size: int
    ) -> tuple[list[Review], int]:
        """Reviews visíveis recebidas por um user (endpoint público). Exclui hidden."""
        base = select(Review).where(
            Review.reviewee_id == reviewee_id,
            Review.visible_at.is_not(None),
            Review.visible_at <= datetime.now(UTC),
            Review.hidden_at.is_(None),
        )
        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(Review.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def list_received_for_user(
        self, reviewee_id: uuid.UUID, *, page: int, page_size: int
    ) -> tuple[list[Review], int]:
        """Todas reviews recebidas (visíveis ou não) — pra /me/reviews."""
        base = select(Review).where(Review.reviewee_id == reviewee_id)
        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(Review.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def list_for_contract(self, contract_id: uuid.UUID) -> list[Review]:
        result = await self._session.execute(
            select(Review)
            .where(Review.contract_id == contract_id)
            .order_by(Review.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_distribution(self, reviewee_id: uuid.UUID) -> dict[int, int]:
        """COUNT de reviews visíveis agrupadas por stars. Exclui hidden."""
        result = await self._session.execute(
            select(Review.stars, func.count())
            .where(
                Review.reviewee_id == reviewee_id,
                Review.visible_at.is_not(None),
                Review.visible_at <= datetime.now(UTC),
                Review.hidden_at.is_(None),
            )
            .group_by(Review.stars)
        )
        dist: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for stars, count in result.all():
            dist[int(stars)] = int(count)
        return dist

    async def mark_visible(self, review_ids: list[uuid.UUID]) -> int:
        """Batch update visible_at = now() para reviews específicas."""
        if not review_ids:
            return 0
        result = cast(
            CursorResult[Any],
            await self._session.execute(
                update(Review)
                .where(Review.id.in_(review_ids))
                .values(visible_at=datetime.now(UTC))
            ),
        )
        await self._session.flush()
        return int(result.rowcount or 0)

    async def find_orphan_reviews_to_reveal(self) -> list[Review]:
        """Reviews com visible_at NULL e created_at > 7 dias (pra cron reveal)."""
        cutoff = datetime.now(UTC) - timedelta(days=7)
        result = await self._session.execute(
            select(Review).where(
                Review.visible_at.is_(None),
                Review.created_at <= cutoff,
            )
        )
        return list(result.scalars().all())
