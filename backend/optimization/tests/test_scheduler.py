"""Tests for optimization scheduler."""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from backend.optimization import api as opt_api


def test_scheduler_job_registration(monkeypatch) -> None:
    """Scheduler registers hourly aggregate job."""
    monkeypatch.setattr(opt_api, "scheduler", BackgroundScheduler())
    monkeypatch.setattr(
        opt_api.store,
        "create_hourly_continuous_aggregate",
        lambda: None,
    )
    opt_api.start_scheduler()
    jobs = opt_api.scheduler.get_jobs()
    assert len(jobs) == 1
    job = jobs[0]
    assert isinstance(job.trigger, IntervalTrigger)
    assert int(job.trigger.interval.total_seconds()) == 3600
    opt_api.scheduler.shutdown()


def test_metrics_collection_scheduled(monkeypatch) -> None:
    """Metrics collection job should be added on startup."""
    monkeypatch.setattr(opt_api, "scheduler", BackgroundScheduler())
    opt_api.start_metrics_collection()
    jobs = {job.id for job in opt_api.scheduler.get_jobs()}
    assert "collect_metrics" in jobs
    opt_api.scheduler.shutdown()
