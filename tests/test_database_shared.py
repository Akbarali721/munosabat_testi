"""Shared-database / invite-token visibility tests (Web vs Bot sessions)."""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid
from datetime import datetime
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import (
    database_log_info,
    normalize_database_url,
    resolve_database_url,
)
from app.models import (
    Base,
    Gender,
    Participant,
    ParticipantRole,
    RelationshipStage,
    Session,
    SessionStatus,
)
from app.services.invite_token import ensure_invite_token, get_session_by_invite_token


class DatabaseUrlUnitTests(unittest.TestCase):
    def test_normalize_postgres_schemes(self):
        self.assertEqual(
            normalize_database_url("postgres://u:p@host:5432/db"),
            "postgresql+psycopg://u:p@host:5432/db",
        )
        self.assertEqual(
            normalize_database_url("postgresql://u:p@host/db"),
            "postgresql+psycopg://u:p@host/db",
        )
        self.assertEqual(
            normalize_database_url("postgresql+psycopg://u:p@host/db"),
            "postgresql+psycopg://u:p@host/db",
        )

    def test_log_info_hides_password(self):
        info = database_log_info("postgresql+psycopg://user:secret@db.example:5432/qadam")
        self.assertEqual(info["backend"], "postgresql")
        self.assertEqual(info["host"], "db.example:5432")
        self.assertEqual(info["database"], "qadam")
        blob = " ".join(info.values())
        self.assertNotIn("secret", blob)
        self.assertNotIn("user:", blob)

    def test_production_requires_database_url(self):
        with patch.dict(os.environ, {"RAILWAY_ENVIRONMENT": "production"}, clear=False):
            os.environ.pop("DATABASE_URL", None)
            with self.assertRaises(RuntimeError):
                resolve_database_url()

    def test_local_fallback_sqlite(self):
        env = {k: v for k, v in os.environ.items() if k not in {"DATABASE_URL", "RAILWAY_ENVIRONMENT", "ENVIRONMENT", "APP_ENV"}}
        with patch.dict(os.environ, env, clear=True):
            self.assertTrue(resolve_database_url().startswith("sqlite:///"))


class SharedInviteTokenTests(unittest.TestCase):
    """Simulate Web service write + Bot service read on the same DB file/engine URL."""

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db_url = f"sqlite:///{self._tmp.name}"
        self.engine = create_engine(
            self.db_url,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def tearDown(self):
        self.engine.dispose()
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass

    def _create_web_session_with_token(self) -> str:
        """Web service process: create relationship session + invite token, commit."""
        db = self.SessionFactory()
        try:
            session = Session(
                id=str(uuid.uuid4()),
                relationship_stage=RelationshipStage.newly_meeting,
                status=SessionStatus.awaiting_user_b,
            )
            user_a = Participant(
                session_id=session.id,
                role=ParticipantRole.user_a,
                name="Akbarali",
                gender=Gender.male,
                completed_at=datetime.utcnow(),
                telegram_chat_id=1001,
            )
            db.add(session)
            db.add(user_a)
            db.flush()
            token = ensure_invite_token(db, session)
            db.commit()
            return token
        finally:
            db.close()

    def test_bot_session_can_read_web_invite_token(self):
        token = self._create_web_session_with_token()
        self.assertTrue(token)

        # Separate SessionLocal (= Bot service connection)
        bot_db = self.SessionFactory()
        try:
            found = get_session_by_invite_token(bot_db, token)
            self.assertIsNotNone(found)
            assert found is not None
            self.assertEqual(found.invite_token, token)
        finally:
            bot_db.close()

    def test_commit_visible_to_new_session(self):
        token = self._create_web_session_with_token()
        reader_a = self.SessionFactory()
        reader_b = self.SessionFactory()
        try:
            a = get_session_by_invite_token(reader_a, token)
            b = get_session_by_invite_token(reader_b, token)
            self.assertIsNotNone(a)
            self.assertIsNotNone(b)
            assert a is not None and b is not None
            self.assertEqual(a.id, b.id)
        finally:
            reader_a.close()
            reader_b.close()

    def test_duplicate_invite_token_rejected(self):
        token = self._create_web_session_with_token()
        db = self.SessionFactory()
        try:
            other = Session(
                id=str(uuid.uuid4()),
                relationship_stage=RelationshipStage.newly_meeting,
                status=SessionStatus.awaiting_user_b,
                invite_token=token,
            )
            db.add(other)
            with self.assertRaises(IntegrityError):
                db.commit()
            db.rollback()
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
