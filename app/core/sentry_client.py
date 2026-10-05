"""Sentry initialization — error tracking and performance monitoring.

Apenas inicializa se SENTRY_DSN estiver presente no .env e sentry_sdk instalado.
Filtra eventos PII automaticamente (LGPD): stack frames, breadcrumbs, request e user.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.config import Settings

_REDACTED = "<redacted>"

# Casam como substring do nome da chave (ex.: "access_token", "senha_hash", "Authorization").
_SENSITIVE_SUBSTRINGS = ("password", "senha", "token", "secret", "authorization", "cookie")
# Casam só como palavra inteira da chave, para não apagar "organization" ou "monkey".
_SENSITIVE_WORDS = {"key", "cpf", "cnpj", "rg", "email", "phone", "telefone", "celular"}

_EMAIL_RE = re.compile(r"[\w.+-]+(?:@|%40)[\w-]+(?:\.[\w-]+)+")
_CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")


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
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except ImportError:
        logging.warning("sentry_sdk não instalado; 'uv add sentry-sdk[fastapi]' para habilitar")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        send_default_pii=False,
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


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    if any(s in lowered for s in _SENSITIVE_SUBSTRINGS):
        return True
    return any(word in _SENSITIVE_WORDS for word in re.split(r"[^a-z0-9]+", lowered))


def _redact_text(text: str) -> str:
    return _CPF_RE.sub(_REDACTED, _EMAIL_RE.sub(_REDACTED, text))


def _scrub(value: Any) -> Any:
    """Redige recursivamente chaves sensíveis e e-mails/CPFs em texto livre."""
    if isinstance(value, dict):
        return {
            k: _REDACTED if isinstance(k, str) and _is_sensitive_key(k) else _scrub(v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def _filter_pii(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Remove PII de eventos Sentry.

    Cobre vars de stack frames, breadcrumbs, request (body, query, headers, cookies)
    e user (mantém só o id).
    """
    for exc in event.get("exception", {}).get("values", []):
        for frame in (exc.get("stacktrace") or {}).get("frames", []):
            if "vars" in frame:
                frame["vars"] = _scrub(frame["vars"])

    for breadcrumb in event.get("breadcrumbs", {}).get("values", []):
        if breadcrumb.get("data"):
            breadcrumb["data"] = _scrub(breadcrumb["data"])
        if isinstance(breadcrumb.get("message"), str):
            breadcrumb["message"] = _redact_text(breadcrumb["message"])

    if "request" in event:
        event["request"] = _scrub(event["request"])

    if "user" in event:
        user_id = event["user"].get("id")
        event["user"] = {"id": user_id} if user_id is not None else {}

    return event
