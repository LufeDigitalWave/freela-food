"""Sentry initialization — error tracking and performance monitoring.

Apenas inicializa se SENTRY_DSN estiver presente no .env e sentry_sdk instalado.
Filtra eventos PII automaticamente.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.config import Settings


def init_sentry(settings: Settings) -> None:
    """Inicializa Sentry se DSN foi configurado.

    Integra com: FastAPI, SQLAlchemy, Redis, logging estruturado.
    Filtra PII automaticamente.
    Falha gracefully se sentry_sdk não estiver instalado.
    """
    if not settings.sentry_dsn:
        logging.info("Sentry DSN não configurado; error tracking desabilitado")
        return

    try:
        import sentry_sdk  # type: ignore[import-not-found]
        from sentry_sdk.integrations.fastapi import (  # type: ignore[import-not-found]
            FastApiIntegration,
        )
        from sentry_sdk.integrations.logging import (  # type: ignore[import-not-found]
            LoggingIntegration,
        )
        from sentry_sdk.integrations.sqlalchemy import (  # type: ignore[import-not-found]
            SqlalchemyIntegration,
        )
    except ImportError:
        logging.warning("sentry_sdk não instalado; 'uv add sentry-sdk[fastapi]' para habilitar")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        traces_sample_rate=0.1 if settings.env == "prod" else 1.0,
        profiles_sample_rate=0.1 if settings.env == "prod" else 0.0,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
        ],
        before_send=_filter_pii,
    )
    logging.info(f"Sentry inicializado (env={settings.env})")


def _filter_pii(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Remove PII de eventos Sentry.

    Filtra emails, CPF, RG, passwords de breadcrumbs e stack frames.
    """
    _sensitive_keys = {"password", "token", "secret", "key", "cpf", "rg", "email"}

    # Remover vars sensíveis de stack frames
    if "exception" in event:
        for exc in event.get("exception", {}).get("values", []):
            stacktrace = exc.get("stacktrace")
            if stacktrace:
                for frame in stacktrace.get("frames", []):
                    if "vars" in frame:
                        frame["vars"] = {
                            k: "<redacted>" if any(s in k.lower() for s in _sensitive_keys) else v
                            for k, v in frame["vars"].items()
                        }

    # Remover de breadcrumbs
    for breadcrumb in event.get("breadcrumbs", {}).get("values", []):
        if breadcrumb.get("data"):
            breadcrumb["data"] = {
                k: "<redacted>" if any(s in k.lower() for s in _sensitive_keys) else v
                for k, v in breadcrumb["data"].items()
            }

    return event
