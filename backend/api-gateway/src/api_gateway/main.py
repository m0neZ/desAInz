"""API Gateway FastAPI application."""

import logging
import os
import uuid
from time import perf_counter
from typing import Callable, Coroutine, cast

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from brotli_asgi import BrotliMiddleware
from backend.shared.cache import get_async_client
from fastapi.security import HTTPAuthorizationCredentials
from prometheus_client import Counter, Histogram

from .routes import router, close_http_clients
from backend.shared.tracing import configure_tracing
from backend.shared.profiling import add_profiling
from backend.shared.metrics import register_metrics
from backend.shared.security import add_security_headers, require_status_api_key
from backend.shared.responses import json_cached
from backend.shared.logging import configure_logging
from backend.shared.db import run_migrations_if_needed
from backend.shared import ServiceName, add_error_handlers, configure_sentry
from backend.shared.config import settings as shared_settings
from .rate_limiter import UserRateLimiter
from .settings import settings
from .auth import verify_token


configure_logging()
logger = logging.getLogger(__name__)

REQUEST_LATENCY = Histogram(
    "api_gateway_request_latency_seconds",
    "Latency histogram for API Gateway requests",
    ["method", "endpoint"],
)
ERROR_COUNTER = Counter(
    "api_gateway_error_total",
    "Total number of API Gateway error responses",
    ["method", "endpoint", "status_code"],
)

tags_metadata = [
    {"name": "Status", "description": "Health and readiness endpoints."},
    {"name": "Authentication", "description": "Issue and revoke JWT tokens."},
    {"name": "Roles", "description": "Manage user role assignments."},
    {"name": "Maintenance", "description": "Run maintenance tasks."},
    {"name": "tRPC", "description": "Proxy calls to the backend tRPC service."},
    {"name": "Optimization", "description": "Retrieve optimization hints."},
    {"name": "Audit", "description": "Query audit log entries."},
    {"name": "Models", "description": "Manage available AI models."},
    {"name": "Publish", "description": "Manage publishing tasks."},
    {"name": "Protected", "description": "Endpoints requiring authentication."},
    {"name": "Flags", "description": "Query and modify feature flags."},
    {"name": "Privacy", "description": "Handle deletion requests and PII purging."},
]

SERVICE_NAME = os.getenv("SERVICE_NAME", ServiceName.API_GATEWAY.value)
app = FastAPI(title="API Gateway", openapi_tags=tags_metadata)
app.add_middleware(
    CORSMiddleware,
    allow_origins=shared_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Compress large responses using Brotli with gzip fallback for clients that
# do not support Brotli encoding.
app.add_middleware(BrotliMiddleware, minimum_size=1000, gzip_fallback=True)
configure_tracing(app, SERVICE_NAME)
configure_sentry(app, SERVICE_NAME)
add_profiling(app)
add_error_handlers(app)
register_metrics(app)
add_security_headers(app)


@app.on_event("startup")  # type: ignore[misc]
async def apply_migrations() -> None:
    """Ensure database schema is current."""
    await run_migrations_if_needed("backend/shared/db/alembic_api_gateway.ini")


rate_limiter = UserRateLimiter(
    settings.rate_limit_per_user,
    settings.rate_limit_window,
    get_async_client(),
)


def _identify_user(request: Request) -> str:
    """Return identifier for rate limiting, token subject or client IP."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        try:
            payload = verify_token(credentials)
            sub = cast(str | None, payload.get("sub"))
            if sub is not None:
                return sub
        except Exception:  # pragma: no cover - invalid tokens treated as anonymous
            pass
    return cast(str, request.client.host)


@app.middleware("http")  # type: ignore[misc]
async def add_correlation_id(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Ensure each request includes a correlation ID and record metrics."""
    start = perf_counter()
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    try:
        import sentry_sdk

        sentry_sdk.set_tag("correlation_id", correlation_id)
    except Exception:  # pragma: no cover - sentry optional
        pass
    logger.info(
        "request received",
        extra={
            "correlation_id": correlation_id,
            "user": _identify_user(request),
            "path": request.url.path,
            "method": request.method,
        },
    )
    try:
        response = await call_next(request)
    except Exception:
        ERROR_COUNTER.labels(request.method, request.url.path, "500").inc()
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(
            perf_counter() - start
        )
        raise
    if response.status_code >= 500:
        ERROR_COUNTER.labels(
            request.method, request.url.path, str(response.status_code)
        ).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(
        perf_counter() - start
    )
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.middleware("http")  # type: ignore[misc]
async def enforce_rate_limit(
    request: Request,
    call_next: Callable[[Request], Coroutine[None, None, Response]],
) -> Response:
    """Reject requests that exceed the per-user limit."""
    user_id = _identify_user(request)
    if not await rate_limiter.acquire(user_id):
        return Response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content="Rate limit exceeded",
        )
    return await call_next(request)


@app.get("/health", tags=["Status"], summary="Service liveness")  # type: ignore[misc]
async def health() -> Response:
    """Return service liveness."""
    return json_cached({"status": "ok"})


@app.get("/ready", tags=["Status"], summary="Service readiness")  # type: ignore[misc]
async def ready(request: Request) -> Response:
    """Return service readiness."""
    require_status_api_key(request)
    return json_cached({"status": "ready"})


app.include_router(router)
app.add_event_handler("shutdown", close_http_clients)
