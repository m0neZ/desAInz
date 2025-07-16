"""Nostalgia source adapter."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class NostalgiaAdapter(BaseAdapter):
    """Adapter for Nostalgia API."""

    async def fetch(self) -> list[dict[str, Any]]:
        """Return a list of nostalgia posts."""
        resp = await self._request("/posts/6")
        return [resp.json()]
