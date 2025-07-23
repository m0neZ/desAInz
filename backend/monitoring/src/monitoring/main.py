"""
Expose Prometheus metrics and logs via FastAPI.

Environment variables
---------------------
CELERY_BROKER_URL:
    Connection string for the Celery broker. Defaults to
    ``"redis://localhost:6379/0"``.
CELERY_QUEUES:
    Comma-separated list of queues to consume. Defaults to ``"celery"``.
"""

from __future__ import annotations

import logging
import uuid
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Coroutine, Iterable

import httpx
import asyncio
from backend.shared.http import DEFAULT_TIMEOUT, get_async_http_client

import psutil
from fastapi import FastAPI, Request, Response
from backend.shared.security import require_status_api_key
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Histogram
from backend.shared.metrics import register_metrics
from backend.shared.security import add_security_headers
from backend.shared.responses import json_cached

from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared import add_error_handlers, configure_sentry
from backend.shared.config import settings as shared_settings
from backend.shared.db import session_scope
from backend.shared.db.models import Idea, Listing, Mockup, Signal
from sqlalchemy import func, select

from .pagerduty import trigger_sla_violation, trigger_queue_backlog
from .metrics_store import (
    PublishLatencyMetric,
    TimescaleMetricsStore,
    LATENCY_CACHE_KEY,
)

from backend.shared.cache import sync_get, sync_set
import redis

LAST_ALERT_KEY = "sla:last_alert"
QUEUE_ALERT_KEY = "queue:last_alert"

from .logging_config import configure_logging
from .settings import Settings, settings
from scripts.daily_summary import generate_daily_summary


async def get_http_client() -> httpx.AsyncClient:
    """Return a shared HTTP client instance."""
    return await get_async_http_client()


metrics_store = TimescaleMetricsStore()

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=shared_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
configure_tracing(app, settings.app_name)
configure_sentry(app, settings.app_name)
add_profiling(app)
add_error_handlers(app)
register_metrics(app)
add_security_headers(app)


@app.on_event("shutdown")
def shutdown_store() -> None:
    """Close metrics store connections on shutdown."""
    metrics_store.close()


SIGNAL_TO_PUBLISH_SECONDS = Histogram(
    "signal_to_publish_seconds",
    "Latency from first signal ingestion to listing publish per idea",
    buckets=(60, 300, 900, 1800, 3600, 7200, 10800),
)


@app.middleware("http")
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Attach a correlation ID and record metrics."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    try:
        import sentry_sdk

        sentry_sdk.set_tag("correlation_id", correlation_id)
    except Exception:  # pragma: no cover - sentry optional
        pass

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.get("/overview")
async def overview() -> dict[str, float]:
    """Return basic system information."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_mb": psutil.virtual_memory().used / 1024**2,
    }


@app.get("/analytics")
async def analytics() -> dict[str, float]:
    """Return metrics derived from the TimescaleDB store."""
    since = datetime.utcnow() - timedelta(days=1)
    active = metrics_store.get_active_users(since)
    error_rate = metrics_store.get_error_rate(since)
    return {"active_users": float(active), "error_rate": error_rate}


@app.get("/status")
async def status() -> dict[str, str]:
    """Return health status for core services."""
    services = {
        "mockup_generation": "http://mockup-generation:8000/health",
        "marketplace_publisher": "http://marketplace-publisher:8000/health",
        "orchestrator": "http://orchestrator:8000/health",
    }
    results: dict[str, str] = {}
    client = await get_http_client()
    for name, url in services.items():
        try:
            resp = await client.get(url)
            results[name] = (
                resp.json().get("status") if resp.status_code == 200 else "down"
            )
        except Exception:  # pragma: no cover - network failures
            results[name] = "down"
    return results


def _record_latencies() -> list[float]:
    """Record per-idea publish latency and return all values."""
    stmt = (
        select(
            Idea.id,
            func.min(Signal.timestamp),
            func.min(Listing.created_at),
        )
        .join(Signal, Signal.idea_id == Idea.id)
        .join(Mockup, Mockup.idea_id == Idea.id)
        .join(Listing, Listing.mockup_id == Mockup.id)
        .group_by(Idea.id)
    )
    with session_scope() as session:
        rows = session.execute(stmt).all()
    latencies: list[float] = []
    metrics: list[PublishLatencyMetric] = []
    for idea_id, signal_time, listing_time in rows:
        seconds = (listing_time - signal_time).total_seconds()
        latencies.append(seconds)
        SIGNAL_TO_PUBLISH_SECONDS.observe(seconds)
        metrics.append(
            PublishLatencyMetric(
                idea_id=idea_id,
                timestamp=listing_time,
                latency_seconds=seconds,
            )
        )
    metrics_store.add_latencies(metrics)
    return latencies


def get_average_latency() -> float:
    """Return cached average latency or compute and store it."""
    cached = sync_get(LATENCY_CACHE_KEY)
    if cached is not None:
        try:
            return float(cached)
        except (TypeError, ValueError):
            pass
    latencies = _record_latencies()
    avg = sum(latencies) / max(len(latencies), 1)
    try:
        sync_set(LATENCY_CACHE_KEY, str(avg), ttl=300)
    except Exception:  # pragma: no cover - redis optional
        pass
    return avg


def get_queue_length() -> int:
    """Return total length of configured Celery queues."""
    url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    queues = os.getenv("CELERY_QUEUES", "celery").split(",")
    client = redis.Redis.from_url(url)
    try:
        return int(sum(client.llen(q) for q in queues))
    finally:
        client.close()


def _check_queue_backlog(cfg: Settings = settings) -> int:
    """Return queue length and trigger alert when threshold exceeded."""
    length = get_queue_length()
    threshold = getattr(
        cfg,
        "queue_backlog_threshold",
        getattr(cfg, "queue_backlog_threshold", 50),
    )
    if length > threshold:
        last = sync_get(QUEUE_ALERT_KEY)
        cooldown = getattr(
            cfg,
            "queue_backlog_alert_cooldown_minutes",
            getattr(cfg, "queue_backlog_alert_cooldown_minutes", 60),
        )
        now = time.time()
        try:
            last_ts = float(last) if last is not None else 0.0
        except (TypeError, ValueError):
            last_ts = 0.0
        if last is None or now - last_ts >= cooldown * 60:
            trigger_queue_backlog(length)
            try:
                sync_set(QUEUE_ALERT_KEY, str(now))
            except Exception:  # pragma: no cover - redis optional
                pass
    return length


def _check_sla(cfg: Settings = settings) -> float:
    """Return average latency and trigger PagerDuty when breached."""
    avg = get_average_latency()
    if avg == 0.0:
        return avg
    threshold = getattr(cfg, "SLA_THRESHOLD_HOURS", cfg.sla_threshold_hours)
    if avg > threshold * 3600:
        last = sync_get(LAST_ALERT_KEY)
        cooldown = getattr(
            cfg,
            "SLA_ALERT_COOLDOWN_MINUTES",
            cfg.sla_alert_cooldown_minutes,
        )
        now = time.time()
        try:
            last_ts = float(last) if last is not None else 0.0
        except (TypeError, ValueError):
            last_ts = 0.0
        if last is None or now - last_ts >= cooldown * 60:
            trigger_sla_violation(avg / 3600)
            try:
                sync_set(LAST_ALERT_KEY, str(now))
            except Exception:  # pragma: no cover - redis optional
                pass
    return avg


@app.get("/sla")
async def sla() -> dict[str, float]:
    """Check SLA status and emit PagerDuty alert if violated."""
    avg = _check_sla()
    return {"average_seconds": avg}


@app.get("/latency")
async def latency() -> dict[str, float]:
    """Return average signal-to-publish latency without triggering alerts."""
    avg = get_average_latency()
    return {"average_seconds": avg}


@app.get("/queue_length")
async def queue_length() -> dict[str, int]:
    """Check queue backlog and emit PagerDuty alert when needed."""
    length = _check_queue_backlog()
    return {"length": length}


@app.get("/daily_summary")
async def daily_summary() -> dict[str, object]:
    """Return the daily summary generated from recent activity."""
    summary = await generate_daily_summary()
    return dict(summary)


@app.get("/daily_summary/report")
async def daily_summary_report() -> dict[str, object]:
    """Return the latest persisted daily summary report."""
    path = Path(settings.daily_summary_file)
    if not path.exists():
        return {}
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    return dict(data)


@app.get("/logs")
async def logs() -> dict[str, str]:
    """Return the latest application logs."""
    path = Path(settings.log_file)
    if not path.exists():
        return {"logs": ""}
    lines = path.read_text(encoding="utf-8").splitlines()[-100:]
    return {"logs": "\n".join(lines)}


@app.get("/health")
async def health() -> Response:
    """Return service liveness."""
    return json_cached({"status": "ok"})


@app.get("/ready")
async def ready(request: Request) -> Response:
    """Return service readiness."""
    require_status_api_key(request)
    return json_cached({"status": "ready"})


if __name__ == "__main__":  # pragma: no cover
    import asyncio as _asyncio
    import uvloop
    import uvicorn

    _asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    uvicorn.run(
        "monitoring.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
