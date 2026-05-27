"""structlog setup com filtro de PII."""

import logging
import sys
from typing import Any, cast

import structlog
from structlog.typing import EventDict

from app.core.config import get_settings

# Chaves cujo valor é redigido em qualquer log (PII / segredos)
_REDACTED_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "cpf",
        "rg",
        "email",
        "phone",
        "phone_number",
        "telefone",
        "token",
        "access_token",
        "refresh_token",
        "jwt_secret",
        "authorization",
    }
)


def _redact_pii(_logger: Any, _method_name: str, event_dict: EventDict) -> EventDict:
    for key in list(event_dict.keys()):
        if key.lower() in _REDACTED_KEYS:
            event_dict[key] = "<REDACTED>"
    return event_dict


def configure_logging() -> None:
    """Chame uma vez no startup (app.main)."""
    settings = get_settings()
    level = getattr(logging, settings.log_level)

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    renderer: Any = (
        structlog.dev.ConsoleRenderer(colors=True)
        if settings.env == "dev"
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_pii,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
