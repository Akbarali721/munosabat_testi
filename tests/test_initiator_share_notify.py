"""User1 completion → bot share keyboard notification."""

from __future__ import annotations

import asyncio
import unittest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.copy.notifications import initiator_answers_saved
from app.database import Base
from app.models import (
    Gender,
    Participant,
    ParticipantRole,
    RelationshipStage,
    Session,
    SessionStatus,
)
from app.services.invite_share import (
    PARTNER_SHARE_TEXT,
    build_partner_deep_link,
    build_telegram_share_url,
    initiator_invite_keyboard,
)
from app.services.invite_token import ensure_invite_token
from app.services.notifications import notify_initiator_answers_saved


class InviteShareHelpersTests(unittest.TestCase):
    def test_share_url_encodes_deep_link_and_text(self):
        with patch("app.services.invite_share.get_settings") as mock_settings:
            mock_settings.return_value.resolve_bot_username.return_value = "qadam_loyihaBot"
            mock_settings.return_value.webapp_base_url = "https://app.example"
            deep = build_partner_deep_link("tok_abc")
            share = build_telegram_share_url("tok_abc")
            kb = initiator_invite_keyboard("tok_abc", "session-1")

        self.assertEqual(deep, "https://t.me/qadam_loyihaBot?start=rel_invite_tok_abc")
        self.assertIn("t.me/share/url", share or "")
        self.assertIn("rel_invite_tok_abc", share or "")
        self.assertIsNotNone(kb)
        rows = kb["inline_keyboard"]
        self.assertEqual(rows[0][0]["text"], "💌 Juftimga yuborish")
        self.assertIn("share/url", rows[0][0]["url"])
        self.assertEqual(rows[1][0]["text"], "⏳ Holatni ko‘rish")
        self.assertIn("/session/session-1/status", rows[1][0]["web_app"]["url"])
        self.assertIn("Juftlik suhbati", PARTNER_SHARE_TEXT)


class InitiatorShareNotifyTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def _session(self) -> Session:
        session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.newly_meeting,
            status=SessionStatus.awaiting_user_b,
            initiator_telegram_id=1001,
        )
        user_a = Participant(
            session_id=session.id,
            role=ParticipantRole.user_a,
            name="Akbarali",
            gender=Gender.male,
            completed_at=datetime.utcnow(),
            telegram_chat_id=1001,
        )
        self.db.add_all([session, user_a])
        ensure_invite_token(self.db, session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def test_sends_share_keyboard_to_initiator(self):
        session = self._session()
        with (
            patch("app.services.notifications.SessionLocal", self.SessionLocal),
            patch("app.services.notifications.telegram_client") as mock_client,
            patch("app.services.invite_share.get_settings") as mock_settings,
        ):
            mock_settings.return_value.resolve_bot_username.return_value = "qadam_loyihaBot"
            mock_settings.return_value.webapp_base_url = "https://app.example"
            mock_client.enabled = True
            mock_client.send_message = AsyncMock(return_value=True)

            ok = asyncio.get_event_loop().run_until_complete(
                notify_initiator_answers_saved(session.id)
            )

        self.assertTrue(ok)
        mock_client.send_message.assert_awaited_once()
        args, kwargs = mock_client.send_message.await_args
        self.assertEqual(args[0], 1001)
        self.assertEqual(args[1], initiator_answers_saved())
        markup = kwargs.get("reply_markup")
        self.assertIsNotNone(markup)
        self.assertEqual(markup["inline_keyboard"][0][0]["text"], "💌 Juftimga yuborish")

        self.db.refresh(session)
        self.assertIsNotNone(session.initiator_share_notified_at)

    def test_idempotent_second_call_skips_resend(self):
        session = self._session()
        session.initiator_share_notified_at = datetime.utcnow()
        self.db.commit()

        with (
            patch("app.services.notifications.SessionLocal", self.SessionLocal),
            patch("app.services.notifications.telegram_client") as mock_client,
        ):
            mock_client.enabled = True
            mock_client.send_message = AsyncMock(return_value=True)
            ok = asyncio.get_event_loop().run_until_complete(
                notify_initiator_answers_saved(session.id)
            )

        self.assertTrue(ok)
        mock_client.send_message.assert_not_awaited()

    def test_telegram_failure_does_not_raise(self):
        session = self._session()
        with (
            patch("app.services.notifications.SessionLocal", self.SessionLocal),
            patch("app.services.notifications.telegram_client") as mock_client,
            patch("app.services.invite_share.get_settings") as mock_settings,
        ):
            mock_settings.return_value.resolve_bot_username.return_value = "qadam_loyihaBot"
            mock_settings.return_value.webapp_base_url = "https://app.example"
            mock_client.enabled = True
            mock_client.send_message = AsyncMock(side_effect=RuntimeError("down"))

            ok = asyncio.get_event_loop().run_until_complete(
                notify_initiator_answers_saved(session.id)
            )

        self.assertFalse(ok)
        self.db.refresh(session)
        self.assertIsNone(session.initiator_share_notified_at)


if __name__ == "__main__":
    unittest.main()
