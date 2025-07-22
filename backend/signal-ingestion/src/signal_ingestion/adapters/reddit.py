"""Reddit source adapter."""

from __future__ import annotations

from typing import Any

from ..settings import settings
from .base import BaseAdapter


class RedditAdapter(BaseAdapter):
    """Adapter for Reddit API using the public JSON endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        proxies: list[str] | None = None,
        rate_limit: int = 5,
        fetch_limit: int | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Initialize adapter with endpoint configuration."""
        self.fetch_limit = fetch_limit or settings.reddit_fetch_limit
        self.user_agent = user_agent or settings.reddit_user_agent
        super().__init__(base_url or "https://www.reddit.com", proxies, rate_limit)

    async def fetch(self) -> list[dict[str, Any]]:
        """Return the top posts from ``r/python``."""
        headers = {"User-Agent": self.user_agent}
        remaining = self.fetch_limit
        resp = await self._request(
            f"/r/python/top.json?limit={remaining}", headers=headers
        )
        if resp is None:
            return []
        data = resp.json()
        posts = data["data"]["children"]
        after = data["data"].get("after")
        while after and len(posts) < self.fetch_limit:
            remaining = self.fetch_limit - len(posts)
            resp = await self._request(
                f"/r/python/top.json?limit={remaining}&after={after}",
                headers=headers,
            )
            if resp is None:
                break
            page = resp.json()
            posts.extend(page["data"]["children"])
            after = page["data"].get("after")
        data["data"]["children"] = posts[: self.fetch_limit]
        return [data]
