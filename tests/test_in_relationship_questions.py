"""Seed va tartib tekshiruvlari — Yangi turmush qurganlar."""

from __future__ import annotations

import unittest

from app.constants import IN_RELATIONSHIP_SCENARIO_ORDER
from app.question_seeds import IN_RELATIONSHIP_QUESTIONS, ordered_questions_for_gender
from app.services.pair_narrative import pair_comparison_line


class InRelationshipQuestionsTests(unittest.TestCase):
    def test_twelve_pairs_two_genders(self) -> None:
        male = [q for q in IN_RELATIONSHIP_QUESTIONS if q["gender_target"] == "male"]
        female = [q for q in IN_RELATIONSHIP_QUESTIONS if q["gender_target"] == "female"]
        self.assertEqual(len(male), 12)
        self.assertEqual(len(female), 12)

    def test_order_matches_constants(self) -> None:
        for gender in ("male", "female"):
            ordered = ordered_questions_for_gender(gender, stage="in_relationship")
            ids = [q["scenario_id"] for q in ordered]
            self.assertEqual(ids, IN_RELATIONSHIP_SCENARIO_ORDER)

    def test_four_options_and_pair_keys_align(self) -> None:
        by_id: dict[str, dict[str, dict]] = {}
        for q in IN_RELATIONSHIP_QUESTIONS:
            by_id.setdefault(q["scenario_id"], {})[q["gender_target"]] = q
        for scenario_id, genders in by_id.items():
            self.assertIn("male", genders)
            self.assertIn("female", genders)
            for g in ("male", "female"):
                self.assertEqual(len(genders[g]["options"]), 4)

    def test_male_question_codes(self) -> None:
        male = ordered_questions_for_gender("male", stage="in_relationship")
        codes = [q.get("question_code") for q in male]
        expected = [f"newlywed_male_{i:02d}" for i in range(1, 13)]
        self.assertEqual(codes, expected)

    def test_male_q1_exact_text(self) -> None:
        male = ordered_questions_for_gender("male", stage="in_relationship")
        self.assertIn("Ishdan charchab uyga kelganingizda", male[0]["text"])

    def test_pair_narrative_same_pair_key(self) -> None:
        line = pair_comparison_line(
            "in_relationship",
            "newlywed_04",
            "ask_calmly",
            "set_rule_together",
            "Ali",
            "Zuhra",
        )
        self.assertIn("Ali", line)
        self.assertIn("Zuhra", line)


if __name__ == "__main__":
    unittest.main()
