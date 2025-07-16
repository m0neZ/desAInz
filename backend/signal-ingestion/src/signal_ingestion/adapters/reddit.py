"""Reddit source adapter."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class RedditAdapter(BaseAdapter):
    """Adapter for Reddit API."""

    async def fetch(self) -> list[dict[str, Any]]:
        """Return a list of Reddit posts."""
        resp = await self._request("/posts/3")
        return [resp.json()]
