"""Global configuration loaded from environment variables."""

from __future__ import annotations

from pydantic import AnyUrl, Field, HttpUrl, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration for backend services."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", secrets_dir="/run/secrets"
    )

    database_url: AnyUrl = AnyUrl("sqlite:///shared.db")
    pgbouncer_url: AnyUrl | None = None
    kafka_bootstrap_servers: str = "localhost:9092"
    schema_registry_url: HttpUrl = HttpUrl("http://localhost:8081")
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")
    score_cache_ttl: int = 3600
    trending_ttl: int = 3600
    trending_max_keywords: int = 100
    trending_cache_ttl: int = 30
    s3_endpoint: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket: str | None = None
    s3_base_url: str | None = None
    cdn_distribution_id: str | None = None
    secret_key: str | None = None
    auth0_domain: str | None = None
    auth0_client_id: str | None = None
    weights_token: str | None = None
    allowed_origins: list[str] = Field(default_factory=list)
    content_security_policy: str | None = None
    hsts: str | None = None
    allow_status_unauthenticated: bool = True

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: str | list[str]) -> list[str]:
        """Parse comma separated origins from environment variables."""
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    @field_validator(
        "score_cache_ttl",
        "trending_ttl",
        "trending_max_keywords",
        "trending_cache_ttl",
    )
    @classmethod
    def _positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be positive")
        return value

    @property
    def effective_database_url(self) -> AnyUrl:
        """Return ``pgbouncer_url`` if set, otherwise ``database_url``."""
        return self.pgbouncer_url or self.database_url


Settings.model_rebuild()
settings: Settings = Settings()
