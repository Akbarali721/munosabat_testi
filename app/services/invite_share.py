"""Build partner invite deep-links and Telegram share URLs."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from app.config import get_settings

RELATIONSHIP_BOT_USERNAME = "munosabat_testBot"

PARTNER_SHARE_TEXT = (
    "Men Juftlik suhbatini boshladim.\n\n"
    "Bir-biringizni yaxshiroq tushunish uchun "
    "siz ham 12 ta savolga javob bering 👇"
)

INITIATOR_COMPLETE_MESSAGE = (
    "Sizning qismingiz tayyor ✅\n\n"
    "Endi havolani juftingizga yuboring. "
    "U ham javob bergach, suhbat natijasi ochiladi."
)


def _relationship_bot_username() -> str:
    return get_settings().resolve_bot_username() or RELATIONSHIP_BOT_USERNAME


def build_partner_deep_link(invite_token: str) -> str | None:
    if not invite_token:
        return None
    username = _relationship_bot_username()
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
            [{"text": "💌 Juftimga yuborish", "url": share_url}],
            [{"text": "⏳ Holatni ko‘rish", "web_app": {"url": status_url}}],
        ]
    }
