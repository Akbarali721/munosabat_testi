from dataclasses import dataclass

from app.constants import SCENARIO_DISPLAY_TITLES
from app.services.result_copy import build_free_result_copy
from app.services.results import ScenarioComparison, SessionResult


@dataclass
class RevealStep:
    emoji: str
    title: str
    body: str


@dataclass
class ResultReveal:
    steps: list[RevealStep]
    partner_names: str


def _interesting_fact(
    comparisons: list[ScenarioComparison],
    name_a: str,
    name_b: str,
) -> str:
    if not comparisons:
        return (
            f"{name_a} va {name_b} bir-biriga ochiq bo‘lishga tayyorsiz — "
            f"bu o‘zi allaqachon chiroyli boshlanish."
        )

    aligned = sorted(comparisons, key=lambda c: c.difference)
    top = aligned[0]
    title = SCENARIO_DISPLAY_TITLES.get(top.scenario_id, top.title)

    if top.difference == 0:
        return (
            f"«{title}» vaziyatida ikkalangiz ham bir xil yo‘nalishda qaror qilgansiz — "
            f"bu kundalik hayotda kamdan-kam darhol seziladi, lekin mustahkam juftlik belgisi."
        )

    if top.difference <= 1:
        return (
            f"«{title}» bo‘yicha {name_a} va {name_b} juda yaqin fikrdalar — "
            f"bu sizda yashirin moslik borligini anglatadi."
        )

    gap = sorted(comparisons, key=lambda c: c.difference, reverse=True)[0]
    gap_title = SCENARIO_DISPLAY_TITLES.get(gap.scenario_id, gap.title)
    return (
        f"«{gap_title}» bo‘yicha biroz farq bor — bu sizni uzoqlashtirmaydi, "
        f"aksincha bir-biringiz haqida yangi narsa bilish uchun qiziqarli suhbat mavzusi."
    )


def build_result_reveal(result: SessionResult) -> ResultReveal:
    copy = build_free_result_copy(result)
    name_a = result.user_a.name
    name_b = result.user_b.name
    daily_tip = copy.weekly_actions[0] if copy.weekly_actions else (
        "Bugun bir-biringizga «nimaga minnatdorman?» deb so‘rang."
    )

    steps = [
        RevealStep(
            emoji="❤️",
            title="Umumiy tahlil",
            body=(
                f"Sizlarning bir-biringizni tushunish darajasi — {result.compatibility_score}%.\n\n"
                f"{copy.warm_summary}"
            ),
        ),
        RevealStep(
            emoji="😊",
            title="Eng kuchli umumiy jihat",
            body=copy.strength_line,
        ),
        RevealStep(
            emoji="💬",
            title="Bir-biringiz haqidagi qiziqarli fakt",
            body=_interesting_fact(result.comparisons, name_a, name_b),
        ),
        RevealStep(
            emoji="🌱",
            title="Bugungi tavsiya",
            body=daily_tip,
        ),
    ]

    return ResultReveal(
        steps=steps,
        partner_names=f"{name_a} va {name_b}",
    )
