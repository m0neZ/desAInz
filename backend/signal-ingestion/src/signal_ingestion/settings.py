"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Store configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "signal-ingestion"
    log_level: str = "INFO"
    signal_retention_days: int = 90
    dedup_error_rate: float = 0.01
    dedup_capacity: int = 100_000
    dedup_ttl: int = 86_400


settings = Settings()
