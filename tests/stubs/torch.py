"""Minimal torch stub for unit tests."""


class cuda:
    """CUDA device functions."""

    @staticmethod
    def is_available() -> bool:  # pragma: no cover - simple stub
        """Return ``False`` as CUDA is unavailable during tests."""
        return False

    @staticmethod
    def empty_cache() -> None:  # pragma: no cover - simple stub
        """No-op cache clear."""
        return None

    @staticmethod
    def ipc_collect() -> None:  # pragma: no cover - simple stub
        """No-op IPC collector."""
        return None


__all__ = ["cuda"]
