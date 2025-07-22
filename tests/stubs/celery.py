"""Minimal Celery stub for tests."""

from types import SimpleNamespace


class Celery:
    """Simplified Celery class used in tests."""

    def __init__(self, *args: object, **_kwargs: object) -> None:
        self.conf = SimpleNamespace(result_backend=None)

    def task(self, *d_args: object, **d_kwargs: object):  # pragma: no cover
        """Return a decorator that leaves the function unmodified."""

        def decorator(func):
            return func

        return decorator


__all__ = ["Celery"]
