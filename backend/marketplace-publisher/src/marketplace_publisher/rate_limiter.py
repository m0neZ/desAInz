"""Simple Redis-based rate limiter."""

from __future__ import annotations

import redis


class RateLimiter:
    """Token-based rate limiting using Redis."""

    def __init__(self, client: redis.Redis) -> None:
        """Store the Redis ``client`` used for state."""
        self._client = client

    def acquire(self, key: str, limit: int, period: int = 86400) -> bool:
        """Return ``True`` if a token is acquired for ``key`` within ``limit``."""
        with self._client.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(key)
                    current = int(pipe.get(key) or 0)
                    if current >= limit:
                        pipe.unwatch()
                        return False
                    pipe.multi()
                    pipe.incr(key)
                    if current == 0:
                        pipe.expire(key, period)
                    pipe.execute()
                    return True
                except redis.WatchError:
                    continue
