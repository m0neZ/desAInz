"""Global configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration for backend services."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", secrets_dir="/run/secrets"
    )

    database_url: str = "sqlite:///shared.db"
    kafka_bootstrap_servers: str = "localhost:9092"
    schema_registry_url: str = "http://localhost:8081"
    redis_url: str = "redis://localhost:6379/0"
    score_cache_ttl: int = 3600
    trending_ttl: int = 3600
    s3_endpoint: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket: str | None = None
    secret_key: str | None = None
    allowed_origins: list[str] = ["*"]


settings = Settings()
