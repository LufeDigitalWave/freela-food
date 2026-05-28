"""Helpers pra criar entidades de teste (User, profiles, jobs, applications, contracts).

Cada factory recebe `session: AsyncSession` e retorna o model criado, já com
flush() executado. Não commita — assume controle transacional do test.
"""

from __future__ import annotations

import uuid  # noqa: F401  (usado pelas factories nas próximas tasks)
from datetime import UTC, datetime, timedelta  # noqa: F401
from decimal import Decimal  # noqa: F401

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401

# Factories serão preenchidas conforme as tasks adicionam os models.
