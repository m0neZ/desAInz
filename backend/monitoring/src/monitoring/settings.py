"""Application settings for the monitoring service."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration loaded from environment variables."""

    app_name: str = "monitoring"
    log_file: str = "app.log"

    model_config = {"env_file": ".env"}


settings = Settings()
