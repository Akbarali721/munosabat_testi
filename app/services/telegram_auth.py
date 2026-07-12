"""Telegram WebApp initData verification."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from app.config import get_settings

# Reject initData older than 24 hours
AUTH_DATE_MAX_AGE_SECONDS = 24 * 60 * 60


class TelegramAuthError(Exception):
    pass


@dataclass(frozen=True)
class TelegramWebAppUser:
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


def validate_init_data(
    init_data: str,
    *,
    bot_token: str | None = None,
    max_age_seconds: int = AUTH_DATE_MAX_AGE_SECONDS,
) -> TelegramWebAppUser:
    """
    Validate Telegram WebApp initData per Telegram docs:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data or not init_data.strip():
        raise TelegramAuthError("initData yo‘q")

    token = bot_token if bot_token is not None else get_settings().telegram_bot_token
    if not token:
        raise TelegramAuthError("Bot token sozlanmagan")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise TelegramAuthError("initData hash yo‘q")

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed.items())
    )
    secret_key = hmac.new(
        b"WebAppData",
        token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    calculated = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise TelegramAuthError("initData imzosi noto‘g‘ri")

    auth_date_raw = parsed.get("auth_date")
    if not auth_date_raw:
        raise TelegramAuthError("auth_date yo‘q")
    try:
        auth_date = int(auth_date_raw)
    except ValueError as exc:
        raise TelegramAuthError("auth_date noto‘g‘ri") from exc

    if max_age_seconds > 0 and (time.time() - auth_date) > max_age_seconds:
        raise TelegramAuthError("initData muddati o‘tgan")

    user_raw = parsed.get("user")
    if not user_raw:
        raise TelegramAuthError("user ma’lumoti yo‘q")
    try:
        user_data = json.loads(user_raw)
    except json.JSONDecodeError as exc:
        raise TelegramAuthError("user JSON noto‘g‘ri") from exc

    user_id = user_data.get("id")
    if not isinstance(user_id, int):
        raise TelegramAuthError("user.id yo‘q")

    return TelegramWebAppUser(
        id=user_id,
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        username=user_data.get("username"),
    )


def extract_init_data_from_request(
    *,
    header_value: str | None = None,
    form_value: str | None = None,
    query_value: str | None = None,
) -> str | None:
    for value in (header_value, form_value, query_value):
        if value and value.strip():
            return value.strip()
    return None
