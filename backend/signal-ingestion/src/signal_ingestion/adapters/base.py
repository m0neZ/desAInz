"""Base adapter with rate limiting and proxy rotation."""

from __future__ import annotations

import itertools
import os
import asyncio
import atexit
from typing import Any, Iterable, Optional, cast

from ..rate_limit import AdapterRateLimiter
from backend.shared.cache import async_get, async_set

import httpx
from backend.shared.http import DEFAULT_TIMEOUT

_ASYNC_CLIENT: httpx.AsyncClient | None = None


async def get_async_client() -> httpx.AsyncClient:
    """Return a shared ``AsyncClient`` instance."""
    global _ASYNC_CLIENT
    if _ASYNC_CLIENT is None:
        _ASYNC_CLIENT = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
    return _ASYNC_CLIENT


@atexit.register
def _close_client() -> None:
    if _ASYNC_CLIENT is not None:
        asyncio.run(_ASYNC_CLIENT.aclose())


class BaseAdapter:
    """Provide HTTP fetching with rate limiting and rotating proxies."""

    _limiters: dict[type, AdapterRateLimiter] = {}

    def __init__(
        self,
        base_url: str,
        proxies: Optional[Iterable[str | None]] = None,
        rate_limit: int = 5,
        retries: int = 3,
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
        retries:
            Number of attempts for each request before raising an error.
        """
        self.base_url = base_url
        self.retries = retries
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
    ) -> httpx.Response | None:
        """
        Return the response for ``path`` using ETag caching.

        The cached ETag for ``path`` is sent via ``If-None-Match`` and any new
        ETag value is persisted. ``None`` is returned when the server responds
        with ``304 Not Modified`` to signal that processing should be skipped.
        """
        await self._rate_limiter.acquire(self.__class__.__name__)
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        etag_key = f"etag:{url}"
        req_headers = dict(headers or {})
        cached_etag = await async_get(etag_key)
        if cached_etag:
            req_headers["If-None-Match"] = cached_etag

        client = await get_async_client()
        for attempt in range(self.retries):
            proxy = next(self._proxies_cycle)
            try:
                resp = await client.get(
                    url,
                    headers=req_headers or None,
                    proxies=cast(Any, proxy),
                )
                if resp.status_code == 304:
                    return None
                if etag := resp.headers.get("ETag"):
                    await async_set(etag_key, etag)
                resp.raise_for_status()
                return resp
            except httpx.HTTPError:
                if attempt >= self.retries - 1:
                    raise
                await asyncio.sleep(2**attempt)

        raise RuntimeError("Unreachable")

    async def fetch(self) -> list[dict[str, object]]:
        """Fetch raw data from the remote source."""
        raise NotImplementedError
