"""Reddit source adapter."""

from __future__ import annotations

from typing import Any

import os

from .base import BaseAdapter


class RedditAdapter(BaseAdapter):
    """Adapter for Reddit API using a JSON feed."""

    def __init__(
        self,
        base_url: str | None = None,
        proxies: list[str] | None = None,
        rate_limit: int = 5,
    ) -> None:
        """Initialize adapter with optional ``base_url``."""
        super().__init__(
            base_url or "https://jsonplaceholder.typicode.com", proxies, rate_limit
        )

    async def fetch(self) -> list[dict[str, Any]]:
        """Return a list with top post data from ``r/python``."""
        resp = await self._request("/posts/3")
        return [resp.json()]
