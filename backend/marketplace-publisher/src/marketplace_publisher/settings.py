"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Store configuration derived from environment variables."""

    app_name: str = "marketplace-publisher"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost/db"
    unleash_url: str | None = None
    unleash_token: str | None = None
    unleash_environment: str = "development"

    class Config:
        """Pydantic configuration for ``Settings``."""

        env_file = ".env"


settings = Settings()
