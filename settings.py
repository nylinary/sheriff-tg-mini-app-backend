from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    postgres_dsn: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    initdata_max_age_seconds: int = 300

    # JWT auth
    jwt_secret: str = "change-me"  # set JWT_SECRET in env
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 900        # 15 min
    refresh_token_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days

    # Cookie settings
    cookie_secure: bool = True
    cookie_samesite: str = "none"  # 'none' required for TG webview + cross-site cookies

    # Optional: where to forward leads as webhook
    lead_webhook_url: str | None = None

    # Webflow CMS (for exchange rates)
    webflow_cms_items_url: str | None = None  # e.g. https://api.webflow.com/v2/collections/<id>/items
    webflow_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
