"""Profiling utilities for FastAPI and Flask apps."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Coroutine

from fastapi import FastAPI, Request, Response
from flask import Flask, g, request

__all__ = ["add_fastapi_profiler", "add_flask_profiler"]


def add_fastapi_profiler(app: FastAPI) -> None:
    """Attach middleware measuring request duration in milliseconds."""
    logger = logging.getLogger("profiling")

    @app.middleware("http")
    async def profile_middleware(
        request: Request,
        call_next: Callable[[Request], Coroutine[Any, Any, Response]],
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request completed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "duration_ms": duration_ms,
            },
        )
        return response


def add_flask_profiler(app: Flask) -> None:
    """Attach hooks measuring request duration in milliseconds."""
    logger = logging.getLogger("profiling")

    @app.before_request
    def _start_timer() -> None:
        g.start_time = time.perf_counter()

    @app.after_request
    def _log_response(response: Response) -> Response:
        start: float = getattr(g, "start_time", time.perf_counter())
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request completed",
            extra={
                "path": request.path,
                "method": request.method,
                "duration_ms": duration_ms,
            },
        )
        return response
