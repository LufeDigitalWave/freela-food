"""Service de Profile — orquestra repos, audit, storage."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, PermissionDenied
from app.domain.models.establishment_profile import EstablishmentProfile
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.repositories.profile_repository import ProfileRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.schemas.profile import (
    EstablishmentProfileCreate,
    EstablishmentProfileRead,
    EstablishmentProfileUpdate,
    FreelancerProfileCreate,
    FreelancerProfileRead,
    FreelancerProfileUpdate,
)
from app.utils.audit import write_audit_log


def _freelancer_to_read(p: FreelancerProfile) -> FreelancerProfileRead:
    return FreelancerProfileRead(
        user_id=p.user_id,
        display_name=p.display_name,
        bio=p.bio,
        phone=p.phone,
        avatar_url=p.avatar_url,
        has_cpf=p.cpf_encrypted is not None,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _establishment_to_read(p: EstablishmentProfile) -> EstablishmentProfileRead:
    return EstablishmentProfileRead(
        user_id=p.user_id,
        business_name=p.business_name,
        address_line=p.address_line,
        neighborhood=p.neighborhood,
        city=p.city,
        state=p.state,
        cep=p.cep,
        phone=p.phone,
        avatar_url=p.avatar_url,
        has_cnpj=p.cnpj_encrypted is not None,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._profile_repo = ProfileRepository(session)
        self._user_repo = UserRepository(session)

    # ── Freelancer ────────────────────────────────────────────────────────────

    async def create_freelancer(
        self, user_id: uuid.UUID, payload: FreelancerProfileCreate
    ) -> FreelancerProfileRead:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        if user.role != "freelancer":
            raise PermissionDenied("Apenas freelancers podem criar este perfil")

        existing = await self._profile_repo.get_freelancer(user_id)
        if existing is not None:
            raise ConflictError("Perfil de freelancer já existe")

        profile = await self._profile_repo.create_freelancer(
            user_id=user_id,
            display_name=payload.display_name,
            bio=payload.bio,
            phone=payload.phone,
            cpf=payload.cpf,
        )
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="create",
            entity="freelancer_profile",
            entity_id=user_id,
            diff={
                "display_name": payload.display_name,
                "has_phone": payload.phone is not None,
                "has_cpf": payload.cpf is not None,
            },
        )
        await self._session.commit()
        return _freelancer_to_read(profile)

    async def update_freelancer(
        self, user_id: uuid.UUID, payload: FreelancerProfileUpdate
    ) -> FreelancerProfileRead:
        profile = await self._profile_repo.get_freelancer(user_id)
        if profile is None:
            raise NotFoundError("Perfil de freelancer não encontrado")

        changed = dict(payload.model_dump(exclude_unset=True).items())
        profile = await self._profile_repo.update_freelancer(
            profile,
            display_name=payload.display_name,
            bio=payload.bio,
            phone=payload.phone,
            cpf=payload.cpf,
        )
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="update",
            entity="freelancer_profile",
            entity_id=user_id,
            diff={k: (v if k != "cpf" else "<changed>") for k, v in changed.items()},
        )
        await self._session.commit()
        return _freelancer_to_read(profile)

    async def get_freelancer(self, user_id: uuid.UUID) -> FreelancerProfileRead | None:
        profile = await self._profile_repo.get_freelancer(user_id)
        return _freelancer_to_read(profile) if profile is not None else None

    # ── Establishment ─────────────────────────────────────────────────────────

    async def create_establishment(
        self, user_id: uuid.UUID, payload: EstablishmentProfileCreate
    ) -> EstablishmentProfileRead:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        if user.role != "establishment":
            raise PermissionDenied("Apenas estabelecimentos podem criar este perfil")

        existing = await self._profile_repo.get_establishment(user_id)
        if existing is not None:
            raise ConflictError("Perfil de estabelecimento já existe")

        profile = await self._profile_repo.create_establishment(
            user_id=user_id,
            business_name=payload.business_name,
            address_line=payload.address_line,
            neighborhood=payload.neighborhood,
            city=payload.city,
            state=payload.state,
            cep=payload.cep,
            phone=payload.phone,
            cnpj=payload.cnpj,
        )
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="create",
            entity="establishment_profile",
            entity_id=user_id,
            diff={
                "business_name": payload.business_name,
                "has_cnpj": payload.cnpj is not None,
            },
        )
        await self._session.commit()
        return _establishment_to_read(profile)

    async def update_establishment(
        self, user_id: uuid.UUID, payload: EstablishmentProfileUpdate
    ) -> EstablishmentProfileRead:
        profile = await self._profile_repo.get_establishment(user_id)
        if profile is None:
            raise NotFoundError("Perfil de estabelecimento não encontrado")

        changed = dict(payload.model_dump(exclude_unset=True).items())
        profile = await self._profile_repo.update_establishment(
            profile,
            business_name=payload.business_name,
            address_line=payload.address_line,
            neighborhood=payload.neighborhood,
            city=payload.city,
            state=payload.state,
            cep=payload.cep,
            phone=payload.phone,
            cnpj=payload.cnpj,
        )
        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="update",
            entity="establishment_profile",
            entity_id=user_id,
            diff={k: (v if k != "cnpj" else "<changed>") for k, v in changed.items()},
        )
        await self._session.commit()
        return _establishment_to_read(profile)

    async def get_establishment(
        self, user_id: uuid.UUID
    ) -> EstablishmentProfileRead | None:
        profile = await self._profile_repo.get_establishment(user_id)
        return _establishment_to_read(profile) if profile is not None else None

    # ── Avatar ────────────────────────────────────────────────────────────────

    async def set_avatar_url(self, user_id: uuid.UUID, url: str) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")

        if user.role == "freelancer":
            f_profile = await self._profile_repo.get_freelancer(user_id)
            if f_profile is None:
                raise NotFoundError("Crie o perfil antes do avatar")
            await self._profile_repo.update_freelancer(f_profile, avatar_url=url)
        elif user.role == "establishment":
            e_profile = await self._profile_repo.get_establishment(user_id)
            if e_profile is None:
                raise NotFoundError("Crie o perfil antes do avatar")
            await self._profile_repo.update_establishment(e_profile, avatar_url=url)
        else:
            raise PermissionDenied("Admin não tem perfil")

        await write_audit_log(
            self._session,
            actor_id=user_id,
            action="update",
            entity=f"{user.role}_profile",
            entity_id=user_id,
            diff={"avatar_url": url},
        )
        await self._session.commit()
