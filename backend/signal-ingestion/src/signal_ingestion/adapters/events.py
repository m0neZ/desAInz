"""Events source adapter."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class EventsAdapter(BaseAdapter):
    """Adapter for events API."""

    async def fetch(self) -> list[dict[str, Any]]:
        """Return a list of events."""
        resp = await self._request("/posts/5")
        return [resp.json()]
