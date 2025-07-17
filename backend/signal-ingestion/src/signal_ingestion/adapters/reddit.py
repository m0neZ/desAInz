"""Reddit source adapter."""

from __future__ import annotations

from typing import Any

import os

from .base import BaseAdapter


class RedditAdapter(BaseAdapter):
    """Adapter for Reddit API using a JSON feed."""

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize adapter with optional ``base_url``."""
        super().__init__(base_url or "https://r.jina.ai/https://www.reddit.com")

    async def fetch(self) -> list[dict[str, Any]]:
        """Return a list with top post data from ``r/python``."""
        resp = await self._request("/r/python/top.json?limit=1")
        return [resp.json()]
