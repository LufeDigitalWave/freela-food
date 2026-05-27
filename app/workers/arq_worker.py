"""ARQ WorkerSettings — skeleton sem tasks. Tasks reais entram em Sprints futuros."""

from typing import Any, ClassVar

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger


async def startup(_ctx: dict[str, Any]) -> None:
    configure_logging()
    get_logger("arq.worker").info("worker.startup")


async def shutdown(_ctx: dict[str, Any]) -> None:
    get_logger("arq.worker").info("worker.shutdown")


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


class WorkerSettings:
    """Carregado por `arq app.workers.arq_worker.WorkerSettings`."""

    functions: ClassVar[list[Any]] = []  # tasks entram aqui
    redis_settings = _redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = 60
    max_jobs = 10
