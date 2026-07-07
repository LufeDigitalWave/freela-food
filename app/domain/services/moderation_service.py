"""Service de moderação — reports, hide/unhide reviews (Sprint 8)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateReport,
    NotFoundError,
    ReportNotPending,
    ReviewAlreadyHidden,
    ReviewNotHidden,
    SelfReportForbidden,
)
from app.domain.models.review import Review
from app.domain.repositories.report_repository import ReportRepository
from app.domain.schemas.report import (
    ReportCreate,
    ReportList,
    ReportRead,
    ResolveRequest,
)
from app.domain.services.notification_service import NotificationService
from app.utils.audit import write_audit_log


class ModerationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._reports = ReportRepository(session)
        self._notifications = NotificationService(session)

    # ── User-facing ───────────────────────────────────────────────────────────

    async def create_report(
        self, *, user_id: uuid.UUID, payload: ReportCreate
    ) -> ReportRead:
        """Cria denúncia. User não pode reportar a si mesmo."""
        # Self-report check
        if payload.target_type == "user" and payload.target_id == user_id:
            raise SelfReportForbidden()

        # Duplicata pendente
        if await self._reports.has_pending_duplicate(
            reporter_id=user_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
        ):
            raise DuplicateReport()

        report = await self._reports.create(
            reporter_id=user_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
            reason=payload.reason,
            description=payload.description,
        )

        # Notificação de confirmação
        await self._notifications.emit(
            user_id=user_id,
            type="report.submitted",
            payload={"report_id": str(report.id), "target_type": payload.target_type},
        )

        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="create",
            entity="report",
            entity_id=report.id,
            diff={"target_type": payload.target_type, "reason": payload.reason},
        )

        await self._session.commit()
        return ReportRead.model_validate(report)

    async def list_my_reports(
        self, *, user_id: uuid.UUID, page: int, page_size: int
    ) -> ReportList:
        items, total = await self._reports.list_for_reporter(
            user_id, page=page, page_size=page_size
        )
        return ReportList(
            items=[ReportRead.model_validate(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── Admin ─────────────────────────────────────────────────────────────────

    async def list_reports(
        self,
        *,
        status: str | None = None,
        target_type: str | None = None,
        reason: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ReportList:
        items, total = await self._reports.list_all(
            status=status,
            target_type=target_type,
            reason=reason,
            page=page,
            page_size=page_size,
        )
        return ReportList(
            items=[ReportRead.model_validate(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_report(
        self, *, report_id: uuid.UUID
    ) -> ReportRead:
        report = await self._reports.get_by_id(report_id)
        if report is None:
            raise NotFoundError("Denúncia não encontrada")
        return ReportRead.model_validate(report)

    async def resolve_report(
        self,
        *,
        admin_id: uuid.UUID,
        report_id: uuid.UUID,
        payload: ResolveRequest,
    ) -> ReportRead:
        report = await self._reports.get_by_id(report_id)
        if report is None:
            raise NotFoundError("Denúncia não encontrada")
        if report.status != "pending":
            raise ReportNotPending()

        report.status = payload.status
        report.resolved_by = admin_id
        report.resolved_at = datetime.now(UTC)
        report.resolution_note = payload.resolution_note
        await self._session.flush()

        # Notificar reporter
        await self._notifications.emit(
            user_id=report.reporter_id,
            type="report.resolved",
            payload={
                "report_id": str(report.id),
                "status": payload.status,
            },
        )

        await write_audit_log(
            self._session,
            actor_id=admin_id,
            action="resolve",
            entity="report",
            entity_id=report.id,
            diff={"status": payload.status},
        )

        await self._session.commit()
        await self._session.refresh(report)
        return ReportRead.model_validate(report)

    async def hide_review(
        self, *, admin_id: uuid.UUID, review_id: uuid.UUID
    ) -> None:
        review = await self._session.scalar(
            select(Review).where(Review.id == review_id)
        )
        if review is None:
            raise NotFoundError("Review não encontrada")
        if review.hidden_at is not None:
            raise ReviewAlreadyHidden()

        review.hidden_at = datetime.now(UTC)
        review.hidden_by = admin_id
        await self._session.flush()

        # Notificar autor da review
        await self._notifications.emit(
            user_id=review.reviewer_id,
            type="review.hidden",
            payload={"review_id": str(review.id), "contract_id": str(review.contract_id)},
        )

        await write_audit_log(
            self._session,
            actor_id=admin_id,
            action="hide",
            entity="review",
            entity_id=review.id,
        )

        await self._session.commit()

    async def unhide_review(
        self, *, admin_id: uuid.UUID, review_id: uuid.UUID
    ) -> None:
        review = await self._session.scalar(
            select(Review).where(Review.id == review_id)
        )
        if review is None:
            raise NotFoundError("Review não encontrada")
        if review.hidden_at is None:
            raise ReviewNotHidden()

        review.hidden_at = None
        review.hidden_by = None
        await self._session.flush()

        # Notificar autor
        await self._notifications.emit(
            user_id=review.reviewer_id,
            type="review.unhidden",
            payload={"review_id": str(review.id)},
        )

        await write_audit_log(
            self._session,
            actor_id=admin_id,
            action="unhide",
            entity="review",
            entity_id=review.id,
        )

        await self._session.commit()
