"""Feature flag utilities supporting LaunchDarkly and environment overrides."""

from __future__ import annotations

import json
import os
import time
from typing import Any

import redis
from UnleashClient import UnleashClient
from ldclient import LDClient

_unleash_client: UnleashClient | None = None
_ld_client: LDClient | None = None
_redis: redis.Redis[str] | None = None
_cache: dict[str, tuple[bool, float]] = {}
_cache_ttl: int = 30
_defaults: dict[str, bool] = {}
_env_flags: dict[str, bool] = {}


def initialize() -> None:
    """Initialize clients and cache settings from the environment."""
    global _unleash_client, _ld_client, _redis, _cache_ttl, _defaults, _env_flags
    if _unleash_client or _ld_client:
        return

    env_flags = os.getenv("FEATURE_FLAGS", "{}")
    try:
        _env_flags = {k: bool(v) for k, v in json.loads(env_flags).items()}
    except json.JSONDecodeError:
        _env_flags = {}

    defaults_env = os.getenv("FEATURE_FLAGS_DEFAULTS", "{}")
    try:
        _defaults = {k: bool(v) for k, v in json.loads(defaults_env).items()}
    except json.JSONDecodeError:
        _defaults = {}

    _cache_ttl = int(os.getenv("FEATURE_FLAGS_CACHE_TTL", "30"))

    redis_url = os.getenv("FEATURE_FLAGS_REDIS_URL")
    if redis_url:
        _redis = redis.Redis(redis_url, decode_responses=True)

    url = os.getenv("UNLEASH_URL")
    token = os.getenv("UNLEASH_API_TOKEN")
    app_name = os.getenv("UNLEASH_APP_NAME", "desainz")
    if url and token:
        _unleash_client = UnleashClient(
            url=url, app_name=app_name, custom_headers={"Authorization": token}
        )
        _unleash_client.initialize_client()

    sdk_key = os.getenv("LAUNCHDARKLY_SDK_KEY")
    if sdk_key:
        _ld_client = LDClient(sdk_key)


def is_enabled(name: str, context: dict[str, Any] | None = None) -> bool:
    """Return ``True`` if the feature ``name`` is enabled."""
    cached = _cache.get(name)
    now = time.monotonic()
    if cached and cached[1] > now:
        return cached[0]

    default = _defaults.get(name, False)
    result = None

    if name in _env_flags:
        result = _env_flags[name]

    if result is None and _redis is not None:
        try:
            raw = _redis.get(name)
            if raw is not None:
                result = raw.lower() in {"1", "true", "yes"}
        except Exception:
            result = None

    if result is None and _ld_client is not None:
        try:
            result = bool(
                _ld_client.variation(name, context or {"key": "server"}, default)
            )
        except Exception:
            result = default

    if result is None and _unleash_client is not None:
        try:
            result = _unleash_client.is_enabled(name, context or {}, lambda *_: default)
        except Exception:
            result = default

    if result is None:
        result = default

    _cache[name] = (result, now + _cache_ttl)
    return result


def shutdown() -> None:
    """Gracefully close any open clients."""
    if _unleash_client is not None:
        _unleash_client.destroy()
    if _ld_client is not None:
        _ld_client.close()
