"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore[misc]
    """Store configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    app_name: str = "signal-ingestion"
    log_level: str = "INFO"
    signal_retention_days: int = 90
    dedup_error_rate: float = 0.01
    dedup_capacity: int = 100_000
    dedup_ttl: int = 86_400
    ingest_interval_minutes: int = 60
    http_proxies: HttpUrl | None = None
    adapter_rate_limit: int = 5

    @field_validator(
        "dedup_error_rate",
        "dedup_capacity",
        "dedup_ttl",
        "ingest_interval_minutes",
        "adapter_rate_limit",
    )
    @classmethod
    def _positive(cls, value: float | int) -> float | int:
        if isinstance(value, float):
            if not 0 <= value <= 1:
                raise ValueError("dedup_error_rate must be in [0,1]")
            return value
        if value <= 0:
            raise ValueError("must be positive")
        return value


Settings.model_rebuild()
settings: Settings = Settings()
