"""Helper de audit log — escreve em audit_log via SQLAlchemy.

IP e User-Agent vêm de ContextVars preenchidas por middleware HTTP.
Em jobs ARQ (sem request), ficam None.
"""

import uuid
from contextvars import ContextVar
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.audit_log import AuditLog

request_ip: ContextVar[str | None] = ContextVar("request_ip", default=None)
request_ua: ContextVar[str | None] = ContextVar("request_ua", default=None)


async def write_audit_log(
    session: AsyncSession,
    *,
    actor_id: uuid.UUID | None,
    action: str,
    entity: str,
    entity_id: uuid.UUID | None = None,
    diff: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            diff=diff or {},
            ip=request_ip.get(),
            user_agent=request_ua.get(),
        )
    )
    await session.flush()
