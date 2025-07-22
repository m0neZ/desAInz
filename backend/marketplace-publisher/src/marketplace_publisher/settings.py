"""Application settings loaded from environment variables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import AnyUrl, HttpUrl, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict  # noqa: I201

from backend.shared.config import settings as shared_settings

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from .db import Marketplace


class Settings(BaseSettings):
    """Store configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    app_name: str = "marketplace-publisher"
    log_level: str = "INFO"
    database_url: AnyUrl = AnyUrl(shared_settings.effective_database_url)
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

    redbubble_client_id: str | None = None
    redbubble_client_secret: str | None = None
    redbubble_api_key: str | None = None
    redbubble_redirect_uri: HttpUrl | None = None
    redbubble_authorize_url: HttpUrl | None = (
        "https://www.redbubble.com/oauth/authorize"
    )
    redbubble_token_url: HttpUrl | None = "https://www.redbubble.com/oauth/token"
    redbubble_scope: str | None = "read write"

    amazon_merch_client_id: str | None = None
    amazon_merch_client_secret: str | None = None
    amazon_merch_api_key: str | None = None
    amazon_merch_redirect_uri: HttpUrl | None = None
    amazon_merch_authorize_url: HttpUrl | None = "https://www.amazon.com/ap/oa"
    amazon_merch_token_url: HttpUrl | None = "https://api.amazon.com/auth/o2/token"
    amazon_merch_scope: str | None = "merch_edit merch_read"

    etsy_client_id: str | None = None
    etsy_client_secret: str | None = None
    etsy_api_key: str | None = None
    etsy_redirect_uri: HttpUrl | None = None
    etsy_authorize_url: HttpUrl | None = "https://www.etsy.com/oauth/connect"
    etsy_token_url: HttpUrl | None = "https://api.etsy.com/v3/public/oauth/token"
    etsy_scope: str | None = "listings_r listings_w"

    society6_client_id: str | None = None
    society6_client_secret: str | None = None
    society6_api_key: str | None = None
    society6_redirect_uri: HttpUrl | None = None
    society6_authorize_url: HttpUrl | None = "https://society6.com/oauth/authorize"
    society6_token_url: HttpUrl | None = "https://society6.com/oauth/token"
    society6_scope: str | None = "create read"

    webhook_secret_redbubble: str | None = None
    webhook_secret_amazon_merch: str | None = None
    webhook_secret_etsy: str | None = None
    webhook_secret_society6: str | None = None
    webhook_secret_zazzle: str | None = None

    zazzle_client_id: str | None = None
    zazzle_client_secret: str | None = None
    zazzle_api_key: str | None = None
    zazzle_redirect_uri: HttpUrl | None = None
    zazzle_authorize_url: HttpUrl | None = "https://api.zazzle.com/v1/oauth/authorize"
    zazzle_token_url: HttpUrl | None = "https://api.zazzle.com/v1/oauth/token"
    zazzle_scope: str | None = "manage_products"

    @property
    def webhook_secrets(self) -> dict[Marketplace, str]:
        """Return mapping of marketplaces to webhook secrets."""

        secrets: dict[Marketplace, str] = {}
        for marketplace in Marketplace:
            value = getattr(self, f"webhook_secret_{marketplace.value}")
            if value:
                secrets[marketplace] = value
        return secrets

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

    @field_validator(
        "unleash_api_token",
        "redbubble_client_id",
        "redbubble_client_secret",
        "redbubble_api_key",
        "amazon_merch_client_id",
        "amazon_merch_client_secret",
        "amazon_merch_api_key",
        "etsy_client_id",
        "etsy_client_secret",
        "etsy_api_key",
        "society6_client_id",
        "society6_client_secret",
        "society6_api_key",
        "zazzle_client_id",
        "zazzle_client_secret",
        "zazzle_api_key",
        mode="before",
    )
    @classmethod
    def _strip_token(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


Settings.model_rebuild()
settings: Settings = Settings()
