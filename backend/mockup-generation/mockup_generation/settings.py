"""Configuration for the mockup generation service."""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):  # type: ignore[misc]
    """Expose API keys and provider selection."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", secrets_dir="/run/secrets"
    )

    stability_ai_api_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4"
    fallback_provider: Literal["stability", "openai"] = "stability"

    @field_validator("fallback_provider")  # type: ignore[misc]
    @classmethod
    def _valid_provider(cls, value: str) -> str:
        if value not in {"stability", "openai"}:
            raise ValueError("invalid provider")
        return value


Settings.model_rebuild()
settings: Settings = Settings()
