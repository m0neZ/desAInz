"""Simple request profiling middleware for HTTP requests."""

from __future__ import annotations

from logging import getLogger
import time
from typing import Any, Callable, Coroutine

from fastapi import FastAPI, Request, Response
from flask import Flask, request as flask_request

logger = getLogger(__name__)


def add_profiling(app: FastAPI | Flask) -> None:
    """Attach middleware to profile request durations."""
    if isinstance(app, FastAPI):

        @app.middleware("http")  # type: ignore[misc]
        async def _profile(
            request: Request,
            call_next: Callable[[Request], Coroutine[Any, Any, Response]],
        ) -> Response:
            start = time.perf_counter()
            response = await call_next(request)
            duration = (time.perf_counter() - start) * 1000
            logger.info(
                "request timing",
                extra={"path": request.url.path, "duration_ms": duration},
            )
            return response

    else:

        @app.before_request  # type: ignore[misc]
        def _before_request() -> None:
            setattr(flask_request, "_start_time", time.perf_counter())

        @app.after_request  # type: ignore[misc]
        def _after_request(response: Response) -> Response:
            start = getattr(flask_request, "_start_time", None)
            if start is not None:
                duration = (time.perf_counter() - start) * 1000
                logger.info(
                    "request timing",
                    extra={"path": flask_request.path, "duration_ms": duration},
                )
            return response
