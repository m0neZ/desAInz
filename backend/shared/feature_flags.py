"""Feature flag utilities using Unleash."""

from __future__ import annotations

import os
from typing import Any

from UnleashClient import UnleashClient

_client: UnleashClient | None = None


def initialize() -> None:
    """Initialize the global Unleash client if configuration is present."""
    global _client  # noqa: PLW0603
    if _client is not None:
        return
    url = os.getenv("UNLEASH_URL")
    token = os.getenv("UNLEASH_API_TOKEN")
    app_name = os.getenv("UNLEASH_APP_NAME", "desainz")
    if url and token:
        _client = UnleashClient(
            url=url, app_name=app_name, custom_headers={"Authorization": token}
        )
        _client.initialize_client()


def is_enabled(name: str, context: dict[str, Any] | None = None) -> bool:
    """Return ``True`` if the feature ``name`` is enabled."""
    if _client is None:
        return False
    return _client.is_enabled(name, context or {})


def shutdown() -> None:
    """Gracefully close the Unleash client."""
    if _client is not None:
        _client.destroy()
