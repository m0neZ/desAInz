"""JWT-based authentication utilities for the analytics service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Callable, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select

from backend.shared.db import session_scope
from backend.shared.db.models import UserRole
from backend.shared.config import settings as shared_settings

SECRET_KEY = shared_settings.secret_key or "change_this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

auth_scheme = HTTPBearer()


def create_access_token(data: Dict[str, Any]) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return cast(str, jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> Dict[str, Any]:
    """Verify the provided JWT token and return its payload."""
    token = credentials.credentials
    try:
        payload = cast(
            Dict[str, Any], jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        )
    except JWTError as exc:  # pragma: no cover - errors yield JWTError
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token",
        ) from exc
    return payload


def require_role(required_role: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Return dependency validating the authenticated user has ``required_role``."""

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
