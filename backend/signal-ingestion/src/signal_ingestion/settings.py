"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Store configuration derived from environment variables."""

    app_name: str = "signal-ingestion"
    log_level: str = "INFO"
    signal_retention_days: int = 90

    class Config:
        """Pydantic configuration for ``Settings``."""

        env_file = ".env"


settings = Settings()
