"""Feature flag helpers using Unleash."""

from __future__ import annotations

from typing import Any

from UnleashClient import UnleashClient


client: UnleashClient | None = None


def init(url: str | None, token: str | None, environment: str, app_name: str) -> None:
    """Initialize the global Unleash client."""
    global client
    if url:
        client = UnleashClient(
            url=url,
            app_name=app_name,
            custom_headers={"Authorization": token} if token else None,
            environment=environment,
        )
        client.initialize_client()


def shutdown() -> None:
    """Stop the Unleash client."""
    if client:
        client.destroy()


def is_enabled(flag: str, context: dict[str, Any] | None = None) -> bool:
    """Return True if ``flag`` is enabled."""
    if client:
        return client.is_enabled(flag, context)
    return False
