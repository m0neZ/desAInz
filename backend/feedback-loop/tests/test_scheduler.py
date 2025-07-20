"""Tests for feedback loop scheduler."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
from types import ModuleType, SimpleNamespace
from typing import Callable, Dict, cast

from apscheduler.triggers.interval import IntervalTrigger

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT.parent))
sys.path.append(str(ROOT / "feedback-loop"))
sys.path.append(str(ROOT / "marketplace-publisher" / "src"))

dummy_pub = ModuleType("marketplace_publisher.publisher")
dummy_pub.CLIENTS = cast(Dict[str, object], {})  # type: ignore[attr-defined]
sys.modules.setdefault("marketplace_publisher", ModuleType("marketplace_publisher"))
sys.modules["marketplace_publisher.publisher"] = dummy_pub
sys.modules.setdefault(
    "marketplace_publisher.clients",
    ModuleType("marketplace_publisher.clients"),
)
sys.modules["marketplace_publisher.clients"].BaseClient = object  # type: ignore[attr-defined]
_weight_repo = ModuleType("scoring_engine.weight_repository")
_weight_repo.update_weights = lambda **_: None  # type: ignore[attr-defined]
sys.modules.setdefault("scoring_engine", ModuleType("scoring_engine"))
sys.modules.setdefault("scoring_engine.weight_repository", _weight_repo)

SPEC = importlib.util.spec_from_file_location(
    "feedback_loop.scheduler",
    ROOT / "feedback-loop" / "feedback_loop" / "scheduler.py",
)
assert SPEC is not None
assert SPEC.loader is not None
scheduler_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scheduler_mod)
setup_scheduler = scheduler_mod.setup_scheduler


class FakeScheduler:
    """Collect jobs instead of scheduling them."""

    def __init__(self) -> None:
        self.jobs: list[tuple[Callable[..., object], object, dict[str, object]]] = []

    def add_job(
        self, func: Callable[..., object], trigger: object, **kwargs: object
    ) -> None:
        """Record a scheduled job."""
        self.jobs.append((func, trigger, kwargs))

    def get_jobs(self) -> list[tuple[Callable[..., object], object, dict[str, object]]]:
        """Return registered jobs."""
        return self.jobs


def test_jobs_registered(monkeypatch) -> None:
    """Setup should register ingest and update jobs."""

    fake = FakeScheduler()
    monkeypatch.setattr(scheduler_mod, "BackgroundScheduler", lambda: fake)
    monkeypatch.setattr(
        scheduler_mod,
        "settings",
        SimpleNamespace(
            publisher_metrics_interval_minutes=5,
            weight_update_interval_minutes=10,
        ),
    )
    scheduler = setup_scheduler([], "http://api")
    assert scheduler is fake
    names = [job[0].__name__ for job in fake.get_jobs()]
    assert {"hourly_ingest", "nightly_update"} <= set(names)
    ingest_job = next(
        job for job in fake.get_jobs() if job[0].__name__ == "hourly_ingest"
    )
    assert isinstance(ingest_job[1], IntervalTrigger)
    assert ingest_job[1].interval.total_seconds() == 5 * 60
    update_job = next(
        job for job in fake.get_jobs() if job[0].__name__ == "nightly_update"
    )
    assert isinstance(update_job[1], IntervalTrigger)
    assert update_job[1].interval.total_seconds() == 10 * 60
