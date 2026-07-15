"""Premium access gate: payment status + admin approval."""

from __future__ import annotations

import json
import unittest
import uuid
from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (
    Answer,
    Gender,
    Participant,
    ParticipantRole,
    PremiumPaymentStatus,
    RelationshipStage,
    ScenarioQuestion,
    Session,
    SessionStatus,
)
from app.question_seeds import ALL_QUESTIONS
from app.services.payment import approve_premium, premium_access_granted


def _seed_questions(db) -> None:
    for item in ALL_QUESTIONS:
        stage = RelationshipStage(item["stage"])
        gender = Gender(item["gender_target"])
        db.add(
            ScenarioQuestion(
                scenario_id=item["scenario_id"],
                stage=stage,
                gender=gender,
                dimension=item["dimension"],
                text=item["text"],
                options_json=json.dumps(item["options"], ensure_ascii=False),
            )
        )
    db.commit()


class PremiumAccessTests(unittest.TestCase):
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

    def _complete_session(self) -> Session:
        session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.in_relationship,
            status=SessionStatus.complete,
            is_premium_unlocked=False,
            premium_payment_status=PremiumPaymentStatus.pending,
        )
        user_a = Participant(
            session_id=session.id,
            role=ParticipantRole.user_a,
            name="Akbarali",
            gender=Gender.male,
            completed_at=datetime.utcnow(),
            telegram_chat_id=1001,
        )
        user_b = Participant(
            session_id=session.id,
            role=ParticipantRole.user_b,
            name="Shaxnoza",
            gender=Gender.female,
            completed_at=datetime.utcnow(),
            telegram_chat_id=2002,
        )
        self.db.add_all([session, user_a, user_b])
        self.db.flush()

        questions_a = (
            self.db.query(ScenarioQuestion)
            .filter_by(stage=RelationshipStage.in_relationship, gender=Gender.male)
            .all()
        )
        questions_b = {
            q.scenario_id: q
            for q in self.db.query(ScenarioQuestion)
            .filter_by(stage=RelationshipStage.in_relationship, gender=Gender.female)
            .all()
        }
        for q in questions_a:
            qb = questions_b[q.scenario_id]
            self.db.add(
                Answer(
                    session_id=session.id,
                    participant_id=user_a.id,
                    scenario_id=q.scenario_id,
                    scenario_question_id=q.id,
                    choice_index=0,
                    choice_weight=3,
                )
            )
            self.db.add(
                Answer(
                    session_id=session.id,
                    participant_id=user_b.id,
                    scenario_id=q.scenario_id,
                    scenario_question_id=qb.id,
                    choice_index=0,
                    choice_weight=3,
                )
            )
        self.db.commit()
        self.db.refresh(session)
        return session

    def _admin_login(self):
        with patch("app.routers.admin.get_settings") as mock_settings:
            mock_settings.return_value.admin_secret = "secret-admin"
            return self.client.post(
                "/admin/login",
                data={"password": "secret-admin"},
                follow_redirects=False,
            )

    def test_pending_premium_route_redirects(self):
        session = self._complete_session()
        self.assertFalse(premium_access_granted(session))
        response = self.client.get(f"/session/{session.id}/premium", follow_redirects=False)
        self.assertIn(response.status_code, (302, 303, 403))
        if response.status_code in (302, 303):
            self.assertIn("/premium/payment", response.headers["location"])
        self.assertNotIn("Sizlarning chuqur juftlik profili", response.text)

    def test_love_alias_pending_redirects(self):
        session = self._complete_session()
        response = self.client.get(
            f"/love/session/{session.id}/premium",
            follow_redirects=False,
        )
        self.assertIn(response.status_code, (302, 303, 403))
        if response.status_code in (302, 303):
            self.assertIn("/premium/payment", response.headers["location"])

    def test_approved_premium_route_200(self):
        session = self._complete_session()
        approve_premium(self.db, session, actor="test")
        self.db.commit()
        response = self.client.get(f"/session/{session.id}/premium", follow_redirects=False)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Sizlarning chuqur juftlik profili", response.text)

    def test_invalid_token_404(self):
        response = self.client.get("/session/not-a-real-token/premium", follow_redirects=False)
        self.assertEqual(response.status_code, 404)

    def test_direct_url_keeps_premium_closed(self):
        session = self._complete_session()
        # Simulate unlock click (demo) — still pending
        unlock = self.client.post(
            f"/session/{session.id}/premium/unlock",
            data={"role": "user_a"},
            follow_redirects=False,
        )
        self.assertEqual(unlock.status_code, 303)
        direct = self.client.get(f"/session/{session.id}/premium", follow_redirects=False)
        self.assertEqual(direct.status_code, 302)
        self.assertIn("/premium/payment", direct.headers["location"])
        challenge = self.client.get(
            f"/session/{session.id}/challenge",
            follow_redirects=False,
        )
        self.assertEqual(challenge.status_code, 302)
        self.db.refresh(session)
        self.assertFalse(premium_access_granted(session))
        self.assertEqual(session.premium_payment_status, PremiumPaymentStatus.pending)

    def test_admin_approval_opens_premium(self):
        session = self._complete_session()
        pending = self.client.get(f"/session/{session.id}/premium", follow_redirects=False)
        self.assertEqual(pending.status_code, 302)

        with patch("app.routers.admin.get_settings") as mock_settings:
            mock_settings.return_value.admin_secret = "secret-admin"
            login = self.client.post(
                "/admin/login",
                data={"password": "secret-admin"},
                follow_redirects=False,
            )
            self.assertEqual(login.status_code, 303)
            approve = self.client.post(
                f"/admin/relationship-sessions/{session.id}/approve-premium",
                follow_redirects=False,
            )
            self.assertEqual(approve.status_code, 303)

            self.db.expire_all()
            session = self.db.get(Session, session.id)
            self.assertTrue(premium_access_granted(session))
            self.assertEqual(session.premium_payment_status, PremiumPaymentStatus.approved)
            self.assertTrue(session.is_premium_unlocked)

            opened = self.client.get(f"/session/{session.id}/premium", follow_redirects=False)
            self.assertEqual(opened.status_code, 200)
            self.assertIn("Sizlarning chuqur juftlik profili", opened.text)
    def test_admin_reject_and_reblock(self):
        session = self._complete_session()
        approve_premium(self.db, session, actor="test")
        self.db.commit()

        with patch("app.routers.admin.get_settings") as mock_settings:
            mock_settings.return_value.admin_secret = "secret-admin"
            self.client.post(
                "/admin/login",
                data={"password": "secret-admin"},
                follow_redirects=False,
            )
            reblock = self.client.post(
                f"/admin/relationship-sessions/{session.id}/reblock-premium",
                follow_redirects=False,
            )
            self.assertEqual(reblock.status_code, 303)

            self.db.expire_all()
            session = self.db.get(Session, session.id)
            self.assertFalse(premium_access_granted(session))
            closed = self.client.get(f"/session/{session.id}/premium", follow_redirects=False)
            self.assertEqual(closed.status_code, 302)

            self.client.post(
                f"/admin/relationship-sessions/{session.id}/reject-premium",
                follow_redirects=False,
            )

            self.db.expire_all()
            session = self.db.get(Session, session.id)
            self.assertEqual(session.premium_payment_status, PremiumPaymentStatus.rejected)
            self.assertFalse(session.is_premium_unlocked)

    def test_payment_page_available_while_pending(self):
        session = self._complete_session()
        page = self.client.get(
            f"/session/{session.id}/premium/payment?role=user_a",
            follow_redirects=False,
        )
        self.assertEqual(page.status_code, 200)
        self.assertIn("To‘liq tahlilni ochish", page.text)
        love = self.client.get(
            f"/love/session/{session.id}/premium/payment",
            follow_redirects=False,
        )
        self.assertEqual(love.status_code, 200)


if __name__ == "__main__":
    unittest.main()
