"""Lightweight relationship event log (admin / analytics)."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session as DbSession

from app.models import RelationshipEvent

logger = logging.getLogger(__name__)


def log_relationship_event(
    db: DbSession,
    *,
    session_id: str,
    event_type: str,
    telegram_id: int | None = None,
    payload: str | None = None,
    commit: bool = False,
) -> None:
    try:
        db.add(
            RelationshipEvent(
                session_id=session_id,
                event_type=event_type,
                telegram_id=telegram_id,
                payload=payload or "",
                created_at=datetime.utcnow(),
            )
        )
        if commit:
            db.commit()
        else:
            db.flush()
    except Exception:
        logger.exception(
            "Failed to log relationship event type=%s session_id=%s",
            event_type,
            session_id,
        )
        try:
            db.rollback()
        except Exception:
            pass
