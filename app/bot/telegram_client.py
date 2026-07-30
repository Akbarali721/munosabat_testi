from typing import Any

import httpx

from app.config import get_settings


class TelegramClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._token = settings.telegram_bot_token
        self._base = f"https://api.telegram.org/bot{self._token}" if self._token else None

    @property
    def enabled(self) -> bool:
        return bool(self._base)

    async def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        button_text: str | None = None,
        button_url: str | None = None,
        web_app_url: str | None = None,
        reply_markup: dict[str, Any] | None = None,
    ) -> bool:
        if not self._base:
            return False

        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
        }

        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        elif web_app_url and button_text:
            payload["reply_markup"] = {
                "inline_keyboard": [
                    [{"text": button_text, "web_app": {"url": web_app_url}}]
                ],
            }
        elif button_text and button_url:
            # Legacy URL button — prefer web_app for Mini App flows
            payload["reply_markup"] = {
                "inline_keyboard": [[{"text": button_text, "url": button_url}]],
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(f"{self._base}/sendMessage", json=payload)
            return response.is_success

    async def get_chat(self, chat_id: int) -> dict[str, Any] | None:
        if not self._base:
            return None
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self._base}/getChat",
                params={"chat_id": chat_id},
            )
            if not response.is_success:
                return None
            data = response.json()
            if not data.get("ok"):
                return None
            result = data.get("result")
            return result if isinstance(result, dict) else None

    def web_app_inline_keyboard(self, button_text: str, web_app_url: str) -> dict[str, Any]:
        return {
            "inline_keyboard": [
                [{"text": button_text, "web_app": {"url": web_app_url}}]
            ]
        }

    def start_relationship_reply_keyboard(self, web_app_url: str) -> dict[str, Any]:
        return {
            "keyboard": [
                [{"text": "💬 Juftlik suhbatini boshlash", "web_app": {"url": web_app_url}}]
            ],
            "resize_keyboard": True,
            "is_persistent": True,
        }


telegram_client = TelegramClient()
