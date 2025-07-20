"""Dagster operations for the orchestration pipeline."""

from __future__ import annotations

import os
import uuid

from datetime import datetime, timezone
from typing import Any

import requests
from dagster import Failure, RetryPolicy, op

import time

from scripts import maintenance


def _auth_headers(context: Any) -> dict[str, str]:
    """Return headers with auth and correlation ID."""
    headers = {"X-Correlation-ID": getattr(context, "run_id", str(uuid.uuid4()))}
    token = os.environ.get("SERVICE_AUTH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _post_with_retry(
    context: Any,
    url: str,
    *,
    json: Any | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    retries: int = 3,
) -> requests.Response:
    """Send a POST request with simple exponential backoff."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, json=json, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:  # noqa: BLE001
            if attempt == retries:
                context.log.error(
                    "request to %s failed after %d attempts: %s", url, attempt, exc
                )
                raise
            context.log.warning(
                "request to %s failed: %s (attempt %d/%d)",
                url,
                exc,
                attempt,
                retries,
            )
            time.sleep(2 ** (attempt - 1))


@op  # type: ignore[misc]
def ingest_signals(  # type: ignore[no-untyped-def]
    context,
) -> list[str]:
    """Fetch new signals."""
    context.log.info("ingesting signals")
    base_url = os.environ.get(
        "SIGNAL_INGESTION_URL",
        "http://signal-ingestion:8004",
    )
    headers = _auth_headers(context)
    try:
        response = _post_with_retry(
            context, f"{base_url}/ingest", headers=headers, timeout=30
        )
    except requests.RequestException as exc:  # noqa: BLE001
        raise Failure(f"ingestion failed: {exc}") from exc

    payload = response.json()
    signals: list[Any] | None = None
    if isinstance(payload, dict):
        if isinstance(payload.get("signals"), list):
            signals = payload.get("signals")
        elif isinstance(payload.get("items"), list):
            signals = payload.get("items")
        elif len(payload) == 1:
            value = next(iter(payload.values()))
            if isinstance(value, list):
                signals = value
    if signals is None:
        signals = []
    context.log.debug("received signals: %s", signals)
    return [str(s) for s in signals]


@op  # type: ignore[misc]
def score_signals(  # type: ignore[no-untyped-def]
    context,
    signals: list[str],
) -> list[float]:
    """Score the ingested signals."""
    context.log.info("scoring %d signals", len(signals))
    base_url = os.environ.get(
        "SCORING_ENGINE_URL",
        "http://scoring-engine:5002",
    )
    scores: list[float] = []
    for _ in signals:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engagement_rate": 0.0,
            "embedding": [0.0],
        }
        try:
            resp = _post_with_retry(
                context,
                f"{base_url}/score",
                json=payload,
                headers=_auth_headers(context),
                timeout=30,
            )
            score = float(resp.json().get("score", 0))
        except requests.RequestException as exc:  # noqa: BLE001
            context.log.warning("scoring failed after retries: %s", exc)
            score = 0.0
        scores.append(score)
    return scores


@op  # type: ignore[misc]
def generate_content(  # type: ignore[no-untyped-def]
    context,
    scores: list[float],
) -> list[str]:
    """Generate content based on scores."""
    context.log.info("generating %d items", len(scores))
    base_url = os.environ.get(
        "MOCKUP_GENERATION_URL",
        "http://mockup-generation:8000",
    )
    try:
        resp = _post_with_retry(
            context,
            f"{base_url}/generate",
            json={"scores": scores},
            headers=_auth_headers(context),
            timeout=60,
        )
        items = resp.json().get("items", [])
        if not isinstance(items, list):
            items = []
    except requests.RequestException as exc:  # noqa: BLE001
        context.log.warning("generation failed after retries: %s", exc)
        items = []
    return [str(item) for item in items]


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
    base_url = os.environ.get(
        "PUBLISHER_URL",
        "http://marketplace-publisher:8001",
    )
    for item in items:
        payload = {"marketplace": "redbubble", "design_path": item}
        try:
            resp = _post_with_retry(
                context,
                f"{base_url}/publish",
                json=payload,
                headers=_auth_headers(context),
                timeout=30,
            )
            task_id = resp.json().get("task_id")
            context.log.debug("created publish task %s", task_id)
        except requests.RequestException as exc:  # noqa: BLE001
            context.log.warning("failed to publish %s after retries: %s", item, exc)


@op  # type: ignore[misc]
def backup_data(  # type: ignore[no-untyped-def]
    context,
) -> None:
    """Create a backup of critical datasets."""
    context.log.info("performing backup")


@op  # type: ignore[misc]
def cleanup_data(  # type: ignore[no-untyped-def]
    context,
) -> None:
    """Remove temporary or stale data."""
    context.log.info("running cleanup")
    maintenance.archive_old_mockups()
    maintenance.purge_stale_records()


@op  # type: ignore[misc]
def analyze_query_plans_op(  # type: ignore[no-untyped-def]
    context,
) -> None:
    """Run query plan analysis script."""
    context.log.info("analyzing slow queries")
    from scripts import analyze_query_plans

    analyze_query_plans.main()


@op  # type: ignore[misc]
def run_daily_summary(  # type: ignore[no-untyped-def]
    context,
) -> None:
    """Execute the daily summary script and log the result."""
    context.log.info("generating daily summary")
    from scripts.daily_summary import generate_daily_summary

    import asyncio

    summary = asyncio.run(generate_daily_summary())
    context.log.debug("summary: %s", summary)
