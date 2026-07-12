import json

from sqlalchemy.orm import Session as DbSession

from app.constants import SESSION_QUESTION_COUNT, STAGE_SCENARIO_ORDER
from app.models import Gender, RelationshipStage, ScenarioQuestion
from app.services.spouse_label import apply_spouse_labels


def parse_options(question: ScenarioQuestion, gender: Gender | None = None) -> list[dict]:
    options = json.loads(question.options_json)
    if gender is not None and (
        question.stage == RelationshipStage.married
        or any("{spouse" in option.get("text", "") for option in options)
    ):
        return [
            {**option, "text": apply_spouse_labels(option["text"], gender)}
            for option in options
        ]
    return options


def question_text_for_display(question: ScenarioQuestion, gender: Gender) -> str:
    text = question.text
    if question.stage == RelationshipStage.married or "{spouse" in text:
        return apply_spouse_labels(text, gender)
    return text


def get_option_text(
    question: ScenarioQuestion,
    choice_index: int,
    gender: Gender | None = None,
) -> str:
    options = parse_options(question, gender=gender)
    if 0 <= choice_index < len(options):
        return options[choice_index]["text"]
    return ""


def get_option_weight(question: ScenarioQuestion, choice_index: int) -> int:
    options = json.loads(question.options_json)
    if 0 <= choice_index < len(options):
        return int(options[choice_index]["weight"])
    return 0


def get_questions_for_participant(
    db: DbSession,
    stage: RelationshipStage,
    gender: Gender,
) -> list[ScenarioQuestion]:
    questions = (
        db.query(ScenarioQuestion)
        .filter(
            ScenarioQuestion.stage == stage,
            ScenarioQuestion.gender == gender,
        )
        .all()
    )
    order_map = {
        sid: idx
        for idx, sid in enumerate(STAGE_SCENARIO_ORDER.get(stage.value, []))
    }
    questions.sort(key=lambda q: order_map.get(q.scenario_id, 999))
    return questions


def questions_ready(
    db: DbSession,
    stage: RelationshipStage,
    gender: Gender,
) -> bool:
    count = (
        db.query(ScenarioQuestion)
        .filter(
            ScenarioQuestion.stage == stage,
            ScenarioQuestion.gender == gender,
        )
        .count()
    )
    return count >= SESSION_QUESTION_COUNT
