"""API routes including REST and tRPC-compatible endpoints."""

from typing import Any, Dict, cast
from hashlib import md5
import os

import httpx
from backend.shared.http import DEFAULT_TIMEOUT
import asyncio

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
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
import sqlalchemy as sa

from .auth import (
    verify_token,
    require_role,
    revoke_token,
)
from .models import FlagState, MetadataPatch, RoleAssignment, UsernameRequest
from .audit import log_admin_action
from backend.analytics.auth import create_access_token
from datetime import UTC, datetime
from backend.shared.cache import async_get, async_set, get_async_client
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

SIGNAL_INGESTION_URL = os.environ.get(
    "SIGNAL_INGESTION_URL", "http://signal-ingestion:8004"
)
from .rate_limiter import UserRateLimiter
from .settings import settings

PUBLISHER_URL = os.environ.get(
    "PUBLISHER_URL",
    "http://marketplace-publisher:8000",
)

TRPC_SERVICE_URL = os.environ.get("TRPC_SERVICE_URL", "http://backend:8000")
OPTIMIZATION_URL = os.environ.get(
    "OPTIMIZATION_URL",
    "http://optimization:8000",
)
MONITORING_URL = os.environ.get(
    "MONITORING_URL",
    "http://monitoring:8000",
)
ANALYTICS_URL = os.environ.get(
    "ANALYTICS_URL",
    "http://analytics:8000",
)

# Redis set storing runs awaiting manual approval
PENDING_RUNS_KEY = "pending_runs"

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
}
auth_scheme = HTTPBearer()

router = APIRouter()

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


def _identify_user(request: Request) -> str:
    """Return identifier for rate limiting."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        try:
            payload = verify_token(credentials)
            sub = cast(str | None, payload.get("sub"))
            if sub is not None:
                return sub
        except Exception:  # pragma: no cover - invalid token
            pass
    return cast(str, request.client.host)


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
    tags=["Optimization"],
    dependencies=[Depends(limit_optimization)],
)
monitoring_router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"],
    dependencies=[Depends(limit_monitoring)],
)
analytics_router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(limit_analytics)],
)
approvals_router = APIRouter(prefix="/approvals", tags=["Approvals"])
privacy_router = APIRouter(
    prefix="/privacy",
    tags=["Privacy"],
    dependencies=[Depends(require_role("admin"))],
)


@approvals_router.get("/", summary="List pending run IDs")
async def list_pending_runs() -> Dict[str, list[str]]:
    """Return IDs of runs awaiting manual approval."""
    client = get_async_client()
    run_ids = await client.smembers(PENDING_RUNS_KEY)
    return {"runs": sorted(run_ids)}


@router.get("/status", tags=["Status"], summary="Public status")
async def status_endpoint() -> Dict[str, str]:
    """Public status endpoint."""
    return {"status": "ok"}


@router.get("/api/health", tags=["Status"], summary="System health")
async def system_health() -> Dict[str, str]:
    """Return aggregated health information for all services."""
    results: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
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
async def issue_token(body: UsernameRequest) -> Dict[str, str]:
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
    return {
        "access_token": token,
        "refresh_token": refresh,
        "token_type": "bearer",
    }


@router.post("/auth/revoke", tags=["Authentication"], summary="Revoke JWT token")
async def revoke_auth_token(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> Dict[str, str]:
    """Invalidate the provided JWT token."""
    payload = verify_token(credentials)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti is None or exp is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    revoke_token(str(jti), datetime.fromtimestamp(exp, tz=UTC))
    return {"status": "revoked"}


@router.post("/auth/refresh", tags=["Authentication"], summary="Refresh JWT token")
async def refresh_auth_token(body: Dict[str, str]) -> Dict[str, str]:
    """Issue new tokens using ``refresh_token`` in ``body``."""
    token = body.get("refresh_token")
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
    return {
        "access_token": access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.get("/roles", tags=["Roles"], summary="List user roles")
async def list_roles(
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> list[Dict[str, str]]:
    """Return all user role assignments."""
    with session_scope() as session:
        rows = session.execute(select(UserRole.username, UserRole.role)).all()
    log_admin_action(payload.get("sub", "unknown"), "list_roles")
    return [{"username": row.username, "role": row.role} for row in rows]


@router.post("/roles/{username}", tags=["Roles"], summary="Assign role")
async def assign_role(
    username: str,
    body: RoleAssignment,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
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
    return {"username": username, "role": role}


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
) -> Dict[str, Any]:
    """Protected endpoint requiring ``admin`` role."""
    log_admin_action(payload.get("sub", "unknown"), "access_protected")
    return {"user": payload.get("sub")}


@router.post("/maintenance/cleanup", tags=["Maintenance"], summary="Run cleanup")
async def trigger_cleanup(
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Run cleanup tasks immediately."""
    maintenance.archive_old_mockups()
    maintenance.purge_stale_records()
    log_admin_action(payload.get("sub", "unknown"), "trigger_cleanup")
    return {"status": "ok"}


@privacy_router.delete("/signals", summary="Purge stored PII")
async def purge_pii_endpoint(
    limit: int | None = None,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, Any]:
    """Remove PII from stored signals."""
    from signal_ingestion.privacy import purge_pii_rows

    purged = await purge_pii_rows(limit)
    log_admin_action(payload.get("sub", "unknown"), "purge_pii", {"rows": purged})
    return {"status": "ok", "purged": purged}


@approvals_router.post("/{run_id}", summary="Approve job run")
async def approve_run(
    run_id: str,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Approve the Dagster run identified by ``run_id``."""
    await async_set(f"approval:{run_id}", "true", ttl=3600)
    await get_async_client().srem(PENDING_RUNS_KEY, run_id)
    log_admin_action(payload.get("sub", "unknown"), "approve_run", {"run_id": run_id})
    return {"status": "approved"}


@approvals_router.get("/{run_id}", summary="Check approval status")
async def check_approval(run_id: str) -> Dict[str, bool]:
    """Return ``True`` if ``run_id`` has been approved."""
    approved = await async_get(f"approval:{run_id}") is not None
    return {"approved": approved}


@router.post("/trpc/{procedure}", tags=["tRPC"], summary="Proxy tRPC call")
async def trpc_endpoint(
    procedure: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> Response:
    """Proxy tRPC call to the configured backend service."""
    verify_token(credentials)
    url = f"{TRPC_SERVICE_URL}/trpc/{procedure}"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
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
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(list[str], resp.json())


@router.get("/trending", tags=["Trending"], summary="Popular keywords")
async def trending(limit: int = 10) -> list[str]:
    """Return up to ``limit`` trending keywords from the ingestion service."""
    url = f"{SIGNAL_INGESTION_URL}/trending?limit={limit}"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(list[str], resp.json())


@monitoring_router.get("/overview", summary="System overview")
async def monitoring_overview() -> Dict[str, Any]:
    """Proxy overview metrics from the monitoring service."""
    url = f"{MONITORING_URL}/overview"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(Dict[str, Any], resp.json())


@monitoring_router.get("/status", summary="Service status")
async def monitoring_status() -> Dict[str, Any]:
    """Proxy service status from the monitoring service."""
    url = f"{MONITORING_URL}/status"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(Dict[str, Any], resp.json())


@analytics_router.get("/ab_test_results/{ab_test_id}", summary="A/B test results")
async def ab_test_results(ab_test_id: int) -> Dict[str, Any]:
    """Proxy aggregated A/B test results."""
    url = f"{ANALYTICS_URL}/ab_test_results/{ab_test_id}"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(Dict[str, Any], resp.json())


@analytics_router.get("/low_performers", summary="Lowest performing listings")
async def low_performers(limit: int = 10) -> list[Dict[str, Any]]:
    """Proxy low performer data from the analytics service."""
    url = f"{ANALYTICS_URL}/low_performers?limit={limit}"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(list[Dict[str, Any]], resp.json())


@optimization_router.get(
    "/recommendations",
    summary="Top optimization actions",
)
async def recommendations() -> list[str]:
    """Return top optimization actions from the optimization service."""
    url = f"{OPTIMIZATION_URL}/recommendations"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return cast(list[str], resp.json())


@router.get("/audit-logs", tags=["Audit"], summary="Retrieve audit logs")
async def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, Any]:
    """Return paginated audit log entries."""
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
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> list[dict[str, Any]]:
    """Return all available AI models."""
    from mockup_generation.model_repository import list_models

    log_admin_action(payload.get("sub", "unknown"), "list_models")
    return [m.__dict__ for m in list_models()]


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
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
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
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
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
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            while True:
                overview = await client.get(f"{MONITORING_URL}/overview")
                analytics = await client.get(f"{MONITORING_URL}/analytics")
                data: Dict[str, Any] = {}
                if overview.status_code == 200:
                    data.update(cast(Dict[str, Any], overview.json()))
                if analytics.status_code == 200:
                    data.update(cast(Dict[str, Any], analytics.json()))
                await websocket.send_json(data)
                await asyncio.sleep(settings.ws_interval_ms / 1000)
    except WebSocketDisconnect:
        return


router.include_router(optimization_router)
router.include_router(monitoring_router)
router.include_router(analytics_router)
router.include_router(approvals_router)
router.include_router(privacy_router)
