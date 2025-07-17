"""Nostalgia source adapter."""

from __future__ import annotations

from typing import Any

import os

from .base import BaseAdapter


class NostalgiaAdapter(BaseAdapter):
    """Adapter for the Internet Archive search API."""

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize adapter with optional ``base_url``."""
        super().__init__(base_url or "https://archive.org")

    async def fetch(self) -> list[dict[str, Any]]:
        """Return one search result for nostalgia-related items."""
        query = os.environ.get("NOSTALGIA_QUERY", 'subject:"nostalgia"')
        resp = await self._request(f"/advancedsearch.php?q={query}&output=json&rows=1")
        return [resp.json()]
