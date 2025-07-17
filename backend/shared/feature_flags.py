"""Feature flag utilities using Unleash with simple caching.

Flags are read from an Unleash server when configuration is available. Results
are cached for ``UNLEASH_CACHE_TTL`` seconds and fall back to values defined in
``UNLEASH_DEFAULTS`` (JSON mapping from flag names to booleans) when Unleash is
disabled or errors occur.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from UnleashClient import UnleashClient

_client: UnleashClient | None = None
_cache: dict[str, tuple[bool, float]] = {}
_cache_ttl: int = 30
_defaults: dict[str, bool] = {}


def initialize() -> None:
    """Initialize the global Unleash client if configuration is present."""
    global _client, _cache_ttl, _defaults  # noqa: PLW0603
    if _client is not None:
        return
    defaults_env = os.getenv("UNLEASH_DEFAULTS", "{}")
    try:
        _defaults = {k: bool(v) for k, v in json.loads(defaults_env).items()}
    except json.JSONDecodeError:
        _defaults = {}
    _cache_ttl = int(os.getenv("UNLEASH_CACHE_TTL", "30"))
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
    cached = _cache.get(name)
    now = time.monotonic()
    if cached and cached[1] > now:
        return cached[0]

    default = _defaults.get(name, False)

    def _fallback(_: str, __: dict[str, Any]) -> bool:
        return default

    if _client is None:
        result = default
    else:
        try:
            result = _client.is_enabled(name, context or {}, _fallback)
        except Exception:
            result = default

    _cache[name] = (result, now + _cache_ttl)
    return result


def shutdown() -> None:
    """Gracefully close the Unleash client."""
    if _client is not None:
        _client.destroy()
