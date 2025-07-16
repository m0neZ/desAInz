"""Application settings for the monitoring service."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "monitoring"
    log_file: str = "app.log"
    sla_threshold_hours: float = 2.0


settings = Settings()
