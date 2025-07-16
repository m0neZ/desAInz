"""Application settings for the monitoring service."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):  # type: ignore[misc]
    """Configuration loaded from environment variables."""

    app_name: str = "monitoring"
    log_file: str = "app.log"

    class Config:
        """Pydantic configuration."""

        env_file = ".env"


settings = Settings()
