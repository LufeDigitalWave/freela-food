"""Refresh tokens — opaque tokens stored as SHA-256 hash in Redis."""

import hashlib
import secrets
import uuid

from app.core.config import get_settings
from app.core.redis_client import get_redis

_PREFIX = "refresh:"


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def store_refresh_token(user_id: uuid.UUID, token: str) -> None:
    settings = get_settings()
    redis = await get_redis()
    key = f"{_PREFIX}{_hash(token)}"
    ttl = settings.refresh_token_expire_days * 86400
    await redis.set(key, str(user_id), ex=ttl)


async def validate_refresh_token(token: str) -> uuid.UUID | None:
    redis = await get_redis()
    key = f"{_PREFIX}{_hash(token)}"
    user_id_str = await redis.get(key)
    if not user_id_str:
        return None
    return uuid.UUID(user_id_str)


async def revoke_refresh_token(token: str) -> None:
    redis = await get_redis()
    key = f"{_PREFIX}{_hash(token)}"
    await redis.delete(key)


async def revoke_all_for_user(user_id: uuid.UUID) -> None:
    redis = await get_redis()
    async for key in redis.scan_iter(f"{_PREFIX}*"):
        val = await redis.get(key)
        if val and val == str(user_id):
            await redis.delete(key)
