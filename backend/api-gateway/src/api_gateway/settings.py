"""Application settings for the API Gateway."""

from __future__ import annotations

from pydantic import Field, HttpUrl, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.shared.config import settings as shared_settings


class Settings(BaseSettings):
    """Configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    app_name: str = "api-gateway"
    redis_url: RedisDsn = RedisDsn(shared_settings.redis_url)
    rate_limit_per_user: int = 60
    rate_limit_window: int = 60
    ws_interval_ms: int = Field(5000, alias="API_GATEWAY_WS_INTERVAL_MS")
    request_cache_ttl: int = Field(0, alias="API_GATEWAY_REQUEST_CACHE_TTL")
    signal_ingestion_url: HttpUrl = HttpUrl("http://signal-ingestion:8004")
    publisher_url: HttpUrl = HttpUrl("http://marketplace-publisher:8000")
    trpc_service_url: HttpUrl = HttpUrl("http://backend:8000")
    optimization_url: HttpUrl = HttpUrl("http://optimization:8000")
    monitoring_url: HttpUrl = HttpUrl("http://monitoring:8000")
    analytics_url: HttpUrl = HttpUrl("http://analytics:8000")
    auth0_domain: str | None = Field(
        default=shared_settings.auth0_domain,
        alias="AUTH0_DOMAIN",
    )
    """Auth0 tenant domain for validating tokens."""

    auth0_client_id: str | None = Field(
        default=shared_settings.auth0_client_id,
        alias="AUTH0_CLIENT_ID",
    )
    """Client identifier issued by Auth0."""

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
