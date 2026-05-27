"""Singleton async para Redis."""

from __future__ import annotations

from redis.asyncio import Redis, from_url

from app.core.config import get_settings

_redis: Redis[str] | None = None


def get_redis() -> Redis[str]:
    global _redis
    if _redis is None:
        _redis = from_url(
            get_settings().redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
