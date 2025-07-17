"""Tests for feature flag utilities."""

from __future__ import annotations

import importlib
from typing import Iterator
from unittest import mock

import pytest

from backend.shared import feature_flags


@pytest.fixture(autouse=True)  # type: ignore[misc]
def reload_module() -> Iterator[None]:
    """Reload feature_flags module after each test."""
    yield
    importlib.reload(feature_flags)


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Flags fall back to defaults when Unleash is disabled."""
    monkeypatch.delenv("UNLEASH_URL", raising=False)
    monkeypatch.delenv("UNLEASH_API_TOKEN", raising=False)
    monkeypatch.setenv("UNLEASH_DEFAULTS", '{"demo": true}')
    feature_flags.initialize()
    assert feature_flags.is_enabled("demo") is True
    assert feature_flags.is_enabled("missing") is False


def test_caching(monkeypatch: pytest.MonkeyPatch) -> None:
    """Calls to Unleash are cached for the configured TTL."""
    monkeypatch.setenv("UNLEASH_URL", "http://example.com")
    monkeypatch.setenv("UNLEASH_API_TOKEN", "tkn")
    monkeypatch.setenv("UNLEASH_CACHE_TTL", "60")
    client = mock.MagicMock()
    client.is_enabled.return_value = True
    monkeypatch.setattr(feature_flags, "UnleashClient", lambda **_: client)
    feature_flags.initialize()
    assert feature_flags.is_enabled("flag") is True
    assert feature_flags.is_enabled("flag") is True
    client.is_enabled.assert_called_once()


def test_error_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Errors from Unleash return the configured default."""
    monkeypatch.setenv("UNLEASH_URL", "http://example.com")
    monkeypatch.setenv("UNLEASH_API_TOKEN", "tkn")
    monkeypatch.setenv("UNLEASH_DEFAULTS", '{"flag": false}')
    client = mock.MagicMock()
    client.is_enabled.side_effect = RuntimeError("boom")
    monkeypatch.setattr(feature_flags, "UnleashClient", lambda **_: client)
    feature_flags.initialize()
    assert feature_flags.is_enabled("flag") is False
