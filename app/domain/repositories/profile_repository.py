"""Repository de Profile (freelancer + estabelecimento) com pgcrypto."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.domain.models.establishment_profile import EstablishmentProfile
from app.domain.models.freelancer_profile import FreelancerProfile


class ProfileRepository:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()

    @property
    def _enc_key(self) -> str:
        return self._settings.db_encryption_key.get_secret_value()

    # ── Freelancer ────────────────────────────────────────────────────────────

    async def get_freelancer(self, user_id: uuid.UUID) -> FreelancerProfile | None:
        result = await self._session.execute(
            select(FreelancerProfile).where(
                FreelancerProfile.user_id == user_id,
                FreelancerProfile.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create_freelancer(
        self,
        *,
        user_id: uuid.UUID,
        display_name: str,
        bio: str | None,
        phone: str | None,
        cpf: str | None,
    ) -> FreelancerProfile:
        profile = FreelancerProfile(
            user_id=user_id,
            display_name=display_name,
            bio=bio,
            phone=phone,
            cpf_encrypted=(await self._encrypt(cpf)) if cpf is not None else None,
        )
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def update_freelancer(
        self,
        profile: FreelancerProfile,
        *,
        display_name: str | None = None,
        bio: str | None = None,
        phone: str | None = None,
        cpf: str | None = None,
        avatar_url: str | None = None,
    ) -> FreelancerProfile:
        if display_name is not None:
            profile.display_name = display_name
        if bio is not None:
            profile.bio = bio
        if phone is not None:
            profile.phone = phone
        if cpf is not None:
            profile.cpf_encrypted = await self._encrypt(cpf)
        if avatar_url is not None:
            profile.avatar_url = avatar_url
        await self._session.flush()
        # onupdate=now() marca updated_at como expired — refresh evita lazy reload fora do greenlet
        await self._session.refresh(profile)
        return profile

    async def decrypt_freelancer_cpf(self, profile: FreelancerProfile) -> str | None:
        if profile.cpf_encrypted is None:
            return None
        return await self._decrypt(profile.cpf_encrypted)

    # ── Establishment ─────────────────────────────────────────────────────────

    async def get_establishment(self, user_id: uuid.UUID) -> EstablishmentProfile | None:
        result = await self._session.execute(
            select(EstablishmentProfile).where(
                EstablishmentProfile.user_id == user_id,
                EstablishmentProfile.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create_establishment(
        self,
        *,
        user_id: uuid.UUID,
        business_name: str,
        address_line: str | None,
        neighborhood: str | None,
        city: str | None,
        state: str | None,
        cep: str | None,
        phone: str | None,
        cnpj: str | None,
    ) -> EstablishmentProfile:
        profile = EstablishmentProfile(
            user_id=user_id,
            business_name=business_name,
            address_line=address_line,
            neighborhood=neighborhood,
            city=city,
            state=state,
            cep=cep,
            phone=phone,
            cnpj_encrypted=(await self._encrypt(cnpj)) if cnpj is not None else None,
        )
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def update_establishment(
        self,
        profile: EstablishmentProfile,
        *,
        business_name: str | None = None,
        address_line: str | None = None,
        neighborhood: str | None = None,
        city: str | None = None,
        state: str | None = None,
        cep: str | None = None,
        phone: str | None = None,
        cnpj: str | None = None,
        avatar_url: str | None = None,
    ) -> EstablishmentProfile:
        if business_name is not None:
            profile.business_name = business_name
        if address_line is not None:
            profile.address_line = address_line
        if neighborhood is not None:
            profile.neighborhood = neighborhood
        if city is not None:
            profile.city = city
        if state is not None:
            profile.state = state
        if cep is not None:
            profile.cep = cep
        if phone is not None:
            profile.phone = phone
        if cnpj is not None:
            profile.cnpj_encrypted = await self._encrypt(cnpj)
        if avatar_url is not None:
            profile.avatar_url = avatar_url
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def decrypt_establishment_cnpj(
        self, profile: EstablishmentProfile
    ) -> str | None:
        if profile.cnpj_encrypted is None:
            return None
        return await self._decrypt(profile.cnpj_encrypted)

    # ── pgcrypto helpers ──────────────────────────────────────────────────────

    async def _encrypt(self, plain: str) -> bytes:
        result = await self._session.execute(
            select(func.pgp_sym_encrypt(plain, self._enc_key))
        )
        return result.scalar_one()  # type: ignore[no-any-return]

    async def _decrypt(self, encrypted: bytes) -> str:
        result = await self._session.execute(
            select(func.pgp_sym_decrypt(encrypted, self._enc_key))
        )
        return result.scalar_one()  # type: ignore[no-any-return]
