"""Dagster jobs composing the orchestration pipeline."""

from __future__ import annotations

from dagster import RetryPolicy, job

DEFAULT_JOB_RETRY_POLICY = RetryPolicy(max_retries=3, delay=1)

from .ops import (
    await_approval,
    backup_data,
    cleanup_data,
    analyze_query_plans_op,
    rotate_k8s_secrets_op,
    run_daily_summary,
    generate_content,
    ingest_signals,
    publish_content,
    score_signals,
    sync_listing_states_op,
)
from .hooks import record_failure, record_success


@job(retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def idea_job() -> None:
    """Pipeline from ingestion to publishing."""
    signals = ingest_signals()
    scores = score_signals(signals)
    items = generate_content(scores)
    await_approval()
    publish_content(items)


@job(hooks={record_success, record_failure}, retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def backup_job() -> None:
    """Job running the backup operation."""
    backup_data()


@job(hooks={record_success, record_failure}, retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def cleanup_job() -> None:
    """Job running periodic cleanup."""
    cleanup_data()


@job(hooks={record_success, record_failure}, retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def analyze_query_plans_job() -> None:
    """Job collecting EXPLAIN plans for slow queries."""
    analyze_query_plans_op()


@job(hooks={record_success, record_failure}, retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def daily_summary_job() -> None:
    """Job generating the daily activity summary."""
    run_daily_summary()


@job(hooks={record_success, record_failure}, retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def rotate_secrets_job() -> None:
    """Job rotating API tokens and updating Kubernetes secrets."""
    rotate_k8s_secrets_op()


@job(hooks={record_success, record_failure}, retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def sync_listings_job() -> None:
    """Job synchronizing marketplace listing states."""
    sync_listing_states_op()
