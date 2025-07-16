"""API routes including REST and tRPC-compatible endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status as http_status

from .auth import require_role, verify_token
from backend.shared.db import session_scope
from backend.shared.db.models import Role, UserRole
from pydantic import BaseModel

router = APIRouter()


class AssignRoleRequest(BaseModel):
    """Request body for role assignment."""

    user_id: str
    role: str


@router.get("/status")
async def status() -> Dict[str, str]:
    """Public status endpoint."""
    return {"status": "ok"}


@router.get("/protected")
async def protected(
    payload: Dict[str, Any] = Depends(require_role("viewer")),
) -> Dict[str, Any]:
    """Protected endpoint requiring viewer role."""
    return {"user": payload.get("sub")}


@router.post("/roles/assign")
async def assign_role(
    request: AssignRoleRequest,
    payload: Dict[str, Any] = Depends(require_role("admin")),
) -> Dict[str, str]:
    """Assign a role to a user."""
    with session_scope() as session:
        role = session.query(Role).filter_by(name=request.role).one_or_none()
        if role is None:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "Unknown role")
        existing = (
            session.query(UserRole).filter_by(user_id=request.user_id).one_or_none()
        )
        if existing:
            existing.role = role
        else:
            session.add(UserRole(user_id=request.user_id, role=role))
    return {"status": "assigned"}


@router.post("/trpc/{procedure}")
async def trpc_endpoint(
    procedure: str,
    payload: Dict[str, Any] = Depends(verify_token),
) -> Dict[str, Any]:
    """TRPC-compatible endpoint."""
    if procedure == "ping":
        return {"result": {"message": "pong", "user": payload.get("sub")}}
    return {"error": f"Procedure '{procedure}' not found"}
