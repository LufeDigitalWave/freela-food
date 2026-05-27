"""Fixtures globais de teste."""

import asyncio
import sys
from collections.abc import AsyncIterator

import pytest

# asyncpg requer SelectorEventLoop no Windows (ProactorEventLoop quebra em testes).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Cliente HTTPX async com transporte ASGI direto pra `app`."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
