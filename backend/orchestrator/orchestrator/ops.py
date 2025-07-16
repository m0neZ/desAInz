"""Dagster operations for the orchestration pipeline."""

from __future__ import annotations

import os
from typing import List

from dagster import Failure, RetryPolicy, op


@op
def ingest_signals(context) -> List[str]:
    """Fetch new signals."""
    context.log.info("ingesting signals")
    # Placeholder for actual ingestion logic
    return ["signal-1"]


@op
def score_signals(context, signals: List[str]) -> List[float]:
    """Score the ingested signals."""
    context.log.info("scoring %d signals", len(signals))
    # Placeholder for actual scoring logic
    return [1.0 for _ in signals]


@op
def generate_content(context, scores: List[float]) -> List[str]:
    """Generate content based on scores."""
    context.log.info("generating %d items", len(scores))
    # Placeholder for actual generation logic
    return [f"item-{i}" for i, _ in enumerate(scores)]


@op
def await_approval() -> None:
    """Fail if publishing has not been approved."""
    if os.environ.get("APPROVE_PUBLISHING") != "true":
        raise Failure("publishing not approved")


@op(retry_policy=RetryPolicy(max_retries=3, delay=1))
def publish_content(context, items: List[str]) -> None:
    """Publish generated content."""
    context.log.info("publishing %d items", len(items))
    # Placeholder for actual publish logic
    for item in items:
        context.log.debug("published %s", item)
