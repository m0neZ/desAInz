"""Base adapter with rate limiting and proxy rotation."""

from __future__ import annotations

import itertools
import asyncio
import atexit
from typing import Any, Iterable, Optional, cast

from ..rate_limit import AdapterRateLimiter
from ..settings import settings
from backend.shared.cache import async_get, async_set

import httpx
from backend.shared.http import DEFAULT_TIMEOUT

_HTTP_CLIENTS: dict[str | None, httpx.AsyncClient] = {}


async def get_http_client(proxy: str | None) -> httpx.AsyncClient:
    """Return a cached HTTP client for ``proxy``."""
    client = _HTTP_CLIENTS.get(proxy)
    if client is None:
        client = httpx.AsyncClient(proxy=cast(Any, proxy), timeout=DEFAULT_TIMEOUT)
        _HTTP_CLIENTS[proxy] = client
    return client


@atexit.register
def _close_clients() -> None:
    async def _close_all() -> None:
        for cli in _HTTP_CLIENTS.values():
            await cli.aclose()
        _HTTP_CLIENTS.clear()

    asyncio.run(_close_all())


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
        self._rate_limiter = BaseAdapter._limiters.setdefault(
            self.__class__,
            AdapterRateLimiter({self.__class__.__name__: rate_limit}),
        )
        if proxies is None:
            raw = settings.http_proxies
            parsed = str(raw).split(",") if raw else []
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

        for attempt in range(self.retries):
            proxy = next(self._proxies_cycle)
            client = await get_http_client(proxy)
            try:
                resp = await client.get(url, headers=req_headers or None)
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
