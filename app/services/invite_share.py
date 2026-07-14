"""Build partner invite deep-links and Telegram share URLs."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from app.config import get_settings

PARTNER_SHARE_TEXT = (
    "Men Qadam’da munosabat testini boshladim.\n\n"
    "Bizning umumiy natijamizni bilish uchun "
    "siz ham savollarga javob bering 👇"
)

INITIATOR_COMPLETE_MESSAGE = (
    "Siz testning birinchi qismini yakunladingiz ✅\n\n"
    "Endi havolani sherigingizga yuboring. "
    "U ham savollarga javob bergach, sizning umumiy natijangiz tayyor bo‘ladi."
)


def build_partner_deep_link(invite_token: str) -> str | None:
    if not invite_token:
        return None
    username = get_settings().resolve_bot_username()
    if not username:
        return None
    return f"https://t.me/{username}?start=rel_invite_{invite_token}"


def build_telegram_share_url(invite_token: str, *, share_text: str = PARTNER_SHARE_TEXT) -> str | None:
    deep_link = build_partner_deep_link(invite_token)
    if not deep_link:
        return None
    return (
        "https://t.me/share/url"
        f"?url={quote(deep_link, safe='')}"
        f"&text={quote(share_text, safe='')}"
    )


def build_status_webapp_url(session_id: str) -> str:
    return f"{get_settings().webapp_base_url}/session/{session_id}/status"


def initiator_invite_keyboard(invite_token: str, session_id: str) -> dict[str, Any] | None:
    """Inline keyboard: share to partner + open status WebApp."""
    share_url = build_telegram_share_url(invite_token)
    if not share_url:
        return None
    status_url = build_status_webapp_url(session_id)
    return {
        "inline_keyboard": [
            [{"text": "💌 Sherikka yuborish", "url": share_url}],
            [{"text": "⏳ Test holatini ko‘rish", "web_app": {"url": status_url}}],
        ]
    }
