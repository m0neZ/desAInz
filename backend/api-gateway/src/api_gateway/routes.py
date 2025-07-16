"""API routes including REST and tRPC-compatible endpoints."""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import select

from fastapi import APIRouter, Depends, HTTPException, status

from backend.shared.db import session_scope
from backend.shared.db.models import Role, UserRole
from .auth import require_role, verify_token

router = APIRouter()


@router.get("/status")  # type: ignore[misc]
async def status_endpoint() -> Dict[str, str]:
    """Public status endpoint."""
    return {"status": "ok"}


@router.get("/protected")  # type: ignore[misc]
async def protected(
    payload: Dict[str, Any] = Depends(require_role("viewer")),
) -> Dict[str, Any]:
    """Protected endpoint requiring a valid token."""
    return {"user": payload.get("sub")}


@router.post("/trpc/{procedure}")  # type: ignore[misc]
async def trpc_endpoint(
    procedure: str,
    payload: Dict[str, Any] = Depends(verify_token),
) -> Dict[str, Any]:
    """tRPC-compatible endpoint."""
    if procedure == "ping":
        return {"result": {"message": "pong", "user": payload.get("sub")}}
    return {"error": f"Procedure '{procedure}' not found"}


@router.post("/roles/{user_id}")  # type: ignore[misc]
async def assign_role(
    user_id: str,
    role: str,
    _payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Assign a role to a user."""
    with session_scope() as session:
        role_obj = session.execute(
            select(Role).where(Role.name == role)
        ).scalar_one_or_none()
        if role_obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
            )
        existing = session.execute(
            select(UserRole).where(UserRole.user_id == user_id)
        ).scalar_one_or_none()
        if existing:
            existing.role_id = role_obj.id
        else:
            session.add(UserRole(user_id=user_id, role_id=role_obj.id))
    return {"status": "assigned"}
