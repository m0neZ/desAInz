"""Verify standardized error responses."""

# mypy: ignore-errors

import sys
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "marketplace-publisher" / "src"))
sys.path.insert(0, str(ROOT))
import types

if "selenium" not in sys.modules:
    sel = types.ModuleType("selenium")
    webdriver = types.ModuleType("webdriver")
    firefox = types.ModuleType("firefox")
    options = types.ModuleType("options")
    options.Options = object
    firefox.options = options
    webdriver.firefox = firefox
    sel.webdriver = webdriver
    sys.modules["selenium"] = sel
    sys.modules["selenium.webdriver"] = webdriver
    sys.modules["selenium.webdriver.firefox"] = firefox
    sys.modules["selenium.webdriver.firefox.options"] = options
stub_publisher = types.ModuleType("marketplace_publisher.publisher")
stub_publisher.publish_with_retry = lambda *a, **k: None
sys.modules.setdefault("marketplace_publisher.publisher", stub_publisher)
from marketplace_publisher.main import app


def test_not_found_response(monkeypatch) -> None:
    """Unknown task ID should return error schema."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    with TestClient(app) as client:
        response = client.get("/progress/9999")
        assert response.status_code == 404
        body = response.json()
        assert set(body) == {"error", "trace_id"}
        assert body["error"]
        assert body["trace_id"]
