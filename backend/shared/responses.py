"""Helper utilities for HTTP responses."""

from __future__ import annotations

import zlib
from typing import AsyncIterator, Iterable

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


def gzip_iter(text_iter: Iterable[str]) -> Iterable[bytes]:
    """Yield gzip-compressed bytes from an iterable of strings."""
    compressor = zlib.compressobj(wbits=31)
    for chunk in text_iter:
        data = compressor.compress(chunk.encode())
        if data:
            yield data
    data = compressor.flush()
    if data:
        yield data


async def gzip_aiter(text_iter: AsyncIterator[str]) -> AsyncIterator[bytes]:
    """Yield gzip-compressed bytes from an async iterator of strings."""
    compressor = zlib.compressobj(wbits=31)
    async for chunk in text_iter:
        data = compressor.compress(chunk.encode())
        if data:
            yield data
    data = compressor.flush()
    if data:
        yield data
