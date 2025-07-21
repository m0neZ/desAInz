"""Tests for OAuth-enabled marketplace clients."""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import os
from datetime import datetime

import pytest
import responses

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from marketplace_publisher import clients  # noqa: E402
from marketplace_publisher.settings import settings


def _setup_settings(monkeypatch: pytest.MonkeyPatch, prefix: str) -> None:
    """Populate settings for a client."""
    monkeypatch.setattr(settings, f"{prefix.lower()}_client_id", "id", raising=False)
    monkeypatch.setattr(
        settings, f"{prefix.lower()}_client_secret", "secret", raising=False
    )
    monkeypatch.setattr(
        settings,
        f"{prefix.lower()}_token_url",
        "https://example.com/token",
        raising=False,
    )
    monkeypatch.setattr(settings, f"{prefix.lower()}_api_key", "key", raising=False)


@pytest.mark.parametrize(
    "client_cls,prefix,publish_url",
    [
        (clients.RedbubbleClient, "redbubble", "https://api.redbubble.com/v1/publish"),
        (
            clients.AmazonMerchClient,
            "amazon_merch",
            "https://merch.amazon.com/api/publish",
        ),
        (clients.EtsyClient, "etsy", "https://openapi.etsy.com/v3/application/publish"),
        (clients.Society6Client, "society6", "https://api.society6.com/v1/publish"),
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

    _setup_settings(monkeypatch, prefix)
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


def test_token_refresh_on_expiry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Ensure tokens are refreshed when expired."""

    _setup_settings(monkeypatch, "redbubble")
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://example.com/token",
            json={"access_token": "tok1", "expires_in": 0},
        )
        rsps.add(
            responses.POST,
            "https://api.redbubble.com/v1/publish",
            json={"id": 1},
        )
        rsps.add(
            responses.POST,
            "https://example.com/token",
            json={"access_token": "tok2"},
        )
        rsps.add(
            responses.POST,
            "https://api.redbubble.com/v1/publish",
            json={"id": 2},
        )

        design = tmp_path / "d.png"
        design.write_text("x")
        client = clients.RedbubbleClient()
        assert client.publish_design(design, {}) == "1"
        assert client.publish_design(design, {}) == "2"
        assert rsps.calls[0].request.url == "https://example.com/token"
        assert rsps.calls[2].request.url == "https://example.com/token"


def test_refresh_on_unauthorized(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Refresh token when API returns 401."""

    _setup_settings(monkeypatch, "redbubble")
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://example.com/token",
            json={"access_token": "tok1"},
        )
        rsps.add(
            responses.POST,
            "https://api.redbubble.com/v1/publish",
            status=401,
        )
        rsps.add(
            responses.POST,
            "https://example.com/token",
            json={"access_token": "tok2"},
        )
        rsps.add(
            responses.POST,
            "https://api.redbubble.com/v1/publish",
            json={"id": 2},
        )

        design = tmp_path / "d.png"
        design.write_text("x")
        client = clients.RedbubbleClient()
        assert client.publish_design(design, {}) == "2"
        assert rsps.calls[0].request.url == "https://example.com/token"
        assert rsps.calls[1].request.status_code == 401
        assert rsps.calls[2].request.url == "https://example.com/token"


@pytest.mark.asyncio()
async def test_tokens_persisted_and_reused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Load tokens from database and refresh when expired."""

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from marketplace_publisher import db

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    await db.init_db()

    _setup_settings(monkeypatch, "redbubble")

    async with session_factory() as session:
        await db.upsert_oauth_token(
            session,
            db.Marketplace.redbubble,
            "old",
            "refresh",
            datetime.utcnow(),
        )

    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://example.com/token",
            json={"access_token": "new"},
        )
        rsps.add(
            responses.POST,
            "https://api.redbubble.com/v1/publish",
            json={"id": 3},
        )

        design = tmp_path / "d.png"
        design.write_text("x")
        client = clients.RedbubbleClient()
        assert client.publish_design(design, {}) == "3"

    async with session_factory() as session:
        token = await db.get_oauth_token(session, db.Marketplace.redbubble)
        assert token is not None
        assert token.access_token == "new"


@pytest.mark.asyncio()
async def test_oauth_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test OAuth login and callback storing tokens."""

    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from marketplace_publisher import db, main

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    import importlib
    import backend.shared.db as shared_db

    importlib.reload(shared_db)
    shared_db.Base.metadata.create_all(shared_db.engine)
    pytest.run = lambda *a, **k: None  # placeholder

    monkeypatch.setattr(main, "app", main.app)
    monkeypatch.setattr(main.publisher, "CLIENTS", main.publisher.CLIENTS)

    _setup_settings(monkeypatch, "redbubble")

    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://example.com/token",
            json={"access_token": "tok", "refresh_token": "r"},
        )
        with TestClient(main.app) as client:
            resp = client.get("/oauth/redbubble")
            assert resp.status_code == 200
            state = resp.json()["authorization_url"].split("state=")[1]
            resp = client.get(f"/oauth/redbubble/callback?code=1&state={state}")
            assert resp.status_code == 200

    async with session_factory() as session:
        token = await db.get_oauth_token(session, db.Marketplace.redbubble)
        assert token is not None
        assert token.refresh_token == "r"
