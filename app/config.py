import os
from functools import lru_cache


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    def __init__(self) -> None:
        self.telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN") or None
        self.telegram_bot_username: str | None = os.getenv("TELEGRAM_BOT_USERNAME") or None
        self.app_base_url: str = (
            os.getenv("APP_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
        )
        webapp = (os.getenv("WEBAPP_BASE_URL") or "").strip().rstrip("/")
        self.webapp_base_url: str = webapp or self.app_base_url
        self.payment_mode: str = (os.getenv("PAYMENT_MODE", "demo") or "demo").lower()
        self.payme_merchant_id: str | None = os.getenv("PAYME_MERCHANT_ID") or None
        self.payme_secret_key: str | None = os.getenv("PAYME_SECRET_KEY") or None
        self.cron_secret: str | None = os.getenv("CRON_SECRET") or None

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token)

    @property
    def payme_configured(self) -> bool:
        return bool(self.payme_merchant_id and self.payme_secret_key)

    @property
    def payment_demo(self) -> bool:
        return self.payment_mode != "payme" or not self.payme_configured

    def bot_link_url(self, start_payload: str) -> str | None:
        raw = (self.telegram_bot_username or "").strip()
        if not raw:
            return None
        username = raw.lstrip("@").strip()
        if not username:
            return None
        return f"https://t.me/{username}?start={start_payload}"
