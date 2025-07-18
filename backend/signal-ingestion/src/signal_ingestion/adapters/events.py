"""Events source adapter."""

from __future__ import annotations

from typing import Any

import os

from .base import BaseAdapter


class EventsAdapter(BaseAdapter):
    """Adapter for public holiday events API."""

    def __init__(
        self,
        base_url: str | None = None,
        proxies: list[str] | None = None,
        rate_limit: int = 5,
    ) -> None:
        """Initialize adapter with optional ``base_url``."""
        super().__init__(base_url or "https://date.nager.at", proxies, rate_limit)

    async def fetch(self) -> list[dict[str, Any]]:
        """Return upcoming US public holidays."""
        resp = await self._request("/api/v3/NextPublicHolidays/US")
        return [resp.json()[0]]
