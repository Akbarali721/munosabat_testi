from typing import TypedDict


class QuestionOption(TypedDict, total=False):
    text: str
    weight: int
    code: str
    value: str


class QuestionSeed(TypedDict, total=False):
    scenario_id: str
    stage: str
    gender_target: str
    dimension: str
    text: str
    options: list[QuestionOption]
    question_code: str


def _build_options(specs: list[tuple[str, str]]) -> list[QuestionOption]:
    codes = ("A", "B", "C", "D")
    return [
        {"code": codes[i], "text": text, "value": value, "weight": 4 - i}
        for i, (text, value) in enumerate(specs)
    ]


def _options_from_specs(
    option_specs: list[tuple[str, str] | tuple[str, int]],
) -> list[QuestionOption]:
    if not option_specs:
        return []
    if isinstance(option_specs[0][1], int):
        return [
            {"text": text, "weight": int(weight)}
            for text, weight in option_specs  # type: ignore[misc]
        ]
    return _build_options(option_specs)  # type: ignore[arg-type]


def _q(
    scenario_id: str,
    gender_target: str,
    dimension: str,
    text: str,
    option_specs: list[tuple[str, str] | tuple[str, int]],
    stage: str,
    question_code: str | None = None,
) -> QuestionSeed:
    seed: QuestionSeed = {
        "scenario_id": scenario_id,
        "stage": stage,
        "gender_target": gender_target,
        "dimension": dimension,
        "text": text,
        "options": _options_from_specs(option_specs),
    }
    if question_code:
        seed["question_code"] = question_code
    return seed
