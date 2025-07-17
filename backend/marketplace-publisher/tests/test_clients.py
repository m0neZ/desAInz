"""Tests for OAuth-enabled marketplace clients."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import os

import pytest
import requests

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from marketplace_publisher import clients


def _setup_env(monkeypatch: pytest.MonkeyPatch, prefix: str) -> None:
    """Set environment variables for a client."""
    monkeypatch.setenv(f"{prefix}_CLIENT_ID", "id")
    monkeypatch.setenv(f"{prefix}_CLIENT_SECRET", "secret")
    monkeypatch.setenv(f"{prefix}_TOKEN_URL", "https://example.com/token")
    monkeypatch.setenv(f"{prefix}_API_KEY", "key")


@pytest.mark.parametrize(
    "client_cls,prefix,publish_url",
    [
        (clients.RedbubbleClient, "REDBUBBLE", "https://api.redbubble.com/v1/publish"),
        (
            clients.AmazonMerchClient,
            "AMAZON_MERCH",
            "https://api.amazonmerch.com/v1/publish",
        ),
        (clients.EtsyClient, "ETSY", "https://api.etsy.com/v3/publish"),
        (clients.Society6Client, "SOCIETY6", "https://api.society6.com/v1/publish"),
    ],
)
def test_publish_design_oauth(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    client_cls: Callable[[], clients.BaseClient],
    prefix: str,
    publish_url: str,
) -> None:
    """Ensure clients fetch tokens and attach auth headers."""

    _setup_env(monkeypatch, prefix)
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_post(url: str, *args: Any, **kwargs: Any) -> Any:
        calls.append((url, kwargs))

        class Resp:
            def __init__(self, data: dict[str, Any]) -> None:
                self._data = data

            def raise_for_status(self) -> None:  # noqa: D401
                """No-op to simulate successful request."""

            def json(self) -> dict[str, Any]:
                return self._data

        if url == "https://example.com/token":
            return Resp({"access_token": "tok"})
        assert kwargs["headers"]["Authorization"] == "Bearer tok"
        assert kwargs["headers"]["X-API-Key"] == "key"
        return Resp({"id": 1})

    monkeypatch.setattr(requests, "post", fake_post)

    design = tmp_path / "d.png"
    design.write_text("x")
    client = client_cls()
    listing_id = client.publish_design(design, {"title": "t"})

    assert listing_id == "1"
    assert calls[0][0] == "https://example.com/token"
    assert calls[1][0] == publish_url
