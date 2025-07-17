"""YouTube source adapter."""

from __future__ import annotations

from typing import Any

import os

from .base import BaseAdapter


class YouTubeAdapter(BaseAdapter):
    """Adapter for YouTube API using the oEmbed endpoint."""

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize adapter with optional ``base_url``."""
        super().__init__(base_url or "https://noembed.com")

    async def fetch(self) -> list[dict[str, Any]]:
        """Return metadata for a single YouTube video."""
        video_url = os.environ.get(
            "YOUTUBE_DEMO_URL",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )
        resp = await self._request(f"/embed?url={video_url}")
        return [resp.json()]
