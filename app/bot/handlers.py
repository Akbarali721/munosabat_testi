from sqlalchemy.orm import Session as DbSession

from app.bot.telegram_client import telegram_client
from app.config import get_settings
from app.copy.notifications import (
    invite_already_taken,
    invite_invalid,
    invite_partner_continue,
    invite_partner_welcome,
    invite_self_blocked,
    invite_session_complete,
    telegram_link_confirmed,
    telegram_link_invalid,
    telegram_welcome,
)
from app.models import Gender, Participant, ParticipantRole, Session, SessionStatus
from app.services.invite_token import get_session_by_invite_token

PENDING_PARTNER_NAME = "__pending__"


def _webapp_start_url() -> str:
    return f"{get_settings().webapp_base_url}/start"


def _partner_entry_url(session_id: str) -> str:
    """Partner opens join (or questions if profile already set)."""
    return f"{get_settings().webapp_base_url}/session/{session_id}/join"


def _result_webapp_url(session_id: str) -> str:
    return f"{get_settings().webapp_base_url}/session/{session_id}/result"


async def handle_update(update: dict, db: DbSession) -> None:
    message = update.get("message")
    if not message or "text" not in message:
        return

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return

    text = message["text"].strip()
    if not text.startswith("/start"):
        return

    parts = text.split(maxsplit=1)
    payload = parts[1] if len(parts) > 1 else ""

    if payload.startswith("rel_invite_"):
        token = payload.removeprefix("rel_invite_")
        await _handle_rel_invite(chat_id, token, db)
        return

    if payload.startswith("link_"):
        session_id = payload.removeprefix("link_")
        await _link_user_a(chat_id, session_id, db)
        return

    await _send_welcome_with_start(chat_id)


async def _send_welcome_with_start(chat_id: int) -> None:
    start_url = _webapp_start_url()
    await telegram_client.send_message(
        chat_id,
        telegram_welcome(),
        reply_markup=telegram_client.start_relationship_reply_keyboard(start_url),
    )
    await telegram_client.send_message(
        chat_id,
        "Yoki shu tugma orqali oching:",
        button_text="❤️ Munosabat testini boshlash",
        web_app_url=start_url,
    )


async def _handle_rel_invite(chat_id: int, token: str, db: DbSession) -> None:
    session = get_session_by_invite_token(db, token)
    if not session:
        await telegram_client.send_message(chat_id, invite_invalid())
        return

    user_a = (
        db.query(Participant)
        .filter(
            Participant.session_id == session.id,
            Participant.role == ParticipantRole.user_a,
        )
        .first()
    )
    user_b = (
        db.query(Participant)
        .filter(
            Participant.session_id == session.id,
            Participant.role == ParticipantRole.user_b,
        )
        .first()
    )

    if user_a and user_a.telegram_chat_id == chat_id:
        await telegram_client.send_message(chat_id, invite_self_blocked())
        return

    if session.status == SessionStatus.complete or (
        user_a and user_a.completed_at and user_b and user_b.completed_at
    ):
        if user_b and user_b.telegram_chat_id == chat_id:
            await telegram_client.send_message(
                chat_id,
                invite_session_complete(),
                button_text="📊 Natijani ko‘rish",
                web_app_url=_result_webapp_url(session.id),
            )
            return
        await telegram_client.send_message(chat_id, invite_already_taken())
        return

    if user_b and user_b.telegram_chat_id and user_b.telegram_chat_id != chat_id:
        await telegram_client.send_message(chat_id, invite_already_taken())
        return

    if user_b and user_b.telegram_chat_id == chat_id:
        if user_b.completed_at:
            await telegram_client.send_message(
                chat_id,
                invite_session_complete(),
                button_text="📊 Natijani ko‘rish",
                web_app_url=_result_webapp_url(session.id),
            )
            return
        await telegram_client.send_message(
            chat_id,
            invite_partner_continue(),
            button_text="❤️ Testni boshlash",
            web_app_url=_partner_entry_url(session.id),
        )
        return

    if not user_b:
        user_b = Participant(
            session_id=session.id,
            role=ParticipantRole.user_b,
            name=PENDING_PARTNER_NAME,
            gender=Gender.female,
            telegram_chat_id=chat_id,
        )
        db.add(user_b)
    else:
        user_b.telegram_chat_id = chat_id

    if session.status == SessionStatus.awaiting_user_b:
        session.status = SessionStatus.awaiting_user_b_answers
    db.commit()

    await telegram_client.send_message(
        chat_id,
        invite_partner_welcome(),
        button_text="❤️ Testni boshlash",
        web_app_url=_partner_entry_url(session.id),
    )


async def _link_user_a(chat_id: int, session_id: str, db: DbSession) -> None:
    session = db.get(Session, session_id)
    if not session:
        await telegram_client.send_message(chat_id, telegram_link_invalid())
        return

    user_a = (
        db.query(Participant)
        .filter(
            Participant.session_id == session_id,
            Participant.role == ParticipantRole.user_a,
        )
        .first()
    )
    if not user_a:
        await telegram_client.send_message(chat_id, telegram_link_invalid())
        return

    user_a.telegram_chat_id = chat_id
    db.commit()
    await telegram_client.send_message(chat_id, telegram_link_confirmed())
