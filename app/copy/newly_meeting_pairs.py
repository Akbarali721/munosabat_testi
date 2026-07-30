"""Natija izohlari — Endi tanishayotganlar (pair_key bo‘yicha)."""

VALUE_PHRASES: dict[str, str] = {
    "listening": "tinglash va tushunishni kutasiz",
    "problem_solving": "maslahat va yechim izlashni afzal ko‘rasiz",
    "affection": "mehr va yaqinlikni kutasiz",
    "space": "biroz yolg‘iz vaqt berishni xohlaysiz",
    "time": "birga vaqt o‘tkazishda sevgini his qilasiz",
    "words": "iliq so‘zlarda sevgini ko‘rasiz",
    "acts_of_service": "amalda yordamda sevgini ko‘rasiz",
    "remembering": "mayda narsalarni eslab qolishda qadrlaysiz",
    "understand_busy": "bandlikni tabiiy deb qabul qilasiz",
    "fear_losing_interest": "aloqa kamayganda xavotirlanasiz",
    "initiate_contact": "o‘zingiz birinchi bo‘lib aloqaga chiqasiz",
    "mirror_distance": "masofani nusxa ko‘chirasiz",
}


def same_choice_line(pair_key: str, value: str, name_a: str, name_b: str) -> str:
    phrase = VALUE_PHRASES.get(value)
    if phrase:
        return f"{name_a} va {name_b} ikkalasi ham {phrase} — bu yaqin nuqtani mustahkamlaydi."
    return (
        f"{name_a} va {name_b} bu savolda o‘xshash yo‘nalishni tanladilar — "
        f"buni ochiq muloqot bilan davom ettiring."
    )


def different_choice_line(
    pair_key: str,
    value_a: str,
    value_b: str,
    name_a: str,
    name_b: str,
) -> str:
    phrase_a = VALUE_PHRASES.get(value_a, "boshqa ehtiyojni ifodalaysiz")
    phrase_b = VALUE_PHRASES.get(value_b, "boshqa ehtiyojni ifodalaysiz")
    return (
        f"{name_a} {phrase_a}, {name_b} esa {phrase_b}. "
        f"Bu farqni kichik, aniq qadamlar bilan yumshatish oson."
    )
