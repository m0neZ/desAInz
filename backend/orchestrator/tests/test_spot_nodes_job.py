"""Tests for the maintain spot nodes job."""

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

from orchestrator.jobs import maintain_spot_nodes_job  # noqa: E402


def test_maintain_spot_nodes_job(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the maintain nodes utility is invoked."""
    calls: list[str] = []

    def fake_maintain(*args: object, **kwargs: object) -> None:
        calls.append("called")

    monkeypatch.setattr("scripts.manage_spot_instances.maintain_nodes", fake_maintain)
    monkeypatch.setenv("SPOT_AMI_ID", "ami-1")
    monkeypatch.setenv("SPOT_INSTANCE_TYPE", "t3.micro")
    monkeypatch.setenv("SPOT_KEY_NAME", "k")
    monkeypatch.setenv("SPOT_SECURITY_GROUP", "sg")
    monkeypatch.setenv("SPOT_SUBNET_ID", "sn")

    instance = DagsterInstance.ephemeral()
    result = maintain_spot_nodes_job.execute_in_process(instance=instance)
    assert result.success
    assert calls == ["called"]
