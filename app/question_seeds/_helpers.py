from typing import TypedDict


class QuestionOption(TypedDict):
    text: str
    weight: int


class QuestionSeed(TypedDict):
    scenario_id: str
    stage: str
    gender_target: str
    dimension: str
    text: str
    options: list[QuestionOption]


def _q(
    scenario_id: str,
    gender_target: str,
    dimension: str,
    text: str,
    options: list[tuple[str, int]],
    stage: str,
) -> QuestionSeed:
    return {
        "scenario_id": scenario_id,
        "stage": stage,
        "gender_target": gender_target,
        "dimension": dimension,
        "text": text,
        "options": [{"text": t, "weight": w} for t, w in options],
    }
