"""VCR tests for marketplace API clients."""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import http.server
import socketserver
import threading
import pytest
import vcr
import sys
from types import ModuleType, SimpleNamespace
from enum import Enum

_options_mod = ModuleType("options")
setattr(_options_mod, "Options", object)
sys.modules.setdefault("selenium.webdriver.firefox.options", _options_mod)
_pgvector_mod = ModuleType("pgvector.sqlalchemy")


class _Vector:
    def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
        """Lightweight stub of ``Vector``."""


setattr(_pgvector_mod, "Vector", _Vector)
sys.modules.setdefault("pgvector.sqlalchemy", _pgvector_mod)

_db_stub = ModuleType("marketplace_publisher.db")


class Marketplace(str, Enum):
    """Stub enumeration of marketplaces."""

    redbubble = "redbubble"
    amazon_merch = "amazon_merch"
    etsy = "etsy"
    society6 = "society6"
    zazzle = "zazzle"


setattr(_db_stub, "Marketplace", Marketplace)
setattr(_db_stub, "get_oauth_token_sync", lambda *a, **k: None)
setattr(_db_stub, "upsert_oauth_token_sync", lambda *a, **k: None)
sys.modules.setdefault("marketplace_publisher.db", _db_stub)
_watchdog_events = ModuleType("watchdog.events")
setattr(_watchdog_events, "FileSystemEventHandler", object)
sys.modules.setdefault("watchdog.events", _watchdog_events)
_watchdog_observers = ModuleType("watchdog.observers")
setattr(_watchdog_observers, "Observer", object)
sys.modules.setdefault("watchdog.observers", _watchdog_observers)

_watchdog_events = ModuleType("watchdog.events")
setattr(_watchdog_events, "FileSystemEventHandler", object)
sys.modules.setdefault("watchdog.events", _watchdog_events)

from marketplace_publisher import clients
from marketplace_publisher.settings import settings


def _setup_settings(
    monkeypatch: pytest.MonkeyPatch, prefix: str, token_url: str
) -> None:
    """Populate settings for a client with ``token_url``."""
    monkeypatch.setattr(settings, f"{prefix.lower()}_client_id", "id", raising=False)
    monkeypatch.setattr(
        settings, f"{prefix.lower()}_client_secret", "secret", raising=False
    )
    monkeypatch.setattr(
        settings, f"{prefix.lower()}_token_url", token_url, raising=False
    )
    monkeypatch.setattr(settings, f"{prefix.lower()}_api_key", "key", raising=False)


class _Handler(http.server.BaseHTTPRequestHandler):
    """Serve token, publish and metrics responses."""

    def do_POST(self) -> None:  # noqa: D401
        if self.path == "/token":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"access_token": "tok"}')
        elif self.path == "/publish":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"id": 1}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self) -> None:  # noqa: D401
        if self.path == "/metrics/1":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"views": 1}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args: object) -> None:  # noqa: D401
        return None


@pytest.mark.parametrize(
    "client_cls,prefix",
    [
        (clients.RedbubbleClient, "redbubble"),
        (clients.AmazonMerchClient, "amazon_merch"),
        (clients.EtsyClient, "etsy"),
        (clients.Society6Client, "society6"),
        (clients.ZazzleClient, "zazzle"),
    ],
)
def test_client_publish_and_metrics_vcr(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    client_cls: Callable[[], clients.BaseClient],
    prefix: str,
) -> None:
    """Record publish and metrics calls to sandbox endpoints."""

    with socketserver.TCPServer(("127.0.0.1", 0), _Handler) as srv:
        thread = threading.Thread(target=srv.serve_forever)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{srv.server_address[1]}"
            _setup_settings(monkeypatch, prefix, f"{base_url}/token")
            client = client_cls()
            client.publish_url = f"{base_url}/publish"
            client.metrics_path_template = f"{base_url}/metrics/{{listing_id}}"

            design = tmp_path / "design.png"
            design.write_text("x")

            cassette_path = (
                Path(__file__).with_name("cassettes") / f"{prefix}_client.yaml"
            )
            with vcr.use_cassette(str(cassette_path), record_mode="new_episodes"):
                listing_id = client.publish_design(design, {"title": "t"})
                metrics = client.get_listing_metrics(1)
        finally:
            srv.shutdown()
            thread.join()

    assert listing_id == "1"
    assert metrics == {"views": 1}
