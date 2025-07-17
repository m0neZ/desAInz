"""Application settings for the API Gateway."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.shared.config import settings as shared_settings


class Settings(BaseSettings):
    """Configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "api-gateway"
    redis_url: str = shared_settings.redis_url
    rate_limit_per_user: int = 60
    rate_limit_window: int = 60


settings = Settings()
