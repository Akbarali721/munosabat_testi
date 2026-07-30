"""Participant question list: 12 per gender/stage, no legacy mix."""

from __future__ import annotations

import json
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.constants import (
    IN_RELATIONSHIP_SCENARIO_ORDER,
    SCENARIO_ORDER,
    SESSION_QUESTION_COUNT,
)
from app.database import Base, get_db
from app.main import app
from app.models import Gender, Participant, ParticipantRole, RelationshipStage, ScenarioQuestion, Session
from app.question_seeds import ALL_QUESTIONS
from app.services.scenarios import (
    active_scenario_ids_for_stage,
    get_questions_for_participant,
    questions_ready,
)


def _db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _seed_all_questions(db) -> None:
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


def _seed_legacy_newly_meeting_male(db) -> None:
    legacy_ids = [
        "promise_call",
        "small_attention",
        "phone_attention",
        "being_late",
        "friends_plan",
        "first_bill",
        "different_opinion",
        "mother_call",
        "private_secret",
        "future_talk",
        "interrupting",
        "initiative",
    ]
    for sid in legacy_ids:
        db.add(
            ScenarioQuestion(
                scenario_id=sid,
                stage=RelationshipStage.newly_meeting,
                gender=Gender.male,
                dimension="legacy",
                text=f"Legacy {sid}",
                options_json=json.dumps(
                    [{"text": "A", "weight": 4}, {"text": "B", "weight": 3}],
                    ensure_ascii=False,
                ),
            )
        )
    db.commit()


class ParticipantQuestionLoadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = _db_session()
        _seed_all_questions(self.db)
        _seed_legacy_newly_meeting_male(self.db)

    def tearDown(self) -> None:
        self.db.close()

    def _assert_twelve_active_only(
        self,
        stage: RelationshipStage,
        gender: Gender,
        expected_order: list[str],
    ) -> None:
        self.assertTrue(questions_ready(self.db, stage, gender))
        questions = get_questions_for_participant(self.db, stage, gender)
        self.assertEqual(len(questions), SESSION_QUESTION_COUNT)
        self.assertEqual([q.scenario_id for q in questions], expected_order)
        self.assertTrue(all(q.stage == stage for q in questions))
        self.assertTrue(all(q.gender == gender for q in questions))

    def test_male_newly_meeting_twelve_no_legacy(self) -> None:
        self._assert_twelve_active_only(
            RelationshipStage.newly_meeting,
            Gender.male,
            SCENARIO_ORDER,
        )
        ids = {q.scenario_id for q in get_questions_for_participant(
            self.db, RelationshipStage.newly_meeting, Gender.male
        )}
        self.assertNotIn("promise_call", ids)

    def test_female_newly_meeting_twelve(self) -> None:
        self._assert_twelve_active_only(
            RelationshipStage.newly_meeting,
            Gender.female,
            SCENARIO_ORDER,
        )

    def test_male_in_relationship_twelve(self) -> None:
        self._assert_twelve_active_only(
            RelationshipStage.in_relationship,
            Gender.male,
            IN_RELATIONSHIP_SCENARIO_ORDER,
        )

    def test_female_in_relationship_twelve(self) -> None:
        self._assert_twelve_active_only(
            RelationshipStage.in_relationship,
            Gender.female,
            IN_RELATIONSHIP_SCENARIO_ORDER,
        )

    def test_pair_keys_match_across_genders(self) -> None:
        for stage in (RelationshipStage.newly_meeting, RelationshipStage.in_relationship):
            male_ids = [
                q.scenario_id
                for q in get_questions_for_participant(self.db, stage, Gender.male)
            ]
            female_ids = [
                q.scenario_id
                for q in get_questions_for_participant(self.db, stage, Gender.female)
            ]
            self.assertEqual(male_ids, female_ids)
            self.assertEqual(male_ids, active_scenario_ids_for_stage(stage))

    def test_legacy_rows_do_not_inflate_ready_count(self) -> None:
        only_legacy = (
            self.db.query(ScenarioQuestion)
            .filter(
                ScenarioQuestion.stage == RelationshipStage.newly_meeting,
                ScenarioQuestion.gender == Gender.male,
                ScenarioQuestion.scenario_id == "promise_call",
            )
            .count()
        )
        self.assertEqual(only_legacy, 1)
        active = get_questions_for_participant(
            self.db, RelationshipStage.newly_meeting, Gender.male
        )
        self.assertEqual(len(active), 12)


class QuestionsPageProgressTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = _db_session()
        _seed_all_questions(self.db)
        _seed_legacy_newly_meeting_male(self.db)

        def override_get_db():
            yield self.db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.db.close()

    def _create_session(self, gender: Gender, stage: RelationshipStage) -> tuple[str, str]:
        session = Session(relationship_stage=stage)
        self.db.add(session)
        self.db.flush()
        participant = Participant(
            session_id=session.id,
            role=ParticipantRole.user_a,
            name="Test",
            gender=gender,
        )
        self.db.add(participant)
        self.db.commit()
        return session.id, "user_a"

    def test_questions_page_shows_twelve_steps_male(self) -> None:
        session_id, role = self._create_session(
            Gender.male, RelationshipStage.newly_meeting
        )
        response = self.client.get(f"/session/{session_id}/questions?role={role}")
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertEqual(html.count('class="quiz-step'), 12)
        self.assertIn('data-question-total="12"', html)
        self.assertIn('1 / 12', html)

    def test_questions_page_female_not_male_set(self) -> None:
        session_id, role = self._create_session(
            Gender.female, RelationshipStage.in_relationship
        )
        response = self.client.get(f"/session/{session_id}/questions?role={role}")
        self.assertEqual(response.status_code, 200)
        female_q = (
            self.db.query(ScenarioQuestion)
            .filter(
                ScenarioQuestion.stage == RelationshipStage.in_relationship,
                ScenarioQuestion.gender == Gender.female,
                ScenarioQuestion.scenario_id == IN_RELATIONSHIP_SCENARIO_ORDER[0],
            )
            .one()
        )
        self.assertIn(female_q.text[:40], response.text)


if __name__ == "__main__":
    unittest.main()
