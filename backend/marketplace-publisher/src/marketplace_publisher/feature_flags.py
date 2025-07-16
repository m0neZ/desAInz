"""Access feature flags via Unleash."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from UnleashClient import UnleashClient


@lru_cache(maxsize=1)
def _client() -> UnleashClient:
    """Return a cached Unleash client instance."""
    url = os.getenv("UNLEASH_URL", "http://localhost:4242/api")
    token = os.getenv("UNLEASH_TOKEN", "")
    app_name = os.getenv("UNLEASH_APP_NAME", "desainz")
    client = UnleashClient(
        url=url, app_name=app_name, custom_headers={"Authorization": token}
    )
    client.initialize_client()
    return client


def is_enabled(flag: str, context: dict[str, Any] | None = None) -> bool:
    """Return ``True`` if ``flag`` is enabled for the given ``context``."""
    return _client().is_enabled(flag, context or {})
