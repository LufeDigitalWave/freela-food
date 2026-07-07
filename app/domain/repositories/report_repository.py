"""Repository de Report (Sprint 8)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.report import Report


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        reporter_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
        reason: str,
        description: str | None,
    ) -> Report:
        report = Report(
            reporter_id=reporter_id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            description=description,
            created_at=datetime.now(UTC),
        )
        self._session.add(report)
        await self._session.flush()
        await self._session.refresh(report)
        return report

    async def get_by_id(self, report_id: uuid.UUID) -> Report | None:
        result = await self._session.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()

    async def has_pending_duplicate(
        self,
        *,
        reporter_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
    ) -> bool:
        result = await self._session.scalar(
            select(func.count())
            .select_from(Report)
            .where(
                Report.reporter_id == reporter_id,
                Report.target_type == target_type,
                Report.target_id == target_id,
                Report.status == "pending",
            )
        )
        return (result or 0) > 0

    async def list_for_reporter(
        self,
        reporter_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Report], int]:
        base = select(Report).where(Report.reporter_id == reporter_id)
        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(Report.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def list_all(
        self,
        *,
        status: str | None = None,
        target_type: str | None = None,
        reason: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Report], int]:
        base = select(Report)
        if status:
            base = base.where(Report.status == status)
        if target_type:
            base = base.where(Report.target_type == target_type)
        if reason:
            base = base.where(Report.reason == reason)

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(Report.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)
