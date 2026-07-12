import logging
from datetime import datetime

from app.bot.telegram_client import telegram_client
from app.config import get_settings
from app.copy.notifications import (
    initiator_answers_saved,
    result_ready_for_initiator,
    result_ready_for_partner,
)
from app.database import SessionLocal
from app.models import Participant, ParticipantRole, Session, SessionStatus

logger = logging.getLogger(__name__)


def _result_webapp_url(session_id: str) -> str:
    return f"{get_settings().webapp_base_url}/session/{session_id}/result"


async def notify_initiator_answers_saved(session_id: str) -> None:
    if not telegram_client.enabled:
        return
    db = SessionLocal()
    try:
        user_a = (
            db.query(Participant)
            .filter(
                Participant.session_id == session_id,
                Participant.role == ParticipantRole.user_a,
            )
            .first()
        )
        if not user_a or not user_a.telegram_chat_id:
            return
        await telegram_client.send_message(
            user_a.telegram_chat_id,
            initiator_answers_saved(),
        )
    finally:
        db.close()


async def send_result_notifications(session_id: str) -> None:
    """Send independent result web_app messages; mark notified only after API success."""
    if not telegram_client.enabled:
        logger.debug("Telegram disabled — skip result notifications for %s", session_id)
        return

    db = SessionLocal()
    try:
        session = db.get(Session, session_id)
        if not session or session.status != SessionStatus.complete:
            return

        user_a = (
            db.query(Participant)
            .filter(
                Participant.session_id == session_id,
                Participant.role == ParticipantRole.user_a,
            )
            .first()
        )
        user_b = (
            db.query(Participant)
            .filter(
                Participant.session_id == session_id,
                Participant.role == ParticipantRole.user_b,
            )
            .first()
        )
        if not user_a or not user_b:
            return

        result_url = _result_webapp_url(session_id)

        for participant, text in (
            (user_a, result_ready_for_initiator()),
            (user_b, result_ready_for_partner()),
        ):
            if participant.result_notified_at:
                continue
            if not participant.telegram_chat_id:
                logger.info(
                    "Skip result notify — no telegram_chat_id for participant %s",
                    participant.id,
                )
                continue

            sent = await telegram_client.send_message(
                participant.telegram_chat_id,
                text,
                button_text="📊 Natijani ko‘rish",
                web_app_url=result_url,
            )
            if sent:
                participant.result_notified_at = datetime.utcnow()
                db.commit()
                logger.info(
                    "Result notification sent to chat %s",
                    participant.telegram_chat_id,
                )
            else:
                logger.warning(
                    "Failed result notification for participant %s session %s",
                    participant.id,
                    session_id,
                )
    finally:
        db.close()


# Backward-compatible alias used by older call sites
async def send_session_ready_notification(session_id: str) -> None:
    await send_result_notifications(session_id)
