"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Store configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    app_name: str = "service-template"
    log_level: str = "INFO"


settings = Settings()
