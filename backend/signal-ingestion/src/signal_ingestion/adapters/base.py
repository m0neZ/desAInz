"""Base adapter with rate limiting and proxy rotation."""

from __future__ import annotations

import asyncio
import itertools
import os
from typing import Any, Iterable, Optional, cast

import httpx


class BaseAdapter:
    """Provide HTTP fetching with rate limiting and rotating proxies."""

    def __init__(
        self,
        base_url: str,
        proxies: Optional[Iterable[str | None]] = None,
        rate_limit: int = 5,
    ) -> None:
        """Instantiate the adapter."""
        self.base_url = base_url
        self._rate_limiter = asyncio.Semaphore(rate_limit)
        if proxies is None:
            raw = os.environ.get("HTTP_PROXIES")
            parsed = raw.split(",") if raw else []
            proxy_list = cast(list[str | None], parsed)
            if not proxy_list:
                proxy_list = [None]
        else:
            proxy_list = list(proxies)
        self._proxies_cycle = itertools.cycle(proxy_list)

    async def _request(
        self, path: str, *, headers: dict[str, str] | None = None
    ) -> httpx.Response:
        """Perform a GET request respecting rate limits and proxies."""
        async with self._rate_limiter:
            proxy = next(self._proxies_cycle)
            async with httpx.AsyncClient(proxy=cast(Any, proxy)) as client:
                resp = await client.get(f"{self.base_url}{path}", headers=headers)
                resp.raise_for_status()
                return resp

    async def fetch(self) -> list[dict[str, object]]:
        """Fetch raw data from the remote source."""
        raise NotImplementedError
