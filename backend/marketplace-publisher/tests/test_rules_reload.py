"""Test dynamic reloading of marketplace rules."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterator

import pytest
from marketplace_publisher import rules
from marketplace_publisher.db import Marketplace


@pytest.fixture(autouse=True)
def _stop_watcher() -> Iterator[None]:
    """Stop the rules watcher after each test."""
    yield
    rules.stop_watching_rules()


def _write_rules(path: Path, limit: int) -> None:
    path.write_text(
        (
            "redbubble:\n"
            "  max_file_size_mb: 10\n"
            "  max_width: 100\n"
            "  max_height: 100\n"
            f"  upload_limit: {limit}\n"
        ),
        encoding="utf-8",
    )


def test_rules_reload(tmp_path: Path) -> None:
    """Verify that rules reload when the file changes."""
    rules_path = tmp_path / "rules.yaml"
    _write_rules(rules_path, 5)
    rules.load_rules(rules_path, watch=True)
    assert rules.get_upload_limit(Marketplace.redbubble) == 5

    _write_rules(rules_path, 7)
    for _ in range(10):
        if rules.get_upload_limit(Marketplace.redbubble) == 7:
            break
        time.sleep(0.1)

    assert rules.get_upload_limit(Marketplace.redbubble) == 7
