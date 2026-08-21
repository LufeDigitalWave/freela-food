"""Testes unitários para refresh_tokens.py (dual-index Redis)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.refresh_tokens import (
    _hash,
    generate_refresh_token,
    revoke_all_for_user,
    revoke_refresh_token,
    store_refresh_token,
    validate_refresh_token,
)


def test_generate_token_is_unique():
    t1 = generate_refresh_token()
    t2 = generate_refresh_token()
    assert t1 != t2
    assert len(t1) >= 48


def test_hash_is_deterministic():
    token = "test-token-123"
    assert _hash(token) == _hash(token)
    assert len(_hash(token)) == 64


def test_hash_different_for_different_tokens():
    assert _hash("token-a") != _hash("token-b")


def _make_mock_redis() -> MagicMock:
    """Cria mock de Redis.

    get_redis() retorna Redis sync (não awaitable).
    Redis.get(), .smembers() são async (awaitable).
    Redis.pipeline() é sync, retorna pipeline cujos métodos são sync,
    mas .execute() é async.
    """
    redis = MagicMock()
    pipe = MagicMock()
    pipe.execute = AsyncMock(return_value=[True, True, True])
    redis.pipeline.return_value = pipe
    redis.get = AsyncMock(return_value=None)
    redis.smembers = AsyncMock(return_value=set())
    return redis


@patch("app.core.refresh_tokens.get_redis")
@patch("app.core.refresh_tokens.get_settings")
async def test_store_creates_dual_index(mock_get_settings: MagicMock, mock_get_redis: MagicMock):
    """Verifica que store cria tanto o forward quanto o reverse index."""
    user_id = uuid.uuid4()
    token = "my-refresh-token"
    token_hash = _hash(token)

    redis = _make_mock_redis()
    mock_get_redis.return_value = redis

    settings = MagicMock()
    settings.refresh_token_expire_days = 30
    mock_get_settings.return_value = settings

    await store_refresh_token(user_id, token)

    pipe = redis.pipeline.return_value
    pipe.set.assert_called_once_with(f"refresh:{token_hash}", str(user_id), ex=30 * 86400)
    pipe.sadd.assert_called_once_with(f"user_tokens:{user_id}", token_hash)
    pipe.expire.assert_called_once_with(f"user_tokens:{user_id}", 30 * 86400)
    pipe.execute.assert_awaited_once()


@patch("app.core.refresh_tokens.get_redis")
async def test_validate_returns_user_id(mock_get_redis: MagicMock):
    user_id = uuid.uuid4()

    redis = _make_mock_redis()
    redis.get = AsyncMock(return_value=str(user_id))
    mock_get_redis.return_value = redis

    result = await validate_refresh_token("valid-token")
    assert result == user_id


@patch("app.core.refresh_tokens.get_redis")
async def test_validate_returns_none_for_invalid(mock_get_redis: MagicMock):
    redis = _make_mock_redis()
    redis.get = AsyncMock(return_value=None)
    mock_get_redis.return_value = redis

    result = await validate_refresh_token("invalid-token")
    assert result is None


@patch("app.core.refresh_tokens.get_redis")
async def test_revoke_deletes_forward_and_reverse(mock_get_redis: MagicMock):
    """Verifica que revoke remove tanto forward quanto reverse index."""
    user_id = uuid.uuid4()
    token = "token-to-revoke"
    token_hash = _hash(token)

    redis = _make_mock_redis()
    redis.get = AsyncMock(return_value=str(user_id))
    mock_get_redis.return_value = redis

    await revoke_refresh_token(token)

    pipe = redis.pipeline.return_value
    pipe.delete.assert_called_once_with(f"refresh:{token_hash}")
    pipe.srem.assert_called_once_with(f"user_tokens:{user_id}", token_hash)


@patch("app.core.refresh_tokens.get_redis")
async def test_revoke_all_deletes_all_user_tokens(mock_get_redis: MagicMock):
    """Verifica que revoke_all apaga todos os tokens do user via reverse index."""
    user_id = uuid.uuid4()
    hashes = {"hash1", "hash2", "hash3"}

    redis = _make_mock_redis()
    redis.smembers = AsyncMock(return_value=hashes)
    pipe = MagicMock()
    pipe.execute = AsyncMock(return_value=[1] * (len(hashes) + 1))
    redis.pipeline.return_value = pipe
    mock_get_redis.return_value = redis

    await revoke_all_for_user(user_id)

    redis.smembers.assert_awaited_once_with(f"user_tokens:{user_id}")
    assert pipe.delete.call_count == len(hashes) + 1


@patch("app.core.refresh_tokens.get_redis")
async def test_revoke_all_noop_if_no_tokens(mock_get_redis: MagicMock):
    """Se user não tem tokens, revoke_all não faz nada."""
    user_id = uuid.uuid4()

    redis = _make_mock_redis()
    redis.smembers = AsyncMock(return_value=set())
    mock_get_redis.return_value = redis

    await revoke_all_for_user(user_id)

    redis.pipeline.assert_not_called()
