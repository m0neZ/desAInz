"""Test automatic reloading of marketplace rules."""

from __future__ import annotations

import sys
import time
import types
from enum import Enum
from pathlib import Path
from typing import Iterator

sys.path.append(
    str(
        Path(__file__).resolve().parents[1]
        / "backend"
        / "marketplace-publisher"
        / "src"
    )
)


class _Marketplace(str, Enum):
    redbubble = "redbubble"


stub_db = types.ModuleType("marketplace_publisher.db")
stub_db.Marketplace = _Marketplace  # type: ignore[attr-defined]
sys.modules["marketplace_publisher.db"] = stub_db

import pytest
from marketplace_publisher import rules

Marketplace = _Marketplace


@pytest.fixture(autouse=True)  # type: ignore[misc]
def _stop_watcher() -> Iterator[None]:
    """Stop watcher after each test."""
    yield
    rules.stop_watching_rules()


def _write_rules(path: Path, limit: int) -> None:
    path.write_text(
        (
            "redbubble:\n"
            f"  max_file_size_mb: 10\n"
            f"  max_width: 100\n"
            f"  max_height: 100\n"
            f"  upload_limit: {limit}\n"
        ),
        encoding="utf-8",
    )


def test_reload_on_change(tmp_path: Path) -> None:
    """Rules should reload when the file changes."""
    rules_path = tmp_path / "rules.yaml"
    _write_rules(rules_path, 5)
    rules.load_rules(rules_path, watch=True)
    assert rules.get_upload_limit(Marketplace.redbubble) == 5

    _write_rules(rules_path, 7)
    # give watchdog some time to process the event
    for _ in range(10):
        if rules.get_upload_limit(Marketplace.redbubble) == 7:
            break
        time.sleep(0.1)

    assert rules.get_upload_limit(Marketplace.redbubble) == 7
