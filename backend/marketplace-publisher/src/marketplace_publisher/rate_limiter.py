"""Redis-backed rate limiter for publishing.

Implements a simple fixed-window algorithm using Redis
for distributed coordination across service instances.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Mapping

from redis.asyncio import Redis

from .db import Marketplace


class MarketplaceRateLimiter:
    """Manage per-marketplace request limits."""

    def __init__(
        self,
        redis: Redis,
        limits: Mapping[Marketplace, int],
        window: int,
    ) -> None:
        """Instantiate the rate limiter.

        Args:
            redis: Redis client instance.
            limits: Allowed requests per window for each marketplace.
            window: Window size in seconds.
        """
        self._redis = redis
        self._limits = limits
        self._window = window

    async def acquire(self, marketplace: Marketplace) -> bool:
        """Attempt to consume a request slot.

        Args:
            marketplace: Marketplace for which to consume a slot.

        Returns:
            ``True`` if a slot was consumed, ``False`` if the limit
            has been exceeded.
        """
        limit = self._limits.get(marketplace)
        if limit is None:
            return True
        now = int(time.time())
        window = now // self._window
        key = f"rate:{marketplace.value}:{window}"
        count = await self._redis.incr(key)
        if count == 1:
            await self._redis.expire(key, self._window)
        if count > limit:
            await asyncio.sleep(0)
            return False
        return True
