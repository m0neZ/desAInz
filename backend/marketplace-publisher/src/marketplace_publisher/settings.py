"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic import AnyUrl, HttpUrl, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.shared.config import settings as shared_settings


class Settings(BaseSettings):
    """Store configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    app_name: str = "marketplace-publisher"
    log_level: str = "INFO"
    database_url: AnyUrl = AnyUrl(shared_settings.database_url)
    redis_url: RedisDsn = RedisDsn(shared_settings.redis_url)
    rate_limit_redbubble: int = 60
    rate_limit_amazon_merch: int = 60
    rate_limit_etsy: int = 60
    rate_limit_society6: int = 60
    rate_limit_window: int = 60
    max_attempts: int = 3
    unleash_url: HttpUrl | None = None
    unleash_api_token: str | None = None
    unleash_app_name: str = "marketplace-publisher"
    slack_webhook_url: HttpUrl | None = None

    @field_validator(
        "rate_limit_redbubble",
        "rate_limit_amazon_merch",
        "rate_limit_etsy",
        "rate_limit_society6",
        "rate_limit_window",
        "max_attempts",
    )
    @classmethod
    def _positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be positive")
        return value


Settings.model_rebuild()
settings: Settings = Settings()
