"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.shared.config import settings as shared_settings


class Settings(BaseSettings):
    """Store configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    app_name: str = "marketplace-publisher"
    log_level: str = "INFO"
    database_url: str = shared_settings.database_url
    redis_url: str = shared_settings.redis_url
    rate_limit_redbubble: int = 60
    rate_limit_amazon_merch: int = 60
    rate_limit_etsy: int = 60
    rate_limit_society6: int = 60
    rate_limit_window: int = 60
    unleash_url: str | None = None
    unleash_api_token: str | None = None
    unleash_app_name: str = "marketplace-publisher"
    slack_webhook_url: str | None = None


settings = Settings()
