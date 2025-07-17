"""API routes including REST and tRPC-compatible endpoints."""

from typing import Any, Dict, cast
import os

import httpx

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
import sqlalchemy as sa

from .auth import verify_token, require_role
from .audit import log_admin_action
from backend.shared.db import session_scope
from backend.shared.db.models import AuditLog, UserRole
from mockup_generation.model_repository import list_models, set_default
from scripts import maintenance

PUBLISHER_URL = os.environ.get(
    "PUBLISHER_URL",
    "http://marketplace-publisher:8000",
)

TRPC_SERVICE_URL = os.environ.get("TRPC_SERVICE_URL", "http://backend:8000")
auth_scheme = HTTPBearer()

router = APIRouter()


@router.get("/status")
async def status_endpoint() -> Dict[str, str]:
    """Public status endpoint."""
    return {"status": "ok"}


@router.get("/roles")
async def list_roles(
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> list[Dict[str, str]]:
    """Return all user role assignments."""
    with session_scope() as session:
        rows = session.execute(select(UserRole.username, UserRole.role)).all()
    log_admin_action(payload.get("sub", "unknown"), "list_roles")
    return [{"username": row.username, "role": row.role} for row in rows]


@router.post("/roles/{username}")
async def assign_role(
    username: str,
    body: Dict[str, str],
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Assign ``role`` in ``body`` to ``username``."""
    role = body.get("role")
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


@router.get("/protected")
async def protected(
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, Any]:
    """Protected endpoint requiring ``admin`` role."""
    log_admin_action(payload.get("sub", "unknown"), "access_protected")
    return {"user": payload.get("sub")}


@router.post("/maintenance/cleanup")
async def trigger_cleanup(
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Run cleanup tasks immediately."""
    maintenance.archive_old_mockups()
    maintenance.purge_stale_records()
    log_admin_action(payload.get("sub", "unknown"), "trigger_cleanup")
    return {"status": "ok"}


@router.post("/trpc/{procedure}")
async def trpc_endpoint(
    procedure: str,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> Dict[str, Any]:
    """Proxy tRPC call to the configured backend service."""
    verify_token(credentials)
    url = f"{TRPC_SERVICE_URL}/trpc/{procedure}"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=await request.json(),
            headers={"Authorization": f"Bearer {credentials.credentials}"},
        )
    if response.status_code != 200:
        raise HTTPException(response.status_code, response.text)
    return cast(Dict[str, Any], response.json())


@router.get("/audit-logs")
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


@router.get("/models")
async def get_models(
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> list[dict[str, Any]]:
    """Return all available AI models."""
    log_admin_action(payload.get("sub", "unknown"), "list_models")
    return [m.__dict__ for m in list_models()]


@router.post("/models/{model_id}/default")
async def switch_default_model(
    model_id: int,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Switch the default model used for mockup generation."""
    try:
        set_default(model_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    log_admin_action(payload.get("sub", "unknown"), "switch_model", {"id": model_id})
    return {"status": "ok"}


@router.patch("/publish-tasks/{task_id}")
async def edit_publish_task(
    task_id: int,
    body: Dict[str, Any],
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Edit metadata for a pending publish task."""
    url = f"{PUBLISHER_URL}/tasks/{task_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.patch(url, json=body)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    log_admin_action(
        payload.get("sub", "unknown"),
        "edit_publish_task",
        {"task_id": task_id, "metadata": body},
    )
    return {"status": "updated"}


@router.post("/publish-tasks/{task_id}/retry")
async def retry_publish_task(
    task_id: int,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Re-trigger publishing for a task."""
    url = f"{PUBLISHER_URL}/tasks/{task_id}/retry"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url)
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    log_admin_action(
        payload.get("sub", "unknown"),
        "retry_publish_task",
        {"task_id": task_id},
    )
    return {"status": "scheduled"}
