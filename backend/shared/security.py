"""Utilities for adding common security headers."""

from __future__ import annotations

from typing import Callable, Coroutine

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


def add_security_headers(app: FastAPI) -> None:
    """Attach security headers to all responses from ``app``."""

    async def _set_headers(
        request: Request,
        call_next: Callable[[Request], Coroutine[None, None, Response]],
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
