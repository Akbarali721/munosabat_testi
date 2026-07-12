"""Invite token helpers for relationship sessions."""

from __future__ import annotations

import secrets

from sqlalchemy.orm import Session as DbSession

from app.models import Session


def generate_invite_token() -> str:
    return secrets.token_urlsafe(24)


def ensure_invite_token(db: DbSession, session: Session, *, max_attempts: int = 8) -> str:
    """Assign a unique invite_token if missing; retry on rare collisions."""
    if session.invite_token:
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
        db.flush()
        return token

    raise RuntimeError("invite_token yaratib bo‘lmadi")


def get_session_by_invite_token(db: DbSession, token: str) -> Session | None:
    if not token:
        return None
    return db.query(Session).filter(Session.invite_token == token).first()
