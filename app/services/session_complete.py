"""Complete partner submission with locking and independent notifications."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session as DbSession

from app.models import Participant, ParticipantRole, Session, SessionStatus
from app.services.results import build_session_result

logger = logging.getLogger(__name__)


def complete_partner_session(db: DbSession, session_id: str) -> bool:
    """
    Mark session complete if both participants finished.
    Returns True if this call transitioned to complete (caller should notify).
    Idempotent under concurrent submits via row lock when supported.
    """
    # Prefer SELECT FOR UPDATE on Postgres; SQLite ignores / works without
    try:
        session = (
            db.query(Session)
            .filter(Session.id == session_id)
            .with_for_update()
            .first()
        )
    except Exception:
        session = db.get(Session, session_id)

    if not session:
        return False

    if session.status == SessionStatus.complete:
        return False

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
    if not user_a or not user_b or not user_a.completed_at or not user_b.completed_at:
        return False

    # Ensure result can be built once before flipping status
    result = build_session_result(db, session)
    if not result:
        logger.error("build_session_result failed for session %s", session_id)
        return False

    session.status = SessionStatus.complete
    db.commit()
    return True
