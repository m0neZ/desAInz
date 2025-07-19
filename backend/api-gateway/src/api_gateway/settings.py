"""Application settings for the API Gateway."""

from __future__ import annotations

from pydantic import RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.shared.config import settings as shared_settings


class Settings(BaseSettings):
    """Configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    app_name: str = "api-gateway"
    redis_url: RedisDsn = RedisDsn(shared_settings.redis_url)
    rate_limit_per_user: int = 60
    rate_limit_window: int = 60

    @field_validator("rate_limit_per_user", "rate_limit_window")
    @classmethod
    def _positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be positive")
        return value


Settings.model_rebuild()
settings: Settings = Settings()
