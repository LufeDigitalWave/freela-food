"""Rate limiting middleware — Redis-backed sliding window."""

import time

from fastapi import HTTPException, Request, status

from app.core.config import get_settings
from app.core.redis_client import get_redis


async def check_rate_limit(
    request: Request,
    *,
    key_prefix: str,
    limit: int,
    window_seconds: int = 60,
) -> None:
    redis = await get_redis()
    ip = request.client.host if request.client else "unknown"
    key = f"ratelimit:{key_prefix}:{ip}"

    now = time.time()
    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window_seconds)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window_seconds + 1)
    results = await pipe.execute()

    count = results[2]
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas requisições. Aguarde um momento.",
            headers={"Retry-After": str(window_seconds)},
        )


async def rate_limit_login(request: Request) -> None:
    settings = get_settings()
    await check_rate_limit(request, key_prefix="login", limit=settings.rate_limit_login)


async def rate_limit_register(request: Request) -> None:
    settings = get_settings()
    await check_rate_limit(request, key_prefix="register", limit=settings.rate_limit_register)
