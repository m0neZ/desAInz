"""Dagster operations for the orchestration pipeline."""

import os
from time import monotonic
from typing import Any, List, Tuple

from dagster import Failure, OpExecutionContext, RetryPolicy, op

from backend.shared.metrics import record_idea_latency


@op
def ingest_signals(context: OpExecutionContext) -> Tuple[List[str], float]:
    """Fetch new signals and return them with the start timestamp."""
    context.log.info("ingesting signals")
    # Placeholder for actual ingestion logic
    signals = ["signal-1"]
    return signals, monotonic()


@op
def score_signals(
    context: OpExecutionContext, payload: Tuple[List[str], float]
) -> Tuple[List[float], float]:
    """Score the ingested signals."""
    signals, start = payload
    context.log.info("scoring %d signals", len(signals))
    # Placeholder for actual scoring logic
    scores = [1.0 for _ in signals]
    return scores, start


@op
def generate_content(
    context: OpExecutionContext, payload: Tuple[List[float], float]
) -> Tuple[List[str], float]:
    """Generate content based on scores."""
    scores, start = payload
    context.log.info("generating %d items", len(scores))
    # Placeholder for actual generation logic
    items = [f"item-{i}" for i, _ in enumerate(scores)]
    return items, start


@op
def await_approval() -> None:
    """Fail if publishing has not been approved."""
    if os.environ.get("APPROVE_PUBLISHING") != "true":
        raise Failure("publishing not approved")


@op(retry_policy=RetryPolicy(max_retries=3, delay=1))
def publish_content(
    context: OpExecutionContext, payload: Tuple[List[str], float]
) -> None:
    """Publish generated content and record latency."""
    items, start = payload
    context.log.info("publishing %d items", len(items))
    for item in items:
        record_idea_latency(monotonic() - start)
        context.log.debug("published %s", item)
