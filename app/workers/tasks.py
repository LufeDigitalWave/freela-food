"""ARQ tasks (cron jobs)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.core.storage import delete_avatar
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
