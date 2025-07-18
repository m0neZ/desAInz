"""TikTok source adapter."""

from __future__ import annotations

from typing import Any

import os

from .base import BaseAdapter


class TikTokAdapter(BaseAdapter):
    """Adapter for TikTok API using the public oEmbed endpoint."""

    def __init__(
        self,
        base_url: str | None = None,
        proxies: list[str] | None = None,
        rate_limit: int = 5,
    ) -> None:
        """Initialize adapter with optional ``base_url``."""
        super().__init__(base_url or "https://www.tiktok.com", proxies, rate_limit)

    async def fetch(self) -> list[dict[str, Any]]:
        """Return a list with metadata for a single TikTok video."""
        video_url = os.environ.get(
            "TIKTOK_DEMO_URL",
            "https://www.tiktok.com/@scout2015/video/6718335390845095173",
        )
        resp = await self._request(f"/oembed?url={video_url}")
        return [resp.json()]
