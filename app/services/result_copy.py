from dataclasses import dataclass

from app.constants import SCENARIO_DISPLAY_TITLES
from app.copy.result_free import warmth_summary
from app.copy.traits import (
    DEFAULT_TRAITS,
    DEFAULT_WEEKLY_ACTIONS,
    DIMENSION_TRAITS,
    SOFT_GROWTH_DEFAULT,
    SOFT_GROWTH_TEMPLATE,
    STRENGTH_TEMPLATES,
    WEEKLY_ACTIONS_BY_DIMENSION,
)
from app.services.results import ScenarioComparison, SessionResult


@dataclass
class FreeResultCopy:
    score_label: str
    warm_summary: str
    traits_for_a: list[str]
    traits_for_b: list[str]
    traits_heading_a: str
    traits_heading_b: str
    strength_line: str
    soft_growth: str
    weekly_actions: list[str]


def _traits_from_comparisons(
    comparisons: list[ScenarioComparison],
    count: int = 3,
) -> list[str]:
    traits: list[str] = []
    seen: set[str] = set()
    for comp in comparisons:
        for trait in DIMENSION_TRAITS.get(comp.dimension, DEFAULT_TRAITS):
            if trait not in seen:
                traits.append(trait)
                seen.add(trait)
            if len(traits) >= count:
                return traits
    while len(traits) < count:
        for trait in DEFAULT_TRAITS:
            if trait not in seen:
                traits.append(trait)
                seen.add(trait)
            if len(traits) >= count:
                break
    return traits[:count]


def _strength_line(strongest: list[ScenarioComparison]) -> str:
    if not strongest:
        return STRENGTH_TEMPLATES[2]
    labels = [
        SCENARIO_DISPLAY_TITLES.get(c.scenario_id, c.title)
        for c in strongest[:2]
    ]
    if len(labels) == 1:
        areas = labels[0]
    else:
        areas = f"{labels[0]} va {labels[1]}"
    return STRENGTH_TEMPLATES[1].format(areas=areas)


def _soft_growth_line(gaps: list[ScenarioComparison]) -> str:
    meaningful = [c for c in gaps if c.difference > 1]
    if not meaningful:
        return SOFT_GROWTH_DEFAULT
    labels = [
        SCENARIO_DISPLAY_TITLES.get(c.scenario_id, c.title)
        for c in meaningful[:2]
    ]
    areas = labels[0] if len(labels) == 1 else f"{labels[0]} va {labels[1]}"
    return SOFT_GROWTH_TEMPLATE.format(areas=areas)


def _weekly_actions(gaps: list[ScenarioComparison], fallback: list[str]) -> list[str]:
    actions: list[str] = []
    seen: set[str] = set()
    for comp in sorted(gaps, key=lambda c: c.difference, reverse=True):
        action = WEEKLY_ACTIONS_BY_DIMENSION.get(comp.dimension)
        if action and action not in seen:
            actions.append(action)
            seen.add(action)
        if len(actions) >= 3:
            return actions
    for action in fallback:
        if action not in seen:
            actions.append(action)
            seen.add(action)
        if len(actions) >= 3:
            break
    for action in DEFAULT_WEEKLY_ACTIONS:
        if action not in seen:
            actions.append(action)
        if len(actions) >= 3:
            break
    return actions[:3]


def build_free_result_copy(result: SessionResult) -> FreeResultCopy:
    name_a = result.user_a.name
    name_b = result.user_b.name
    aligned = sorted(result.comparisons, key=lambda c: c.difference)
    gaps = sorted(result.comparisons, key=lambda c: c.difference, reverse=True)

    return FreeResultCopy(
        score_label="Bir-biringizni tushunish darajasi",
        warm_summary=warmth_summary(result.compatibility_score),
        traits_heading_a=f"{name_b} sizda qadrlaydigan fazilatlar",
        traits_heading_b=f"{name_a} sizda qadrlaydigan fazilatlar",
        traits_for_a=_traits_from_comparisons(aligned),
        traits_for_b=_traits_from_comparisons(list(reversed(aligned))),
        strength_line=_strength_line(result.strongest_areas),
        soft_growth=_soft_growth_line(gaps),
        weekly_actions=_weekly_actions(gaps, result.suggestions),
    )
