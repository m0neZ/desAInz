"""Tests for ``SeleniumFallback`` using a mock web server."""

from __future__ import annotations

from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
from typing import Iterator
import os

import pytest
import yaml
import selenium.webdriver

from marketplace_publisher import rules
from marketplace_publisher.clients import SeleniumFallback
from marketplace_publisher.db import Marketplace

ORIG_SELENIUM_SKIP = os.getenv("SELENIUM_SKIP")


@pytest.fixture(autouse=True)
def _enable_selenium(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use the real Firefox driver unless ``SELENIUM_SKIP=1`` was set."""
    if ORIG_SELENIUM_SKIP == "1":
        pytest.skip("SELENIUM_SKIP=1")
    monkeypatch.delenv("SELENIUM_SKIP", raising=False)
    monkeypatch.setattr(
        "selenium.webdriver.Firefox",
        selenium.webdriver.Firefox,
        raising=False,
    )


@pytest.fixture()
def marketplace_form_server(tmp_path: Path) -> Iterator[str]:
    """Start a temporary HTTP server serving a simple form."""

    page = tmp_path / "form.html"
    page.write_text(
        """
        <html>
        <body>
        <input type='file' id='upload'/>
        <input type='text' id='title'/>
        <button id='submit' onclick="this.setAttribute('data-clicked','1')">Submit</button>
        </body>
        </html>
        """,
        encoding="utf-8",
    )

    handler = partial(SimpleHTTPRequestHandler, directory=tmp_path)
    server = HTTPServer(("localhost", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://localhost:{server.server_port}/{page.name}"
    finally:
        server.shutdown()
        thread.join()


def _write_rules(tmp_path: Path, url: str, bad: bool = False) -> Path:
    """Return rules file path with selectors for ``url``."""
    selectors = {
        "url": url,
        "upload_input": "#upload" if not bad else "#missing",
        "title_input": "#title",
        "submit_button": "#submit",
    }
    data = {
        "redbubble": {
            "max_file_size_mb": 10,
            "max_width": 8000,
            "max_height": 8000,
            "upload_limit": 50,
            "selectors": selectors,
        }
    }
    path = tmp_path / "rules.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


@pytest.mark.asyncio()
async def test_publish_failure_produces_artifacts(
    marketplace_form_server: str, tmp_path: Path
) -> None:
    """Verify screenshots and logs are created when publishing fails."""
    rules_path = _write_rules(tmp_path, marketplace_form_server, bad=True)
    rules.load_rules(rules_path)
    design = tmp_path / "design.png"
    design.write_text("img")
    fallback = SeleniumFallback(screenshot_dir=tmp_path)
    with pytest.raises(Exception):
        await fallback.publish(Marketplace.redbubble, design, {"title": "t"})
    assert list(tmp_path.glob("*.png"))
    assert list(tmp_path.glob("*.log"))
