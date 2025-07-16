"""Redis-backed rate limiter using token buckets."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from redis.asyncio import Redis, WatchError

from .db import Marketplace


class MarketplaceRateLimiter:
    """Manage per-marketplace request limits."""

    def __init__(
        self,
        redis: Redis,
        limits: Mapping[Marketplace, int],
        window: int,
    ) -> None:
        """
        Instantiate the rate limiter.

        Args:
            redis: Redis client instance.
            limits: Allowed requests per window for each marketplace.
            window: Window size in seconds.
        """
        self._redis = redis
        self._limits = limits
        self._window = window

    async def acquire(self, marketplace: Marketplace) -> bool:
        """
        Attempt to consume a request slot.

        Args:
            marketplace: Marketplace for which to consume a slot.

        Returns:
            ``True`` if a slot was consumed, ``False`` if the limit
            has been exceeded.
        """
        limit = self._limits.get(marketplace)
        if limit is None:
            return True
        key = f"tokens:{marketplace.value}"
        async with self._redis.pipeline() as pipe:
            while True:
                try:
                    await pipe.watch(key)
                    raw: Any = await pipe.get(key)
                    if raw is None:
                        pipe.multi()  # type: ignore[no-untyped-call]
                        pipe.set(key, limit - 1, ex=self._window)
                        await pipe.execute()
                        return True
                    tokens = int(raw)
                    if tokens <= 0:
                        await pipe.unwatch()  # type: ignore[no-untyped-call]
                        await asyncio.sleep(0)
                        return False
                    pipe.multi()  # type: ignore[no-untyped-call]
                    pipe.decr(key)
                    await pipe.execute()
                    return True
                except WatchError:
                    continue
