"""Tests for queue backlog alert logic."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import fakeredis

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from monitoring import main as main_module  # noqa: E402


def _import_main(monkeypatch: Any) -> Any:
    monkeypatch.setitem(
        sys.modules,
        "psycopg2",
        types.SimpleNamespace(connect=lambda *a, **k: types.SimpleNamespace()),
    )
    return main_module


def test_queue_backlog_respects_cooldown(monkeypatch: Any) -> None:
    """Alerts are throttled according to cooldown settings."""
    main = _import_main(monkeypatch)
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(main.redis.Redis, "from_url", lambda *_a, **_k: fake)
    monkeypatch.setattr(main, "sync_get", lambda key: fake.get(key))
    monkeypatch.setattr(
        main, "sync_set", lambda key, value, ttl=None: fake.set(key, value)
    )
    monkeypatch.setattr(main.settings, "queue_backlog_threshold", 1)
    monkeypatch.setattr(main.settings, "queue_backlog_alert_cooldown_minutes", 10)
    fake.rpush("celery", b"job")
    times = iter([1000.0, 1000.0, 1000.0 + 601])

    def fake_time() -> float:
        try:
            return next(times)
        except StopIteration:  # pragma: no cover - extra calls
            return 1000.0 + 601

    monkeypatch.setattr(main.time, "time", fake_time)
    triggered: list[int] = []

    monkeypatch.setattr(
        main, "trigger_queue_backlog", lambda length: triggered.append(length)
    )
    main._check_queue_backlog()
    main._check_queue_backlog()
    main._check_queue_backlog()
    assert len(triggered) == 2
