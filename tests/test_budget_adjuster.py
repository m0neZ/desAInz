"""Tests for ThompsonBudgetAdjuster."""

from feedback_loop.budget_adjuster import ThompsonBudgetAdjuster


def test_budget_adjustment_monopolizes_budget() -> None:
    """Budget should go entirely to sampled variant."""
    adjuster = ThompsonBudgetAdjuster(
        priors={"A": (1, 1), "B": (1, 1)}, budgets={"A": 50.0, "B": 50.0}
    )
    adjuster.update("A", 1)
    adjusted = adjuster.adjust_budgets()
    assert sum(adjusted.values()) == 100.0
    assert list(adjusted.values()).count(0.0) == 1
