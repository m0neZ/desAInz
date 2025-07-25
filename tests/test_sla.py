"""Tests for SLA monitoring logic."""

from __future__ import annotations

from pathlib import Path
import sys
import types
import os
from datetime import UTC, datetime

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "backend" / "monitoring" / "src")
)

otel_mod = types.ModuleType("opentelemetry.exporter.otlp.proto.http.trace_exporter")
otel_mod.OTLPSpanExporter = object  # type: ignore[attr-defined]
sys.modules.setdefault(
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    otel_mod,
)
os.makedirs("/run/secrets", exist_ok=True)

import pytest


def _import_main(monkeypatch: pytest.MonkeyPatch):
    """Import ``monitoring.main`` with database connections patched."""
    monkeypatch.setitem(
        sys.modules,
        "psycopg2",
        types.SimpleNamespace(connect=lambda *a, **k: types.SimpleNamespace()),
    )
    from monitoring import main as main_module  # noqa: E402

    return main_module


def test_check_sla_triggers_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    """Alert should be triggered when average latency is high."""
    triggered = {}

    def fake_trigger(duration):
        triggered["hours"] = duration

    main = _import_main(monkeypatch)
    monkeypatch.setattr(main, "trigger_sla_violation", fake_trigger)

    recorded = []

    def fake_record() -> list[float]:
        metrics = [
            main.PublishLatencyMetric(1, datetime.now(UTC), 7200.0),
            main.PublishLatencyMetric(1, datetime.now(UTC), 10800.0),
        ]
        main.metrics_store.add_latencies(metrics)
        return [m.latency_seconds for m in metrics]

    class DummyStore:
        def add_latency(self, metric):
            recorded.append(metric)

        def add_latencies(self, metrics):
            recorded.extend(metrics)

    monkeypatch.setattr(main, "metrics_store", DummyStore())
    monkeypatch.setattr(main, "_record_latencies", fake_record)
    cfg = main.Settings(SLA_THRESHOLD_HOURS=2)
    avg = main._check_sla(cfg)
    assert triggered["hours"] == avg / 3600
    assert avg == 9000.0
    assert len(recorded) == 2


def test_check_sla_below_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    """No alert should be sent when average latency is low."""
    main = _import_main(monkeypatch)
    monkeypatch.setattr(main, "_record_latencies", lambda: [60.0, 30.0])
    monkeypatch.setattr(main, "metrics_store", object())
    cfg = main.Settings(SLA_THRESHOLD_HOURS=2)
    called = []

    def fake_trigger(duration):
        called.append(duration)

    monkeypatch.setattr(main, "trigger_sla_violation", fake_trigger)
    avg = main._check_sla(cfg)
    assert called == []
    assert avg == 45.0
