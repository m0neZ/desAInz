"""API routes including REST and tRPC-compatible endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from .auth import verify_token, require_role
from backend.shared.db import session_scope
from backend.shared.db.models import UserRole

router = APIRouter()


@router.get("/status")  # type: ignore[misc]
async def status_endpoint() -> Dict[str, str]:
    """Public status endpoint."""
    return {"status": "ok"}


@router.get("/roles")  # type: ignore[misc]
async def list_roles(
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> list[Dict[str, str]]:
    """Return all user role assignments."""
    with session_scope() as session:
        rows = session.execute(select(UserRole.username, UserRole.role)).all()
    return [{"username": row.username, "role": row.role} for row in rows]


@router.post("/roles/{username}")  # type: ignore[misc]
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
    return {"username": username, "role": role}


@router.get("/protected")  # type: ignore[misc]
async def protected(
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, Any]:
    """Protected endpoint requiring ``admin`` role."""
    return {"user": payload.get("sub")}


@router.post("/trpc/{procedure}")  # type: ignore[misc]
async def trpc_endpoint(
    procedure: str,
    payload: Dict[str, Any] = Depends(verify_token),
) -> Dict[str, Any]:
    """TRPC-compatible endpoint."""
    if procedure == "ping":
        return {"result": {"message": "pong", "user": payload.get("sub")}}
    return {"error": f"Procedure '{procedure}' not found"}
