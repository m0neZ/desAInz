"""Instagram source adapter."""

from __future__ import annotations

from typing import Any

import os

from .base import BaseAdapter


class InstagramAdapter(BaseAdapter):
    """Adapter for Instagram oEmbed API."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        proxies: list[str] | None = None,
        rate_limit: int = 5,
    ) -> None:
        """Initialize adapter with optional ``base_url`` and access ``token``."""
        self.token = token or os.environ.get("INSTAGRAM_TOKEN", "")
        super().__init__(
            base_url or "https://graph.facebook.com/v19.0", proxies, rate_limit
        )

    async def fetch(self) -> list[dict[str, Any]]:
        """Return metadata for a single Instagram post."""
        post_url = os.environ.get(
            "INSTAGRAM_DEMO_URL",
            "https://www.instagram.com/p/CgPu2zYHl5m/",
        )
        resp = await self._request(
            f"/instagram_oembed?url={post_url}&access_token={self.token}"
        )
        return [resp.json()]
