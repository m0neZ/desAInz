"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Store configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "marketplace-publisher"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost/db"
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_redbubble: int = 60
    rate_limit_amazon_merch: int = 60
    rate_limit_etsy: int = 60
    rate_limit_window: int = 60
    unleash_url: str = "http://localhost:4242/api"
    unleash_token: str = ""
    unleash_app_name: str = "marketplace-publisher"


settings = Settings()
