"""ARQ tasks (cron jobs)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, select, update

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.core.storage import delete_avatar
from app.domain.models.freelancer_profile import FreelancerProfile
from app.domain.models.job_posting import JobPosting
from app.domain.models.service_contract import ServiceContract
from app.domain.models.user import User

_log = get_logger("workers.tasks")


async def purge_inactive_users(_ctx: dict[str, Any]) -> int:
    """Hard-delete users cujo deleted_at é mais velho que delete_grace_period_days.

    CASCADE remove freelancer_profiles / establishment_profiles automaticamente.
    audit_log entries permanecem (actor_id vira NULL via FK SET NULL).
    """
    settings = get_settings()
    cutoff = datetime.now(UTC) - timedelta(days=settings.delete_grace_period_days)

    purged = 0
    async with SessionLocal() as session:
        result = await session.execute(
            select(User.id).where(
                User.deleted_at.is_not(None),
                User.deleted_at < cutoff,
            )
        )
        user_ids = [row[0] for row in result]

        for user_id in user_ids:
            try:
                await delete_avatar(str(user_id))
            except Exception as exc:
                _log.warning("purge.avatar_delete_failed", user_id=str(user_id), error=str(exc))

            await session.execute(delete(User).where(User.id == user_id))
            purged += 1

        await session.commit()

    _log.info("purge_inactive_users.done", count=purged, cutoff=cutoff.isoformat())
    return purged


async def advance_contract_lifecycle(_ctx: dict[str, Any]) -> dict[str, int]:
    """Cron 5min — avança contratos scheduled→in_progress→completed.

    Idempotente. Usa now() do DB (func.now()) para evitar drift entre app e DB.
    Side effects do completed:
      - FreelancerProfile.completed_contracts_count++
      - JobPosting filled → completed
    Contratos cancelled nunca são tocados (filtro de status).
    """
    log = get_logger("arq.contract_lifecycle")
    started = 0
    completed_ids: list[tuple[str, str]] = []
    async with SessionLocal() as session, session.begin():
        # scheduled → in_progress (start_at <= now < end_at)
        r1 = await session.execute(
            update(ServiceContract)
            .where(
                ServiceContract.status == "scheduled",
                ServiceContract.start_at <= func.now(),
                ServiceContract.end_at > func.now(),
            )
            .values(status="in_progress", updated_at=func.now())
            .returning(ServiceContract.id)
        )
        started = len(r1.all())

        # qualquer scheduled/in_progress com end_at <= now → completed
        r2 = await session.execute(
            update(ServiceContract)
            .where(
                ServiceContract.status.in_(["scheduled", "in_progress"]),
                ServiceContract.end_at <= func.now(),
            )
            .values(status="completed", updated_at=func.now())
            .returning(
                ServiceContract.id,
                ServiceContract.freelancer_id,
                ServiceContract.job_posting_id,
            )
        )
        for row in r2.all():
            completed_ids.append((str(row[0]), str(row[2])))
            # FreelancerProfile counter
            await session.execute(
                update(FreelancerProfile)
                .where(FreelancerProfile.user_id == row[1])
                .values(completed_contracts_count=(FreelancerProfile.completed_contracts_count + 1))
            )
            # Job filled → completed
            await session.execute(
                update(JobPosting)
                .where(
                    JobPosting.id == row[2],
                    JobPosting.status == "filled",
                )
                .values(status="completed", updated_at=func.now())
            )

    log.info("contract_lifecycle.tick", started=started, completed=len(completed_ids))
    return {"started": started, "completed": len(completed_ids)}
