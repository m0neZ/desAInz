"""Redis-backed rate limiter using token buckets."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping

from redis.asyncio import WatchError

from backend.shared.cache import AsyncRedis, get_async_client

__all__ = ["AdapterRateLimiter"]


class AdapterRateLimiter:
    """Manage per-adapter request quotas."""

    def __init__(
        self,
        limits: Mapping[str, int],
        window: int = 1,
        redis: AsyncRedis | None = None,
    ) -> None:
        """Instantiate the limiter with ``limits`` tokens per ``window`` seconds."""
        self._redis = redis or get_async_client()
        self._limits = dict(limits)
        self._window = window

    async def acquire(self, adapter: str) -> None:
        """
        Block until a token is available for ``adapter``.

        This coroutine must be awaited.
        """
        limit = self._limits.get(adapter, self._limits.get("default"))
        if limit is None:
            return
        key = f"adapter_tokens:{adapter}"
        while True:
            async with self._redis.pipeline() as pipe:
                try:
                    await pipe.watch(key)
                    raw = await pipe.get(key)
                    if raw is None:
                        pipe.multi()
                        pipe.set(key, limit - 1, ex=self._window)
                        await pipe.execute()
                        return
                    tokens = int(raw)
                    if tokens <= 0:
                        await pipe.unwatch()
                        await asyncio.sleep(self._window)
                        continue
                    pipe.multi()
                    pipe.decr(key)
                    await pipe.execute()
                    return
                except WatchError:
                    continue
