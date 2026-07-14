"""Bind and preserve session-level Telegram IDs for relationship tests."""

from __future__ import annotations

import logging

from app.models import Participant, ParticipantRole, Session

logger = logging.getLogger(__name__)


def set_initiator_telegram_id(session: Session, telegram_id: int | None) -> None:
    """
    Persist User1 Telegram ID permanently.
    Never overwrite a previously stored initiator_telegram_id.
    Also mirrors onto user_a.telegram_chat_id when empty.
    """
    if not telegram_id:
        return

    if session.initiator_telegram_id is None:
        session.initiator_telegram_id = int(telegram_id)
        logger.info(
            "Bound initiator_telegram_id=%s session_id=%s",
            session.initiator_telegram_id,
            session.id,
        )
    elif session.initiator_telegram_id != int(telegram_id):
        logger.warning(
            "Refusing to overwrite initiator_telegram_id=%s with %s session_id=%s",
            session.initiator_telegram_id,
            telegram_id,
            session.id,
        )

    user_a = next(
        (p for p in session.participants if p.role == ParticipantRole.user_a),
        None,
    )
    if user_a and user_a.telegram_chat_id is None:
        user_a.telegram_chat_id = int(telegram_id)


def set_partner_telegram_id(session: Session, telegram_id: int | None) -> None:
    """
    Persist User2 Telegram ID on the session.
    Never writes into initiator_telegram_id.
    """
    if not telegram_id:
        return

    tid = int(telegram_id)
    if session.initiator_telegram_id is not None and session.initiator_telegram_id == tid:
        logger.warning(
            "partner telegram_id equals initiator; refusing bind session_id=%s tid=%s",
            session.id,
            tid,
        )
        return

    if session.partner_telegram_id is None:
        session.partner_telegram_id = tid
        logger.info(
            "Bound partner_telegram_id=%s session_id=%s",
            session.partner_telegram_id,
            session.id,
        )
    elif session.partner_telegram_id != tid:
        logger.warning(
            "partner_telegram_id already set=%s; ignoring %s session_id=%s",
            session.partner_telegram_id,
            tid,
            session.id,
        )

    user_b = next(
        (p for p in session.participants if p.role == ParticipantRole.user_b),
        None,
    )
    if user_b and user_b.telegram_chat_id is None:
        user_b.telegram_chat_id = tid
    elif user_b and user_b.telegram_chat_id != tid and session.partner_telegram_id == tid:
        # Keep participant row in sync with the session partner id once accepted
        user_b.telegram_chat_id = tid


def resolve_initiator_telegram_id(session: Session, user_a: Participant | None) -> int | None:
    if session.initiator_telegram_id:
        return int(session.initiator_telegram_id)
    if user_a and user_a.telegram_chat_id:
        return int(user_a.telegram_chat_id)
    return None


def resolve_partner_telegram_id(session: Session, user_b: Participant | None) -> int | None:
    if session.partner_telegram_id:
        return int(session.partner_telegram_id)
    if user_b and user_b.telegram_chat_id:
        return int(user_b.telegram_chat_id)
    return None
