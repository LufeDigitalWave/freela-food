"""Service de JobPosting — orquestra repo, profile, audit."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDenied,
    ValidationError,
)
from app.domain.models.job_posting import JobPosting
from app.domain.repositories.job_repository import (
    JobRepository,
    wkb_to_latlng,
)
from app.domain.repositories.profile_repository import ProfileRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.schemas.job import (
    JobPostingCreate,
    JobPostingRead,
    JobPostingReadWithDistance,
    JobPostingUpdate,
    JobSearchResponse,
)
from app.utils.audit import write_audit_log


def _to_read(job: JobPosting) -> JobPostingRead:
    lat, lng = wkb_to_latlng(job.location)
    return JobPostingRead(
        id=job.id,
        establishment_id=job.establishment_id,
        skill_category_id=job.skill_category_id,
        title=job.title,
        description=job.description,
        latitude=lat,
        longitude=lng,
        address_line=job.address_line,
        neighborhood=job.neighborhood,
        city=job.city,
        state=job.state,
        cep=job.cep,
        start_at=job.start_at,
        end_at=job.end_at,
        hourly_rate=job.hourly_rate,
        total_pay=job.total_pay,
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _to_read_with_distance(job: JobPosting, distance_m: float) -> JobPostingReadWithDistance:
    read = _to_read(job)
    return JobPostingReadWithDistance(**read.model_dump(), distance_m=distance_m)


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._jobs = JobRepository(session)
        self._users = UserRepository(session)
        self._profiles = ProfileRepository(session)

    async def create(
        self, user_id: uuid.UUID, payload: JobPostingCreate
    ) -> JobPostingRead:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        if user.role != "establishment":
            raise PermissionDenied(
                "Apenas estabelecimentos podem postar vagas"
            )

        # Resolver location: payload OU perfil
        lat = payload.latitude
        lng = payload.longitude
        if lat is None or lng is None:
            profile = await self._profiles.get_establishment(user_id)
            if profile is None or profile.location is None:
                raise ValidationError(
                    "Forneça latitude/longitude ou complete a localização do perfil"
                )
            lat, lng = wkb_to_latlng(profile.location)

        # Mesmo deal pro endereço — herda do perfil se vazio
        profile = await self._profiles.get_establishment(user_id)
        address_line = payload.address_line or (profile.address_line if profile else None)
        neighborhood = payload.neighborhood or (profile.neighborhood if profile else None)
        city = payload.city or (profile.city if profile else None)
        state = payload.state or (profile.state if profile else None)
        cep = payload.cep or (profile.cep if profile else None)

        job = await self._jobs.create(
            establishment_id=user_id,
            skill_category_id=payload.skill_category_id,
            title=payload.title,
            description=payload.description,
            latitude=lat,
            longitude=lng,
            address_line=address_line,
            neighborhood=neighborhood,
            city=city,
            state=state,
            cep=cep,
            start_at=payload.start_at,
            end_at=payload.end_at,
            hourly_rate=payload.hourly_rate,
            total_pay=payload.total_pay,
            status="open",
        )

        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="create",
            entity="job_posting",
            entity_id=job.id,
            diff={"title": payload.title, "skill_category_id": str(payload.skill_category_id)},
        )
        await self._session.commit()
        return _to_read(job)

    async def get_by_id(self, job_id: uuid.UUID) -> JobPostingRead:
        job = await self._jobs.get_by_id(job_id)
        if job is None:
            raise NotFoundError("Vaga não encontrada")
        return _to_read(job)

    async def update(
        self, user_id: uuid.UUID, job_id: uuid.UUID, payload: JobPostingUpdate
    ) -> JobPostingRead:
        job = await self._jobs.get_by_id(job_id)
        if job is None:
            raise NotFoundError("Vaga não encontrada")
        if job.establishment_id != user_id:
            raise PermissionDenied("Você não é dono dessa vaga")

        changes = payload.model_dump(exclude_unset=True, exclude_none=True)
        update_fields: dict[str, object] = {}
        for key, value in changes.items():
            if key in {"latitude", "longitude"}:
                continue
            update_fields[key] = value

        if payload.latitude is not None and payload.longitude is not None:
            from app.domain.repositories.job_repository import latlng_to_wkb

            update_fields["location"] = latlng_to_wkb(payload.latitude, payload.longitude)

        job = await self._jobs.update(job, **update_fields)
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="update",
            entity="job_posting",
            entity_id=job.id,
            diff={k: str(v) for k, v in changes.items() if k != "description"},
        )
        await self._session.commit()
        return _to_read(job)

    async def cancel(self, user_id: uuid.UUID, job_id: uuid.UUID) -> JobPostingRead:
        job = await self._jobs.get_by_id(job_id)
        if job is None:
            raise NotFoundError("Vaga não encontrada")
        if job.establishment_id != user_id:
            raise PermissionDenied("Você não é dono dessa vaga")
        if job.status in {"cancelled", "completed"}:
            raise ConflictError(f"Vaga já está {job.status}")

        job = await self._jobs.update(job, status="cancelled")
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="cancel",
            entity="job_posting",
            entity_id=job.id,
        )
        await self._session.commit()
        return _to_read(job)

    async def soft_delete(self, user_id: uuid.UUID, job_id: uuid.UUID) -> None:
        job = await self._jobs.get_by_id(job_id)
        if job is None:
            raise NotFoundError("Vaga não encontrada")
        if job.establishment_id != user_id:
            raise PermissionDenied("Você não é dono dessa vaga")

        await self._jobs.soft_delete(job)
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="delete",
            entity="job_posting",
            entity_id=job.id,
        )
        await self._session.commit()

    async def list_owned(
        self, user_id: uuid.UUID, *, page: int, page_size: int
    ) -> tuple[list[JobPostingRead], int]:
        jobs, total = await self._jobs.list_owned(user_id, page=page, page_size=page_size)
        return [_to_read(j) for j in jobs], total

    async def search(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_km: float,
        skill_category_id: uuid.UUID | None,
        only_open: bool,
        future_only: bool,
        page: int,
        page_size: int,
    ) -> JobSearchResponse:
        status_filter = "open" if only_open else None
        start_after = datetime.now(UTC) if future_only else None

        rows, total = await self._jobs.search_by_proximity(
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_km * 1000.0,
            skill_category_id=skill_category_id,
            status_filter=status_filter,
            start_after=start_after,
            page=page,
            page_size=page_size,
        )
        return JobSearchResponse(
            items=[_to_read_with_distance(j, d) for j, d in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
