"""Testes unitários para rate_limit.py (X-Forwarded-For)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.rate_limit import check_rate_limit


def _mock_request(*, ip: str = "1.2.3.4", forwarded_for: str | None = None) -> MagicMock:
    """Cria mock de Request com client.host e headers."""
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = ip
    headers: dict[str, str] = {}
    if forwarded_for:
        headers["x-forwarded-for"] = forwarded_for
    request.headers = MagicMock()
    request.headers.get = lambda key, default=None: headers.get(key, default)
    return request


def _make_redis_mock(count: int = 1) -> MagicMock:
    """Redis mock — pipeline() é sync, pipeline.execute() é async."""
    redis = MagicMock()
    pipe = MagicMock()
    pipe.execute = AsyncMock(return_value=[0, True, count, True])
    redis.pipeline.return_value = pipe
    return redis


@patch("app.core.rate_limit.get_redis")
async def test_uses_forwarded_for_ip(mock_get_redis: MagicMock):
    """Rate limit deve usar X-Forwarded-For quando presente."""
    redis = _make_redis_mock(count=1)
    mock_get_redis.return_value = redis

    request = _mock_request(ip="172.17.0.2", forwarded_for="189.62.149.140, 10.0.0.1")
    await check_rate_limit(request, key_prefix="test", limit=5)

    pipe = redis.pipeline.return_value
    call_args = pipe.zremrangebyscore.call_args[0]
    key = call_args[0]
    assert "189.62.149.140" in key


@patch("app.core.rate_limit.get_redis")
async def test_falls_back_to_client_host(mock_get_redis: MagicMock):
    """Sem X-Forwarded-For, usa request.client.host."""
    redis = _make_redis_mock(count=1)
    mock_get_redis.return_value = redis

    request = _mock_request(ip="192.168.1.100")
    await check_rate_limit(request, key_prefix="login", limit=5)

    pipe = redis.pipeline.return_value
    call_args = pipe.zremrangebyscore.call_args[0]
    key = call_args[0]
    assert "192.168.1.100" in key


@patch("app.core.rate_limit.get_redis")
async def test_raises_429_when_over_limit(mock_get_redis: MagicMock):
    """Deve retornar 429 quando count > limit."""
    redis = _make_redis_mock(count=6)
    mock_get_redis.return_value = redis

    request = _mock_request(ip="1.2.3.4")

    with pytest.raises(HTTPException) as exc_info:
        await check_rate_limit(request, key_prefix="login", limit=5)

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers


@patch("app.core.rate_limit.get_redis")
async def test_allows_when_at_limit(mock_get_redis: MagicMock):
    """Exatamente no limite (count == limit) deve permitir."""
    redis = _make_redis_mock(count=5)
    mock_get_redis.return_value = redis

    request = _mock_request(ip="1.2.3.4")
    # count=5, limit=5 → 5 > 5 é False, deve passar
    await check_rate_limit(request, key_prefix="login", limit=5)


@patch("app.core.rate_limit.get_redis")
async def test_forwarded_for_strips_whitespace(mock_get_redis: MagicMock):
    """X-Forwarded-For pode ter espaço após vírgula."""
    redis = _make_redis_mock(count=1)
    mock_get_redis.return_value = redis

    request = _mock_request(ip="127.0.0.1", forwarded_for="  200.100.50.25  , 10.0.0.1")
    await check_rate_limit(request, key_prefix="api", limit=60)

    pipe = redis.pipeline.return_value
    call_args = pipe.zremrangebyscore.call_args[0]
    key = call_args[0]
    assert "200.100.50.25" in key
    assert " " not in key.split(":")[-1]
