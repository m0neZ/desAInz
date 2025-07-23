"""Tests for trademark checking utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import types
import sys
import enum

# Stub optional dependencies for import before loading the app modules.
dummy = types.ModuleType("dummy")
dummy.__path__ = []  # type: ignore[attr-defined]
selenium_pkg = types.ModuleType("selenium")
selenium_pkg.__path__ = []  # type: ignore[attr-defined]
webdriver_pkg = types.ModuleType("webdriver")
webdriver_pkg.__path__ = []  # type: ignore[attr-defined]
firefox_pkg = types.ModuleType("firefox")
firefox_pkg.__path__ = []  # type: ignore[attr-defined]
options_pkg = types.ModuleType("options")
options_pkg.__path__ = []  # type: ignore[attr-defined]
options_pkg.Options = object
sys.modules.setdefault("selenium", selenium_pkg)
sys.modules.setdefault("selenium.webdriver", webdriver_pkg)
sys.modules.setdefault("selenium.webdriver.firefox", firefox_pkg)
sys.modules.setdefault("selenium.webdriver.firefox.options", options_pkg)
selenium_pkg.webdriver = webdriver_pkg  # type: ignore[attr-defined]
webdriver_pkg.firefox = firefox_pkg  # type: ignore[attr-defined]
firefox_pkg.options = options_pkg  # type: ignore[attr-defined]
post_processor = types.ModuleType("post_processor")


def _noop(_img: object) -> None:
    return None


post_processor.ensure_not_nsfw = _noop
sys.modules.setdefault("mockup_generation.post_processor", post_processor)
db_stub = types.ModuleType("marketplace_publisher.db")


class Marketplace(enum.Enum):
    """Enumeration of supported marketplaces."""

    redbubble = "redbubble"


db_stub.Marketplace = Marketplace
db_stub.get_oauth_token_sync = lambda *_args, **_kwargs: None
db_stub.upsert_oauth_token_sync = lambda *_args, **_kwargs: None
sys.modules.setdefault("marketplace_publisher.db", db_stub)

import requests

import pytest

from marketplace_publisher.trademark import is_trademarked
from marketplace_publisher import publisher, db
from tests.utils import return_true, return_false


class DummyResponse:
    """Minimal response stub for ``requests``."""

    def __init__(self, json_data: dict[str, int]):
        """Store ``json_data`` for later retrieval."""
        self._json_data = json_data

    def raise_for_status(self) -> None:
        """Mimic ``requests.Response.raise_for_status``."""
        return None

    def json(self) -> dict[str, int]:
        """Return the stored JSON payload."""
        return self._json_data


@pytest.mark.parametrize("total", [0, 1])
def test_is_trademarked(monkeypatch: pytest.MonkeyPatch, total: int) -> None:
    """Check trademark detection based on API response."""

    def fake_get(*args: str, **kwargs: str) -> DummyResponse:  # noqa: ANN001
        return DummyResponse({"totalRows": total})

    monkeypatch.setattr(requests, "get", fake_get)
    assert is_trademarked("test") is (total > 0)


def test_publish_design_rejects_trademark(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Return ``trademarked`` when the title violates policy."""

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "1"

    publisher.CLIENTS[db.Marketplace.redbubble] = DummyClient()
    monkeypatch.setattr(publisher, "is_trademarked", return_true)

    design = tmp_path / "d.png"
    design.write_text("x")
    result = publisher.publish_design(
        db.Marketplace.redbubble, design, {"title": "foo"}
    )
    assert result == "trademarked"


def test_publish_design_allows_non_trademark(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Return listing ID when no trademark issues are detected."""

    class DummyClient:
        def publish_design(self, design_path: Path, metadata: dict[str, Any]) -> str:
            return "1"

    publisher.CLIENTS[db.Marketplace.redbubble] = DummyClient()
    monkeypatch.setattr(publisher, "is_trademarked", return_false)

    design = tmp_path / "d.png"
    design.write_text("x")
    result = publisher.publish_design(
        db.Marketplace.redbubble, design, {"title": "foo"}
    )
    assert result == "1"
