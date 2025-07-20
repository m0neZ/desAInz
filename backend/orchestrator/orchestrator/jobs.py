"""Dagster jobs composing the orchestration pipeline."""

from __future__ import annotations

from dagster import job

from .ops import (
    await_approval,
    backup_data,
    cleanup_data,
    analyze_query_plans_op,
    run_daily_summary,
    generate_content,
    ingest_signals,
    publish_content,
    score_signals,
)
from .hooks import record_failure, record_success


@job
def idea_job() -> None:
    """Pipeline from ingestion to publishing."""
    signals = ingest_signals()
    scores = score_signals(signals)
    items = generate_content(scores)
    await_approval()
    publish_content(items)


@job(hooks={record_success, record_failure})
def backup_job() -> None:
    """Job running the backup operation."""
    backup_data()


@job(hooks={record_success, record_failure})
def cleanup_job() -> None:
    """Job running periodic cleanup."""
    cleanup_data()


@job(hooks={record_success, record_failure})
def analyze_query_plans_job() -> None:
    """Job collecting EXPLAIN plans for slow queries."""
    analyze_query_plans_op()


@job(hooks={record_success, record_failure})
def daily_summary_job() -> None:
    """Job generating the daily activity summary."""
    run_daily_summary()
