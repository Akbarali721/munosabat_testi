from app.constants import STAGE_SCENARIO_ORDER
from app.question_seeds._helpers import QuestionOption, QuestionSeed
from app.question_seeds.in_relationship import IN_RELATIONSHIP_QUESTIONS
from app.question_seeds.married import MARRIED_QUESTIONS
from app.question_seeds.newly_meeting import NEWLY_MEETING_QUESTIONS

ALL_QUESTIONS: list[QuestionSeed] = (
    NEWLY_MEETING_QUESTIONS
    + IN_RELATIONSHIP_QUESTIONS
    + MARRIED_QUESTIONS
)

__all__ = [
    "ALL_QUESTIONS",
    "IN_RELATIONSHIP_QUESTIONS",
    "MARRIED_QUESTIONS",
    "NEWLY_MEETING_QUESTIONS",
    "QuestionOption",
    "QuestionSeed",
    "ordered_questions_for_gender",
]


def ordered_questions_for_gender(
    gender_target: str,
    stage: str = "newly_meeting",
) -> list[QuestionSeed]:
    order = STAGE_SCENARIO_ORDER.get(stage, [])
    by_key = {
        (q["scenario_id"], q["gender_target"]): q
        for q in ALL_QUESTIONS
        if q["stage"] == stage and q["gender_target"] == gender_target
    }
    return [by_key[(sid, gender_target)] for sid in order if (sid, gender_target) in by_key]
