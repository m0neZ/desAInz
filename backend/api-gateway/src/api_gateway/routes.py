"""API routes including REST and tRPC-compatible endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from .audit import get_logs, record_action

from .auth import verify_token

router = APIRouter()


@router.get("/status")
async def status() -> Dict[str, str]:
    """Public status endpoint."""
    return {"status": "ok"}


@router.get("/protected")
async def protected(
    payload: Dict[str, Any] = Depends(verify_token),
) -> Dict[str, Any]:
    """Protected endpoint requiring a valid token."""
    record_action(payload.get("sub", "unknown"), "access_protected")
    return {"user": payload.get("sub")}


@router.post("/trpc/{procedure}")
async def trpc_endpoint(
    procedure: str,
    payload: Dict[str, Any] = Depends(verify_token),
) -> Dict[str, Any]:
    """TRPC-compatible endpoint."""
    if procedure == "ping":
        return {"result": {"message": "pong", "user": payload.get("sub")}}
    return {"error": f"Procedure '{procedure}' not found"}


@router.get("/admin/logs")
async def audit_logs(
    page: int = 1,
    limit: int = 50,
    payload: Dict[str, Any] = Depends(verify_token),
) -> Dict[str, Any]:
    """Return paginated audit logs."""
    record_action(payload.get("sub", "unknown"), "view_audit_logs")
    logs = get_logs(page, limit)
    return {"logs": logs, "page": page, "limit": limit}
