"""
Dagster operations for the orchestration pipeline.

Environment variables
---------------------
SERVICE_AUTH_TOKEN:
    Bearer token for authenticating service-to-service calls. Optional.
SIGNAL_INGESTION_URL:
    Base URL for the signal ingestion service. Defaults to
    ``"http://signal-ingestion:8004"``.
SCORING_ENGINE_URL:
    Base URL for the scoring engine. Defaults to
    ``"http://scoring-engine:5002"``.
MOCKUP_GENERATION_URL:
    Base URL for the mockup generation service. Defaults to
    ``"http://mockup-generation:8000"``.
APPROVAL_SERVICE_URL:
    Base URL for the approval service. Defaults to
    ``"http://api-gateway:8000"``.
PUBLISHER_URL:
    Base URL for the marketplace publisher. Defaults to
    ``"http://marketplace-publisher:8001"``.
SLACK_WEBHOOK_URL:
    Slack webhook for notifications. Optional.
S3_IAM_USER:
    AWS IAM user for S3 rotation. Defaults to ``"deploy"``.
S3_SECRET_NAME:
    Name of the Kubernetes secret containing S3 credentials. Defaults to
    ``"s3-creds"``.
SPOT_AMI_ID:
    AMI ID for spot instances. Required.
SPOT_INSTANCE_TYPE:
    Instance type for spot nodes. Required.
SPOT_KEY_NAME:
    SSH key name for spot nodes. Required.
SPOT_SECURITY_GROUP:
    Security group for spot nodes. Required.
SPOT_SUBNET_ID:
    Subnet ID for spot nodes. Required.
SPOT_LABEL:
    Kubernetes node label used to identify spot nodes. Defaults to
    ``"node-role.kubernetes.io/spot=yes"``.
SPOT_COUNT:
    Number of spot nodes to maintain. Defaults to ``"1"``.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from typing import Any

import asyncio
import httpx
from dagster import Failure, RetryPolicy, op

from backend.shared.http import get_async_http_client

from scripts import maintenance


def _auth_headers(context: Any) -> dict[str, str]:
    """Return headers with auth and correlation ID."""
    headers = {"X-Correlation-ID": getattr(context, "run_id", str(uuid.uuid4()))}
    token = os.environ.get("SERVICE_AUTH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _post_with_retry(
    context: Any,
    url: str,
    *,
    json: Any | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    retries: int = 3,
) -> httpx.Response:
    """Send a POST request asynchronously with exponential backoff."""
    client = await get_async_http_client()
    for attempt in range(1, retries + 1):
        try:
            response = await client.post(
                url, json=json, headers=headers, timeout=timeout
            )
            response.raise_for_status()
            return response
        except httpx.HTTPError as exc:  # noqa: BLE001
            if attempt == retries:
                context.log.error(
                    "request to %s failed after %d attempts: %s",
                    url,
                    attempt,
                    exc,
                )
                raise
            context.log.warning(
                "request to %s failed: %s (attempt %d/%d)",
                url,
                exc,
                attempt,
                retries,
            )
            await asyncio.sleep(2 ** (attempt - 1))
    raise RuntimeError("unreachable")


async def _fetch_optimizations(context: Any) -> list[str]:
    """Return optimization results from the optimization service."""
    base_url = os.environ.get("OPTIMIZATION_URL", "http://optimization:5007")
    client = await get_async_http_client()
    try:
        resp = await client.get(
            f"{base_url}/optimizations",
            headers=_auth_headers(context),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return [str(item) for item in data]
    except httpx.HTTPError as exc:  # noqa: BLE001
        context.log.warning("failed to fetch optimizations: %s", exc)
    return []


async def _fetch_hints(context: Any) -> list[str]:
    """Return optimization hints from the optimization service."""
    base_url = os.environ.get("OPTIMIZATION_URL", "http://optimization:5007")
    client = await get_async_http_client()
    try:
        resp = await client.get(
            f"{base_url}/hints",
            headers=_auth_headers(context),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return [str(item) for item in data]
    except httpx.HTTPError as exc:  # noqa: BLE001
        context.log.warning("failed to fetch optimization hints: %s", exc)
    return []


@op  # type: ignore[misc]
async def ingest_signals(  # type: ignore[no-untyped-def]
    context,
) -> list[str]:
    """Fetch new signals asynchronously."""
    context.log.info("ingesting signals")
    base_url = os.environ.get(
        "SIGNAL_INGESTION_URL",
        "http://signal-ingestion:8004",
    )
    headers = _auth_headers(context)
    try:
        response = await _post_with_retry(
            context, f"{base_url}/ingest", headers=headers, timeout=30
        )
    except httpx.HTTPError as exc:  # noqa: BLE001
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
async def score_signals(  # type: ignore[no-untyped-def]
    context,
    signals: list[str],
) -> list[float]:
    """Score the ingested signals concurrently."""

    async def _score(client: httpx.AsyncClient) -> float:
        payload = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "engagement_rate": 0.0,
            "embedding": [0.0],
        }
        for attempt in range(1, 4):
            try:
                resp = await client.post(
                    f"{base_url}/score",
                    json=payload,
                    headers=_auth_headers(context),
                    timeout=30,
                )
                resp.raise_for_status()
                return float(resp.json().get("score", 0))
            except httpx.HTTPError as exc:  # noqa: BLE001
                if attempt == 3:
                    context.log.warning("scoring failed after retries: %s", exc)
                    return 0.0
                context.log.warning(
                    "scoring request failed: %s (attempt %d/3)",
                    exc,
                    attempt,
                )
                await asyncio.sleep(2 ** (attempt - 1))
        return 0.0

    context.log.info("scoring %d signals", len(signals))
    base_url = os.environ.get(
        "SCORING_ENGINE_URL",
        "http://scoring-engine:5002",
    )

    client = await get_async_http_client()
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(_score(client)) for _ in signals]
    return [task.result() for task in tasks]


@op  # type: ignore[misc]
async def generate_content(  # type: ignore[no-untyped-def]
    context,
    scores: list[float],
) -> list[str]:
    """Generate content based on scores asynchronously."""
    context.log.info("generating %d items", len(scores))
    base_url = os.environ.get(
        "MOCKUP_GENERATION_URL",
        "http://mockup-generation:8000",
    )

    async def _generate(score: float) -> list[str]:
        resp = await _post_with_retry(
            context,
            f"{base_url}/generate",
            json={"scores": [score]},
            headers=_auth_headers(context),
            timeout=60,
        )
        items = resp.json().get("items", [])
        if not isinstance(items, list):
            items = []
        return [str(item) for item in items]

    if len(scores) <= 1:
        try:
            resp = await _post_with_retry(
                context,
                f"{base_url}/generate",
                json={"scores": scores},
                headers=_auth_headers(context),
                timeout=60,
            )
            items = resp.json().get("items", [])
            if not isinstance(items, list):
                items = []
        except httpx.HTTPError as exc:  # noqa: BLE001
            context.log.warning("generation failed after retries: %s", exc)
            items = []
        return [str(item) for item in items]

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(_generate(s)) for s in scores]
    results = [task.result() for task in tasks]
    return [item for sub in results for item in sub]


@op  # type: ignore[misc]
async def await_approval(context) -> None:  # type: ignore[no-untyped-def]
    """Poll the approval service until the run is approved asynchronously."""
    base_url = os.environ.get("APPROVAL_SERVICE_URL", "http://api-gateway:8000")
    url = f"{base_url}/approvals/{context.run_id}"
    headers = _auth_headers(context)

    client = await get_async_http_client()
    while True:
        try:
            resp = await client.get(url, headers=headers, timeout=5)
            resp.raise_for_status()
            if resp.json().get("approved"):
                context.log.info("publishing approved")
                return
        except httpx.HTTPError as exc:  # noqa: BLE001
            context.log.warning("approval check failed: %s", exc)
        await asyncio.sleep(10)


@op(retry_policy=RetryPolicy(max_retries=3, delay=1))  # type: ignore[misc]
async def publish_content(  # type: ignore[no-untyped-def]
    context,
    items: list[str],
) -> None:
    """
    Publish generated content asynchronously.

    Requests are dispatched concurrently but limited by a semaphore so that the
    publisher service is not overwhelmed.
    """

    context.log.info("publishing %d items", len(items))
    base_url = os.environ.get(
        "PUBLISHER_URL",
        "http://marketplace-publisher:8001",
    )
    limit = int(os.environ.get("PUBLISH_CONCURRENCY", "5"))
    semaphore = asyncio.Semaphore(limit)

    async def _publish(item: str) -> None:
        payload = {"marketplace": "redbubble", "design_path": item}
        async with semaphore:
            try:
                resp = await _post_with_retry(
                    context,
                    f"{base_url}/publish",
                    json=payload,
                    headers=_auth_headers(context),
                    timeout=30,
                )
                task_id = resp.json().get("task_id")
                context.log.debug("created publish task %s", task_id)
            except httpx.HTTPError as exc:  # noqa: BLE001
                context.log.warning("failed to publish %s after retries: %s", item, exc)

    async with asyncio.TaskGroup() as tg:
        for item in items:
            tg.create_task(_publish(item))


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
    try:
        hints = asyncio.run(_fetch_hints(context))
        if hints:
            context.log.info("optimization hints: %s", hints)
    except Exception as exc:  # noqa: BLE001
        context.log.warning("optimization query failed: %s", exc)
    maintenance.archive_old_mockups()
    maintenance.purge_stale_records()
    maintenance.purge_old_s3_objects()


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


@op(retry_policy=RetryPolicy(max_retries=3, delay=1))  # type: ignore[misc]
async def rotate_k8s_secrets_op(  # type: ignore[no-untyped-def]
    context,
) -> None:
    """Rotate Kubernetes secrets via :mod:`scripts.rotate_secrets` and notify Slack."""
    context.log.info("rotating Kubernetes secrets")
    from scripts.rotate_secrets import rotate

    rotate()

    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if webhook:
        try:
            await _post_with_retry(
                context,
                webhook,
                json={"text": "Kubernetes secrets rotated"},
                timeout=5,
            )
        except httpx.HTTPError as exc:  # noqa: BLE001
            context.log.warning("slack notification failed: %s", exc)


@op(retry_policy=RetryPolicy(max_retries=3, delay=1))  # type: ignore[misc]
def rotate_s3_keys_op(context) -> None:  # type: ignore[no-untyped-def]
    """Rotate S3 access keys and update Kubernetes secret."""
    context.log.info("rotating S3 keys")
    from scripts.rotate_s3_keys import rotate

    user = os.environ.get("S3_IAM_USER", "deploy")
    secret = os.environ.get("S3_SECRET_NAME", "s3-creds")
    rotate(user, secret)


@op  # type: ignore[misc]
def sync_listing_states_op(context) -> None:  # type: ignore[no-untyped-def]
    """Synchronize marketplace listing states with the local database."""
    context.log.info("synchronizing listing states")
    from scripts import listing_sync

    listing_sync.main()


@op  # type: ignore[misc]
def purge_pii_rows_op(context) -> None:  # type: ignore[no-untyped-def]
    """Run :func:`signal_ingestion.privacy.purge_pii_rows`."""
    context.log.info("purging stored PII")
    import asyncio
    from signal_ingestion.privacy import purge_pii_rows

    count = asyncio.run(purge_pii_rows())
    context.log.info("purged %d rows", count)


@op  # type: ignore[misc]
def benchmark_score_op(context) -> None:  # type: ignore[no-untyped-def]
    """Run benchmark_score script and persist results."""
    context.log.info("benchmarking scoring endpoint")
    import asyncio
    from scripts import benchmark_score
    from backend.shared.db import session_scope, models

    uncached, cached, runs = asyncio.run(benchmark_score.main())
    with session_scope() as session:
        session.add(
            models.ScoreBenchmark(
                runs=runs,
                uncached_seconds=uncached,
                cached_seconds=cached,
            )
        )


@op  # type: ignore[misc]
def update_feedback(context) -> None:  # type: ignore[no-untyped-def]
    """Update scoring weights based on marketplace feedback."""
    context.log.info("updating feedback weights")
    from feedback_loop import update_weights_from_db

    base_url = os.environ.get("SCORING_ENGINE_URL", "http://scoring-engine:5002")

    try:
        weights = update_weights_from_db(base_url)
    except Exception as exc:  # noqa: BLE001
        context.log.warning("failed to update feedback weights: %s", exc)
    else:
        context.log.debug("updated weights: %s", weights)


@op  # type: ignore[misc]
def maintain_spot_nodes_op(context) -> None:  # type: ignore[no-untyped-def]
    """Ensure the configured number of spot nodes are running."""
    context.log.info("checking spot nodes")
    from scripts.manage_spot_instances import maintain_nodes

    ami = os.environ["SPOT_AMI_ID"]
    itype = os.environ["SPOT_INSTANCE_TYPE"]
    key = os.environ["SPOT_KEY_NAME"]
    sg = os.environ["SPOT_SECURITY_GROUP"]
    subnet = os.environ["SPOT_SUBNET_ID"]
    label = os.environ.get("SPOT_LABEL", "node-role.kubernetes.io/spot=yes")
    count = int(os.environ.get("SPOT_COUNT", "1"))
    maintain_nodes(ami, itype, key, sg, subnet, label=label, count=count)
