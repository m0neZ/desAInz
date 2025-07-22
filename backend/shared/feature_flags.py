"""
Feature flag utilities supporting LaunchDarkly, Redis and env overrides.

Results are cached both in memory and Redis for the configured TTL to avoid repeated
provider lookups.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, cast

import redis
from ldclient import LDClient
from ldclient.config import Config
from ldclient.context import Context
from UnleashClient import UnleashClient

_unleash_client: UnleashClient | None = None
_ld_client: LDClient | None = None
_redis: redis.Redis | None = None
_cache: dict[str, tuple[bool, float]] = {}
_cache_ttl: int = 30
_cache_prefix = "ff_cache:"
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
        _ld_client = LDClient(config=Config(sdk_key))


def is_enabled(name: str, context: dict[str, Any] | None = None) -> bool:
    """Return ``True`` if the feature ``name`` is enabled."""
    cached = _cache.get(name)
    now = time.monotonic()
    if cached and cached[1] > now:
        return cached[0]

    if _redis is not None:
        try:
            raw = _redis.get(f"{_cache_prefix}{name}")
            if isinstance(raw, str):
                cached_result = raw == "1"
                _cache[name] = (cached_result, now + _cache_ttl)
                return cached_result
        except Exception:
            pass

    default = _defaults.get(name, False)
    result: bool | None = None

    if name in _env_flags:
        result = _env_flags[name]

    if result is None and _redis is not None:
        try:
            raw = _redis.get(name)
            if isinstance(raw, str):
                result = raw.lower() in {"1", "true", "yes"}
        except Exception:
            result = None

    if result is None and _ld_client is not None:
        try:
            ctx = context if isinstance(context, Context) else Context.create("server")
            result = bool(_ld_client.variation(name, ctx, default))
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
    if _redis is not None:
        try:
            _redis.setex(f"{_cache_prefix}{name}", _cache_ttl, "1" if result else "0")
        except Exception:
            pass
    return result


def set_flag(name: str, enabled: bool) -> None:
    """Set the override for ``name`` to ``enabled``."""
    initialize()
    if _redis is not None:
        try:
            _redis.set(name, "1" if enabled else "0")
        except Exception:
            _env_flags[name] = enabled
    else:
        _env_flags[name] = enabled
    _cache[name] = (enabled, time.monotonic() + _cache_ttl)


def list_flags() -> dict[str, bool]:
    """Return current values for all known flags."""
    initialize()
    names = set(_defaults) | set(_env_flags)
    if _redis is not None:
        try:
            keys = _redis.keys("*")
            if isinstance(keys, list):
                for k in keys:
                    key = str(k)
                    if not key.startswith(_cache_prefix):
                        names.add(key)
        except Exception:
            pass
    return {name: is_enabled(name) for name in names}


def shutdown() -> None:
    """Gracefully close any open clients."""
    if _unleash_client is not None:
        _unleash_client.destroy()
    if _ld_client is not None:
        cast(Any, _ld_client).close()
