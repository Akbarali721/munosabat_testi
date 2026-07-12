import json

from sqlalchemy import inspect
from sqlalchemy.orm import Session as DbSession

from app.database import engine
from app.models import Answer, Gender, RelationshipStage, ScenarioQuestion
from app.question_seeds import ALL_QUESTIONS

QUESTION_SCHEMA_VERSION = 3


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


def seed_scenarios(db: DbSession) -> None:
    reset_question_schema()

    for item in ALL_QUESTIONS:
        stage = RelationshipStage(item["stage"])
        gender = Gender(item["gender_target"])
        options_json = json.dumps(item["options"], ensure_ascii=False)

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

    db.commit()
