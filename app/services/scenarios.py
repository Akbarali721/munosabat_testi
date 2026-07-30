import json

from sqlalchemy.orm import Session as DbSession

from app.constants import SESSION_QUESTION_COUNT, STAGE_SCENARIO_ORDER
from app.models import Gender, RelationshipStage, ScenarioQuestion
from app.services.relationship_stage import question_bank_stage
from app.services.spouse_label import apply_spouse_labels


def active_scenario_ids_for_stage(stage: RelationshipStage) -> list[str]:
    return list(STAGE_SCENARIO_ORDER.get(stage.value, []))


def get_questions_for_participant(
    db: DbSession,
    stage: RelationshipStage,
    gender: Gender,
) -> list[ScenarioQuestion]:
    scenario_ids = active_scenario_ids_for_stage(stage)
    if not scenario_ids:
        return []

    bank_stage = question_bank_stage(stage)
    rows = (
        db.query(ScenarioQuestion)
        .filter(
            ScenarioQuestion.stage == bank_stage,
            ScenarioQuestion.gender == gender,
            ScenarioQuestion.scenario_id.in_(scenario_ids),
        )
        .all()
    )
    by_scenario_id = {row.scenario_id: row for row in rows}
    return [by_scenario_id[sid] for sid in scenario_ids if sid in by_scenario_id]


def count_active_questions_for_participant(
    db: DbSession,
    stage: RelationshipStage,
    gender: Gender,
) -> int:
    scenario_ids = active_scenario_ids_for_stage(stage)
    if not scenario_ids:
        return 0
    bank_stage = question_bank_stage(stage)
    return (
        db.query(ScenarioQuestion)
        .filter(
            ScenarioQuestion.stage == bank_stage,
            ScenarioQuestion.gender == gender,
            ScenarioQuestion.scenario_id.in_(scenario_ids),
        )
        .count()
    )


def questions_ready(
    db: DbSession,
    stage: RelationshipStage,
    gender: Gender,
) -> bool:
    expected = active_scenario_ids_for_stage(stage)
    if len(expected) < SESSION_QUESTION_COUNT:
        return False
    return count_active_questions_for_participant(db, stage, gender) >= SESSION_QUESTION_COUNT


def _decode_options_json(options_json: str) -> tuple[list[dict], str | None]:
    raw = json.loads(options_json)
    if isinstance(raw, dict) and isinstance(raw.get("options"), list):
        code = raw.get("question_code")
        return raw["options"], str(code) if code else None
    if isinstance(raw, list):
        return raw, None
    return [], None


def question_code_for_row(question: ScenarioQuestion) -> str | None:
    _, code = _decode_options_json(question.options_json)
    return code


def question_codes_for_questions(questions: list[ScenarioQuestion]) -> list[str]:
    codes: list[str] = []
    for q in questions:
        code = question_code_for_row(q)
        if code:
            codes.append(code)
        else:
            codes.append(q.scenario_id)
    return codes


def parse_options(question: ScenarioQuestion, gender: Gender | None = None) -> list[dict]:
    options, _ = _decode_options_json(question.options_json)
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
    options, _ = _decode_options_json(question.options_json)
    if 0 <= choice_index < len(options):
        raw = options[choice_index].get("weight")
        if raw is not None:
            return int(raw)
        return 4 - choice_index
    return 0


def get_option_value(question: ScenarioQuestion, choice_index: int) -> str | None:
    options, _ = _decode_options_json(question.options_json)
    if 0 <= choice_index < len(options):
        value = options[choice_index].get("value")
        if value:
            return str(value)
    return None

