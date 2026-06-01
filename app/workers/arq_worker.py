"""ARQ WorkerSettings — cron jobs + setup do worker."""

from typing import Any, ClassVar

from arq.connections import RedisSettings
from arq.cron import cron

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.workers.tasks import advance_contract_lifecycle, purge_inactive_users


async def startup(_ctx: dict[str, Any]) -> None:
    configure_logging()
    get_logger("arq.worker").info("worker.startup")


async def shutdown(_ctx: dict[str, Any]) -> None:
    get_logger("arq.worker").info("worker.shutdown")


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


class WorkerSettings:
    """Carregado por `arq app.workers.arq_worker.WorkerSettings`."""

    functions: ClassVar[list[Any]] = [
        purge_inactive_users,
        advance_contract_lifecycle,
    ]
    cron_jobs: ClassVar[list[Any]] = [
        # 02:00 UTC diário
        cron(purge_inactive_users, hour={2}, minute={0}),  # type: ignore[arg-type]
        # a cada 5min
        cron(
            advance_contract_lifecycle,  # type: ignore[arg-type]
            minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55},
        ),
    ]
    redis_settings = _redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 300  # purge pode demorar se muitos users
    max_jobs = 10
