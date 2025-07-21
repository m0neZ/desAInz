"""Base adapter with rate limiting and proxy rotation."""

from __future__ import annotations

import asyncio
import itertools
import os
from typing import Any, Iterable, Optional, cast

from ..rate_limit import AdapterRateLimiter

import httpx


class BaseAdapter:
    """Provide HTTP fetching with rate limiting and rotating proxies."""

    _limiters: dict[type, AdapterRateLimiter] = {}

    def __init__(
        self,
        base_url: str,
        proxies: Optional[Iterable[str | None]] = None,
        rate_limit: int = 5,
    ) -> None:
        """
        Instantiate the adapter.

        Parameters
        ----------
        base_url:
            API base URL.
        proxies:
            Optional list of proxies rotated on each request.
        rate_limit:
            Maximum number of concurrent requests for this adapter.
        """
        self.base_url = base_url
        if self.__class__ not in BaseAdapter._limiters:
            BaseAdapter._limiters[self.__class__] = AdapterRateLimiter(
                {self.__class__.__name__: rate_limit}
            )
        self._rate_limiter = BaseAdapter._limiters[self.__class__]
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
        await self._rate_limiter.acquire(self.__class__.__name__)
        proxy = next(self._proxies_cycle)
        async with httpx.AsyncClient(proxy=cast(Any, proxy)) as client:
            url = path if path.startswith("http") else f"{self.base_url}{path}"
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp

    async def fetch(self) -> list[dict[str, object]]:
        """Fetch raw data from the remote source."""
        raise NotImplementedError
