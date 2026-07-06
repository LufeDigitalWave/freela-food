"""Service de Review — criação, listagem, stats, visibilidade (Sprint 5)."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ContractNotCompleted,
    DuplicateReview,
    NotFoundError,
    PermissionDenied,
    ReviewWindowClosed,
)
from app.domain.models.establishment_profile import EstablishmentProfile
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.review import Review
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.review_repository import ReviewRepository
from app.domain.schemas.review import (
    ReviewCreate,
    ReviewList,
    ReviewRead,
    ReviewStats,
)
from app.domain.services.notification_service import NotificationService
from app.utils.audit import write_audit_log

_REVIEW_WINDOW_DAYS = 30


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ReviewRepository(session)
        self._contracts = ContractRepository(session)
        self._notifications = NotificationService(session)

    async def create_review(
        self, *, user_id: uuid.UUID, contract_id: uuid.UUID, payload: ReviewCreate
    ) -> ReviewRead:
        """Cria review pós-contrato com regra de visibilidade anti-retaliação."""
        contract = await self._contracts.get_by_id(contract_id)
        if contract is None:
            raise NotFoundError("Contrato não encontrado")

        # Ator deve ser parte do contrato
        if user_id not in (contract.freelancer_id, contract.establishment_id):
            raise PermissionDenied()

        # Contrato precisa estar completed
        if contract.status != "completed":
            raise ContractNotCompleted()

        # Janela de 30 dias
        completed_at = contract.updated_at or contract.created_at
        if datetime.now(UTC) - completed_at > timedelta(days=_REVIEW_WINDOW_DAYS):
            raise ReviewWindowClosed()

        # Sem duplicata
        existing = await self._repo.get_by_contract_and_reviewer(
            contract_id, user_id
        )
        if existing is not None:
            raise DuplicateReview()

        # Calcular reviewee (a outra parte)
        reviewee_id = (
            contract.establishment_id
            if user_id == contract.freelancer_id
            else contract.freelancer_id
        )

        # Criar review
        review = await self._repo.create(
            contract_id=contract_id,
            reviewer_id=user_id,
            reviewee_id=reviewee_id,
            stars=payload.stars,
            comment=payload.comment,
        )

        # Regra de visibilidade: verificar se peer já avaliou
        peer_review = await self._repo.get_peer_review(contract_id, user_id)
        if peer_review is not None:
            # Ambas avaliaram → marcar ambas visíveis
            now = datetime.now(UTC)
            review.visible_at = now
            peer_review.visible_at = now
            await self._session.flush()

            # Notificar ambas partes
            await self._notifications.emit(
                user_id=user_id,
                type="review.both_visible",
                payload={"contract_id": str(contract_id)},
            )
            await self._notifications.emit(
                user_id=reviewee_id,
                type="review.both_visible",
                payload={"contract_id": str(contract_id)},
            )
        else:
            # Primeira review — notificar outra parte (sem revelar conteúdo)
            await self._notifications.emit(
                user_id=reviewee_id,
                type="review.peer_submitted",
                payload={"contract_id": str(contract_id)},
            )

        # Atualizar rating agregado do reviewee
        await self._update_rating(reviewee_id, payload.stars)

        # Audit log
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="create",
            entity="review",
            entity_id=review.id,
            diff={
                "stars": payload.stars,
                "has_comment": payload.comment is not None,
                "contract_id": str(contract_id),
            },
        )

        await self._session.commit()
        return await self._to_read(review)

    async def list_for_contract(
        self, *, user_id: uuid.UUID, contract_id: uuid.UUID
    ) -> list[ReviewRead]:
        """Reviews de um contrato (com visibilidade aplicada)."""
        contract = await self._contracts.get_by_id(contract_id)
        if contract is None:
            raise NotFoundError("Contrato não encontrado")
        if user_id not in (contract.freelancer_id, contract.establishment_id):
            raise PermissionDenied()

        reviews = await self._repo.list_for_contract(contract_id)
        result: list[ReviewRead] = []
        now = datetime.now(UTC)
        for r in reviews:
            # User vê sua própria review OU a do outro se visible_at preenchido
            if r.reviewer_id == user_id or (
                r.visible_at is not None and r.visible_at <= now
            ):
                result.append(await self._to_read(r))
        return result

    async def list_received(
        self, *, user_id: uuid.UUID, page: int, page_size: int
    ) -> ReviewList:
        """Todas reviews recebidas pelo user (/me/reviews)."""
        items, total = await self._repo.list_received_for_user(
            user_id, page=page, page_size=page_size
        )
        return ReviewList(
            items=[await self._to_read(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def list_public(
        self, *, reviewee_id: uuid.UUID, page: int, page_size: int
    ) -> ReviewList:
        """Reviews visíveis de um perfil (endpoint público)."""
        items, total = await self._repo.list_visible_for_user(
            reviewee_id, page=page, page_size=page_size
        )
        return ReviewList(
            items=[await self._to_read(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_stats(self, *, reviewee_id: uuid.UUID) -> ReviewStats:
        """Rating agregado + distribuição por estrela (apenas visíveis)."""
        dist = await self._repo.get_distribution(reviewee_id)
        total = sum(dist.values())
        if total == 0:
            return ReviewStats(average_rating=None, total_reviews=0, distribution=dist)
        avg = sum(stars * count for stars, count in dist.items()) / total
        return ReviewStats(
            average_rating=round(avg, 2),
            total_reviews=total,
            distribution=dist,
        )

    # ── Helpers privados ──────────────────────────────────────────────────────

    async def _update_rating(
        self, reviewee_id: uuid.UUID, new_stars: int
    ) -> None:
        """Atualiza rating agregado no perfil do reviewee (fórmula incremental)."""
        # Tentar freelancer profile primeiro
        fp = await self._session.scalar(
            select(FreelancerProfile).where(
                FreelancerProfile.user_id == reviewee_id
            )
        )
        if fp is not None:
            new_total = fp.total_reviews + 1
            if fp.average_rating is None:
                new_avg = Decimal(new_stars)
            else:
                new_avg = (
                    (fp.average_rating * (new_total - 1) + new_stars) / new_total
                )
            await self._session.execute(
                update(FreelancerProfile)
                .where(FreelancerProfile.user_id == reviewee_id)
                .values(
                    average_rating=round(new_avg, 2),
                    total_reviews=new_total,
                )
            )
            return

        # Senão, establishment profile
        ep = await self._session.scalar(
            select(EstablishmentProfile).where(
                EstablishmentProfile.user_id == reviewee_id
            )
        )
        if ep is not None:
            new_total = ep.total_reviews + 1
            if ep.average_rating is None:
                new_avg = Decimal(new_stars)
            else:
                new_avg = (
                    (ep.average_rating * (new_total - 1) + new_stars) / new_total
                )
            await self._session.execute(
                update(EstablishmentProfile)
                .where(EstablishmentProfile.user_id == reviewee_id)
                .values(
                    average_rating=round(new_avg, 2),
                    total_reviews=new_total,
                )
            )

    async def _to_read(self, review: Review) -> ReviewRead:
        """Converte model pra schema com reviewer_display_name resolvido."""
        display_name = await self._get_display_name(review.reviewer_id)
        return ReviewRead(
            id=review.id,
            contract_id=review.contract_id,
            reviewer_id=review.reviewer_id,
            reviewee_id=review.reviewee_id,
            stars=review.stars,
            comment=review.comment,
            visible_at=review.visible_at,
            created_at=review.created_at,
            reviewer_display_name=display_name,
        )

    async def _get_display_name(self, user_id: uuid.UUID) -> str | None:
        """Resolve display_name do reviewer (freelancer ou establishment)."""
        # Tenta freelancer
        fp: str | None = await self._session.scalar(
            select(FreelancerProfile.display_name).where(
                FreelancerProfile.user_id == user_id
            )
        )
        if fp is not None:
            return fp

        # Tenta establishment
        ep: str | None = await self._session.scalar(
            select(EstablishmentProfile.business_name).where(
                EstablishmentProfile.user_id == user_id
            )
        )
        return ep
