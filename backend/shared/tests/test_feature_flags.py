"""Tests for feature flag utilities."""

from __future__ import annotations

import importlib
from typing import Iterator
from unittest import mock

import fakeredis

import pytest

from backend.shared import feature_flags


@pytest.fixture(autouse=True)  # type: ignore[misc]
def reload_module() -> Iterator[None]:
    """Reload feature_flags module after each test."""
    yield
    importlib.reload(feature_flags)


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flags fall back to defaults when Unleash is disabled."""
    monkeypatch.delenv("LAUNCHDARKLY_SDK_KEY", raising=False)
    monkeypatch.delenv("FEATURE_FLAGS_REDIS_URL", raising=False)
    monkeypatch.setenv("FEATURE_FLAGS_DEFAULTS", '{"demo": true}')
    feature_flags.initialize()
    assert feature_flags.is_enabled("demo") is True
    assert feature_flags.is_enabled("missing") is False


def test_caching(monkeypatch: pytest.MonkeyPatch) -> None:
    """Calls to providers are cached for the configured TTL."""
    monkeypatch.setenv("LAUNCHDARKLY_SDK_KEY", "sdk")
    monkeypatch.setenv("FEATURE_FLAGS_CACHE_TTL", "60")
    client = mock.MagicMock()
    client.variation.return_value = True
    monkeypatch.setattr(feature_flags, "LDClient", lambda *_, **__: client)
    feature_flags.initialize()
    assert feature_flags.is_enabled("flag") is True
    assert feature_flags.is_enabled("flag") is True
    client.variation.assert_called_once()


def test_error_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Errors from providers return the configured default."""
    monkeypatch.setenv("LAUNCHDARKLY_SDK_KEY", "sdk")
    monkeypatch.setenv("FEATURE_FLAGS_DEFAULTS", '{"flag": false}')
    client = mock.MagicMock()
    client.variation.side_effect = RuntimeError("boom")
    monkeypatch.setattr(feature_flags, "LDClient", lambda *_, **__: client)
    feature_flags.initialize()
    assert feature_flags.is_enabled("flag") is False


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment flags override defaults."""
    monkeypatch.setenv("FEATURE_FLAGS", '{"demo": true}')
    feature_flags.initialize()
    assert feature_flags.is_enabled("demo") is True


def test_redis_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flags are read from Redis when configured."""
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setenv("FEATURE_FLAGS_REDIS_URL", "redis://test")
    monkeypatch.setattr(feature_flags.redis, "Redis", lambda *_, **__: fake)
    fake.set("demo", "1")
    feature_flags.initialize()
    assert feature_flags.is_enabled("demo") is True


def test_redis_persistence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flags stored in Redis persist across module reloads."""
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setenv("FEATURE_FLAGS_REDIS_URL", "redis://test")
    monkeypatch.setattr(feature_flags.redis, "Redis", lambda *_, **__: fake)
    feature_flags.initialize()
    feature_flags.set_flag("demo", True)
    importlib.reload(feature_flags)
    feature_flags.initialize()
    assert feature_flags.is_enabled("demo") is True


def test_redis_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flags can be updated in Redis with sensible defaults."""
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setenv("FEATURE_FLAGS_REDIS_URL", "redis://test")
    monkeypatch.setattr(feature_flags.redis, "Redis", lambda *_, **__: fake)
    feature_flags.initialize()
    assert feature_flags.is_enabled("demo") is False
    feature_flags.set_flag("demo", True)
    assert fake.get("demo") == "1"
    assert feature_flags.is_enabled("demo") is True
    feature_flags.set_flag("demo", False)
    assert fake.get("demo") == "0"
    assert feature_flags.is_enabled("demo") is False
