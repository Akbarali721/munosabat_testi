"""Result notification must target session initiator_telegram_id (User1)."""

from __future__ import annotations

import asyncio
import unittest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    Gender,
    Participant,
    ParticipantRole,
    RelationshipStage,
    Session,
    SessionStatus,
)
from app.services.notifications import send_result_notifications
from app.services.session_telegram import (
    set_initiator_telegram_id,
    set_partner_telegram_id,
)


class SessionTelegramBindTests(unittest.TestCase):
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

    def test_partner_cannot_overwrite_initiator(self):
        session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.newly_meeting,
            status=SessionStatus.awaiting_user_b,
            initiator_telegram_id=1001,
        )
        user_a = Participant(
            session_id=session.id,
            role=ParticipantRole.user_a,
            name="A",
            gender=Gender.male,
            telegram_chat_id=1001,
        )
        user_b = Participant(
            session_id=session.id,
            role=ParticipantRole.user_b,
            name="B",
            gender=Gender.female,
        )
        self.db.add_all([session, user_a, user_b])
        self.db.flush()

        set_partner_telegram_id(session, 2002)
        set_initiator_telegram_id(session, 9999)  # must be ignored
        self.db.commit()

        self.assertEqual(session.initiator_telegram_id, 1001)
        self.assertEqual(session.partner_telegram_id, 2002)

    def test_partner_cannot_use_initiator_id(self):
        session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.newly_meeting,
            status=SessionStatus.awaiting_user_b,
            initiator_telegram_id=1001,
        )
        self.db.add(session)
        self.db.flush()
        set_partner_telegram_id(session, 1001)
        self.assertIsNone(session.partner_telegram_id)


class ResultNotifyInitiatorTests(unittest.TestCase):
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

    def _complete_session(self, *, initiator_id=1001, partner_id=2002) -> Session:
        session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.newly_meeting,
            status=SessionStatus.complete,
            initiator_telegram_id=initiator_id,
            partner_telegram_id=partner_id,
        )
        user_a = Participant(
            session_id=session.id,
            role=ParticipantRole.user_a,
            name="Akbarali",
            gender=Gender.male,
            completed_at=datetime.utcnow(),
            telegram_chat_id=initiator_id,
        )
        user_b = Participant(
            session_id=session.id,
            role=ParticipantRole.user_b,
            name="Shaxnoza",
            gender=Gender.female,
            completed_at=datetime.utcnow(),
            telegram_chat_id=partner_id,
        )
        self.db.add_all([session, user_a, user_b])
        self.db.commit()
        return session

    def test_sends_to_initiator_first_with_result_url(self):
        session = self._complete_session()
        with (
            patch("app.services.notifications.SessionLocal", self.SessionLocal),
            patch("app.services.notifications.telegram_client") as mock_client,
            patch(
                "app.services.notifications.get_settings"
            ) as mock_settings,
        ):
            mock_settings.return_value.webapp_base_url = "https://app.example"
            mock_client.enabled = True
            mock_client.send_message = AsyncMock(return_value=True)

            asyncio.get_event_loop().run_until_complete(
                send_result_notifications(session.id, completed_by="user_b")
            )

            self.assertEqual(mock_client.send_message.await_count, 2)
            first = mock_client.send_message.await_args_list[0]
            second = mock_client.send_message.await_args_list[1]
            self.assertEqual(first.args[0], 1001)
            self.assertEqual(second.args[0], 2002)
            self.assertIn(
                f"/session/{session.id}/result",
                first.kwargs.get("web_app_url", ""),
            )
            self.assertEqual(first.kwargs.get("button_text"), "💬 Natijani ko‘rish")

    def test_initiator_notified_even_if_participant_chat_empty(self):
        session = self._complete_session()
        user_a = (
            self.db.query(Participant)
            .filter_by(session_id=session.id, role=ParticipantRole.user_a)
            .one()
        )
        user_a.telegram_chat_id = None
        self.db.commit()

        with (
            patch("app.services.notifications.SessionLocal", self.SessionLocal),
            patch("app.services.notifications.telegram_client") as mock_client,
            patch("app.services.notifications.get_settings") as mock_settings,
        ):
            mock_settings.return_value.webapp_base_url = "https://app.example"
            mock_client.enabled = True
            mock_client.send_message = AsyncMock(return_value=True)

            asyncio.get_event_loop().run_until_complete(
                send_result_notifications(session.id, completed_by="user_b")
            )

            chats = [c.args[0] for c in mock_client.send_message.await_args_list]
            self.assertIn(1001, chats)

    def test_telegram_error_does_not_raise(self):
        session = self._complete_session()
        with (
            patch("app.services.notifications.SessionLocal", self.SessionLocal),
            patch("app.services.notifications.telegram_client") as mock_client,
            patch("app.services.notifications.get_settings") as mock_settings,
        ):
            mock_settings.return_value.webapp_base_url = "https://app.example"
            mock_client.enabled = True
            mock_client.send_message = AsyncMock(side_effect=RuntimeError("network"))

            asyncio.get_event_loop().run_until_complete(
                send_result_notifications(session.id, completed_by="user_b")
            )


if __name__ == "__main__":
    unittest.main()
