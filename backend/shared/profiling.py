"""Profiling utilities for FastAPI and Flask apps."""

from __future__ import annotations

import cProfile
import os
import time
from pathlib import Path
from typing import Callable, Coroutine

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from flask import Flask


_PROFILING_ENV = "ENABLE_PROFILING"


class _FastAPIProfilerMiddleware(BaseHTTPMiddleware):
    """Collect profiling data for each request."""

    def __init__(self, app: ASGIApp, profile_dir: Path) -> None:
        super().__init__(app)
        self.profile_dir = profile_dir

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Coroutine[None, None, Response]],
    ) -> Response:
        if os.environ.get(_PROFILING_ENV) != "1":
            return await call_next(request)
        profile = cProfile.Profile()
        profile.enable()
        try:
            response = await call_next(request)
        finally:
            profile.disable()
            self._dump(profile, request.url.path)
        return response

    def _dump(self, profile: cProfile.Profile, path: str) -> None:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{path.strip('/').replace('/', '_') or 'root'}_{int(time.time())}.prof"
        )
        profile.dump_stats(self.profile_dir / filename)


class _FlaskProfilerMiddleware:
    """WSGI middleware for profiling Flask requests."""

    def __init__(self, app: Flask, profile_dir: Path) -> None:
        self.app = app
        self.profile_dir = profile_dir

    def __call__(self, environ: dict, start_response: Callable) -> list[bytes]:
        if os.environ.get(_PROFILING_ENV) != "1":
            return self.app(environ, start_response)  # type: ignore[return-value]
        profile = cProfile.Profile()
        profile.enable()
        try:
            return self.app(environ, start_response)  # type: ignore[return-value]
        finally:
            profile.disable()
            path = environ.get("PATH_INFO", "root")
            self._dump(profile, path)

    def _dump(self, profile: cProfile.Profile, path: str) -> None:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{path.strip('/').replace('/', '_') or 'root'}_{int(time.time())}.prof"
        )
        profile.dump_stats(self.profile_dir / filename)


def configure_profiling(app: FastAPI | Flask, profile_dir: Path | None = None) -> None:
    """Attach profiling middleware to the given ``app``."""
    directory = profile_dir or Path("/tmp/profiles")
    if isinstance(app, FastAPI):
        app.add_middleware(_FastAPIProfilerMiddleware, profile_dir=directory)
    else:
        app.wsgi_app = _FlaskProfilerMiddleware(
            app.wsgi_app, directory
        )  # type: ignore[assignment]
