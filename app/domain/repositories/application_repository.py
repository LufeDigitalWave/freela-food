"""Repository de Application. Outros métodos serão adicionados em tasks subsequentes."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.application import Application


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        job_posting_id: uuid.UUID,
        freelancer_id: uuid.UUID,
        message: str | None,
    ) -> Application:
        app_ = Application(
            job_posting_id=job_posting_id,
            freelancer_id=freelancer_id,
            message=message,
            status="pending",
        )
        self._session.add(app_)
        await self._session.flush()
        await self._session.refresh(app_)
        return app_

    async def get_by_id(self, app_id: uuid.UUID) -> Application | None:
        result = await self._session.execute(
            select(Application).where(Application.id == app_id)
        )
        return result.scalar_one_or_none()

    async def list_for_job(
        self,
        *,
        job_posting_id: uuid.UUID,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Application], int]:
        base = select(Application).where(
            Application.job_posting_id == job_posting_id
        )
        if status_filter is not None:
            base = base.where(Application.status == status_filter)

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(Application.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def list_for_freelancer(
        self,
        *,
        freelancer_id: uuid.UUID,
        status_filter: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Application], int]:
        base = select(Application).where(Application.freelancer_id == freelancer_id)
        if status_filter is not None:
            base = base.where(Application.status == status_filter)

        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(Application.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)
