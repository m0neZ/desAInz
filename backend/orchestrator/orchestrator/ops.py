"""Dagster operations for the orchestration pipeline."""

from __future__ import annotations

import os

from dagster import Failure, RetryPolicy, op

from scripts.maintenance import archive_old_mockups, purge_stale_records


@op  # type: ignore[misc]
def ingest_signals(  # type: ignore[no-untyped-def]
    context,
) -> list[str]:
    """Fetch new signals."""
    context.log.info("ingesting signals")
    # Placeholder for actual ingestion logic
    return ["signal-1"]


@op  # type: ignore[misc]
def score_signals(  # type: ignore[no-untyped-def]
    context,
    signals: list[str],
) -> list[float]:
    """Score the ingested signals."""
    context.log.info("scoring %d signals", len(signals))
    # Placeholder for actual scoring logic
    return [1.0 for _ in signals]


@op  # type: ignore[misc]
def generate_content(  # type: ignore[no-untyped-def]
    context,
    scores: list[float],
) -> list[str]:
    """Generate content based on scores."""
    context.log.info("generating %d items", len(scores))
    # Placeholder for actual generation logic
    return [f"item-{i}" for i, _ in enumerate(scores)]


@op  # type: ignore[misc]
def await_approval() -> None:
    """Fail if publishing has not been approved."""
    if os.environ.get("APPROVE_PUBLISHING") != "true":
        raise Failure("publishing not approved")


@op(retry_policy=RetryPolicy(max_retries=3, delay=1))  # type: ignore[misc]
def publish_content(  # type: ignore[no-untyped-def]
    context,
    items: list[str],
) -> None:
    """Publish generated content."""
    context.log.info("publishing %d items", len(items))
    # Placeholder for actual publish logic
    for item in items:
        context.log.debug("published %s", item)


@op  # type: ignore[misc]
def backup_data(  # type: ignore[no-untyped-def]
    context,
) -> None:
    """Create a backup of critical datasets."""
    context.log.info("performing backup")
    # Placeholder for backup logic


@op  # type: ignore[misc]
def cleanup_data(  # type: ignore[no-untyped-def]
    context,
) -> None:
    """Run maintenance tasks to free unused resources."""
    context.log.info("running cleanup")
    archive_old_mockups()
    purge_stale_records()
