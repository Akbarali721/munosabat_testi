import logging
import os
from functools import lru_cache
from pathlib import Path

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Project root .env (local). Railway injects env vars into the process — load_dotenv is a no-op there.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_FILE)

_UNSET = object()
_resolved_username_cache: str | None | object = _UNSET


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

    @staticmethod
    def normalize_bot_username(value: str | None) -> str | None:
        if not value:
            return None
        username = value.strip().lstrip("@").strip()
        return username or None

    def resolve_bot_username(self) -> str | None:
        """Env TELEGRAM_BOT_USERNAME, else Telegram getMe (token required)."""
        global _resolved_username_cache

        from_env = self.normalize_bot_username(self.telegram_bot_username)
        if from_env:
            return from_env

        if _resolved_username_cache is not _UNSET:
            return _resolved_username_cache  # type: ignore[return-value]

        username = self._fetch_username_via_get_me()
        _resolved_username_cache = username
        return username

    def _fetch_username_via_get_me(self) -> str | None:
        token = (self.telegram_bot_token or "").strip()
        if not token:
            return None
        try:
            response = httpx.get(
                f"https://api.telegram.org/bot{token}/getMe",
                timeout=10.0,
            )
            payload = response.json()
            if not payload.get("ok"):
                logger.error(
                    "Telegram getMe failed: status=%s body=%s",
                    response.status_code,
                    payload,
                )
                return None
            username = self.normalize_bot_username(
                (payload.get("result") or {}).get("username")
            )
            if not username:
                logger.error("Telegram getMe ok but username missing in result")
            return username
        except Exception:
            logger.exception("Telegram getMe request failed while resolving bot username")
            return None

    def bot_link_url(self, start_payload: str) -> str | None:
        username = self.resolve_bot_username()
        if not username:
            return None
        return f"https://t.me/{username}?start={start_payload}"
