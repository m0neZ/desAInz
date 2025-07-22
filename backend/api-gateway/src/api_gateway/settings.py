"""Application settings for the API Gateway."""

from __future__ import annotations

import os
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
    ws_interval_ms: int = int(os.environ.get("API_GATEWAY_WS_INTERVAL_MS", "5000"))
    request_cache_ttl: int = int(os.environ.get("API_GATEWAY_REQUEST_CACHE_TTL", "0"))

    @field_validator(
        "rate_limit_per_user",
        "rate_limit_window",
        "ws_interval_ms",
        "request_cache_ttl",
    )
    @classmethod
    def _positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be positive")
        return value


Settings.model_rebuild()
settings: Settings = Settings()
