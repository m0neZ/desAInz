from __future__ import annotations

import importlib
import os
import sys
from types import SimpleNamespace

import pytest


def test_no_selenium_flag_sets_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI flag should set SELENIUM_SKIP and run server."""
    calls: dict[str, bool] = {}
    monkeypatch.setitem(
        sys.modules,
        "uvicorn",
        SimpleNamespace(run=lambda *a, **k: calls.setdefault("called", True)),
    )
    monkeypatch.setattr(sys, "argv", ["marketplace_publisher.main", "--no-selenium"])
    os.environ.pop("SELENIUM_SKIP", None)
    import marketplace_publisher.main as module

    importlib.reload(module)
    assert os.environ["SELENIUM_SKIP"] == "1"
    assert calls.get("called")
