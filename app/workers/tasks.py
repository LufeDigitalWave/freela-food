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
from app.domain.models.notification import Notification
from app.domain.models.review import Review
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
    now = datetime.now(UTC)
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
            .returning(
                ServiceContract.id,
                ServiceContract.freelancer_id,
                ServiceContract.establishment_id,
            )
        )
        started_rows = r1.all()
        started = len(started_rows)

        # Notificar ambas partes: contract.started
        for row in started_rows:
            for uid in (row[1], row[2]):
                session.add(
                    Notification(
                        user_id=uid,
                        type="contract.started",
                        payload={"contract_id": str(row[0])},
                        created_at=now,
                    )
                )

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
                ServiceContract.establishment_id,
            )
        )
        for row in r2.all():  # type: ignore[assignment]
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
            # Notificar ambas partes: contract.completed
            for uid in (row[1], row[3]):
                session.add(
                    Notification(
                        user_id=uid,
                        type="contract.completed",
                        payload={"contract_id": str(row[0])},
                        created_at=now,
                    )
                )

    log.info("contract_lifecycle.tick", started=started, completed=len(completed_ids))
    return {"started": started, "completed": len(completed_ids)}


async def reveal_reviews(_ctx: dict[str, Any]) -> dict[str, int]:
    """Cron 5min — revela reviews órfãs após 7 dias (anti-retaliação).

    Idempotente. Marca visible_at = now() em reviews cuja outra parte nunca
    avaliou dentro de 7 dias. Emite notificação review.revealed ao autor.
    """
    log = get_logger("arq.review_lifecycle")
    revealed = 0
    cutoff = datetime.now(UTC) - timedelta(days=7)

    async with SessionLocal() as session, session.begin():
        result = await session.execute(
            select(Review).where(
                Review.visible_at.is_(None),
                Review.created_at <= cutoff,
            )
        )
        orphan_reviews = list(result.scalars().all())

        now = datetime.now(UTC)
        for review in orphan_reviews:
            review.visible_at = now
            # Notificar autor que review está pública
            session.add(
                Notification(
                    user_id=review.reviewer_id,
                    type="review.revealed",
                    payload={
                        "contract_id": str(review.contract_id),
                        "review_id": str(review.id),
                    },
                    created_at=now,
                )
            )
            revealed += 1

    log.info("review_lifecycle.tick", revealed=revealed)
    return {"revealed": revealed}
