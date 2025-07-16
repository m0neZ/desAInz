"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Store configuration derived from environment variables."""

    app_name: str = "marketplace-publisher"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost/db"
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_redbubble: int = 60
    rate_limit_amazon_merch: int = 60
    rate_limit_etsy: int = 60
    rate_limit_window: int = 60

    class Config:
        """Pydantic configuration for ``Settings``."""

        env_file = ".env"


settings = Settings()
