"""YouTube source adapter."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class YouTubeAdapter(BaseAdapter):
    """Adapter for YouTube API."""

    async def fetch(self) -> list[dict[str, Any]]:
        """Return a list of YouTube videos."""
        resp = await self._request("/posts/4")
        return [resp.json()]
