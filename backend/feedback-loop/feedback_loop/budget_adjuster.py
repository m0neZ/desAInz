"""Promotion budget adjustment using Thompson Sampling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np


@dataclass
class ThompsonBudgetAdjuster:
    """Adjust promotion budgets based on A/B test results."""

    priors: Dict[str, tuple[float, float]]
    budgets: Dict[str, float]
    results: Dict[str, list[int]] = field(default_factory=dict)

    def update(self, variant: str, success: int) -> None:
        """Record success/failure for a variant."""
        self.results.setdefault(variant, []).append(success)

    def sample(self) -> str:
        """Sample a variant using Thompson Sampling."""
        samples = {}
        for variant, prior in self.priors.items():
            alpha, beta = prior
            successes = sum(self.results.get(variant, []))
            failures = len(self.results.get(variant, [])) - successes
            samples[variant] = np.random.beta(alpha + successes, beta + failures)
        return max(samples, key=lambda k: samples[k])

    def adjust_budgets(self) -> Dict[str, float]:
        """Adjust budgets proportionally based on sampled variant."""
        chosen = self.sample()
        total_budget = sum(self.budgets.values())
        adjusted = {k: 0.0 for k in self.budgets}
        adjusted[chosen] = total_budget
        self.budgets = adjusted
        return adjusted
