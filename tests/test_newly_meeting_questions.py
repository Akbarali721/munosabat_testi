"""Seed va tartib tekshiruvlari — Endi tanishayotganlar."""

from __future__ import annotations

import json
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.constants import SCENARIO_ORDER
from app.database import Base
from app.models import Gender, RelationshipStage, ScenarioQuestion
from app.question_seeds import NEWLY_MEETING_QUESTIONS, ordered_questions_for_gender
from app.question_seeds._helpers import QuestionSeed
from app.services import seed_scenarios


def _option_values(seed: QuestionSeed) -> list[str]:
    return [opt["value"] for opt in seed["options"] if "value" in opt]


class NewlyMeetingQuestionsTests(unittest.TestCase):
    def test_twelve_pairs_two_genders(self) -> None:
        male = [q for q in NEWLY_MEETING_QUESTIONS if q["gender_target"] == "male"]
        female = [q for q in NEWLY_MEETING_QUESTIONS if q["gender_target"] == "female"]
        self.assertEqual(len(male), 12)
        self.assertEqual(len(female), 12)

    def test_order_matches_constants(self) -> None:
        for gender in ("male", "female"):
            ordered = ordered_questions_for_gender(gender, stage="newly_meeting")
            ids = [q["scenario_id"] for q in ordered]
            self.assertEqual(ids, SCENARIO_ORDER)

    def test_shared_value_slugs_per_pair(self) -> None:
        by_id: dict[str, dict[str, QuestionSeed]] = {}
        for q in NEWLY_MEETING_QUESTIONS:
            by_id.setdefault(q["scenario_id"], {})[q["gender_target"]] = q
        for scenario_id, genders in by_id.items():
            self.assertEqual(_option_values(genders["male"]), _option_values(genders["female"]), scenario_id)

    def test_seed_idempotent_and_options_have_codes(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()
        seed_scenarios(db)
        count = (
            db.query(ScenarioQuestion)
            .filter(ScenarioQuestion.stage == RelationshipStage.newly_meeting)
            .count()
        )
        self.assertEqual(count, 24)
        row = (
            db.query(ScenarioQuestion)
            .filter(
                ScenarioQuestion.stage == RelationshipStage.newly_meeting,
                ScenarioQuestion.gender == Gender.male,
                ScenarioQuestion.scenario_id == "emotional_support",
            )
            .one()
        )
        options = json.loads(row.options_json)
        self.assertEqual([o["code"] for o in options], ["A", "B", "C", "D"])
        self.assertEqual(options[0]["value"], "listening")
        seed_scenarios(db)
        self.assertEqual(
            db.query(ScenarioQuestion)
            .filter(ScenarioQuestion.stage == RelationshipStage.newly_meeting)
            .count(),
            24,
        )
        db.close()


if __name__ == "__main__":
    unittest.main()
