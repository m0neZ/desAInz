"""Instagram source adapter."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter
from ..settings import settings


class InstagramAdapter(BaseAdapter):
    """Adapter for Instagram Graph API."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        user_id: str | None = None,
        fetch_limit: int | None = None,
        proxies: list[str] | None = None,
        rate_limit: int = 5,
    ) -> None:
        """Initialize adapter with API credentials and limits."""
        self.token = token or settings.instagram_token or ""
        self.user_id = user_id or settings.instagram_user_id or ""
        self.fetch_limit = fetch_limit or settings.instagram_fetch_limit
        super().__init__(
            base_url or "https://graph.facebook.com/v19.0", proxies, rate_limit
        )

    async def fetch(self) -> list[dict[str, Any]]:
        """Return recent media posts for the configured user."""
        path = (
            f"/{self.user_id}/media?fields=id,caption,permalink"
            f"&limit={self.fetch_limit}&access_token={self.token}"
        )
        resp = await self._request(path)
        if resp is None:
            return []
        data = resp.json()
        posts = data.get("data", [])
        next_url = data.get("paging", {}).get("next")
        while next_url and len(posts) < self.fetch_limit:
            resp = await self._request(next_url)
            if resp is None:
                break
            page = resp.json()
            posts.extend(page.get("data", []))
            next_url = page.get("paging", {}).get("next")
        return posts[: self.fetch_limit]
