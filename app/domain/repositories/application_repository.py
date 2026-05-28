"""Repository de Application. Outros métodos serão adicionados em tasks subsequentes."""

import uuid

from sqlalchemy import select
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
