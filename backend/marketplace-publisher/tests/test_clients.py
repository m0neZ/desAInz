"""Tests for OAuth-enabled marketplace clients."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import os

import pytest
import responses

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
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://example.com/token",
            json={"access_token": "tok"},
        )
        rsps.add(
            responses.POST,
            publish_url,
            json={"id": 1},
        )

        design = tmp_path / "d.png"
        design.write_text("x")
        client = client_cls()
        listing_id = client.publish_design(design, {"title": "t"})

        assert listing_id == "1"
        assert rsps.calls[0].request.url == "https://example.com/token"
        assert rsps.calls[1].request.url == publish_url
        assert rsps.calls[1].request.headers["Authorization"] == "Bearer tok"
        assert rsps.calls[1].request.headers["X-API-Key"] == "key"
