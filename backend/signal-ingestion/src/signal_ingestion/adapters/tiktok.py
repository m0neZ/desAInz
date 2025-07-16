"""TikTok source adapter."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class TikTokAdapter(BaseAdapter):
    """Adapter for TikTok API."""

    async def fetch(self) -> list[dict[str, Any]]:
        """Return a list of TikTok posts."""
        resp = await self._request("/posts/1")
        return [resp.json()]
