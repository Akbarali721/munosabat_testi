from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session as DbSession

from app.bot.handlers import handle_update
from app.config import get_settings
from app.database import get_db

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request, db: DbSession = Depends(get_db)):
    settings = get_settings()
    if not settings.telegram_enabled:
        raise HTTPException(status_code=503, detail="Telegram bot sozlanmagan")

    update = await request.json()
    await handle_update(update, db)
    return {"ok": True}
