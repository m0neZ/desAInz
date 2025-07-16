"""Tests for A/B test budget allocation."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from feedback_loop import ABTestManager


def test_budget_allocation(tmp_path) -> None:
    """Budget allocation should favor successful variant."""
    manager = ABTestManager(database_url=f"sqlite:///{tmp_path}/abtest.db")
    # record some results
    for _ in range(10):
        manager.record_result("A", True)
        manager.record_result("B", False)
    allocation = manager.allocate_budget(total_budget=100.0)
    assert allocation.variant_a > allocation.variant_b
