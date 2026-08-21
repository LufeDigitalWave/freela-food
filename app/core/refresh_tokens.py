"""Refresh tokens — opaque tokens stored as SHA-256 hash in Redis.

Dual-index approach:
  - Forward: refresh:{hash} → user_id (lookup by token)
  - Reverse: user_tokens:{user_id} → set of hashes (revoke all O(m))
"""

import hashlib
import secrets
import uuid

from app.core.config import get_settings
from app.core.redis_client import get_redis

_PREFIX = "refresh:"
_USER_PREFIX = "user_tokens:"


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def store_refresh_token(user_id: uuid.UUID, token: str) -> None:
    settings = get_settings()
    redis = await get_redis()
    token_hash = _hash(token)
    key = f"{_PREFIX}{token_hash}"
    user_key = f"{_USER_PREFIX}{user_id}"
    ttl = settings.refresh_token_expire_days * 86400

    pipe = redis.pipeline()
    pipe.set(key, str(user_id), ex=ttl)
    pipe.sadd(user_key, token_hash)
    pipe.expire(user_key, ttl)
    await pipe.execute()


async def validate_refresh_token(token: str) -> uuid.UUID | None:
    redis = await get_redis()
    key = f"{_PREFIX}{_hash(token)}"
    user_id_str = await redis.get(key)
    if not user_id_str:
        return None
    return uuid.UUID(user_id_str)


async def revoke_refresh_token(token: str) -> None:
    redis = await get_redis()
    token_hash = _hash(token)
    key = f"{_PREFIX}{token_hash}"

    # Get user_id before deleting (to cleanup reverse index)
    user_id_str = await redis.get(key)

    pipe = redis.pipeline()
    pipe.delete(key)
    if user_id_str:
        pipe.srem(f"{_USER_PREFIX}{user_id_str}", token_hash)
    await pipe.execute()


async def revoke_all_for_user(user_id: uuid.UUID) -> None:
    """Revoga todos refresh tokens de um user. O(m) onde m = tokens do user."""
    redis = await get_redis()
    user_key = f"{_USER_PREFIX}{user_id}"

    # Buscar todos os hashes desse user
    token_hashes = await redis.smembers(user_key)
    if not token_hashes:
        return

    # Deletar todos tokens + o set reverso
    pipe = redis.pipeline()
    for token_hash in token_hashes:
        pipe.delete(f"{_PREFIX}{token_hash}")
    pipe.delete(user_key)
    await pipe.execute()
