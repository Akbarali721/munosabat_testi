import json

from sqlalchemy import inspect
from sqlalchemy.orm import Session as DbSession

from app.database import engine
from app.models import Answer, Gender, RelationshipStage, ScenarioQuestion
from app.question_seeds import ALL_QUESTIONS

QUESTION_SCHEMA_VERSION = 5


def _needs_schema_reset() -> bool:
    inspector = inspect(engine)
    if "scenario_questions" not in inspector.get_table_names():
        return False
    columns = {col["name"] for col in inspector.get_columns("scenario_questions")}
    return "dimension" not in columns or "options_json" not in columns


def reset_question_schema() -> None:
    if not _needs_schema_reset():
        return
    Answer.__table__.drop(engine, checkfirst=True)
    ScenarioQuestion.__table__.drop(engine, checkfirst=True)
    ScenarioQuestion.__table__.create(engine, checkfirst=True)
    Answer.__table__.create(engine, checkfirst=True)


def _active_scenario_ids_by_stage() -> dict[str, set[str]]:
    by_stage: dict[str, set[str]] = {}
    for item in ALL_QUESTIONS:
        by_stage.setdefault(item["stage"], set()).add(item["scenario_id"])
    return by_stage


def purge_orphan_questions(
    db: DbSession,
    stage: RelationshipStage,
    active_scenario_ids: set[str],
) -> None:
    if not active_scenario_ids:
        return
    candidates = (
        db.query(ScenarioQuestion)
        .filter(
            ScenarioQuestion.stage == stage,
            ScenarioQuestion.scenario_id.notin_(active_scenario_ids),
        )
        .all()
    )
    for question in candidates:
        linked = (
            db.query(Answer.id)
            .filter(Answer.scenario_question_id == question.id)
            .first()
        )
        if linked:
            continue
        db.delete(question)


def seed_scenarios(db: DbSession) -> None:
    reset_question_schema()

    for item in ALL_QUESTIONS:
        stage = RelationshipStage(item["stage"])
        gender = Gender(item["gender_target"])
        options_payload: dict | list = item["options"]
        if item.get("question_code"):
            options_payload = {
                "question_code": item["question_code"],
                "options": item["options"],
            }
        options_json = json.dumps(options_payload, ensure_ascii=False)

        existing = (
            db.query(ScenarioQuestion)
            .filter(
                ScenarioQuestion.scenario_id == item["scenario_id"],
                ScenarioQuestion.stage == stage,
                ScenarioQuestion.gender == gender,
            )
            .first()
        )
        if existing:
            existing.dimension = item["dimension"]
            existing.text = item["text"]
            existing.options_json = options_json
        else:
            db.add(
                ScenarioQuestion(
                    scenario_id=item["scenario_id"],
                    stage=stage,
                    gender=gender,
                    dimension=item["dimension"],
                    text=item["text"],
                    options_json=options_json,
                )
            )

    active_by_stage = _active_scenario_ids_by_stage()
    for stage_value, scenario_ids in active_by_stage.items():
        if stage_value in (
            RelationshipStage.newly_meeting.value,
            RelationshipStage.in_relationship.value,
        ):
            purge_orphan_questions(db, RelationshipStage(stage_value), scenario_ids)

    db.commit()
