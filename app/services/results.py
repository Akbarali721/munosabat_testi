from dataclasses import dataclass

from sqlalchemy.orm import Session as DbSession

from app.constants import DIMENSION_LABELS, RESULT_DIMENSION_GROUPS
from app.copy.result_free import warmth_summary
from app.models import Participant, ParticipantRole, ScenarioQuestion, Session
from app.services.scenarios import get_option_text, question_text_for_display


@dataclass
class ScenarioComparison:
    scenario_id: str
    title: str
    dimension: str
    user_a_weight: int
    user_b_weight: int
    user_a_label: str
    user_b_label: str
    difference: int
    user_a_prompt: str
    user_b_prompt: str


@dataclass
class DimensionScore:
    key: str
    label: str
    stars: int


@dataclass
class SessionResult:
    compatibility_score: int
    compatibility_summary: str
    strongest_areas: list[ScenarioComparison]
    misunderstanding_areas: list[ScenarioComparison]
    comparisons: list[ScenarioComparison]
    suggestions: list[str]
    dimension_scores: list[DimensionScore]
    talk_topics: list[str]
    user_a: Participant
    user_b: Participant


def _dimension_label(dimension: str) -> str:
    return DIMENSION_LABELS.get(dimension, dimension.replace("_", " ").title())


def _stars_from_avg_diff(avg_diff: float) -> int:
    if avg_diff <= 0.5:
        return 5
    if avg_diff <= 1.0:
        return 4
    if avg_diff <= 1.8:
        return 3
    if avg_diff <= 2.5:
        return 2
    return 1


def _build_dimension_scores(comparisons: list[ScenarioComparison]) -> list[DimensionScore]:
    scores: list[DimensionScore] = []
    for key, group in RESULT_DIMENSION_GROUPS.items():
        group_comps = [c for c in comparisons if c.dimension in group["dimensions"]]
        if not group_comps:
            scores.append(DimensionScore(key=key, label=group["label"], stars=3))
            continue
        avg_diff = sum(c.difference for c in group_comps) / len(group_comps)
        scores.append(
            DimensionScore(
                key=key,
                label=group["label"],
                stars=_stars_from_avg_diff(avg_diff),
            )
        )
    return scores


def _suggestion_for_gap(
    comparison: ScenarioComparison,
    name_a: str,
    name_b: str,
) -> str:
    if comparison.difference <= 1:
        return ""

    if comparison.user_a_weight > comparison.user_b_weight:
        higher, lower = name_a, name_b
    else:
        higher, lower = name_b, name_a

    return (
        f"«{comparison.title}» bo‘yicha {higher} va {lower} turlicha qaror qilgan. "
        f"Bu haqda tinch suhbat qilib, nima uchun shunday his qilganingizni ayting."
    )


def build_session_result(db: DbSession, session: Session) -> SessionResult | None:
    participants = {p.role: p for p in session.participants}
    user_a = participants.get(ParticipantRole.user_a)
    user_b = participants.get(ParticipantRole.user_b)
    if not user_a or not user_b:
        return None

    answers_a = {a.scenario_id: a for a in user_a.answers}
    answers_b = {a.scenario_id: a for a in user_b.answers}

    if not answers_a or not answers_b:
        return None

    comparisons: list[ScenarioComparison] = []
    for scenario_id in sorted(answers_a.keys(), key=lambda sid: sid):
        if scenario_id not in answers_b:
            continue

        a_answer = answers_a[scenario_id]
        b_answer = answers_b[scenario_id]
        weight_a = a_answer.choice_weight
        weight_b = b_answer.choice_weight
        diff = abs(weight_a - weight_b)

        a_question = (
            db.query(ScenarioQuestion)
            .filter(
                ScenarioQuestion.scenario_id == scenario_id,
                ScenarioQuestion.gender == user_a.gender,
                ScenarioQuestion.stage == session.relationship_stage,
            )
            .first()
        )
        b_question = (
            db.query(ScenarioQuestion)
            .filter(
                ScenarioQuestion.scenario_id == scenario_id,
                ScenarioQuestion.gender == user_b.gender,
                ScenarioQuestion.stage == session.relationship_stage,
            )
            .first()
        )

        dimension = a_question.dimension if a_question else ""
        comparisons.append(
            ScenarioComparison(
                scenario_id=scenario_id,
                title=_dimension_label(dimension),
                dimension=dimension,
                user_a_weight=weight_a,
                user_b_weight=weight_b,
                user_a_label=get_option_text(
                    a_question, a_answer.choice_index, gender=user_a.gender
                )
                if a_question
                else "",
                user_b_label=get_option_text(
                    b_question, b_answer.choice_index, gender=user_b.gender
                )
                if b_question
                else "",
                difference=diff,
                user_a_prompt=question_text_for_display(a_question, user_a.gender)
                if a_question
                else "",
                user_b_prompt=question_text_for_display(b_question, user_b.gender)
                if b_question
                else "",
            )
        )

    if not comparisons:
        return None

    max_diff = 3
    avg_diff = sum(c.difference for c in comparisons) / len(comparisons)
    compatibility_score = max(0, min(100, round(100 - (avg_diff / max_diff * 100))))
    summary = warmth_summary(compatibility_score)

    by_alignment = sorted(comparisons, key=lambda c: c.difference)
    strongest = by_alignment[:3]
    misunderstandings = sorted(comparisons, key=lambda c: c.difference, reverse=True)[:3]

    suggestions = [
        s
        for c in misunderstandings
        if (s := _suggestion_for_gap(c, user_a.name, user_b.name))
    ]

    if not suggestions:
        suggestions = [
            "Xotirjam vaqt ajratib, hozir munosabatda sizga nima muhimligini bir-biringiz bilan ulashing.",
            "Yaxshi mos kelgan bitta vaziyatni tanlang va qiyin mavzularni shu usulda muhokama qiling.",
        ]

    talk_topics = [c.title for c in misunderstandings[:3]]
    dimension_scores = _build_dimension_scores(comparisons)

    return SessionResult(
        compatibility_score=compatibility_score,
        compatibility_summary=summary,
        strongest_areas=strongest,
        misunderstanding_areas=misunderstandings,
        comparisons=comparisons,
        suggestions=suggestions[:5],
        dimension_scores=dimension_scores,
        talk_topics=talk_topics,
        user_a=user_a,
        user_b=user_b,
    )
