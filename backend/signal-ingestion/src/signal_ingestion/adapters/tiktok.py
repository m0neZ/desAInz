"""TikTok source adapter."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter
from ..settings import settings


class TikTokAdapter(BaseAdapter):
    """Adapter for TikTok API using the public oEmbed endpoint."""

    def __init__(
        self,
        base_url: str | None = None,
        proxies: list[str] | None = None,
        rate_limit: int = 5,
        video_urls: list[str] | None = None,
        fetch_limit: int | None = None,
    ) -> None:
        """Initialize adapter with optional ``base_url``."""
        self.video_urls = video_urls or [
            v.strip()
            for v in (settings.tiktok_video_urls or "").split(",")
            if v.strip()
        ]
        if not self.video_urls:
            self.video_urls = [
                "https://www.tiktok.com/@scout2015/video/6718335390845095173"
            ]
        self.fetch_limit = fetch_limit or settings.tiktok_fetch_limit
        super().__init__(base_url or "https://www.tiktok.com", proxies, rate_limit)

    async def fetch(self) -> list[dict[str, Any]]:
        """Return metadata for configured TikTok videos."""
        results: list[dict[str, Any]] = []
        for url in self.video_urls[: self.fetch_limit]:
            resp = await self._request(f"/oembed?url={url}")
            if resp is None:
                continue
            results.append(resp.json())
        return results
