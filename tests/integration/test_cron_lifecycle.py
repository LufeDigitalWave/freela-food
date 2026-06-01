"""Testes do cron advance_contract_lifecycle."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.job_posting import JobPosting
from app.domain.models.service_contract import ServiceContract
from app.workers.tasks import advance_contract_lifecycle
from tests.factories import (
    make_application,
    make_contract,
    make_establishment,
    make_freelancer,
    make_job,
    make_skill_category,
)


async def _setup_contract(
    *,
    start_offset_hours: float,
    end_offset_hours: float,
    status: str = "scheduled",
) -> dict[str, Any]:
    # Sufixo único por execução: o DB da VPS é compartilhado, emails fixos
    # colidiriam no unique constraint de users.email entre runs.
    suffix = uuid.uuid4().hex[:8]
    now = datetime.now(UTC)
    start = now + timedelta(hours=start_offset_hours)
    end = now + timedelta(hours=end_offset_hours)
    async with SessionLocal() as session:
        est, _ = await make_establishment(
            session, email=f"cron-est-{suffix}@test.com"
        )
        fl, _ = await make_freelancer(session, email=f"cron-fl-{suffix}@test.com")
        cat = await make_skill_category(session)
        job = await make_job(
            session,
            establishment_id=est.id,
            skill_category_id=cat.id,
            status="filled",
            start_at=start,
            end_at=end,
        )
        a = await make_application(
            session,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            status="accepted",
        )
        c = await make_contract(
            session,
            application_id=a.id,
            job_posting_id=job.id,
            freelancer_id=fl.id,
            establishment_id=est.id,
            start_at=start,
            end_at=end,
            status=status,
        )
        await session.commit()
        return {
            "contract_id": c.id,
            "job_id": job.id,
            "fl_id": fl.id,
        }


async def test_scheduled_to_in_progress() -> None:
    """Contrato com start_at no passado e end_at no futuro → in_progress."""
    ctx = await _setup_contract(start_offset_hours=-1, end_offset_hours=3)
    res = await advance_contract_lifecycle({})
    assert res["started"] >= 1
    async with SessionLocal() as session:
        c = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.id == ctx["contract_id"]
                )
            )
        ).scalar_one()
        assert c.status == "in_progress"


async def test_in_progress_to_completed() -> None:
    ctx = await _setup_contract(
        start_offset_hours=-5, end_offset_hours=-1, status="in_progress"
    )
    res = await advance_contract_lifecycle({})
    assert res["completed"] >= 1
    async with SessionLocal() as session:
        c = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.id == ctx["contract_id"]
                )
            )
        ).scalar_one()
        assert c.status == "completed"


async def test_scheduled_skips_directly_to_completed_when_recovery() -> None:
    """Cron parou; scheduled com end_at já passado → vai direto pra completed."""
    ctx = await _setup_contract(start_offset_hours=-10, end_offset_hours=-5)
    await advance_contract_lifecycle({})
    async with SessionLocal() as session:
        c = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.id == ctx["contract_id"]
                )
            )
        ).scalar_one()
        assert c.status == "completed"


async def test_completed_increments_counter() -> None:
    ctx = await _setup_contract(
        start_offset_hours=-5, end_offset_hours=-1, status="in_progress"
    )
    await advance_contract_lifecycle({})
    async with SessionLocal() as session:
        prof = (
            await session.execute(
                select(FreelancerProfile).where(
                    FreelancerProfile.user_id == ctx["fl_id"]
                )
            )
        ).scalar_one()
        assert prof.completed_contracts_count == 1


async def test_completed_marks_job_completed() -> None:
    ctx = await _setup_contract(
        start_offset_hours=-5, end_offset_hours=-1, status="in_progress"
    )
    await advance_contract_lifecycle({})
    async with SessionLocal() as session:
        job = (
            await session.execute(
                select(JobPosting).where(JobPosting.id == ctx["job_id"])
            )
        ).scalar_one()
        assert job.status == "completed"


async def test_idempotent_run_twice() -> None:
    """2 execuções seguidas — segunda não duplica side-effects."""
    ctx = await _setup_contract(
        start_offset_hours=-5, end_offset_hours=-1, status="in_progress"
    )
    await advance_contract_lifecycle({})
    await advance_contract_lifecycle({})
    # nosso contrato já foi completado no 1º run; 2º não o conta de novo
    async with SessionLocal() as session:
        prof = (
            await session.execute(
                select(FreelancerProfile).where(
                    FreelancerProfile.user_id == ctx["fl_id"]
                )
            )
        ).scalar_one()
        assert prof.completed_contracts_count == 1
        c = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.id == ctx["contract_id"]
                )
            )
        ).scalar_one()
        assert c.status == "completed"


async def test_cancelled_ignored() -> None:
    """Contrato cancelled NÃO é tocado pelo cron."""
    ctx = await _setup_contract(
        start_offset_hours=-5, end_offset_hours=-1, status="scheduled"
    )
    # Marca como cancelled manualmente antes do cron
    async with SessionLocal() as session:
        c = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.id == ctx["contract_id"]
                )
            )
        ).scalar_one()
        c.status = "cancelled"
        c.cancelled_by = "establishment"
        c.cancelled_at = datetime.now(UTC)
        await session.commit()

    await advance_contract_lifecycle({})

    async with SessionLocal() as session:
        c2 = (
            await session.execute(
                select(ServiceContract).where(
                    ServiceContract.id == ctx["contract_id"]
                )
            )
        ).scalar_one()
        assert c2.status == "cancelled"
