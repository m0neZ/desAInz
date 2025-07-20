"""Shared JWT authentication utilities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Callable, cast
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select

from backend.shared.db import session_scope
from backend.shared.db.models import RevokedToken
from backend.shared.config import settings as shared_settings

SECRET_KEY = shared_settings.secret_key or "change_this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

auth_scheme = HTTPBearer()


def create_access_token(data: Dict[str, Any]) -> str:
    """Return a signed JWT access token with a unique ``jti``."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "jti": str(uuid4())})
    return cast(str, jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> Dict[str, Any]:
    """Validate ``credentials`` and return the decoded payload."""
    token = credentials.credentials
    try:
        payload = cast(
            Dict[str, Any], jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        )
    except JWTError as exc:  # pragma: no cover - jose raises JWTError for any issue
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
        ) from exc
    jti = cast(str | None, payload.get("jti"))
    if jti is not None:
        with session_scope() as session:
            exists = session.execute(
                select(RevokedToken.id).where(RevokedToken.jti == jti)
            ).scalar_one_or_none()
        if exists is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token revoked",
            )
    return payload


def revoke_token(jti: str, expires_at: datetime) -> None:
    """Persist ``jti`` so the token cannot be used again."""
    with session_scope() as session:
        session.add(RevokedToken(jti=jti, expires_at=expires_at))
