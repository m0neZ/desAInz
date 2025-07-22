"""Dagster jobs composing the orchestration pipeline."""

from __future__ import annotations

from dagster import RetryPolicy, job

DEFAULT_JOB_RETRY_POLICY = RetryPolicy(max_retries=3, delay=1)

from .hooks import record_failure, record_success
from .ops import (
    analyze_query_plans_op,
    await_approval,
    backup_data,
    benchmark_score_op,
    cleanup_data,
    generate_content,
    ingest_signals,
    maintain_spot_nodes_op,
    publish_content,
    purge_pii_rows_op,
    rotate_k8s_secrets_op,
    rotate_s3_keys_op,
    run_daily_summary,
    score_signals,
    sync_listing_states_op,
    update_feedback,
)


@job(op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def idea_job() -> None:
    """Pipeline from ingestion to publishing."""
    signals = ingest_signals()
    scores = score_signals(signals)
    items = generate_content(scores)
    await_approval()
    publish_content(items)


@job(hooks={record_success, record_failure}, op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def backup_job() -> None:
    """Job running the backup operation."""
    backup_data()


@job(hooks={record_success, record_failure}, op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def cleanup_job() -> None:
    """Job running periodic cleanup."""
    cleanup_data()


@job(hooks={record_success, record_failure}, op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def analyze_query_plans_job() -> None:
    """Job collecting EXPLAIN plans for slow queries."""
    analyze_query_plans_op()


@job(hooks={record_success, record_failure}, op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def daily_summary_job() -> None:
    """Job generating the daily activity summary."""
    run_daily_summary()


@job(hooks={record_success, record_failure}, op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def rotate_secrets_job() -> None:
    """Job rotating API tokens and updating Kubernetes secrets."""
    await_approval()
    rotate_k8s_secrets_op()


@job(hooks={record_success, record_failure}, op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def rotate_s3_keys_job() -> None:
    """Job rotating S3 keys and updating Kubernetes secrets."""
    await_approval()
    rotate_s3_keys_op()


@job(hooks={record_success, record_failure}, op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def sync_listings_job() -> None:
    """Job synchronizing marketplace listing states."""
    sync_listing_states_op()


@job(hooks={record_success, record_failure}, op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def privacy_purge_job() -> None:
    """Job removing PII from stored signals."""
    purge_pii_rows_op()


@job(hooks={record_success, record_failure}, op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def benchmark_score_job() -> None:
    """Job benchmarking scoring service and recording results."""
    benchmark_score_op()


@job(op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def signal_ingestion_job() -> None:
    """Job that only ingests signals."""
    ingest_signals()


@job(op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def scoring_job() -> None:
    """Job that ingests and scores signals."""
    signals = ingest_signals()
    score_signals(signals)


@job(op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def mockup_generation_job() -> None:
    """Job that ingests, scores, and generates mockups."""
    signals = ingest_signals()
    scores = score_signals(signals)
    generate_content(scores)


@job(op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def publishing_job() -> None:
    """Job that ingests, scores, generates, and publishes content."""
    signals = ingest_signals()
    scores = score_signals(signals)
    items = generate_content(scores)
    await_approval()
    publish_content(items)


@job(hooks={record_success, record_failure}, op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def feedback_update_job() -> None:
    """Job updating scoring weights from feedback data."""
    update_feedback()


@job(hooks={record_success, record_failure}, op_retry_policy=DEFAULT_JOB_RETRY_POLICY)  # type: ignore[misc]
def maintain_spot_nodes_job() -> None:
    """Job ensuring spot nodes are present."""
    maintain_spot_nodes_op()
