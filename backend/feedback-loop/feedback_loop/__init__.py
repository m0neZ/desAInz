"""Feedback loop service components."""

from .ab_testing import ABTestManager, BudgetAllocation
from .weight_updater import update_weights
from .ingestion import ingest_metrics

try:  # Optional dependency
    from .scheduler import setup_scheduler
except Exception:  # pragma: no cover - scheduler may depend on optional libs
    setup_scheduler = None

__all__ = [
    "ABTestManager",
    "BudgetAllocation",
    "update_weights",
    "ingest_metrics",
    "setup_scheduler",
]
