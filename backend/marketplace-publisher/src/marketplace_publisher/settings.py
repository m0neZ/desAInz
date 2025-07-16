"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Store configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "marketplace-publisher"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost/db"


settings = Settings()
