"""Redis-backed token bucket rate limiter."""

from __future__ import annotations

import asyncio
from redis.asyncio import Redis, WatchError


class UserRateLimiter:
    """Manage request quotas for individual users."""

    def __init__(self, redis: Redis, limit: int, window: int) -> None:
        """Instantiate the limiter with ``limit`` tokens per ``window`` seconds."""
        self._redis = redis
        self._limit = limit
        self._window = window

    async def acquire(self, user_id: str) -> bool:
        """Consume a token for ``user_id`` if available."""
        key = f"tokens:{user_id}"
        async with self._redis.pipeline() as pipe:
            while True:
                try:
                    await pipe.watch(key)
                    raw = await pipe.get(key)
                    if raw is None:
                        pipe.multi()
                        pipe.set(key, self._limit - 1, ex=self._window)
                        await pipe.execute()
                        return True
                    tokens = int(raw)
                    if tokens <= 0:
                        await pipe.unwatch()
                        await asyncio.sleep(0)
                        return False
                    pipe.multi()
                    pipe.decr(key)
                    await pipe.execute()
                    return True
                except WatchError:
                    continue
