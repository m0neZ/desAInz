"""Utilities for adding common security headers."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


def add_security_headers(app: FastAPI) -> None:
    """Attach security headers to all responses from ``app``."""

    async def _set_headers(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        if settings.content_security_policy:
            response.headers.setdefault(
                "Content-Security-Policy", settings.content_security_policy
            )
        if settings.hsts:
            response.headers.setdefault("Strict-Transport-Security", settings.hsts)
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=_set_headers)


def require_status_api_key(request: Request) -> None:
    """Validate API key header for readiness endpoints."""
    if not settings.allow_status_unauthenticated and not request.headers.get(
        "X-API-Key"
    ):
        raise HTTPException(status_code=401, detail="missing api key")
