from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.constants import SCENARIO_DISPLAY_TITLES, SEVEN_DAY_EXERCISES
from app.copy.result_experience import (
    COMM_DIFFERENT,
    COMM_HIGH,
    COMM_LOW,
    COMM_MID,
    COMM_SIMILAR,
    DIFF_BY_DIMENSION,
    DIFF_DEFAULT,
    DIFF_HIGH_SCORE,
    DIFF_SMALL,
    PERSONAL_COMBOS,
    PERSONAL_PRIMARY,
    PERSONAL_SECONDARY,
    PREMIUM_BLOCK_TITLES,
    PREMIUM_GAP_TEMPLATES,
    PREMIUM_LEAD,
    PREMIUM_STRENGTH_TEMPLATES,
    PREMIUM_SUBLEAD,
    PREMIUM_TEASER_LINES,
    STRENGTH_BY_DIMENSION,
    STRENGTH_DEFAULT,
    STRENGTH_HIGH_ALIGN,
    STRENGTH_LOW,
    STRENGTH_MID,
    TIP_BY_DIMENSION,
    TIP_DEFAULT,
)
from app.copy.result_free import warmth_summary
from app.models import Participant, ParticipantRole
from app.services.results import ScenarioComparison, SessionResult

COMM_DIMENSIONS = {
    "communication_initiative",
    "conflict_style",
    "respect_listening",
    "attention",
}

# Lightweight category mapping for narrative analysis (does not change score math)
CATEGORY_DIMENSION_MAP: dict[str, set[str]] = {
    "hamkorlik": {"responsibility", "priority_time", "family_values"},
    "muloqot": {
        "communication_initiative",
        "conflict_style",
        "respect_listening",
    },
    "ishonch": {"responsibility_trust", "trust_privacy"},
    "hissiy_yaqinlik": {"attention", "respect_attention"},
    "masuliyat": {"responsibility", "responsibility_trust"},
    "murosa": {"conflict_style", "family_values"},
    "kelajak": {"future_vision"},
    "kundalik_etibor": {"attention", "priority_time", "respect_attention"},
    "pul": {"money_values"},
}

# Map answer dimensions → inferred personal styles (high vs low weight)
STYLE_HIGH_MAP = {
    "respect_listening": "listening",
    "conflict_style": "compromise",
    "responsibility": "responsibility",
    "responsibility_trust": "responsibility",
    "communication_initiative": "open_comm",
    "attention": "intimacy",
    "respect_attention": "intimacy",
    "money_values": "practical",
    "future_vision": "practical",
    "priority_time": "intimacy",
}

STYLE_LOW_MAP = {
    "conflict_style": "withdrawal",
    "communication_initiative": "delay",
    "attention": "withdrawal",
    "money_values": "control",
    "family_values": "control",
    "respect_listening": "self_justify",
    "future_vision": "delay",
}


@dataclass
class ResultBlock:
    emoji: str
    title: str
    body: str
    items: list[str] | None = None


@dataclass
class PremiumBlock:
    key: str
    title: str
    body: str | None
    items: list[str] | None
    locked: bool
    teaser: str


@dataclass
class ResultExperience:
    partner_names: str
    stage_label: str
    score: int
    intro_summary: str
    free_blocks: list[ResultBlock]
    personal_title: str
    personal_body: str
    premium_headline: str
    premium_lead: str
    premium_sublead: str
    premium_blocks: list[PremiumBlock]
    premium_unlocked: bool
    viewer_role: str
    viewer_name: str


def _area_label(comp: ScenarioComparison) -> str:
    return SCENARIO_DISPLAY_TITLES.get(comp.scenario_id, comp.title)


def _score_band(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 55:
        return "mid"
    return "low"


def _pick_variant(variants: dict[str, str], *keys: str) -> str:
    for key in keys:
        if key in variants:
            return variants[key]
    return variants.get("default", "")


def _avg_weight_for_viewer(
    comparisons: list[ScenarioComparison],
    role: ParticipantRole,
) -> dict[str, float]:
    buckets: dict[str, list[int]] = defaultdict(list)
    for comp in comparisons:
        weight = comp.user_a_weight if role == ParticipantRole.user_a else comp.user_b_weight
        buckets[comp.dimension].append(weight)
    return {
        dim: sum(values) / len(values)
        for dim, values in buckets.items()
        if values
    }


def _infer_styles(avg_weights: dict[str, float]) -> list[str]:
    scores: dict[str, float] = defaultdict(float)
    for dim, avg in avg_weights.items():
        if avg >= 3.2:
            style = STYLE_HIGH_MAP.get(dim)
            if style:
                scores[style] += avg
        elif avg <= 2.2:
            style = STYLE_LOW_MAP.get(dim)
            if style:
                scores[style] += (3.0 - avg)

    if not scores:
        return ["open_comm", "listening"]

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [key for key, _ in ranked[:2]]


def _personal_sentence(name: str, styles: list[str]) -> str:
    primary = styles[0] if styles else "open_comm"
    secondary = styles[1] if len(styles) > 1 else None

    if secondary:
        combo = PERSONAL_COMBOS.get((primary, secondary))
        if combo:
            return combo.format(name=name)

    primary_text = PERSONAL_PRIMARY.get(primary, PERSONAL_PRIMARY["open_comm"]).format(
        name=name
    )
    if secondary and secondary != primary:
        secondary_text = PERSONAL_SECONDARY.get(secondary, "")
        if secondary_text:
            return f"{primary_text} {secondary_text}"
    return primary_text


def _communication_block(comparisons: list[ScenarioComparison], score: int) -> str:
    comm = [c for c in comparisons if c.dimension in COMM_DIMENSIONS]
    if not comm:
        return COMM_MID
    avg_diff = sum(c.difference for c in comm) / len(comm)
    band = _score_band(score)

    if avg_diff <= 0.7:
        if band == "high":
            return COMM_HIGH
        return COMM_SIMILAR
    if avg_diff <= 1.6:
        return COMM_MID
    if band == "low":
        return COMM_LOW
    return COMM_DIFFERENT


def _strength_block(result: SessionResult) -> str:
    strongest = result.strongest_areas
    if not strongest:
        return STRENGTH_DEFAULT

    top = strongest[0]
    area = _area_label(top)
    band = _score_band(result.compatibility_score)
    similar = top.difference <= 1
    variants = STRENGTH_BY_DIMENSION.get(top.dimension, {})

    if top.difference == 0 and result.compatibility_score >= 75:
        return STRENGTH_HIGH_ALIGN.format(area=area)

    if similar:
        key = f"{band}_similar"
        text = _pick_variant(variants, key, f"{band}_different", "default")
        if text:
            return text
        if band == "high":
            return STRENGTH_HIGH_ALIGN.format(area=area)
        if band == "mid":
            return STRENGTH_MID.format(area=area)
        return STRENGTH_LOW.format(area=area)

    text = _pick_variant(variants, f"{band}_different", "default")
    if text:
        return text
    if band == "mid":
        return STRENGTH_MID.format(area=area)
    if band == "low":
        return STRENGTH_LOW.format(area=area)
    return STRENGTH_DEFAULT


def _difference_block(result: SessionResult) -> str:
    gaps = result.misunderstanding_areas
    if not gaps:
        return DIFF_DEFAULT

    top = gaps[0]
    area = _area_label(top)
    band = _score_band(result.compatibility_score)
    variants = DIFF_BY_DIMENSION.get(top.dimension, {})

    if top.difference <= 1:
        return DIFF_SMALL.format(area=area)

    if top.difference >= 3:
        text = _pick_variant(variants, "high_gap", "default")
        if text:
            return text
    elif top.difference == 2:
        text = _pick_variant(variants, "mid_gap", "default")
        if text:
            return text
    else:
        text = _pick_variant(variants, "small_gap", "default")
        if text:
            return text

    if band == "high":
        return DIFF_HIGH_SCORE.format(area=area)
    return DIFF_DEFAULT


def _top_gap_category_dimension(comparisons: list[ScenarioComparison]) -> str | None:
    """Pick a narrative category with the largest average answer gap."""
    best_dim: str | None = None
    best_avg = -1.0
    for dims in CATEGORY_DIMENSION_MAP.values():
        comps = [c for c in comparisons if c.dimension in dims]
        if not comps:
            continue
        avg = sum(c.difference for c in comps) / len(comps)
        if avg > best_avg:
            best_avg = avg
            best_dim = max(comps, key=lambda c: c.difference).dimension
    return best_dim


def _tip_block(result: SessionResult) -> str:
    gaps = result.misunderstanding_areas
    if gaps:
        tip = TIP_BY_DIMENSION.get(gaps[0].dimension)
        if tip:
            return tip
    category_dim = _top_gap_category_dimension(result.comparisons)
    if category_dim:
        tip = TIP_BY_DIMENSION.get(category_dim)
        if tip:
            return tip
    if result.suggestions:
        return result.suggestions[0]
    return TIP_DEFAULT


def _style_blurb(name: str, styles: list[str]) -> str:
    return _personal_sentence(name, styles)


def _named_gap_line(comp: ScenarioComparison, name_a: str, name_b: str) -> str:
    area = _area_label(comp)
    if comp.user_a_weight >= comp.user_b_weight:
        higher, lower = name_a, name_b
    else:
        higher, lower = name_b, name_a

    if comp.difference >= 3:
        return PREMIUM_GAP_TEMPLATES["high"].format(
            area=area, higher=higher, lower=lower
        )
    if comp.difference == 2:
        return PREMIUM_GAP_TEMPLATES["mid"].format(area=area)
    return PREMIUM_GAP_TEMPLATES["soft"].format(area=area)


def _premium_strength_items(result: SessionResult) -> list[str]:
    items: list[str] = []
    band = _score_band(result.compatibility_score)
    for comp in result.strongest_areas[:3]:
        area = _area_label(comp)
        if comp.difference == 0:
            items.append(PREMIUM_STRENGTH_TEMPLATES["aligned"].format(area=area))
        elif comp.difference <= 1:
            items.append(PREMIUM_STRENGTH_TEMPLATES["close"].format(area=area))
        elif band == "high":
            items.append(PREMIUM_STRENGTH_TEMPLATES["score_high"].format(area=area))
        else:
            dim_variants = STRENGTH_BY_DIMENSION.get(comp.dimension, {})
            text = _pick_variant(dim_variants, "default") or STRENGTH_DEFAULT
            items.append(text)
    while len(items) < 3:
        items.append(STRENGTH_DEFAULT)
    return items[:3]


def _premium_gap_items(result: SessionResult) -> list[str]:
    name_a = result.user_a.name
    name_b = result.user_b.name
    items = [
        _named_gap_line(comp, name_a, name_b)
        for comp in result.misunderstanding_areas[:2]
    ]
    while len(items) < 2:
        items.append(DIFF_DEFAULT)
    return items[:2]


def _unspoken_needs(
    result: SessionResult,
    styles_a: list[str],
    styles_b: list[str],
) -> list[str]:
    name_a = result.user_a.name
    name_b = result.user_b.name
    needs: list[str] = []

    if "intimacy" in styles_a or "listening" in styles_a:
        needs.append(
            f"{name_a} ko‘proq tinglanish va yumshoq e’tibor kutishi mumkin — "
            f"lekin buni har doim ochiq aytmasligi mumkin."
        )
    if "practical" in styles_a or "responsibility" in styles_a:
        needs.append(
            f"{name_a} amaliy yordam va aniq qadamlarni qadrlashi mumkin."
        )
    if "intimacy" in styles_b or "open_comm" in styles_b:
        needs.append(
            f"{name_b} ochiq suhbat va hissiy yaqinlikni ko‘proq kutishi mumkin."
        )
    if "compromise" in styles_b or "listening" in styles_b:
        needs.append(
            f"{name_b} tinch, hukmsiz tinglanishni qadrlashi mumkin."
        )
    if "withdrawal" in styles_a or "delay" in styles_a:
        needs.append(
            f"{name_a} ba’zan avval tinchlanish vaqtini kutishi mumkin — "
            f"bosimsiz yaqinlashish yordam beradi."
        )
    if "control" in styles_b or "self_justify" in styles_b:
        needs.append(
            f"{name_b} o‘z fikrini eshitilishini kutishi mumkin — "
            f"avval tinglash, keyin javob berish foydali."
        )

    if len(needs) < 2:
        needs.append(
            "Ikkalangiz ham ba’zan ehtiyojlaringizni ichingizda saqlaysiz — "
            "kichik savol bilan ochish osonlashadi."
        )
    return needs[:4]


def _five_tips(result: SessionResult) -> list[str]:
    tips: list[str] = []
    for gap in result.misunderstanding_areas[:3]:
        tip = TIP_BY_DIMENSION.get(gap.dimension)
        if tip and tip not in tips:
            tips.append(tip)
    for suggestion in result.suggestions:
        if suggestion not in tips:
            tips.append(suggestion)
        if len(tips) >= 5:
            break
    defaults = [
        TIP_DEFAULT,
        "Har kuni bitta minnatdorchilik ayting — aniq va samimiy.",
        "Mojaro chiqqanda avval 10 daqiqa tinchlaning, keyin gaplashing.",
        "Haftada bir marta «faqat biz» vaqtini belgilang.",
        "Kelajak haqida qisqa, lekin muntazam gaplashing.",
    ]
    for tip in defaults:
        if tip not in tips:
            tips.append(tip)
        if len(tips) >= 5:
            break
    return tips[:5]


def _seven_day_plan(result: SessionResult) -> list[str]:
    """Personalize first days using top gap/strength; keep rest from base plan."""
    plan: list[str] = []
    gap = result.misunderstanding_areas[0] if result.misunderstanding_areas else None
    strength = result.strongest_areas[0] if result.strongest_areas else None

    for day, (title, text) in enumerate(SEVEN_DAY_EXERCISES, start=1):
        if day == 1 and gap:
            area = _area_label(gap)
            plan.append(
                f"Kun 1: «{area}» haqida yumshoq suhbat — "
                f"har biringiz 2 daqiqadan nima his qilayotganingizni ayting."
            )
        elif day == 2 and strength:
            area = _area_label(strength)
            plan.append(
                f"Kun 2: Kuchli tomoningizni eslang — «{area}» da "
                f"nima yaxshi ishlayotganini bir-biringizga ayting."
            )
        else:
            plan.append(f"Kun {day}: {title} — {text}")
    return plan


def _premium_blocks(
    result: SessionResult,
    *,
    unlocked: bool,
    styles_a: list[str],
    styles_b: list[str],
) -> list[PremiumBlock]:
    name_a = result.user_a.name
    name_b = result.user_b.name
    titles = [
        PREMIUM_BLOCK_TITLES[0],
        PREMIUM_BLOCK_TITLES[1],
        PREMIUM_BLOCK_TITLES[2].format(name_a=name_a, name_b=name_b),
        PREMIUM_BLOCK_TITLES[3].format(name_a=name_a, name_b=name_b),
        PREMIUM_BLOCK_TITLES[4],
        PREMIUM_BLOCK_TITLES[5],
        PREMIUM_BLOCK_TITLES[6],
    ]

    bodies: list[tuple[str | None, list[str] | None]] = [
        (None, _premium_strength_items(result)),
        (None, _premium_gap_items(result)),
        (_style_blurb(name_a, styles_a), None),
        (_style_blurb(name_b, styles_b), None),
        (None, _unspoken_needs(result, styles_a, styles_b)),
        (None, _five_tips(result)),
        (None, _seven_day_plan(result)),
    ]

    blocks: list[PremiumBlock] = []
    for index, title in enumerate(titles):
        body, items = bodies[index]
        teaser = PREMIUM_TEASER_LINES[min(index, len(PREMIUM_TEASER_LINES) - 1)]
        blocks.append(
            PremiumBlock(
                key=f"premium_{index + 1}",
                title=title,
                body=body if unlocked else None,
                items=items if unlocked else None,
                locked=not unlocked,
                teaser=teaser,
            )
        )
    return blocks


def build_result_experience(
    result: SessionResult,
    *,
    viewer: Participant,
    stage_label: str,
    premium_unlocked: bool,
) -> ResultExperience:
    role = viewer.role
    avg_a = _avg_weight_for_viewer(result.comparisons, ParticipantRole.user_a)
    avg_b = _avg_weight_for_viewer(result.comparisons, ParticipantRole.user_b)
    styles_a = _infer_styles(avg_a)
    styles_b = _infer_styles(avg_b)
    viewer_styles = styles_a if role == ParticipantRole.user_a else styles_b

    free_blocks = [
        ResultBlock(
            emoji="💪",
            title="Sizlarning kuchli tomoningiz",
            body=_strength_block(result),
        ),
        ResultBlock(
            emoji="⚖️",
            title="Qarashlaringiz farq qiladigan nuqta",
            body=_difference_block(result),
        ),
        ResultBlock(
            emoji="💬",
            title="Sizlarning muloqot uslubingiz",
            body=_communication_block(result.comparisons, result.compatibility_score),
        ),
        ResultBlock(
            emoji="✨",
            title="Bugun sinab ko‘ring",
            body=_tip_block(result),
        ),
    ]

    return ResultExperience(
        partner_names=f"{result.user_a.name} va {result.user_b.name}",
        stage_label=stage_label,
        score=result.compatibility_score,
        intro_summary=warmth_summary(result.compatibility_score),
        free_blocks=free_blocks,
        personal_title=f"{viewer.name} uchun shaxsiy xulosa",
        personal_body=_personal_sentence(viewer.name, viewer_styles),
        premium_headline="🔐 Sizlarning to‘liq tahlilingiz tayyor",
        premium_lead=PREMIUM_LEAD,
        premium_sublead=PREMIUM_SUBLEAD,
        premium_blocks=_premium_blocks(
            result,
            unlocked=premium_unlocked,
            styles_a=styles_a,
            styles_b=styles_b,
        ),
        premium_unlocked=premium_unlocked,
        viewer_role=role.value,
        viewer_name=viewer.name,
    )
