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


def test_record_summary(tmp_path) -> None:
    """Daily summary aggregates conversions for each variant."""
    manager = ABTestManager(database_url=f"sqlite:///{tmp_path}/abtest.db")
    for _ in range(3):
        manager.record_result("A", True)
    for _ in range(2):
        manager.record_result("B", True)
    manager.record_result("B", False)

    manager.record_summary()

    with manager.session_scope() as session:
        summary = session.query(manager.daily_summary_class).one()
        assert summary.conversions_a == 3
        assert summary.conversions_b == 2
