"""JWT-based authentication utilities for the analytics service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Callable, cast

from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from backend.shared.auth import jwt as shared_jwt
from backend.shared.db import session_scope
from backend.shared.db.models import UserRole

# Re-export shared constants and helpers for backward compatibility
create_access_token = shared_jwt.create_access_token
verify_token = shared_jwt.verify_token
revoke_token = shared_jwt.revoke_token
auth_scheme = shared_jwt.auth_scheme
SECRET_KEY = shared_jwt.SECRET_KEY
ALGORITHM = shared_jwt.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = shared_jwt.ACCESS_TOKEN_EXPIRE_MINUTES


def require_role(required_role: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Return a dependency that checks the user has ``required_role``."""

    def _checker(payload: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
        username = cast(str | None, payload.get("sub"))
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
            )
        with session_scope() as session:
            role = session.execute(
                select(UserRole.role).where(UserRole.username == username)
            ).scalar_one_or_none()
        if role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return payload

    return _checker
