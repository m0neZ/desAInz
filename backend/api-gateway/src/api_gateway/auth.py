"""JWT authentication utilities."""

from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Callable, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from backend.shared.db import session_scope
from backend.shared.db.models import Role, UserRole


SECRET_KEY = "change_this"  # In production use env var
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

auth_scheme = HTTPBearer()


def create_access_token(data: Dict[str, Any]) -> str:
    """Create a JWT token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return str(jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> Dict[str, Any]:
    """Verify a JWT token and return the payload."""
    token = credentials.credentials
    try:
        payload = cast(
            Dict[str, Any], jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        )
    except JWTError as exc:  # pragma: no cover
        # jose raises JWTError for all issues
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token"
        ) from exc
    return payload


def require_role(required: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Dependency factory ensuring the user has the required role."""

    def _verify(payload: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
        user_id = str(payload.get("sub"))
        with session_scope() as session:
            role = (
                session.query(Role.name)
                .join(UserRole)
                .filter(UserRole.user_id == user_id)
                .scalar()
            )
        if role != required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return payload

    return _verify
