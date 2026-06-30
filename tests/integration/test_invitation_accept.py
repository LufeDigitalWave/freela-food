"""Aceite de convite (Fluxo B) — contrato + cascade."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.service_contract import ServiceContract
from app.domain.services.invitation_service import InvitationService
from tests.factories import (
    make_establishment,
    make_freelancer,
    make_invitation,
    make_skill_category,
)


async def _setup(
    *,
    start_offset_h: float = 48,
    end_offset_h: float = 52,
    status: str = "pending",
    expires_offset_h: float = 24,
) -> dict:
    suffix = uuid.uuid4().hex[:8]
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        est, _ = await make_establishment(session, email=f"est-{suffix}@test.com")
        fl, _ = await make_freelancer(session, email=f"fl-{suffix}@test.com")
        cat = await make_skill_category(session)
        inv = await make_invitation(
            session,
            establishment_id=est.id,
            freelancer_id=fl.id,
            skill_category_id=cat.id,
            start_at=now + timedelta(hours=start_offset_h),
            end_at=now + timedelta(hours=end_offset_h),
            status=status,
            expires_at=now + timedelta(hours=expires_offset_h),
        )
        await session.commit()
        return {"inv_id": inv.id, "est_id": est.id, "fl_id": fl.id, "cat_id": cat.id}


async def test_accept_creates_contract() -> None:
    ctx = await _setup()
    async with SessionLocal() as session:
        result = await InvitationService(session).accept(
            user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
        )
        assert result.status == "accepted"
    async with SessionLocal() as session:
        contract = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.invitation_id == ctx["inv_id"]
                )
            )
        ).scalar_one()
        assert contract.application_id is None
        assert contract.job_posting_id is None
        assert contract.status == "scheduled"
        assert contract.freelancer_id == ctx["fl_id"]


async def test_accept_copies_terms() -> None:
    ctx = await _setup()
    async with SessionLocal() as session:
        await InvitationService(session).accept(
            user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
        )
    async with SessionLocal() as session:
        contract = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.invitation_id == ctx["inv_id"]
                )
            )
        ).scalar_one()
        assert contract.agreed_hourly_rate is not None


async def test_accept_cascade_declines_overlapping() -> None:
    ctx = await _setup()
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        est2, _ = await make_establishment(
            session, email=f"est2-{uuid.uuid4().hex[:8]}@test.com"
        )
        cat = await make_skill_category(session)
        other = await make_invitation(
            session,
            establishment_id=est2.id,
            freelancer_id=ctx["fl_id"],
            skill_category_id=cat.id,
            start_at=now + timedelta(hours=49),
            end_at=now + timedelta(hours=51),
            status="pending",
            expires_at=now + timedelta(hours=24),
        )
        await session.commit()
        other_id = other.id

    async with SessionLocal() as session:
        await InvitationService(session).accept(
            user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
        )
    async with SessionLocal() as session:
        from app.domain.models.invitation import Invitation

        refreshed = (
            await session.execute(
                select(Invitation).where(Invitation.id == other_id)
            )
        ).scalar_one()
        assert refreshed.status == "declined"


async def test_accept_does_not_touch_nonoverlapping() -> None:
    ctx = await _setup()
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        est2, _ = await make_establishment(
            session, email=f"est2-{uuid.uuid4().hex[:8]}@test.com"
        )
        cat = await make_skill_category(session)
        other = await make_invitation(
            session,
            establishment_id=est2.id,
            freelancer_id=ctx["fl_id"],
            skill_category_id=cat.id,
            start_at=now + timedelta(hours=100),
            end_at=now + timedelta(hours=104),
            status="pending",
            expires_at=now + timedelta(hours=80),
        )
        await session.commit()
        other_id = other.id

    async with SessionLocal() as session:
        await InvitationService(session).accept(
            user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
        )
    async with SessionLocal() as session:
        from app.domain.models.invitation import Invitation

        refreshed = (
            await session.execute(
                select(Invitation).where(Invitation.id == other_id)
            )
        ).scalar_one()
        assert refreshed.status == "pending"


async def test_accept_blocked_by_overlap() -> None:
    """Freelancer já tem contrato sobreposto → FreelancerOverlap."""
    from app.core.exceptions import FreelancerOverlap

    ctx = await _setup()
    async with SessionLocal() as session:
        await InvitationService(session).accept(
            user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
        )
    now = datetime.now(UTC)
    async with SessionLocal() as session:
        est2, _ = await make_establishment(
            session, email=f"est2-{uuid.uuid4().hex[:8]}@test.com"
        )
        cat = await make_skill_category(session)
        inv2 = await make_invitation(
            session,
            establishment_id=est2.id,
            freelancer_id=ctx["fl_id"],
            skill_category_id=cat.id,
            start_at=now + timedelta(hours=49),
            end_at=now + timedelta(hours=51),
            status="pending",
            expires_at=now + timedelta(hours=24),
        )
        await session.commit()
        inv2_id = inv2.id

    async with SessionLocal() as session:
        try:
            await InvitationService(session).accept(
                user_id=ctx["fl_id"], invitation_id=inv2_id
            )
            raise AssertionError("esperava FreelancerOverlap")
        except FreelancerOverlap:
            pass


async def test_accept_blocked_when_expired() -> None:
    from app.core.exceptions import InvitationExpired

    ctx = await _setup(expires_offset_h=-1)
    async with SessionLocal() as session:
        try:
            await InvitationService(session).accept(
                user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
            )
            raise AssertionError("esperava InvitationExpired")
        except InvitationExpired:
            pass


async def test_accept_blocked_when_not_pending() -> None:
    from app.core.exceptions import InvitationNotPending

    ctx = await _setup(status="declined")
    async with SessionLocal() as session:
        try:
            await InvitationService(session).accept(
                user_id=ctx["fl_id"], invitation_id=ctx["inv_id"]
            )
            raise AssertionError("esperava InvitationNotPending")
        except InvitationNotPending:
            pass


async def test_accept_forbidden_for_non_invitee() -> None:
    from app.core.exceptions import PermissionDenied

    ctx = await _setup()
    async with SessionLocal() as session:
        try:
            await InvitationService(session).accept(
                user_id=ctx["est_id"], invitation_id=ctx["inv_id"]
            )
            raise AssertionError("esperava PermissionDenied")
        except PermissionDenied:
            pass
