"""Instagram source adapter."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class InstagramAdapter(BaseAdapter):
    """Adapter for Instagram API."""

    async def fetch(self) -> list[dict[str, Any]]:
        """Return a list of Instagram posts."""
        resp = await self._request("/posts/2")
        return [resp.json()]
