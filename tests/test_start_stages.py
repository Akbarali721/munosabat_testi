"""Start form: two UI categories and question bank mapping."""

import unittest

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Gender, RelationshipStage, Session
from app.services import seed_scenarios
from app.services.relationship_stage import (
    START_FORM_STAGES,
    is_allowed_start_stage,
    question_bank_stage,
)
from app.services.scenarios import get_questions_for_participant, questions_ready


class RelationshipStageMappingTests(unittest.TestCase):
    def test_start_form_has_two_stages(self):
        self.assertEqual(len(START_FORM_STAGES), 2)
        self.assertTrue(is_allowed_start_stage(RelationshipStage.dating))
        self.assertTrue(is_allowed_start_stage(RelationshipStage.newly_married))
        self.assertFalse(is_allowed_start_stage(RelationshipStage.married))
        self.assertFalse(is_allowed_start_stage(RelationshipStage.newly_meeting))

    def test_question_bank_mapping(self):
        self.assertEqual(
            question_bank_stage(RelationshipStage.dating),
            RelationshipStage.newly_meeting,
        )
        self.assertEqual(
            question_bank_stage(RelationshipStage.newly_married),
            RelationshipStage.in_relationship,
        )


class StartPageIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        seed_scenarios(cls.db)
        cls.db.close()

    def setUp(self):
        self.client = TestClient(app)

    def test_start_page_shows_two_categories_only(self):
        resp = self.client.get("/start")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Sizning munosabatingiz qaysi bosqichda?", resp.text)
        self.assertIn("Endi tanishayapmiz", resp.text)
        self.assertIn("Yaqinda oila qurdik", resp.text)
        self.assertIn(
            "Bir-biringizni yaxshiroq tushunishga yordam beradigan hayotiy savollar.",
            resp.text,
        )
        self.assertNotIn('value="married"', resp.text)
        self.assertNotIn('value="newly_meeting"', resp.text)
        self.assertNotIn('value="in_relationship"', resp.text)
        self.assertIn('value="dating"', resp.text)
        self.assertIn('value="newly_married"', resp.text)

    def test_post_dating_creates_session_and_loads_questions(self):
        resp = self.client.post(
            "/start",
            data={
                "name": "Ali",
                "gender": Gender.male.value,
                "relationship_stage": RelationshipStage.dating.value,
            },
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 303)
        location = resp.headers["location"]
        session_id = location.split("/session/")[1].split("/")[0].split("?")[0]
        db = SessionLocal()
        try:
            session = db.get(Session, session_id)
            self.assertIsNotNone(session)
            self.assertEqual(session.relationship_stage, RelationshipStage.dating)
            self.assertTrue(
                questions_ready(db, session.relationship_stage, Gender.male)
            )
            qs = get_questions_for_participant(
                db, session.relationship_stage, Gender.male
            )
            self.assertEqual(len(qs), 12)
        finally:
            db.close()

    def test_post_rejects_legacy_married_stage(self):
        resp = self.client.post(
            "/start",
            data={
                "name": "Test",
                "gender": Gender.female.value,
                "relationship_stage": RelationshipStage.married.value,
            },
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
