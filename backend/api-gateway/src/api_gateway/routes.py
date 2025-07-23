"""API routes including REST and tRPC-compatible endpoints."""

from typing import Any, Dict, AsyncGenerator, cast
from hashlib import md5
from functools import lru_cache

import httpx
from backend.shared.http import DEFAULT_TIMEOUT
import asyncio
import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.routing import APIRoute
from sse_starlette.sse import EventSourceResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
import sqlalchemy as sa

from .auth import (
    verify_token,
    require_role,
    revoke_token,
    router as auth_router,
)
from .models import (
    ApprovalStatus,
    FlagState,
    MetadataPatch,
    PendingRuns,
    PurgeResult,
    RefreshRequest,
    RoleAssignment,
    RoleItem,
    RolesResponse,
    StatusResponse,
    TokenResponse,
    UserResponse,
    UsernameRequest,
)
from .audit import log_admin_action
from backend.analytics.auth import create_access_token
from datetime import UTC, datetime
from backend.shared.responses import cache_header
from backend.shared.cache import async_get, async_set, get_async_client
from backend.shared.config import settings as shared_settings
from backend.shared.feature_flags import (
    list_flags as ff_list,
    set_flag as ff_set,
    is_enabled,
)
from backend.shared.db import session_scope
from backend.shared.db.models import AuditLog, UserRole, RefreshToken
from uuid import uuid4
from datetime import timedelta
from scripts import maintenance


class CacheControlRoute(APIRoute):
    """APIRoute that attaches caching headers and uses Redis for GET responses."""

    def get_route_handler(self):  # type: ignore[override]
        """Return handler that caches GET responses based on request URI."""
        original_handler = super().get_route_handler()

        async def handler(request: Request) -> Response:
            cache_key = None
            ttl = settings.request_cache_ttl
            if request.method == "GET" and ttl > 0:
                key_bytes = f"{request.url.path}?{request.url.query}".encode()
                cache_key = f"route_cache:{md5(key_bytes).hexdigest()}"
                cached = await async_get(cache_key)
                if cached is not None:
                    response = Response(content=cached, media_type="application/json")
                    response.headers.update(cache_header(ttl))
                    return response

            response = await original_handler(request)
            if request.method == "GET":
                response.headers.update(cache_header())
                if cache_key and response.status_code < 400:
                    await async_set(cache_key, response.body.decode(), ttl=ttl)
            return response

        return handler


from .rate_limiter import UserRateLimiter
from .settings import settings

SIGNAL_INGESTION_URL = settings.signal_ingestion_url
PUBLISHER_URL = settings.publisher_url
TRPC_SERVICE_URL = settings.trpc_service_url
OPTIMIZATION_URL = settings.optimization_url
MONITORING_URL = settings.monitoring_url
ANALYTICS_URL = settings.analytics_url

# Redis set storing runs awaiting manual approval
PENDING_RUNS_KEY = "pending_runs"

# Prefix for cached trending keyword lists
TRENDING_CACHE_PREFIX = "trending:list:"

# Cached ``httpx.AsyncClient`` instances for external services
_CLIENTS: dict[str, httpx.AsyncClient] = {}


def _get_client(service: str) -> httpx.AsyncClient:
    """Return a cached HTTP client for ``service``."""
    client = _CLIENTS.get(service)
    if client is None:
        client = httpx.AsyncClient()
        if hasattr(client, "timeout"):
            try:
                client.timeout = DEFAULT_TIMEOUT
            except Exception:  # pragma: no cover - property may be read-only
                pass
        _CLIENTS[service] = client
    return client


async def close_http_clients() -> None:
    """Close all cached HTTP clients."""
    for client in _CLIENTS.values():
        try:
            await client.aclose()
        except Exception:  # pragma: no cover - closing best effort
            pass
    _CLIENTS.clear()


async def get_trending(limit: int = 10, offset: int = 0) -> list[str]:
    """Return trending keywords via ingestion service with Redis caching."""
    cache_key = f"{TRENDING_CACHE_PREFIX}{limit}:{offset}"
    cached = await async_get(cache_key)
    if cached:
        return cast(list[str], json.loads(cached))

    url = f"{SIGNAL_INGESTION_URL}/trending?limit={limit}&offset={offset}"
    client = _get_client("signal_ingestion")
    resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    result = cast(list[str], resp.json())
    await async_set(
        cache_key,
        json.dumps(result),
        ttl=shared_settings.trending_cache_ttl,
    )
    return result


# Mapping of services to their health check endpoints
HEALTH_ENDPOINTS: dict[str, str] = {
    "api_gateway": "http://api-gateway:8000/health",
    "signal_ingestion": "http://signal-ingestion:8004/health",
    "scoring_engine": "http://scoring-engine:5002/health",
    "mockup_generation": "http://mockup-generation:8000/health",
    "marketplace_publisher": f"{PUBLISHER_URL}/health",
    "optimization": f"{OPTIMIZATION_URL}/health",
    "monitoring": f"{MONITORING_URL}/health",
    "analytics": f"{ANALYTICS_URL}/health",
    "feedback_loop": "http://feedback-loop:8000/health",
    "orchestrator": "http://orchestrator:3000/health",
}
auth_scheme = HTTPBearer()

router = APIRouter(route_class=CacheControlRoute)

optimization_limiter = UserRateLimiter(
    settings.rate_limit_per_user,
    settings.rate_limit_window,
    get_async_client(),
)
monitoring_limiter = UserRateLimiter(
    settings.rate_limit_per_user,
    settings.rate_limit_window,
    get_async_client(),
)
analytics_limiter = UserRateLimiter(
    settings.rate_limit_per_user,
    settings.rate_limit_window,
    get_async_client(),
)


@lru_cache(maxsize=256)
def _cached_user(auth_header: str | None, client_host: str) -> str:
    """Return user identifier from ``auth_header`` or ``client_host``."""
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        try:
            payload = verify_token(credentials)
            sub = cast(str | None, payload.get("sub"))
            if sub is not None:
                return sub
        except Exception:  # pragma: no cover - invalid token
            return client_host
    return client_host


def _identify_user(request: Request) -> str:
    """Return identifier for rate limiting."""
    return _cached_user(
        request.headers.get("Authorization"), cast(str, request.client.host)
    )


async def _enforce_rate_limit(request: Request, limiter: UserRateLimiter) -> None:
    """Raise 429 if ``limiter`` has no remaining tokens for the user."""
    if not await limiter.acquire(_identify_user(request)):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")


async def limit_optimization(request: Request) -> None:
    """Rate limit dependency for the optimization router."""
    await _enforce_rate_limit(request, optimization_limiter)


async def limit_monitoring(request: Request) -> None:
    """Rate limit dependency for the monitoring router."""
    await _enforce_rate_limit(request, monitoring_limiter)


async def limit_analytics(request: Request) -> None:
    """Rate limit dependency for the analytics router."""
    await _enforce_rate_limit(request, analytics_limiter)


optimization_router = APIRouter(
    route_class=CacheControlRoute,
    tags=["Optimization"],
    dependencies=[Depends(limit_optimization)],
)
monitoring_router = APIRouter(
    route_class=CacheControlRoute,
    prefix="/monitoring",
    tags=["Monitoring"],
    dependencies=[Depends(limit_monitoring)],
)
analytics_router = APIRouter(
    route_class=CacheControlRoute,
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(limit_analytics)],
)
approvals_router = APIRouter(
    route_class=CacheControlRoute, prefix="/approvals", tags=["Approvals"]
)
privacy_router = APIRouter(
    route_class=CacheControlRoute,
    prefix="/privacy",
    tags=["Privacy"],
    dependencies=[Depends(require_role("admin"))],
)


@approvals_router.get("/", summary="List pending run IDs")
async def list_pending_runs() -> PendingRuns:
    """Return IDs of runs awaiting manual approval."""
    client = get_async_client()
    run_ids = await client.smembers(PENDING_RUNS_KEY)
    return PendingRuns(runs=sorted(run_ids))


@router.get("/status", tags=["Status"], summary="Public status")
async def status_endpoint() -> StatusResponse:
    """Public status endpoint."""
    return StatusResponse(status="ok")


@router.get("/api/health", tags=["Status"], summary="System health")
async def system_health() -> Dict[str, str]:
    """Return aggregated health information for all services."""
    results: dict[str, str] = {}
    client = _get_client("health")
    for name, url in HEALTH_ENDPOINTS.items():
        try:
            resp = await client.get(url)
            results[name] = (
                resp.json().get("status") if resp.status_code == 200 else "down"
            )
        except Exception:  # pragma: no cover - network failures
            results[name] = "down"
    return results


@router.post("/auth/token", tags=["Authentication"], summary="Issue JWT token")
async def issue_token(body: UsernameRequest) -> TokenResponse:
    """Return JWT tokens for ``username`` if it exists."""
    username = body.username
    with session_scope() as session:
        exists = session.execute(
            select(UserRole.id).where(UserRole.username == username)
        ).scalar_one_or_none()
        if exists is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
        refresh = str(uuid4())
        session.add(
            RefreshToken(
                token=refresh,
                username=username,
                expires_at=datetime.now(UTC) + timedelta(days=30),
            )
        )
    token = create_access_token({"sub": username})
    return TokenResponse(
        access_token=token,
        refresh_token=refresh,
    )


@router.post("/auth/revoke", tags=["Authentication"], summary="Revoke JWT token")
async def revoke_auth_token(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> StatusResponse:
    """Invalidate the provided JWT token."""
    payload = verify_token(credentials)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti is None or exp is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    revoke_token(str(jti), datetime.fromtimestamp(exp, tz=UTC))
    return StatusResponse(status="revoked")


@router.post("/auth/refresh", tags=["Authentication"], summary="Refresh JWT token")
async def refresh_auth_token(body: RefreshRequest) -> TokenResponse:
    """Issue new tokens using ``refresh_token`` in ``body``."""
    token = body.refresh_token
    if token is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Missing token")
    with session_scope() as session:
        entry = session.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        ).scalar_one_or_none()
        if entry is None or entry.expires_at < datetime.now(UTC):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        username = entry.username
        session.delete(entry)
        new_refresh = str(uuid4())
        session.add(
            RefreshToken(
                token=new_refresh,
                username=username,
                expires_at=datetime.now(UTC) + timedelta(days=30),
            )
        )
    access = create_access_token({"sub": username})
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
    )


@router.get("/roles", tags=["Roles"], summary="List user roles")
async def list_roles(
    page: int = 1,
    limit: int = 20,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, Any]:
    """Return paginated user role assignments."""
    if page < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid page")
    if limit < 1 or limit > 100:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid limit")
    offset = (page - 1) * limit
    with session_scope() as session:
        rows = session.execute(
            select(UserRole.username, UserRole.role).limit(limit).offset(offset)
        ).all()
        total = session.execute(select(sa.func.count(UserRole.username))).scalar()
    log_admin_action(payload.get("sub", "unknown"), "list_roles")
    return RolesResponse(
        total=total,
        items=[RoleItem(username=row.username, role=row.role) for row in rows],
    )


@router.post("/roles/{username}", tags=["Roles"], summary="Assign role")
async def assign_role(
    username: str,
    body: RoleAssignment,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> RoleItem:
    """Assign ``role`` in ``body`` to ``username``."""
    role = body.role
    if role not in {"admin", "editor", "viewer"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    with session_scope() as session:
        existing = session.execute(
            select(UserRole).where(UserRole.username == username)
        ).scalar_one_or_none()
        if existing:
            existing.role = role
        else:
            session.add(UserRole(username=username, role=role))
    log_admin_action(
        payload.get("sub", "unknown"),
        "assign_role",
        {"username": username, "role": role},
    )
    return RoleItem(username=username, role=role)


@router.get("/feature-flags", tags=["Flags"], summary="List feature flags")
async def list_feature_flags(
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, bool]:
    """Return current feature flag values."""
    log_admin_action(payload.get("sub", "unknown"), "list_flags")
    return ff_list()


@router.post("/feature-flags/{name}", tags=["Flags"], summary="Toggle feature flag")
async def toggle_feature_flag(
    name: str,
    body: FlagState,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, bool]:
    """Set ``name`` to ``body.enabled`` and return the new state."""
    ff_set(name, body.enabled)
    log_admin_action(
        payload.get("sub", "unknown"),
        "toggle_flag",
        {"flag": name, "enabled": body.enabled},
    )
    return {name: is_enabled(name)}


@router.get("/protected", tags=["Protected"], summary="Protected example")
async def protected(
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> UserResponse:
    """Protected endpoint requiring ``admin`` role."""
    log_admin_action(payload.get("sub", "unknown"), "access_protected")
    return UserResponse(user=payload.get("sub"))


@router.post("/maintenance/cleanup", tags=["Maintenance"], summary="Run cleanup")
async def trigger_cleanup(
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> StatusResponse:
    """Run cleanup tasks immediately."""
    maintenance.archive_old_mockups()
    maintenance.purge_stale_records()
    log_admin_action(payload.get("sub", "unknown"), "trigger_cleanup")
    return StatusResponse(status="ok")


@privacy_router.delete("/signals", summary="Purge stored PII")
async def purge_pii_endpoint(
    limit: int | None = None,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> PurgeResult:
    """Remove PII from stored signals."""
    from signal_ingestion.privacy import purge_pii_rows

    purged = await purge_pii_rows(limit)
    log_admin_action(payload.get("sub", "unknown"), "purge_pii", {"rows": purged})
    return PurgeResult(status="ok", purged=purged)


@approvals_router.post("/{run_id}", summary="Approve job run")
async def approve_run(
    run_id: str,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> StatusResponse:
    """Approve the Dagster run identified by ``run_id``."""
    await async_set(f"approval:{run_id}", "true", ttl=3600)
    await get_async_client().srem(PENDING_RUNS_KEY, run_id)
    log_admin_action(payload.get("sub", "unknown"), "approve_run", {"run_id": run_id})
    return StatusResponse(status="approved")


@approvals_router.delete("/{run_id}", summary="Reject job run")
async def reject_run(
    run_id: str,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> StatusResponse:
    """Reject the Dagster run identified by ``run_id``."""
    await get_async_client().srem(PENDING_RUNS_KEY, run_id)
    log_admin_action(payload.get("sub", "unknown"), "reject_run", {"run_id": run_id})
    return StatusResponse(status="rejected")


@approvals_router.get("/{run_id}", summary="Check approval status")
async def check_approval(run_id: str) -> ApprovalStatus:
    """Return ``True`` if ``run_id`` has been approved."""
    approved = await async_get(f"approval:{run_id}") is not None
    return ApprovalStatus(approved=approved)


@router.post("/trpc/{procedure}", tags=["tRPC"], summary="Proxy tRPC call")
async def trpc_endpoint(
    procedure: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> Response:
    """Proxy tRPC call to the configured backend service."""
    verify_token(credentials)
    url = f"{TRPC_SERVICE_URL}/trpc/{procedure}"
    client = _get_client("trpc")
    response = await client.post(
        url,
        json=await request.json(),
        headers={"Authorization": f"Bearer {credentials.credentials}"},
    )
    if response.status_code != 200:
        raise HTTPException(response.status_code, response.text)
    body = response.text
    etag = md5(body.encode("utf-8")).hexdigest()
    if request.headers.get("If-None-Match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return Response(
        content=body,
        media_type="application/json",
        headers={"ETag": etag},
    )


@optimization_router.get(
    "/optimizations",
    summary="Optimization suggestions",
)
async def optimizations() -> list[str]:
    """Return cost optimization suggestions from the optimization service."""
    url = f"{OPTIMIZATION_URL}/optimizations"
    client = _get_client("optimization")
    resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(list[str], resp.json())


@router.get("/trending", tags=["Trending"], summary="Popular keywords")
async def trending(limit: int = 10, offset: int = 0) -> list[str]:
    """Return trending keywords from the ingestion service."""
    return await get_trending(limit, offset)


@monitoring_router.get("/overview", summary="System overview")
async def monitoring_overview() -> Dict[str, Any]:
    """Proxy overview metrics from the monitoring service."""
    url = f"{MONITORING_URL}/overview"
    client = _get_client("monitoring")
    resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(Dict[str, Any], resp.json())


@monitoring_router.get("/status", summary="Service status")
async def monitoring_status() -> Dict[str, Any]:
    """Proxy service status from the monitoring service."""
    url = f"{MONITORING_URL}/status"
    client = _get_client("monitoring")
    resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(Dict[str, Any], resp.json())


@monitoring_router.get("/metrics", summary="Monitoring metrics")
async def monitoring_metrics() -> Response:
    """Proxy Prometheus metrics from the monitoring service."""
    url = f"{MONITORING_URL}/metrics"
    client = _get_client("monitoring")
    resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return Response(
        content=resp.content,
        media_type=resp.headers.get("content-type", "text/plain"),
    )


@analytics_router.get("/ab_test_results/{ab_test_id}", summary="A/B test results")
async def ab_test_results(ab_test_id: int) -> Dict[str, Any]:
    """Proxy aggregated A/B test results."""
    url = f"{ANALYTICS_URL}/ab_test_results/{ab_test_id}"
    client = _get_client("analytics")
    resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(Dict[str, Any], resp.json())


@analytics_router.get("/low_performers", summary="Lowest performing listings")
async def low_performers(page: int = 1, limit: int = 10) -> Dict[str, Any]:
    """Proxy low performer data from the analytics service."""
    if page < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid page")
    if limit < 1 or limit > 100:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid limit")
    offset = (page - 1) * limit
    url = f"{ANALYTICS_URL}/low_performers?limit={limit}&offset={offset}"
    client = _get_client("analytics")
    resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(Dict[str, Any], resp.json())


@optimization_router.get(
    "/recommendations",
    summary="Top optimization actions",
)
async def recommendations() -> list[str]:
    """Return top optimization actions from the optimization service."""
    url = f"{OPTIMIZATION_URL}/recommendations"
    client = _get_client("optimization")
    resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(list[str], resp.json())


@optimization_router.get("/metrics", summary="Optimization metrics")
async def optimization_metrics() -> Response:
    """Proxy Prometheus metrics from the optimization service."""
    url = f"{OPTIMIZATION_URL}/metrics"
    client = _get_client("optimization")
    resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return Response(
        content=resp.content,
        media_type=resp.headers.get("content-type", "text/plain"),
    )


@router.get("/audit-logs", tags=["Audit"], summary="Retrieve audit logs")
async def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, Any]:
    """Return paginated audit log entries."""
    if page < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid page")
    if limit < 1 or limit > 100:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid limit")
    offset = (page - 1) * limit
    with session_scope() as session:
        rows = (
            session.execute(
                select(AuditLog)
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )
        total = session.execute(select(sa.func.count(AuditLog.id))).scalar()
    log_admin_action(payload.get("sub", "unknown"), "get_audit_logs")
    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "username": r.username,
                "action": r.action,
                "details": r.details,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in rows
        ],
    }


@router.get("/models", tags=["Models"], summary="List AI models")
async def get_models(
    limit: int = 100,
    offset: int = 0,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> list[dict[str, Any]]:
    """Return AI models with pagination."""
    from mockup_generation.model_repository import list_models

    log_admin_action(payload.get("sub", "unknown"), "list_models")
    return [m.__dict__ for m in list_models(limit=limit, offset=offset)]


@router.post("/models/{model_id}/default", tags=["Models"], summary="Set default model")
async def switch_default_model(
    model_id: int,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Switch the default model used for mockup generation."""
    from mockup_generation.model_repository import set_default

    try:
        set_default(model_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    log_admin_action(payload.get("sub", "unknown"), "switch_model", {"id": model_id})
    return {"status": "ok"}


@router.patch("/publish-tasks/{task_id}", tags=["Publish"], summary="Edit publish task")
async def edit_publish_task(
    task_id: int,
    body: MetadataPatch,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Edit metadata for a pending publish task."""
    url = f"{PUBLISHER_URL}/tasks/{task_id}"
    client = _get_client("publisher")
    resp = await client.patch(url, json=body.model_dump())
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    log_admin_action(
        payload.get("sub", "unknown"),
        "edit_publish_task",
        {"task_id": task_id, "metadata": body.model_dump()},
    )
    return {"status": "updated"}


@router.post(
    "/publish-tasks/{task_id}/retry", tags=["Publish"], summary="Retry publish task"
)
async def retry_publish_task(
    task_id: int,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Re-trigger publishing for a task."""
    url = f"{PUBLISHER_URL}/tasks/{task_id}/retry"
    client = _get_client("publisher")
    resp = await client.post(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    log_admin_action(
        payload.get("sub", "unknown"),
        "retry_publish_task",
        {"task_id": task_id},
    )
    return {"status": "scheduled"}


@router.websocket("/ws/metrics")
async def metrics_ws(websocket: WebSocket) -> None:
    """Stream monitoring metrics to the connected client."""
    await websocket.accept()
    await websocket.send_json({"interval_ms": settings.ws_interval_ms})
    try:
        client = _get_client("monitoring")
        while True:
            overview_req = client.get(f"{MONITORING_URL}/overview")
            analytics_req = client.get(f"{ANALYTICS_URL}/analytics")
            async with asyncio.TaskGroup() as tg:
                overview_task = tg.create_task(overview_req)
                analytics_task = tg.create_task(analytics_req)
            overview = overview_task.result()
            analytics = analytics_task.result()
            data: Dict[str, Any] = {}
            if overview.status_code == 200:
                data.update(cast(Dict[str, Any], overview.json()))
            if analytics.status_code == 200:
                data.update(cast(Dict[str, Any], analytics.json()))
            await websocket.send_json(data)
            await asyncio.sleep(settings.ws_interval_ms / 1000)
    except WebSocketDisconnect:
        return


@router.get("/sse/metrics")
async def metrics_sse() -> EventSourceResponse:
    """Stream monitoring metrics using Server-Sent Events."""

    async def event_generator() -> AsyncGenerator[str, None]:
        client = _get_client("monitoring")
        while True:
            overview_req = client.get(f"{MONITORING_URL}/overview")
            analytics_req = client.get(f"{ANALYTICS_URL}/analytics")
            async with asyncio.TaskGroup() as tg:
                overview_task = tg.create_task(overview_req)
                analytics_task = tg.create_task(analytics_req)
            overview = overview_task.result()
            analytics = analytics_task.result()
            data: Dict[str, Any] = {}
            if overview.status_code == 200:
                data.update(cast(Dict[str, Any], overview.json()))
            if analytics.status_code == 200:
                data.update(cast(Dict[str, Any], analytics.json()))
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(settings.ws_interval_ms / 1000)

    return EventSourceResponse(event_generator())


router.include_router(optimization_router)
router.include_router(monitoring_router)
router.include_router(analytics_router)
router.include_router(approvals_router)
router.include_router(privacy_router)
router.include_router(auth_router)
