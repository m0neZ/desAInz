"""Tests for latency caching logic."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import fakeredis

# Add monitoring source path
sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "monitoring" / "src")
)

import monitoring.metrics_store as ms  # noqa: E402


def _import_main(monkeypatch):
    """Import monitoring.main with database connections patched."""
    monkeypatch.setitem(
        sys.modules,
        "psycopg2",
        types.SimpleNamespace(connect=lambda *a, **k: types.SimpleNamespace()),
    )
    from monitoring import main as main_module  # noqa: E402

    return main_module


def test_average_latency_cached(monkeypatch):
    """Average latency is cached between calls."""
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(ms, "sync_delete", lambda key: fake.delete(key))
    main = _import_main(monkeypatch)
    monkeypatch.setattr(main, "sync_get", lambda key: fake.get(key))
    monkeypatch.setattr(
        main,
        "sync_set",
        lambda key, value, ttl=None: (
            fake.setex(key, ttl, value) if ttl else fake.set(key, value)
        ),
    )
    calls: list[int] = []

    def fake_record() -> list[float]:
        calls.append(1)
        return [60.0, 120.0]

    monkeypatch.setattr(main, "_record_latencies", fake_record)
    first = main.get_average_latency()
    second = main.get_average_latency()
    assert first == 90.0
    assert second == 90.0
    assert len(calls) == 1


def test_cache_invalidated_on_new_metric(monkeypatch):
    """Cache is cleared when metrics are recorded."""
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(ms, "sync_delete", lambda key: fake.delete(key))
    main = _import_main(monkeypatch)
    monkeypatch.setattr(main, "sync_get", lambda key: fake.get(key))
    monkeypatch.setattr(
        main,
        "sync_set",
        lambda key, value, ttl=None: (
            fake.setex(key, ttl, value) if ttl else fake.set(key, value)
        ),
    )
    calls: list[int] = []

    def fake_record() -> list[float]:
        calls.append(1)
        return [30.0, 60.0]

    monkeypatch.setattr(main, "_record_latencies", fake_record)
    main.get_average_latency()
    assert len(calls) == 1
    ms.invalidate_latency_cache()
    main.get_average_latency()
    assert len(calls) == 2
