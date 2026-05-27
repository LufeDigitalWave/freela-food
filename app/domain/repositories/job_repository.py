"""Repository de JobPosting com busca por proximidade via PostGIS."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.job_posting import JobPosting


def latlng_to_wkb(latitude: float, longitude: float) -> WKBElement:
    """Lat/lng (float) -> WKBElement geography(Point, 4326). PostGIS usa (x=lng, y=lat)."""
    return from_shape(Point(longitude, latitude), srid=4326)


def wkb_to_latlng(wkb: WKBElement) -> tuple[float, float]:
    """WKBElement -> (lat, lng) floats."""
    point = to_shape(wkb)
    return (float(point.y), float(point.x))


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        establishment_id: uuid.UUID,
        skill_category_id: uuid.UUID,
        title: str,
        description: str | None,
        latitude: float,
        longitude: float,
        address_line: str | None,
        neighborhood: str | None,
        city: str | None,
        state: str | None,
        cep: str | None,
        start_at: datetime,
        end_at: datetime,
        hourly_rate: Decimal | None,
        total_pay: Decimal | None,
        status: str = "open",
    ) -> JobPosting:
        job = JobPosting(
            establishment_id=establishment_id,
            skill_category_id=skill_category_id,
            title=title,
            description=description,
            location=latlng_to_wkb(latitude, longitude),
            address_line=address_line,
            neighborhood=neighborhood,
            city=city,
            state=state,
            cep=cep,
            start_at=start_at,
            end_at=end_at,
            hourly_rate=hourly_rate,
            total_pay=total_pay,
            status=status,
        )
        self._session.add(job)
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> JobPosting | None:
        result = await self._session.execute(
            select(JobPosting).where(
                JobPosting.id == job_id,
                JobPosting.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def update(self, job: JobPosting, **fields: object) -> JobPosting:
        for key, value in fields.items():
            if value is None:
                continue
            if key == "location":
                job.location = value  # type: ignore[assignment]
            else:
                setattr(job, key, value)
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def soft_delete(self, job: JobPosting) -> None:
        await self._session.execute(
            update(JobPosting)
            .where(JobPosting.id == job.id)
            .values(deleted_at=datetime.now(UTC))
        )
        await self._session.flush()

    async def list_owned(
        self, establishment_id: uuid.UUID, *, page: int, page_size: int
    ) -> tuple[list[JobPosting], int]:
        base = select(JobPosting).where(
            JobPosting.establishment_id == establishment_id,
            JobPosting.deleted_at.is_(None),
        )
        total = await self._session.scalar(
            select(func.count()).select_from(base.subquery())
        )
        result = await self._session.execute(
            base.order_by(JobPosting.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)

    async def search_by_proximity(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_m: float,
        skill_category_id: uuid.UUID | None,
        status_filter: str | None,
        start_after: datetime | None,
        page: int,
        page_size: int,
    ) -> tuple[list[tuple[JobPosting, float]], int]:
        point_expr = func.ST_SetSRID(
            func.ST_MakePoint(longitude, latitude), 4326
        ).cast(JobPosting.location.type)

        conditions = [
            JobPosting.deleted_at.is_(None),
            func.ST_DWithin(JobPosting.location, point_expr, radius_m),
        ]
        if skill_category_id is not None:
            conditions.append(JobPosting.skill_category_id == skill_category_id)
        if status_filter is not None:
            conditions.append(JobPosting.status == status_filter)
        if start_after is not None:
            conditions.append(JobPosting.start_at >= start_after)

        distance_col = func.ST_Distance(JobPosting.location, point_expr).label("distance_m")

        base = select(JobPosting, distance_col).where(*conditions)

        total = await self._session.scalar(
            select(func.count()).select_from(
                select(JobPosting.id).where(*conditions).subquery()
            )
        )

        result = await self._session.execute(
            base.order_by(distance_col.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows: list[tuple[JobPosting, float]] = [
            (row[0], float(row[1])) for row in result.all()
        ]
        return rows, int(total or 0)
