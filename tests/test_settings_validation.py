"""Tests for environment variable validation in settings classes."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]


def _load_settings(path: Path) -> type:
    import importlib.util

    spec = importlib.util.spec_from_file_location("settings", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.path.insert(0, str(ROOT))

    dummy_shared = ModuleType("backend.shared.config")
    dummy_shared.settings = SimpleNamespace(
        redis_url="redis://localhost:6379/0",
        database_url="sqlite:///db",
    )
    sys.modules.setdefault("backend.shared.config", dummy_shared)
    backend_shared = ModuleType("backend.shared")
    backend_shared.config = dummy_shared
    sys.modules.setdefault("backend.shared", backend_shared)
    sys.modules.setdefault("selenium.webdriver", ModuleType("selenium.webdriver"))
    sys.modules["selenium.webdriver"].Firefox = lambda *a, **k: SimpleNamespace(
        get=lambda *a, **k: None
    )
    sys.modules.setdefault(
        "opentelemetry.sdk.resources", ModuleType("opentelemetry.sdk.resources")
    )
    sys.modules.setdefault("opentelemetry.trace", ModuleType("opentelemetry.trace"))
    sys.modules.setdefault(
        "opentelemetry.instrumentation.fastapi",
        ModuleType("opentelemetry.instrumentation.fastapi"),
    )

    spec.loader.exec_module(module)
    return module.Settings


SISettings = _load_settings(
    ROOT / "backend" / "signal-ingestion" / "src" / "signal_ingestion" / "settings.py"
)
MGSettings = _load_settings(
    ROOT / "backend" / "mockup-generation" / "mockup_generation" / "settings.py"
)
AGSettings = _load_settings(
    ROOT / "backend" / "api-gateway" / "src" / "api_gateway" / "settings.py"
)
MPSettings = _load_settings(
    ROOT
    / "backend"
    / "marketplace-publisher"
    / "src"
    / "marketplace_publisher"
    / "settings.py"
)


def test_signal_ingestion_invalid_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid ingest interval should raise a ``ValidationError``."""
    monkeypatch.setenv("INGEST_INTERVAL_MINUTES", "0")
    with pytest.raises(ValidationError):
        SISettings()


def test_mockup_generation_invalid_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unsupported provider names should be rejected."""
    monkeypatch.setenv("FALLBACK_PROVIDER", "bogus")
    with pytest.raises(ValidationError):
        MGSettings()


def test_api_gateway_invalid_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    """An invalid Redis URL should raise ``ValidationError``."""
    monkeypatch.setenv("REDIS_URL", "not a url")
    with pytest.raises(ValidationError):
        AGSettings()


def test_marketplace_invalid_webhook(monkeypatch: pytest.MonkeyPatch) -> None:
    """Webhook URLs must be valid HTTP URLs."""
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "not-a-url")
    with pytest.raises(ValidationError):
        MPSettings()
