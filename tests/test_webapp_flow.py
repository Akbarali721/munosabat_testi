"""Telegram WebApp flow: invite, waiting, auth, notifications."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import unittest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch
from urllib.parse import urlencode

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.bot.handlers import PENDING_PARTNER_NAME, _handle_rel_invite
from app.config import Settings
from app.database import Base, get_db
from app.main import app
from app.models import (
    Answer,
    Gender,
    Participant,
    ParticipantRole,
    RelationshipStage,
    ScenarioQuestion,
    Session,
    SessionStatus,
)
from app.question_seeds import ALL_QUESTIONS
from app.services.invite_token import ensure_invite_token, generate_invite_token
from app.services.telegram_auth import TelegramAuthError, validate_init_data
from app.services.session_complete import complete_partner_session


def _seed_questions(db) -> None:
    for item in ALL_QUESTIONS:
        db.add(
            ScenarioQuestion(
                scenario_id=item["scenario_id"],
                stage=RelationshipStage(item["stage"]),
                gender=Gender(item["gender_target"]),
                dimension=item["dimension"],
                text=item["text"],
                options_json=json.dumps(item["options"], ensure_ascii=False),
            )
        )
    db.commit()


def _make_init_data(user_id: int, bot_token: str = "TEST_BOT_TOKEN") -> str:
    user = json.dumps({"id": user_id, "first_name": "Test"}, separators=(",", ":"))
    auth_date = str(int(time.time()))
    pairs = {"auth_date": auth_date, "user": user}
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    digest = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    return urlencode({**pairs, "hash": digest})


class TelegramAuthUnitTests(unittest.TestCase):
    def test_valid_init_data(self):
        token = "TEST_BOT_TOKEN"
        raw = _make_init_data(42, token)
        user = validate_init_data(raw, bot_token=token)
        self.assertEqual(user.id, 42)

    def test_invalid_hash(self):
        token = "TEST_BOT_TOKEN"
        raw = _make_init_data(42, token) + "x"
        with self.assertRaises(TelegramAuthError):
            validate_init_data(raw, bot_token=token)

    def test_invite_token_unique_format(self):
        a = generate_invite_token()
        b = generate_invite_token()
        self.assertNotEqual(a, b)
        self.assertGreaterEqual(len(a), 20)

    def test_bot_link_url_strips_at_prefix(self):
        settings = Settings.__new__(Settings)
        settings.telegram_bot_username = "@MyQadamBot"
        url = settings.bot_link_url("rel_invite_abc")
        self.assertEqual(url, "https://t.me/MyQadamBot?start=rel_invite_abc")

    def test_bot_link_url_none_without_username(self):
        settings = Settings.__new__(Settings)
        settings.telegram_bot_username = None
        self.assertIsNone(settings.bot_link_url("rel_invite_abc"))
        settings.telegram_bot_username = "   "
        self.assertIsNone(settings.bot_link_url("rel_invite_abc"))
        settings.telegram_bot_username = "@"
        self.assertIsNone(settings.bot_link_url("rel_invite_abc"))


class WebAppFlowIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        _seed_questions(self.db)

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app, raise_server_exceptions=True)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def _create_initiator_done(self, telegram_id: int = 1001) -> Session:
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
            telegram_chat_id=telegram_id,
        )
        self.db.add(session)
        self.db.add(user_a)
        self.db.flush()
        ensure_invite_token(self.db, session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def _add_answers(self, session: Session, participant: Participant, weight: int = 3) -> None:
        questions = (
            self.db.query(ScenarioQuestion)
            .filter_by(stage=session.relationship_stage, gender=participant.gender)
            .all()
        )
        for q in questions:
            self.db.add(
                Answer(
                    session_id=session.id,
                    participant_id=participant.id,
                    scenario_id=q.scenario_id,
                    scenario_question_id=q.id,
                    choice_index=0,
                    choice_weight=weight,
                )
            )
        self.db.commit()

    def test_user2_finish_goes_to_waiting_not_result(self):
        session = self._create_initiator_done()
        user_a = self.db.query(Participant).filter_by(session_id=session.id).one()
        self._add_answers(session, user_a)

        user_b = Participant(
            session_id=session.id,
            role=ParticipantRole.user_b,
            name="Shaxnoza",
            gender=Gender.female,
            telegram_chat_id=2002,
        )
        self.db.add(user_b)
        self.db.commit()
        self._add_answers(session, user_b, weight=2)

        # Simulate partner submit path via complete + waiting page
        user_b.completed_at = datetime.utcnow()
        self.db.commit()
        newly = complete_partner_session(self.db, session.id)
        self.assertTrue(newly)

        waiting = self.client.get(f"/session/{session.id}/waiting")
        self.assertEqual(waiting.status_code, 200)
        self.assertIn("Javoblaringiz qabul qilindi", waiting.text)
        self.assertNotIn("Bir-biringizni tushunish darajasi", waiting.text)

        # Result without initData shows bootstrap, not full result
        result = self.client.get(f"/session/{session.id}/result")
        self.assertEqual(result.status_code, 200)
        self.assertIn("Natija ochilmoqda", result.text)

    def test_result_forbidden_for_stranger(self):
        session = self._create_initiator_done(telegram_id=1001)
        user_a = self.db.query(Participant).filter_by(session_id=session.id).one()
        self._add_answers(session, user_a)
        user_b = Participant(
            session_id=session.id,
            role=ParticipantRole.user_b,
            name="Shaxnoza",
            gender=Gender.female,
            completed_at=datetime.utcnow(),
            telegram_chat_id=2002,
        )
        self.db.add(user_b)
        self.db.commit()
        self._add_answers(session, user_b)
        complete_partner_session(self.db, session.id)

        with patch("app.routers.pages.validate_init_data") as mock_val:
            from app.services.telegram_auth import TelegramWebAppUser

            mock_val.return_value = TelegramWebAppUser(id=9999)
            resp = self.client.get(
                f"/session/{session.id}/result",
                headers={"X-Telegram-Init-Data": "fake"},
            )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("ko‘ra olmaysiz", resp.text)

    def test_result_allowed_for_participant(self):
        session = self._create_initiator_done(telegram_id=1001)
        user_a = self.db.query(Participant).filter_by(session_id=session.id).one()
        self._add_answers(session, user_a)
        user_b = Participant(
            session_id=session.id,
            role=ParticipantRole.user_b,
            name="Shaxnoza",
            gender=Gender.female,
            completed_at=datetime.utcnow(),
            telegram_chat_id=2002,
        )
        self.db.add(user_b)
        self.db.commit()
        self._add_answers(session, user_b)
        complete_partner_session(self.db, session.id)

        with patch("app.routers.pages.validate_init_data") as mock_val:
            from app.services.telegram_auth import TelegramWebAppUser

            mock_val.return_value = TelegramWebAppUser(id=1001)
            resp = self.client.get(
                f"/session/{session.id}/result",
                headers={"X-Telegram-Init-Data": "fake"},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Sizlarning munosabat tahlili tayyor", resp.text)

    def test_complete_idempotent(self):
        session = self._create_initiator_done()
        user_a = self.db.query(Participant).filter_by(session_id=session.id).one()
        self._add_answers(session, user_a)
        user_b = Participant(
            session_id=session.id,
            role=ParticipantRole.user_b,
            name="Shaxnoza",
            gender=Gender.female,
            completed_at=datetime.utcnow(),
            telegram_chat_id=2002,
        )
        self.db.add(user_b)
        self.db.commit()
        self._add_answers(session, user_b)

        self.assertTrue(complete_partner_session(self.db, session.id))
        self.assertFalse(complete_partner_session(self.db, session.id))

    def test_invite_page_has_deep_link_token(self):
        session = self._create_initiator_done()
        with patch("app.routers.pages.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.telegram_bot_username = "testbot"
            settings.bot_link_url.side_effect = (
                lambda payload: f"https://t.me/testbot?start={payload}"
            )
            resp = self.client.get(f"/invite/{session.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Birinchi qadam tugadi", resp.text)
        self.assertIn("Javoblaringiz saqlandi", resp.text)
        self.assertIn("Siz — testni tugatdingiz", resp.text)
        self.assertIn("Sherigingiz — javobini kutyapmiz", resp.text)
        self.assertIn("Telegram orqali yuborish", resp.text)
        self.assertIn("t.me/share/url", resp.text)
        self.assertNotIn("TELEGRAM_BOT_USERNAME", resp.text)
        self.assertNotIn("Havola faqat siz ikkalangiz uchun", resp.text)
        self.assertNotIn("WebApp", resp.text)
        self.db.refresh(session)
        self.assertTrue(session.invite_token)
        self.assertIn(session.invite_token, resp.text)
        self.assertIn("rel_invite_", resp.text)

    def test_invite_page_friendly_error_without_bot_username(self):
        session = self._create_initiator_done()
        with patch("app.routers.pages.get_settings") as mock_settings:
            settings = mock_settings.return_value
            settings.telegram_bot_username = None
            settings.bot_link_url.return_value = None
            with self.assertLogs("app.routers.pages", level="ERROR") as logs:
                resp = self.client.get(f"/invite/{session.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Ulashish havolasini tayyorlab bo‘lmadi", resp.text)
        self.assertNotIn("TELEGRAM_BOT_USERNAME", resp.text)
        self.assertNotIn("Telegram orqali yuborish", resp.text)
        self.assertTrue(any("TELEGRAM_BOT_USERNAME missing" in line for line in logs.output))

    def test_invite_redirects_if_user_a_incomplete(self):
        session = self._create_initiator_done()
        user_a = (
            self.db.query(Participant)
            .filter_by(session_id=session.id, role=ParticipantRole.user_a)
            .one()
        )
        user_a.completed_at = None
        self.db.commit()
        resp = self.client.get(f"/invite/{session.id}", follow_redirects=False)
        self.assertEqual(resp.status_code, 303)
        self.assertIn("/questions", resp.headers.get("location", ""))

    def test_rel_invite_self_block(self):
        session = self._create_initiator_done(telegram_id=1001)
        with patch("app.bot.handlers.telegram_client") as mock_client:
            mock_client.send_message = AsyncMock(return_value=True)
            import asyncio

            asyncio.get_event_loop().run_until_complete(
                _handle_rel_invite(1001, session.invite_token, self.db)
            )
            args = mock_client.send_message.call_args[0]
            self.assertIn("ikkinchi ishtirokchi", args[1])

    def test_rel_invite_binds_partner(self):
        session = self._create_initiator_done(telegram_id=1001)
        with patch("app.bot.handlers.telegram_client") as mock_client:
            mock_client.send_message = AsyncMock(return_value=True)
            import asyncio

            asyncio.get_event_loop().run_until_complete(
                _handle_rel_invite(2002, session.invite_token, self.db)
            )
        user_b = (
            self.db.query(Participant)
            .filter_by(session_id=session.id, role=ParticipantRole.user_b)
            .one()
        )
        self.assertEqual(user_b.telegram_chat_id, 2002)
        self.assertEqual(user_b.name, PENDING_PARTNER_NAME)
        call_kwargs = mock_client.send_message.call_args.kwargs
        self.assertEqual(call_kwargs.get("button_text"), "❤️ Testni boshlash")
        self.assertIn("web_app_url", call_kwargs)

    def test_third_user_blocked(self):
        session = self._create_initiator_done(telegram_id=1001)
        user_b = Participant(
            session_id=session.id,
            role=ParticipantRole.user_b,
            name=PENDING_PARTNER_NAME,
            gender=Gender.female,
            telegram_chat_id=2002,
        )
        self.db.add(user_b)
        self.db.commit()
        with patch("app.bot.handlers.telegram_client") as mock_client:
            mock_client.send_message = AsyncMock(return_value=True)
            import asyncio

            asyncio.get_event_loop().run_until_complete(
                _handle_rel_invite(3003, session.invite_token, self.db)
            )
            self.assertIn("allaqachon", mock_client.send_message.call_args[0][1])


if __name__ == "__main__":
    unittest.main()
