"""JWT authentication utilities for the API gateway."""

from typing import Any, Dict, Callable, Iterable, cast

from fastapi import APIRouter, Depends, HTTPException, status

from .models import UserResponse

from backend.shared.auth import jwt as shared_jwt

# Re-export shared constants and helpers for backward compatibility
create_access_token = shared_jwt.create_access_token
verify_token = shared_jwt.verify_token
revoke_token = shared_jwt.revoke_token
auth_scheme = shared_jwt.auth_scheme
SECRET_KEY = shared_jwt.SECRET_KEY
ALGORITHM = shared_jwt.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = shared_jwt.ACCESS_TOKEN_EXPIRE_MINUTES


def _extract_roles(payload: Dict[str, Any]) -> Iterable[str]:
    """Return roles from ``payload`` if present."""
    roles = payload.get("roles")
    if isinstance(roles, list):
        return cast(Iterable[str], roles)
    return []


def require_role(required_role: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Ensure the authenticated user has ``required_role``."""

    def _checker(payload: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
        if required_role not in _extract_roles(payload):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role"
            )
        return payload

    return _checker


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/validate", summary="Validate Auth0 JWT")
def validate_token(payload: Dict[str, Any] = Depends(verify_token)) -> UserResponse:
    """Return the authenticated user if ``payload`` is valid."""
    return UserResponse(user=cast(str | None, payload.get("sub")))
