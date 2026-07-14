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
from app.services.events import log_relationship_event
from app.services.invite_share import initiator_invite_keyboard
from app.services.invite_token import ensure_invite_token
from app.services.session_telegram import (
    resolve_initiator_telegram_id,
    resolve_partner_telegram_id,
)

logger = logging.getLogger(__name__)


def _result_webapp_url(session_id: str) -> str:
    return f"{get_settings().webapp_base_url}/session/{session_id}/result"


async def notify_initiator_answers_saved(session_id: str, *, force: bool = False) -> bool:
    """
    Send User1 the partner-share message with inline buttons.
    Returns True if Telegram accepted the message.
    Never raises — completion must survive Telegram failures.
    """
    if not telegram_client.enabled:
        logger.info("Telegram disabled — skip initiator share notify session_id=%s", session_id)
        return False

    db = SessionLocal()
    sent = False
    try:
        session = db.get(Session, session_id)
        if not session:
            return False

        user_a = (
            db.query(Participant)
            .filter(
                Participant.session_id == session_id,
                Participant.role == ParticipantRole.user_a,
            )
            .first()
        )
        chat_id = resolve_initiator_telegram_id(session, user_a)
        if not chat_id:
            logger.info(
                "Skip initiator share notify — no initiator telegram session_id=%s",
                session_id,
            )
            log_relationship_event(
                db,
                session_id=session_id,
                event_type="partner_share_message_skipped_no_telegram",
                commit=True,
            )
            return False

        if session.initiator_share_notified_at and not force:
            logger.info(
                "Skip initiator share notify — already sent session_id=%s at=%s",
                session_id,
                session.initiator_share_notified_at,
            )
            return True

        token = ensure_invite_token(db, session)
        db.commit()

        keyboard = initiator_invite_keyboard(token, session_id)
        if not keyboard:
            logger.error(
                "Cannot build share keyboard — bot username missing session_id=%s",
                session_id,
            )
            log_relationship_event(
                db,
                session_id=session_id,
                event_type="partner_share_message_failed",
                telegram_id=chat_id,
                payload="missing_bot_username_or_token",
                commit=True,
            )
            return False

        logger.info(
            "Sending initiator share notify session_id=%s chat_id=%s token_len=%s",
            session_id,
            chat_id,
            len(token),
        )
        try:
            sent = await telegram_client.send_message(
                chat_id,
                initiator_answers_saved(),
                reply_markup=keyboard,
            )
        except Exception:
            logger.exception(
                "Failed initiator share notify session_id=%s chat_id=%s",
                session_id,
                chat_id,
            )
            log_relationship_event(
                db,
                session_id=session_id,
                event_type="partner_share_message_failed",
                telegram_id=chat_id,
                payload="telegram_exception",
                commit=True,
            )
            return False

        if sent:
            session.initiator_share_notified_at = datetime.utcnow()
            log_relationship_event(
                db,
                session_id=session_id,
                event_type="partner_share_message_created",
                telegram_id=chat_id,
            )
            log_relationship_event(
                db,
                session_id=session_id,
                event_type="initiator_test_completed",
                telegram_id=chat_id,
            )
            db.commit()
            logger.info(
                "Initiator share notify sent session_id=%s chat_id=%s",
                session_id,
                chat_id,
            )
        else:
            log_relationship_event(
                db,
                session_id=session_id,
                event_type="partner_share_message_failed",
                telegram_id=chat_id,
                payload="telegram_api_not_ok",
                commit=True,
            )
            logger.warning(
                "Initiator share notify rejected by Telegram session_id=%s chat_id=%s",
                session_id,
                chat_id,
            )
        return sent
    except Exception:
        logger.exception("notify_initiator_answers_saved crashed session_id=%s", session_id)
        return False
    finally:
        db.close()


async def send_result_notifications(session_id: str, *, completed_by: str = "user_b") -> None:
    """
    Send final result web_app messages.
    Primary recipient is always session.initiator_telegram_id (User1).
    Partner receives a separate message when partner_telegram_id is known.
    Telegram failures must not raise to the request path (caller uses BackgroundTasks).
    """
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

        initiator_id = resolve_initiator_telegram_id(session, user_a)
        partner_id = resolve_partner_telegram_id(session, user_b)
        result_url = _result_webapp_url(session_id)

        logger.info(
            "Result notify prepare session_id=%s initiator_telegram_id=%s "
            "partner_telegram_id=%s completed_by=%s result_url=%s",
            session_id,
            initiator_id,
            partner_id,
            completed_by,
            result_url,
        )

        log_relationship_event(
            db,
            session_id=session_id,
            event_type="relationship_result_generated",
            telegram_id=initiator_id,
        )

        await _send_one_result(
            db,
            participant=user_a,
            chat_id=initiator_id,
            text=result_ready_for_initiator(),
            result_url=result_url,
            session_id=session_id,
            role_label="initiator",
        )

        if partner_id and partner_id != initiator_id:
            await _send_one_result(
                db,
                participant=user_b,
                chat_id=partner_id,
                text=result_ready_for_partner(),
                result_url=result_url,
                session_id=session_id,
                role_label="partner",
            )
        elif not partner_id:
            logger.info(
                "Skip partner result notify — no partner_telegram_id session_id=%s",
                session_id,
            )
        db.commit()
    except Exception:
        logger.exception("send_result_notifications failed session_id=%s", session_id)
    finally:
        db.close()


async def _send_one_result(
    db,
    *,
    participant: Participant,
    chat_id: int | None,
    text: str,
    result_url: str,
    session_id: str,
    role_label: str,
) -> None:
    if participant.result_notified_at:
        logger.info(
            "Skip %s result notify — already notified participant_id=%s",
            role_label,
            participant.id,
        )
        return
    if not chat_id:
        logger.info(
            "Skip %s result notify — missing telegram id session_id=%s participant_id=%s",
            role_label,
            session_id,
            participant.id,
        )
        return

    logger.info(
        "Sending %s result notify session_id=%s chat_id=%s result_url=%s",
        role_label,
        session_id,
        chat_id,
        result_url,
    )
    try:
        sent = await telegram_client.send_message(
            chat_id,
            text,
            button_text="📊 Natijani ko‘rish",
            web_app_url=result_url,
        )
    except Exception:
        logger.exception(
            "Telegram error sending %s result session_id=%s chat_id=%s",
            role_label,
            session_id,
            chat_id,
        )
        return

    if sent:
        participant.result_notified_at = datetime.utcnow()
        if participant.telegram_chat_id is None:
            participant.telegram_chat_id = chat_id
        log_relationship_event(
            db,
            session_id=session_id,
            event_type=(
                "partner_test_completed"
                if role_label == "partner"
                else "initiator_result_notified"
            ),
            telegram_id=chat_id,
        )
        logger.info(
            "Result notification sent role=%s session_id=%s chat_id=%s",
            role_label,
            session_id,
            chat_id,
        )
    else:
        logger.warning(
            "Failed result notification role=%s session_id=%s chat_id=%s",
            role_label,
            session_id,
            chat_id,
        )


async def send_session_ready_notification(session_id: str) -> None:
    await send_result_notifications(session_id)
