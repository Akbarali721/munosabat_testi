from dataclasses import dataclass

from app.constants import (
    PREMIUM_MAP_DIMENSIONS,
    SCENARIO_DISPLAY_TITLES,
    SEVEN_DAY_EXERCISES,
)
from app.copy.premium_experience import (
    CHALLENGE_INTRO,
    HIDDEN_STRENGTH_ALIGNED,
    HIDDEN_STRENGTH_GAP,
    INSIGHT_GROWTH,
    INSIGHT_HIGH,
    OPENING_TEMPLATE,
    SHARE_ROMANTIC,
)
from app.copy.traits import (
    DEFAULT_TRAITS,
    DIMENSION_TRAITS,
    WEEKLY_ACTIONS_BY_DIMENSION,
)
from app.services.results import ScenarioComparison, SessionResult


@dataclass
class MapItem:
    key: str
    label: str
    percent: int
    note: str
    warmth: str


@dataclass
class DailyExercise:
    day: int
    title: str
    text: str


@dataclass
class PartnerInsight:
    emoji: str
    heading: str
    traits: list[str]


@dataclass
class PremiumResultCopy:
    headline: str
    subtitle: str
    opening_message: str
    profile_summary: str
    map_intro: str
    map_items: list[MapItem]
    partner_insights: list[PartnerInsight]
    hidden_strength: str
    relationship_insight: str
    strengths: list[str]
    strengths_intro: str
    suggestions: list[str]
    suggestions_intro: str
    challenge_intro: str
    daily_exercises: list[DailyExercise]
    share_message: str
    share_heading: str


def _warmth_note(percent: int) -> str:
    if percent >= 85:
        return "Bu sizlarning tabiiy kuchli tomoningiz"
    if percent >= 75:
        return "Yaqin va ishonchli yo‘nalish"
    if percent >= 65:
        return "Yana yaqinlashish uchun chiroyli imkoniyat"
    return "Kichik suhbatlar bilan yanada mustahkamlash mumkin"


def _dimension_note(percent: int) -> str:
    if percent >= 85:
        return "Juda yaxshi"
    if percent >= 75:
        return "Yaxshi"
    if percent >= 65:
        return "Yaqin"
    return "Suhbat foydali"


def _percent_from_comparisons(comparisons: list[ScenarioComparison]) -> int:
    if not comparisons:
        return 72
    avg_diff = sum(c.difference for c in comparisons) / len(comparisons)
    return max(0, min(100, round(100 - (avg_diff / 3 * 100))))


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
    for trait in DEFAULT_TRAITS:
        if trait not in seen:
            traits.append(trait)
        if len(traits) >= count:
            break
    return traits[:count]


def _build_map_items(comparisons: list[ScenarioComparison]) -> list[MapItem]:
    items: list[MapItem] = []
    for key, meta in PREMIUM_MAP_DIMENSIONS.items():
        dims = meta["dimensions"]
        group = [c for c in comparisons if c.dimension in dims]
        percent = _percent_from_comparisons(group)
        items.append(
            MapItem(
                key=key,
                label=str(meta["label"]),
                percent=percent,
                note=_dimension_note(percent),
                warmth=_warmth_note(percent),
            )
        )
    return items


def _collect_strengths(comparisons: list[ScenarioComparison], count: int = 5) -> list[str]:
    return _traits_from_comparisons(
        sorted(comparisons, key=lambda c: c.difference),
        count=count,
    )


def _collect_suggestions(comparisons: list[ScenarioComparison], count: int = 5) -> list[str]:
    gaps = sorted(comparisons, key=lambda c: c.difference, reverse=True)
    suggestions: list[str] = []
    seen: set[str] = set()

    for comp in gaps:
        action = WEEKLY_ACTIONS_BY_DIMENSION.get(comp.dimension)
        if action and action not in seen:
            suggestions.append(action)
            seen.add(action)
        if len(suggestions) >= count:
            return suggestions

    fallback = [
        "Har kuni bitta minnatdorchilik gapiring",
        "Mojarodan keyin 24 soat ichida tinch gapiring",
        "Haftalik 20 daqiqalik «faqat biz» vaqti belgilang",
        "Kelajak rejalarini yozib qo‘ying — 3 ta orzu yetarli",
        "Kichik surprizlar orqali yaqinlikni mustahkamlang",
    ]
    for item in fallback:
        if item not in seen:
            suggestions.append(item)
        if len(suggestions) >= count:
            break
    return suggestions[:count]


def _hidden_strength(comparisons: list[ScenarioComparison]) -> str:
    if not comparisons:
        return HIDDEN_STRENGTH_ALIGNED
    avg_diff = sum(c.difference for c in comparisons) / len(comparisons)
    if avg_diff <= 1.2:
        return HIDDEN_STRENGTH_ALIGNED
    return HIDDEN_STRENGTH_GAP


def _relationship_insight(map_items: list[MapItem]) -> str:
    if not map_items:
        return INSIGHT_HIGH.format(dimension="Muloqot")
    best = max(map_items, key=lambda m: m.percent)
    weakest = min(map_items, key=lambda m: m.percent)
    if best.percent >= 75:
        return INSIGHT_HIGH.format(dimension=best.label.lower())
    return INSIGHT_GROWTH.format(dimension=weakest.label.lower())


def _profile_summary(
    name_a: str,
    name_b: str,
    score: int,
    map_items: list[MapItem],
) -> str:
    top = sorted(map_items, key=lambda m: m.percent, reverse=True)[:2]
    labels = " va ".join(m.label.lower() for m in top)
    return (
        f"Siz bir-biringizni {score}% darajada tushunasiz. "
        f"Ayniqsa {labels} yo‘nalishlarida yaqinsiz — "
        f"bu sizlarning «ishonchli qayig‘ingiz» poydevori."
    )


def build_premium_result_copy(result: SessionResult) -> PremiumResultCopy:
    name_a = result.user_a.name
    name_b = result.user_b.name
    names = f"{name_a} va {name_b}"
    map_items = _build_map_items(result.comparisons)
    aligned = sorted(result.comparisons, key=lambda c: c.difference)

    return PremiumResultCopy(
        headline="Sizlarning chuqur juftlik profili",
        subtitle=names,
        opening_message=OPENING_TEMPLATE.format(names=names),
        profile_summary=_profile_summary(
            name_a, name_b, result.compatibility_score, map_items
        ),
        map_intro="Har bir yo‘nalish — sizlarni yanada yaqinlashtirishi mumkin bo‘lgan mavzu.",
        map_items=map_items,
        partner_insights=[
            PartnerInsight(
                emoji="✨",
                heading=f"{name_b} {name_a}da eng ko‘p qadrlaydigan fazilatlar",
                traits=_traits_from_comparisons(aligned, 3),
            ),
            PartnerInsight(
                emoji="💝",
                heading=f"{name_a} {name_b}da eng ko‘p qadrlaydigan fazilatlar",
                traits=_traits_from_comparisons(list(reversed(aligned)), 3),
            ),
        ],
        hidden_strength=_hidden_strength(result.comparisons),
        relationship_insight=_relationship_insight(map_items),
        strengths_intro="Sizlarni boshqa juftliklardan ajratib turadigan 5 ta kuch.",
        strengths=_collect_strengths(result.comparisons),
        suggestions_intro="Kichik qadamlar — katta yaqinlik. Bularni shoshilmasdan sinab ko‘ring.",
        suggestions=_collect_suggestions(result.comparisons),
        challenge_intro=CHALLENGE_INTRO,
        daily_exercises=[
            DailyExercise(day=index, title=title, text=text)
            for index, (title, text) in enumerate(SEVEN_DAY_EXERCISES, start=1)
        ],
        share_heading="Sherigingizga yuborish uchun romantik xabar",
        share_message=SHARE_ROMANTIC.format(
            name_b=name_b,
            score=result.compatibility_score,
        ),
    )
