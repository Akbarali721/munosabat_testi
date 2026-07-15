"""Admin panel auth and relationship session listing."""

from __future__ import annotations

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
    Gender,
    Participant,
    ParticipantRole,
    PaymentOrder,
    PaymentProvider,
    PaymentStatus,
    PremiumPaymentStatus,
    RelationshipStage,
    Session,
    SessionStatus,
)
from app.services.admin_sessions import build_admin_row, detect_problems, mask_token
from app.services.invite_token import ensure_invite_token
from app.constants import PREMIUM_PRICE_UZS


class AdminHelpersUnitTests(unittest.TestCase):
    def test_mask_token(self):
        self.assertEqual(mask_token(None), "—")
        self.assertEqual(mask_token("short"), "short")
        masked = mask_token("abcdefghijklmnopqrstuvwxyz")
        self.assertTrue(masked.startswith("abcdef"))
        self.assertIn("…", masked)

    def test_problem_no_share_notify(self):
        session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.newly_meeting,
            status=SessionStatus.awaiting_user_b,
            invite_token="tok",
        )
        user_a = Participant(
            session_id=session.id,
            role=ParticipantRole.user_a,
            name="A",
            gender=Gender.male,
            completed_at=datetime.utcnow(),
        )
        problems = detect_problems(session, user_a, None)
        self.assertTrue(any(p.code == "no_share_notify" for p in problems))

    def test_pair_label_unknown_partner(self):
        session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.newly_meeting,
            status=SessionStatus.awaiting_user_b,
            initiator_telegram_id=1,
        )
        session.participants = [
            Participant(
                id=str(uuid.uuid4()),
                session_id=session.id,
                role=ParticipantRole.user_a,
                name="Akbarali",
                gender=Gender.male,
                telegram_username="akbarali",
            )
        ]
        row = build_admin_row(session)
        self.assertIn("Hali noma’lum", row.pair_label)
        self.assertIn("@akbarali", row.pair_label)


class AdminPanelIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app, raise_server_exceptions=True)

        session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.newly_meeting,
            status=SessionStatus.awaiting_user_b,
            initiator_telegram_id=1001,
            initiator_share_notified_at=datetime.utcnow(),
        )
        user_a = Participant(
            session_id=session.id,
            role=ParticipantRole.user_a,
            name="Akbarali",
            gender=Gender.male,
            completed_at=datetime.utcnow(),
            telegram_chat_id=1001,
            telegram_username="akbarali",
        )
        self.db.add_all([session, user_a])
        ensure_invite_token(self.db, session)
        self.db.commit()
        self.session_id = session.id

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def test_login_and_list(self):
        with patch("app.routers.admin.get_settings") as mock_settings:
            mock_settings.return_value.admin_secret = "secret-admin"
            denied = self.client.get("/admin/relationship-sessions", follow_redirects=False)
            self.assertEqual(denied.status_code, 303)
            login = self.client.post(
                "/admin/login",
                data={"password": "secret-admin"},
                follow_redirects=False,
            )
            self.assertEqual(login.status_code, 303)
            listing = self.client.get("/admin/relationship-sessions")
            self.assertEqual(listing.status_code, 200)
            self.assertIn("Munosabat sessiyalari", listing.text)
            self.assertIn("Akbarali", listing.text)
            self.assertIn("Hali noma’lum", listing.text)
            detail = self.client.get(f"/admin/relationship-sessions/{self.session_id}")
            self.assertEqual(detail.status_code, 200)
            self.assertIn("Timeline", detail.text)
            self.assertIn(self.session_id, detail.text)

    def test_premium_payments_mobile_markup_and_approve(self):
        pending_session = Session(
            id=str(uuid.uuid4()),
            relationship_stage=RelationshipStage.in_relationship,
            status=SessionStatus.complete,
            initiator_telegram_id=777,
            premium_payment_status=PremiumPaymentStatus.pending,
            is_premium_unlocked=False,
        )
        user_a = Participant(
            session_id=pending_session.id,
            role=ParticipantRole.user_a,
            name="Dilshod",
            gender=Gender.male,
            completed_at=datetime.utcnow(),
            telegram_chat_id=777,
        )
        order = PaymentOrder(
            session_id=pending_session.id,
            amount_uzs=PREMIUM_PRICE_UZS,
            status=PaymentStatus.pending,
            provider=PaymentProvider.demo,
        )
        self.db.add_all([pending_session, user_a, order])
        self.db.commit()

        with patch("app.routers.admin.get_settings") as mock_settings:
            mock_settings.return_value.admin_secret = "secret-admin"
            self.client.post(
                "/admin/login",
                data={"password": "secret-admin"},
                follow_redirects=False,
            )
            page = self.client.get("/admin/premium-payments?admin_token=keep-me")
            self.assertEqual(page.status_code, 200)
            self.assertIn("admin-premium-mobile", page.text)
            self.assertIn("admin-premium-desktop", page.text)
            self.assertIn("admin-payment-card", page.text)
            self.assertIn("Approve Premium", page.text)
            self.assertIn("Dilshod", page.text)
            self.assertIn("admin_token", page.text)
            self.assertIn("keep-me", page.text)

            approve = self.client.post(
                f"/admin/relationship-sessions/{pending_session.id}/approve-premium",
                data={
                    "next": "/admin/premium-payments",
                    "admin_token": "keep-me",
                },
                follow_redirects=False,
            )
            self.assertEqual(approve.status_code, 303)
            self.assertIn("/admin/premium-payments", approve.headers["location"])
            self.assertIn("admin_token=keep-me", approve.headers["location"])

            refreshed = self.client.get("/admin/premium-payments?admin_token=keep-me")
            self.assertEqual(refreshed.status_code, 200)
            # Pending section should no longer list this user as awaiting approve
            # Approved collapsed section should include Dilshod
            self.assertIn("Dilshod", refreshed.text)
            self.assertIn("Tasdiqlangan to‘lovlar", refreshed.text)

        self.db.expire_all()
        updated = self.db.get(Session, pending_session.id)
        self.assertEqual(updated.premium_payment_status, PremiumPaymentStatus.approved)
        self.assertTrue(updated.is_premium_unlocked)


if __name__ == "__main__":
    unittest.main()
