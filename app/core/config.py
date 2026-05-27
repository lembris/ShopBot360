from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "change-me"

    database_url: str = "postgresql+asyncpg://shopbot:shopbot@localhost:5432/shopbot"
    redis_url: str = "redis://localhost:6379/0"

    # WhatsApp provider: meta | twilio | dialog360 | wati
    whatsapp_provider: str = "twilio"
    whatsapp_fallback_providers: str = "wati,dialog360,meta"

    # Meta Cloud API (direct)
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = "your-verify-token"
    whatsapp_api_version: str = "v21.0"

    # Twilio WhatsApp (recommended without Meta direct access)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""  # e.g. whatsapp:+14155238886

    # 360dialog BSP
    dialog360_api_key: str = ""
    dialog360_base_url: str = "https://waba-v2.360dialog.io"

    # WATI.io
    wati_api_token: str = ""
    wati_api_base_url: str = ""  # e.g. https://live-server.wati.io

    allowed_phones: str = "+255700000000"
    jwt_secret: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    rate_limit_per_second: int = 5

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: int = 30
    ai_confidence_threshold: float = 0.7

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    sentry_dsn: str = ""

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_basic: str = ""

    tesseract_cmd: str = Field(default="", validation_alias="TESSERACT_CMD")

    @property
    def allowed_phone_list(self) -> list[str]:
        return [p.strip() for p in self.allowed_phones.split(",") if p.strip()]

    @property
    def whatsapp_fallback_provider_list(self) -> list[str]:
        return [p.strip() for p in self.whatsapp_fallback_providers.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
