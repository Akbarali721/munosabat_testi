"""Invite token helpers for relationship sessions."""

from __future__ import annotations

import secrets
from datetime import datetime

from sqlalchemy.orm import Session as DbSession

from app.models import Session


def generate_invite_token() -> str:
    return secrets.token_urlsafe(24)


def ensure_invite_token(db: DbSession, session: Session, *, max_attempts: int = 8) -> str:
    """Assign a unique invite_token if missing or revoked; retry on rare collisions."""
    if session.invite_token and not getattr(session, "invite_revoked_at", None):
        return session.invite_token

    for _ in range(max_attempts):
        token = generate_invite_token()
        taken = (
            db.query(Session.id)
            .filter(Session.invite_token == token)
            .first()
        )
        if taken:
            continue
        session.invite_token = token
        session.invite_token_created_at = datetime.utcnow()
        session.invite_revoked_at = None
        session.invite_token_used_at = None
        db.flush()
        return token

    raise RuntimeError("invite_token yaratib bo‘lmadi")


def revoke_invite_token(session: Session) -> None:
    session.invite_revoked_at = datetime.utcnow()


def get_session_by_invite_token(db: DbSession, token: str) -> Session | None:
    if not token:
        return None
    session = db.query(Session).filter(Session.invite_token == token).first()
    if not session or getattr(session, "invite_revoked_at", None):
        return None
    return session
