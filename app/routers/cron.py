from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.database import get_db
from app.services.retention import process_due_reminders

router = APIRouter()


@router.post("/internal/cron/reminders")
async def run_reminders_cron(
    db: DbSession = Depends(get_db),
    x_cron_secret: str | None = Header(default=None),
):
    settings = get_settings()
    if settings.cron_secret and x_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=403, detail="Ruxsat yo‘q")

    sent = await process_due_reminders(db)
    return {"ok": True, "sent": sent}
