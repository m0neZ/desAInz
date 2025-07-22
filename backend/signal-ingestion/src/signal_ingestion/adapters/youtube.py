"""YouTube source adapter."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter
from ..settings import settings


class YouTubeAdapter(BaseAdapter):
    """Adapter for YouTube API using the Data and oEmbed endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        proxies: list[str] | None = None,
        rate_limit: int = 5,
        api_key: str | None = None,
        fetch_limit: int | None = None,
    ) -> None:
        """Initialize adapter with API key and limits."""
        self.api_key = api_key or settings.youtube_api_key or ""
        self.fetch_limit = fetch_limit or settings.youtube_fetch_limit
        super().__init__(base_url or "https://www.googleapis.com", proxies, rate_limit)

    async def _oembed(self, video_id: str) -> dict[str, Any]:
        """Fetch oEmbed data for ``video_id``."""
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}"
        resp = await self._request(url)
        if resp is None:
            return {}
        return resp.json()

    async def fetch(self) -> list[dict[str, Any]]:
        """Return metadata for popular YouTube videos."""
        remaining = self.fetch_limit
        resp = await self._request(
            f"/youtube/v3/videos?part=id&chart=mostPopular&maxResults={remaining}&key={self.api_key}"
        )
        if resp is None:
            return []
        data = resp.json()
        ids = [item["id"] for item in data.get("items", [])]
        next_token = data.get("nextPageToken")
        while next_token and len(ids) < self.fetch_limit:
            remaining = self.fetch_limit - len(ids)
            resp = await self._request(
                f"/youtube/v3/videos?part=id&chart=mostPopular&maxResults={remaining}&pageToken={next_token}&key={self.api_key}"
            )
            if resp is None:
                break
            page = resp.json()
            ids.extend([item["id"] for item in page.get("items", [])])
            next_token = page.get("nextPageToken")
        ids = ids[: self.fetch_limit]
        results = []
        for vid in ids:
            results.append(await self._oembed(vid))
        return results
