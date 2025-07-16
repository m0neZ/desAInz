"""API routes including REST and tRPC-compatible endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

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
    return {"user": payload.get("sub")}


@router.post("/trpc/{procedure}")
async def trpc_endpoint(
    procedure: str,
    payload: Dict[str, Any] = Depends(verify_token),
) -> Dict[str, Any]:
    """tRPC-compatible endpoint."""
    if procedure == "ping":
        return {"result": {"message": "pong", "user": payload.get("sub")}}
    return {"error": f"Procedure '{procedure}' not found"}
