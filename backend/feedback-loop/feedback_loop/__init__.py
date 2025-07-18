"""Feedback loop service components."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Any

from .ab_testing import ABTestManager, BudgetAllocation


def _load(module: str) -> ModuleType:
    """Import a module lazily."""
    return import_module(f"feedback_loop.{module}")


def setup_scheduler(*args: Any, **kwargs: Any) -> Any:
    """Return the configured scheduler."""
    return _load("scheduler").setup_scheduler(*args, **kwargs)


def update_weights(*args: Any, **kwargs: Any) -> Any:
    """Proxy to :func:`weight_updater.update_weights`."""
    return _load("weight_updater").update_weights(*args, **kwargs)


def ingest_metrics(*args: Any, **kwargs: Any) -> Any:
    """Proxy to :func:`ingestion.ingest_metrics`."""
    return _load("ingestion").ingest_metrics(*args, **kwargs)


def fetch_marketplace_metrics(*args: Any, **kwargs: Any) -> Any:
    """Proxy to :func:`ingestion.fetch_marketplace_metrics`."""
    return _load("ingestion").fetch_marketplace_metrics(*args, **kwargs)


def store_marketplace_metrics(*args: Any, **kwargs: Any) -> Any:
    """Proxy to :func:`ingestion.store_marketplace_metrics`."""
    return _load("ingestion").store_marketplace_metrics(*args, **kwargs)


def schedule_marketplace_ingestion(*args: Any, **kwargs: Any) -> Any:
    """Proxy to :func:`ingestion.schedule_marketplace_ingestion`."""
    return _load("ingestion").schedule_marketplace_ingestion(*args, **kwargs)


def aggregate_marketplace_metrics(*args: Any, **kwargs: Any) -> Any:
    """Proxy to :func:`ingestion.aggregate_marketplace_metrics`."""
    return _load("ingestion").aggregate_marketplace_metrics(*args, **kwargs)


def update_weights_from_db(*args: Any, **kwargs: Any) -> Any:
    """Proxy to :func:`ingestion.update_weights_from_db`."""
    return _load("ingestion").update_weights_from_db(*args, **kwargs)


__all__ = [
    "ABTestManager",
    "BudgetAllocation",
    "setup_scheduler",
    "update_weights",
    "ingest_metrics",
    "fetch_marketplace_metrics",
    "store_marketplace_metrics",
    "schedule_marketplace_ingestion",
    "aggregate_marketplace_metrics",
    "update_weights_from_db",
]
