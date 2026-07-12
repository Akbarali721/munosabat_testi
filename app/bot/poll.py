"""Local dev: poll Telegram updates when webhook is not configured.

Usage:
    set TELEGRAM_BOT_TOKEN=...
    python -m app.bot.poll
"""

import asyncio
import logging

import httpx

from app.bot.handlers import handle_update
from app.config import get_settings
from app.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def poll() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN o'rnatilmagan")

    base = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    offset = 0
    logger.info("Telegram polling boshlandi...")

    async with httpx.AsyncClient(timeout=35.0) as client:
        while True:
            response = await client.get(
                f"{base}/getUpdates",
                params={"timeout": 30, "offset": offset},
            )
            data = response.json()
            for item in data.get("result", []):
                offset = item["update_id"] + 1
                db = SessionLocal()
                try:
                    await handle_update(item, db)
                finally:
                    db.close()


if __name__ == "__main__":
    asyncio.run(poll())
