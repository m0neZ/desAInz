"""Tests for background metrics collection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from backend.optimization import api as opt_api
from backend.optimization.storage import MetricsStore


def _patch_psutil(monkeypatch: Any) -> None:
    """Stub out ``psutil`` functions used when collecting metrics."""

    class Mem:
        used = 100 * 1024 * 1024

    class Disk:
        used = 200 * 1024 * 1024

    monkeypatch.setattr(opt_api.psutil, "cpu_percent", lambda: 20.0)
    monkeypatch.setattr(opt_api.psutil, "virtual_memory", lambda: Mem())
    monkeypatch.setattr(opt_api.psutil, "disk_usage", lambda _: Disk())


def test_record_resource_usage_persists_metric(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """``record_resource_usage`` stores a metric in ``MetricsStore``."""

    _patch_psutil(monkeypatch)
    store = MetricsStore(f"sqlite:///{tmp_path/'metrics.db'}")
    opt_api.record_resource_usage(store)
    metrics = store.get_recent_metrics(1)
    assert metrics[0].cpu_percent == 20.0
    assert metrics[0].memory_mb == 100.0
    assert metrics[0].disk_usage_mb == 200.0


def test_recent_metrics_endpoint(tmp_path: Path, monkeypatch: Any) -> None:
    """The ``/metrics/recent`` endpoint returns the latest samples."""

    _patch_psutil(monkeypatch)
    opt_api.store = MetricsStore(f"sqlite:///{tmp_path/'metrics.db'}")
    client = TestClient(opt_api.app)

    opt_api.record_resource_usage()  # first metric
    opt_api.record_resource_usage()  # second metric

    resp = client.get("/metrics/recent", params={"limit": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["cpu_percent"] == 20.0
