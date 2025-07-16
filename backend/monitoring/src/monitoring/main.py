"""Expose Prometheus metrics and logs via FastAPI."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
import asyncio
import os
from typing import Any, Callable, Coroutine

import psutil
import requests
from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from sqlalchemy import func, select
from backend.shared.db import session_scope
from backend.shared.db.models import Idea, Mockup

from backend.shared.tracing import configure_tracing

from .logging_config import configure_logging
from .settings import settings

configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name)
configure_tracing(app, settings.app_name)

REQUEST_COUNTER = Counter("http_requests_total", "Total HTTP requests")


@app.middleware("http")
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Attach a correlation ID and record metrics."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    REQUEST_COUNTER.inc()

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.get("/overview")
async def overview() -> dict[str, float]:
    """Return basic system information."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_mb": psutil.virtual_memory().used / 1024**2,
    }


@app.get("/analytics")
async def analytics() -> dict[str, int]:
    """Return placeholder analytics dashboard data."""
    return {"active_users": 0, "error_rate": 0}


@app.get("/logs")
async def logs() -> dict[str, str]:
    """Return the latest application logs."""
    path = Path(settings.log_file)
    if not path.exists():
        return {"logs": ""}
    lines = path.read_text(encoding="utf-8").splitlines()[-100:]
    return {"logs": "\n".join(lines)}


@app.get("/daily-summary")
async def daily_summary() -> dict[str, Any]:
    """Return counts and marketplace statistics for the last day."""

    def _query() -> dict[str, Any]:
        start = datetime.now(timezone.utc) - timedelta(days=1)
        with session_scope() as session:
            ideas = session.scalar(
                select(func.count(Idea.id)).where(Idea.created_at >= start)
            )
            mockups = session.scalar(
                select(func.count(Mockup.id)).where(Mockup.created_at >= start)
            )
        stats: dict[str, int] = {}
        total_ideas = ideas or 0
        total_mockups = mockups or 0
        rate = float(total_mockups) / float(total_ideas) * 100 if total_ideas else 0.0
        return {
            "ideas_generated": ideas,
            "mockup_success_rate": rate,
            "marketplace_stats": stats,
        }

    return await asyncio.to_thread(_query)


def _check_sla() -> None:
    """Check signal-to-publish time and alert if breached."""
    start = datetime.now(timezone.utc) - timedelta(hours=3)
    with session_scope() as session:
        rows = session.execute(
            select(Mockup.created_at, Idea.created_at)
            .join(Idea, Idea.id == Mockup.idea_id)
            .where(Mockup.created_at >= start)
        ).all()
    if not rows:
        return
    max_delta = max((m - i for m, i in rows), default=timedelta())
    if max_delta > timedelta(hours=2):
        _send_pagerduty_alert(
            f"Signal to publish exceeded {max_delta.total_seconds()/3600:.1f}h"
        )


def _send_pagerduty_alert(summary: str) -> None:
    """Notify PagerDuty using Events API."""
    key = os.environ.get("PAGERDUTY_KEY")
    if not key:
        logger.warning("PagerDuty key not configured")
        return
    payload = {
        "routing_key": key,
        "event_action": "trigger",
        "payload": {
            "summary": summary,
            "severity": "warning",
            "source": "monitoring-service",
        },
    }
    try:
        requests.post(
            "https://events.pagerduty.com/v2/enqueue", json=payload, timeout=10
        )
    except Exception as exc:  # pragma: no cover
        logger.error("PagerDuty alert failed: %s", exc)


async def _sla_monitor() -> None:
    """Periodically evaluate SLA metrics."""
    while True:  # pragma: no cover - simple loop
        await asyncio.to_thread(_check_sla)
        await asyncio.sleep(900)


@app.on_event("startup")
async def startup_task() -> None:
    """Start background SLA monitoring."""
    asyncio.create_task(_sla_monitor())


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "monitoring.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
