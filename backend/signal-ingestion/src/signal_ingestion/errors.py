"""Custom exceptions for the signal ingestion service."""


class SignalIngestionError(Exception):
    """Base class for signal ingestion errors."""


class UnknownAdapterError(SignalIngestionError):
    """Raised when an adapter name is not registered."""

    def __init__(self, adapter_name: str) -> None:
        """Store ``adapter_name`` and initialize the message."""
        super().__init__(f"Unknown adapter: {adapter_name}")
        self.adapter_name = adapter_name


class AdapterFetchError(SignalIngestionError):
    """Raised when fetching data from an adapter fails."""

    def __init__(self, adapter_name: str, message: str) -> None:
        """Store context for the failed fetch."""
        super().__init__(f"{adapter_name}: {message}")
        self.adapter_name = adapter_name


class EmbeddingGenerationError(SignalIngestionError):
    """Raised when generating embeddings fails."""

    def __init__(self, reason: str) -> None:
        """Create error with ``reason`` message."""
        super().__init__(reason)
        self.reason = reason
