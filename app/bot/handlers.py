"""Telegram update handlers (httpx client — not aiogram)."""

from __future__ import annotations

import logging
import re
from datetime import datetime

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
from app.services.events import log_relationship_event
from app.services.invite_token import get_session_by_invite_token
from app.services.session_telegram import set_initiator_telegram_id, set_partner_telegram_id

logger = logging.getLogger(__name__)

PENDING_PARTNER_NAME = "__pending__"

# /start or /start@BotName — capture optional deep-link payload
_START_RE = re.compile(r"^/start(?:@\w+)?(?:\s+(.+))?$", re.IGNORECASE | re.DOTALL)


def _webapp_start_url() -> str:
    """Initiator Mini App entry (existing /start page)."""
    return f"{get_settings().webapp_base_url}/start"


def _partner_entry_url(session_id: str) -> str:
    return f"{get_settings().webapp_base_url}/session/{session_id}/join"


def _result_webapp_url(session_id: str) -> str:
    return f"{get_settings().webapp_base_url}/session/{session_id}/result"


def parse_start_payload(text: str) -> str | None:
    """
    Parse a /start command.

    Returns:
      - None if the message is not a /start command
      - "" for plain /start (no deep-link argument)
      - the raw payload string otherwise (e.g. rel_invite_<TOKEN>)
    """
    raw = (text or "").strip()
    match = _START_RE.match(raw)
    if not match:
        return None
    payload = match.group(1)
    return (payload or "").strip()


async def handle_update(update: dict, db: DbSession) -> None:
    message = update.get("message")
    if not message or "text" not in message:
        return

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return

    text = message["text"]
    payload = parse_start_payload(text)
    if payload is None:
        return

    # 1) Plain /start → main menu (never invite lookup)
    if payload == "":
        logger.info("start: plain menu chat_id=%s", chat_id)
        await _send_welcome_with_start(chat_id)
        return

    # 2) Relationship invite deep-link
    if payload.startswith("rel_invite_"):
        token = payload.removeprefix("rel_invite_").strip()
        logger.info(
            "start: rel_invite chat_id=%s token_len=%s",
            chat_id,
            len(token),
        )
        await _handle_rel_invite(chat_id, token, db)
        return

    # Legacy User1 link_{session_id} deep-link
    if payload.startswith("link_"):
        session_id = payload.removeprefix("link_").strip()
        await _link_user_a(chat_id, session_id, db)
        return

    # 3) Unknown payload → main menu (no technical error)
    logger.info("start: unknown payload → menu chat_id=%s payload=%r", chat_id, payload[:64])
    await _send_welcome_with_start(chat_id)


async def _send_welcome_with_start(chat_id: int) -> None:
    start_url = _webapp_start_url()
    await telegram_client.send_message(
        chat_id,
        telegram_welcome(),
        button_text="💬 Juftlik suhbatini boshlash",
        web_app_url=start_url,
    )


async def _handle_rel_invite(chat_id: int, token: str, db: DbSession) -> None:
    # Empty token after rel_invite_ prefix → same as not found
    if not token:
        logger.warning("rel_invite: empty token chat_id=%s", chat_id)
        await telegram_client.send_message(chat_id, invite_invalid())
        return

    session = get_session_by_invite_token(db, token)
    if not session:
        logger.warning(
            "rel_invite: token not found chat_id=%s token_prefix=%r",
            chat_id,
            token[:8],
        )
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

    if (user_a and user_a.telegram_chat_id == chat_id) or (
        session.initiator_telegram_id and session.initiator_telegram_id == chat_id
    ):
        await telegram_client.send_message(chat_id, invite_self_blocked())
        return

    if session.status == SessionStatus.complete or (
        user_a and user_a.completed_at and user_b and user_b.completed_at
    ):
        if user_b and user_b.telegram_chat_id == chat_id:
            await telegram_client.send_message(
                chat_id,
                invite_session_complete(),
                button_text="💬 Natijani ko‘rish",
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
                button_text="💬 Natijani ko‘rish",
                web_app_url=_result_webapp_url(session.id),
            )
            return
        await telegram_client.send_message(
            chat_id,
            invite_partner_continue(),
            button_text="▶️ O‘z qismimni boshlash",
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
        db.flush()
    else:
        user_b.telegram_chat_id = chat_id

    set_partner_telegram_id(session, chat_id)
    if session.partner_started_at is None:
        session.partner_started_at = datetime.utcnow()
    if session.invite_token_used_at is None:
        session.invite_token_used_at = datetime.utcnow()

    if session.status == SessionStatus.awaiting_user_b:
        session.status = SessionStatus.awaiting_user_b_answers

    log_relationship_event(
        db,
        session_id=session.id,
        event_type="partner_deeplink_opened",
        telegram_id=chat_id,
    )
    log_relationship_event(
        db,
        session_id=session.id,
        event_type="partner_attached_to_session",
        telegram_id=chat_id,
    )
    db.commit()

    # Best-effort username lookup for admin panel
    try:
        get_chat = getattr(telegram_client, "get_chat", None)
        chat = None
        if callable(get_chat):
            maybe = get_chat(chat_id)
            if hasattr(maybe, "__await__"):
                chat = await maybe
            elif isinstance(maybe, dict):
                chat = maybe
        if chat and chat.get("username") and user_b:
            user_b.telegram_username = str(chat["username"])
            db.commit()
    except Exception:
        logger.exception("getChat failed for partner chat_id=%s", chat_id)

    await telegram_client.send_message(
        chat_id,
        invite_partner_welcome(),
        button_text="▶️ O‘z qismimni boshlash",
        web_app_url=_partner_entry_url(session.id),
    )
    log_relationship_event(
        db,
        session_id=session.id,
        event_type="partner_test_started",
        telegram_id=chat_id,
        commit=True,
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
    set_initiator_telegram_id(session, chat_id)
    db.commit()
    await telegram_client.send_message(chat_id, telegram_link_confirmed())
