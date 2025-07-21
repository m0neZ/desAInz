"""Tests for the listings synchronization job."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from dagster import DagsterInstance

ROOT = Path(__file__).resolve().parents[3]
ORCHESTRATOR_PATH = ROOT / "backend" / "orchestrator"
sys.path.append(str(ORCHESTRATOR_PATH))  # noqa: E402
MONITORING_SRC = ROOT / "backend" / "monitoring" / "src"
sys.path.append(str(MONITORING_SRC))  # noqa: E402

from orchestrator.jobs import sync_listings_job  # noqa: E402
from orchestrator.schedules import daily_listing_sync_schedule  # noqa: E402


def test_sync_listings_job_structure() -> None:
    """Ensure the job calls the listing sync op."""
    ops = [op.name for op in sync_listings_job.graph.node_dict.values()]
    assert ops == ["sync_listing_states_op"]


def test_daily_listing_sync_schedule() -> None:
    """Schedule should run the listings sync job daily."""
    assert daily_listing_sync_schedule.job == sync_listings_job
    assert daily_listing_sync_schedule.cron_schedule == "0 2 * * *"


def test_sync_listings_job_exec(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the job and ensure the sync function executes."""
    calls: list[str] = []

    def fake_main() -> None:
        calls.append("called")

    monkeypatch.setattr("scripts.listing_sync.main", fake_main)
    instance = DagsterInstance.ephemeral()
    result = sync_listings_job.execute_in_process(instance=instance)
    assert result.success
    assert calls == ["called"]
