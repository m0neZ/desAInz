"""Tests for centroid scheduler configuration and execution."""

# mypy: ignore-errors

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from scoring_engine.centroid_job import compute_and_store_centroids
from scoring_engine.centroid_job import scheduler as module_scheduler
from scoring_engine.centroid_job import start_centroid_scheduler
from scoring_engine.weight_repository import get_centroid

from backend.shared.db import session_scope
from backend.shared.db.models import Embedding


def test_scheduler_configuration(monkeypatch) -> None:
    """Scheduler runs compute job hourly."""
    monkeypatch.setattr("scoring_engine.centroid_job.scheduler", BackgroundScheduler())
    start_centroid_scheduler()
    jobs = module_scheduler.get_jobs()
    assert len(jobs) == 1
    job = jobs[0]
    assert isinstance(job.trigger, IntervalTrigger)
    assert int(job.trigger.interval.total_seconds()) == 3600
    module_scheduler.shutdown()


def test_centroid_job_executes(monkeypatch) -> None:
    """Job computes centroids from stored embeddings."""
    monkeypatch.setattr("scoring_engine.centroid_job.scheduler", BackgroundScheduler())
    with session_scope() as session:
        v1 = [1.0] + [0.0] * 767
        v2 = [0.0] * 767 + [1.0]
        session.add_all(
            [
                Embedding(source="src", embedding=v1),
                Embedding(source="src", embedding=v2),
            ]
        )
        session.flush()
    start_centroid_scheduler()
    # execute the scheduled job directly
    job = module_scheduler.get_jobs()[0]
    job.func()
    module_scheduler.shutdown()
    centroid = get_centroid("src")
    assert centroid == [0.5] + [0.0] * 766 + [0.5]


def test_centroid_job_uses_recent_embeddings(monkeypatch) -> None:
    """Latest embeddings override older ones when computing centroids."""

    monkeypatch.setattr("scoring_engine.centroid_job.scheduler", BackgroundScheduler())

    with session_scope() as session:
        v1 = [1.0] + [0.0] * 767
        v2 = [0.0] * 767 + [1.0]
        session.add(Embedding(source="src", embedding=v1))
        session.flush()

    compute_and_store_centroids(limit=1)
    assert get_centroid("src") == v1

    with session_scope() as session:
        session.add(Embedding(source="src", embedding=v2))
        session.flush()

    compute_and_store_centroids(limit=1)
    assert get_centroid("src") == v2
