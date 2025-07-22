"""Tests for queue backlog alert logic."""

from __future__ import annotations

from typing import Any
from pathlib import Path
import sys
import types

import fakeredis

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))


def _import_main(monkeypatch: Any) -> Any:
    monkeypatch.setitem(
        sys.modules,
        "psycopg2",
        types.SimpleNamespace(connect=lambda *a, **k: types.SimpleNamespace()),
    )
    from monitoring import main as main_module  # noqa: E402

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
    cfg = main.Settings(
        QUEUE_BACKLOG_THRESHOLD=1, QUEUE_BACKLOG_ALERT_COOLDOWN_MINUTES=10
    )
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
    main._check_queue_backlog(cfg)
    main._check_queue_backlog(cfg)
    main._check_queue_backlog(cfg)
    assert len(triggered) == 2
