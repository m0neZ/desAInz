"""Helper utilities for HTTP responses."""

from __future__ import annotations

from fastapi.responses import JSONResponse, Response

CACHE_TTL_SECONDS = 60


def cache_header(ttl: int = CACHE_TTL_SECONDS) -> dict[str, str]:
    """Return Cache-Control header dictionary with ``ttl`` seconds."""
    return {"Cache-Control": f"public, max-age={ttl}"}


def json_cached(
    payload: dict[str, object], ttl: int = CACHE_TTL_SECONDS
) -> JSONResponse:
    """Return ``JSONResponse`` with Cache-Control header."""
    return JSONResponse(content=payload, headers=cache_header(ttl))
