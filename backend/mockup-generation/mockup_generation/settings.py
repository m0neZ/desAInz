"""Configuration for the mockup generation service."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Expose API keys and provider selection."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", secrets_dir="/run/secrets"
    )

    stability_ai_api_key: str | None = None
    openai_api_key: str | None = None
    fallback_provider: str = "stability"


settings = Settings()
