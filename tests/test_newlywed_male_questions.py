"""Male newlywed question load — 12 questions, codes, no female mix."""

from __future__ import annotations

import json
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.constants import IN_RELATIONSHIP_SCENARIO_ORDER, SESSION_QUESTION_COUNT
from app.database import Base, get_db
from app.main import app
from app.models import Gender, Participant, ParticipantRole, RelationshipStage, ScenarioQuestion, Session
from app.question_seeds import ALL_QUESTIONS
from app.services.scenarios import get_questions_for_participant, question_codes_for_questions


def _db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _seed_all(db) -> None:
    for item in ALL_QUESTIONS:
        payload: dict | list = item["options"]
        if item.get("question_code"):
            payload = {"question_code": item["question_code"], "options": item["options"]}
        db.add(
            ScenarioQuestion(
                scenario_id=item["scenario_id"],
                stage=RelationshipStage(item["stage"]),
                gender=Gender(item["gender_target"]),
                dimension=item["dimension"],
                text=item["text"],
                options_json=json.dumps(payload, ensure_ascii=False),
            )
        )
    db.commit()


class NewlywedMaleQuestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = _db_session()
        _seed_all(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def test_male_in_relationship_exactly_twelve(self) -> None:
        qs = get_questions_for_participant(
            self.db, RelationshipStage.in_relationship, Gender.male
        )
        self.assertEqual(len(qs), SESSION_QUESTION_COUNT)
        self.assertEqual([q.scenario_id for q in qs], IN_RELATIONSHIP_SCENARIO_ORDER)

    def test_male_codes(self) -> None:
        qs = get_questions_for_participant(
            self.db, RelationshipStage.in_relationship, Gender.male
        )
        self.assertEqual(
            question_codes_for_questions(qs),
            [f"newlywed_male_{i:02d}" for i in range(1, 13)],
        )

    def test_female_not_in_male_list(self) -> None:
        qs = get_questions_for_participant(
            self.db, RelationshipStage.in_relationship, Gender.male
        )
        self.assertTrue(all(q.gender == Gender.male for q in qs))

    def test_legacy_family_emotional_not_in_active_list(self) -> None:
        db = self.db
        db.add(
            ScenarioQuestion(
                scenario_id="family_emotional_need",
                stage=RelationshipStage.in_relationship,
                gender=Gender.male,
                dimension="legacy",
                text="legacy",
                options_json="[]",
            )
        )
        db.commit()
        qs = get_questions_for_participant(
            db, RelationshipStage.in_relationship, Gender.male
        )
        self.assertEqual(len(qs), 12)
        self.assertTrue(all(sid.startswith("newlywed_") for sid in (q.scenario_id for q in qs)))


class NewlywedMalePageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = _db_session()
        _seed_all(self.db)

        def override_get_db():
            yield self.db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.db.close()

    def test_page_twelve_steps_male_newlywed(self) -> None:
        session = Session(relationship_stage=RelationshipStage.in_relationship)
        self.db.add(session)
        self.db.flush()
        self.db.add(
            Participant(
                session_id=session.id,
                role=ParticipantRole.user_a,
                name="Erkak",
                gender=Gender.male,
            )
        )
        self.db.commit()
        r = self.client.get(f"/session/{session.id}/questions?role=user_a")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text.count('class="quiz-step'), 12)
        self.assertIn("Ishdan charchab uyga kelganingizda", r.text)


if __name__ == "__main__":
    unittest.main()
