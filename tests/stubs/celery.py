"""Minimal Celery stub for tests."""

from types import SimpleNamespace


class Celery:
    """Simplified Celery class used in tests."""

    def __init__(self, *args: object, **_kwargs: object) -> None:
        """Initialize the stub with minimal configuration."""
        self.conf = SimpleNamespace(result_backend=None)

    def task(self, *_: object, **__: object):  # pragma: no cover
        """Return a decorator that leaves the function unmodified."""

        def decorator(func):
            return func

        return decorator


__all__ = ["Celery"]
