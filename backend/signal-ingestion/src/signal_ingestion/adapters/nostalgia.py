"""Nostalgia source adapter."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter
from ..settings import settings


class NostalgiaAdapter(BaseAdapter):
    """Adapter for the Internet Archive search API."""

    def __init__(
        self,
        base_url: str | None = None,
        proxies: list[str] | None = None,
        rate_limit: int = 5,
        query: str | None = None,
        fetch_limit: int | None = None,
    ) -> None:
        """Initialize adapter with optional ``base_url``."""
        self.query = query or settings.nostalgia_query
        self.fetch_limit = fetch_limit or settings.nostalgia_fetch_limit
        super().__init__(base_url or "https://archive.org", proxies, rate_limit)

    async def fetch(self) -> list[dict[str, Any]]:
        """Return search results for nostalgia-related items."""
        remaining = self.fetch_limit
        resp = await self._request(
            f"/advancedsearch.php?q={self.query}&output=json&rows={remaining}"
        )
        if resp is None:
            return []
        data = resp.json()
        docs = data.get("response", {}).get("docs", [])
        start = len(docs)
        while len(docs) < self.fetch_limit:
            remaining = self.fetch_limit - len(docs)
            resp = await self._request(
                f"/advancedsearch.php?q={self.query}&output=json&rows={remaining}&start={start}"
            )
            if resp is None:
                break
            page = resp.json()
            page_docs = page.get("response", {}).get("docs", [])
            if not page_docs:
                break
            docs.extend(page_docs)
            start += len(page_docs)
        data["response"]["docs"] = docs[: self.fetch_limit]
        return [data]
