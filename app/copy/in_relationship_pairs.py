"""Natija izohlari — Yangi turmush qurganlar (pair_key bo‘yicha)."""

from collections.abc import Callable

VALUE_PHRASES: dict[str, str] = {
    "time_attention": "vaqt va e’tibor orqali mehrni ko‘rasiz",
    "listening_understanding": "tinglash va tushunish orqali yaqinlikni his qilasiz",
    "shared_responsibility": "mas’uliyatni bo‘lishish orqali oilani mustahkamlashni xohlaysiz",
    "open_affection": "ochiq mehr ko‘rsatish orqali baxt his qilasiz",
    "quiet_listening": "avval tinch tinglashni kutasiz",
    "problem_solving": "muammoni birgalikda hal qilishni afzal ko‘rasiz",
    "affection_presence": "yonida bo‘lib, mehr ko‘rsatishni kutasiz",
    "give_space": "biroz vaqt berishni xohlaysiz",
    "thanks": "minnatdorchilik so‘zlari orqali qadrlanasiz",
    "dedicated_time": "alohida vaqt va e’tiborni mehr belgisi deb bilasiz",
    "practical_help": "amaliy yordam va qo‘llab-quvvatlashni qadrlaysiz",
    "public_respect": "hurmat va e’tiborni ochiq ko‘rsatishni qadrlaysiz",
}


def _feeling_appreciated_different(
    value_a: str,
    value_b: str,
    name_a: str,
    name_b: str,
) -> str:
    phrase_a = VALUE_PHRASES.get(value_a, "boshqacha usulda mehrni ko‘rasiz")
    phrase_b = VALUE_PHRASES.get(value_b, "boshqacha usulda mehrni ko‘rasiz")
    if {value_a, value_b} == {"dedicated_time", "public_respect"}:
        return (
            f"{name_a} {phrase_a}, {name_b} esa {phrase_b}. "
            f"Demak, ikkovingiz mehrni turli harakatlarda ko‘rasiz — "
            f"buni ochiq gaplashish foydali."
        )
    return (
        f"{name_a} {phrase_a}, {name_b} esa {phrase_b}. "
        f"Bu farqni kichik, aniq harakatlar bilan yumshatish mumkin."
    )


def _feeling_appreciated_same(value: str, name_a: str, name_b: str) -> str:
    if value == "practical_help":
        return (
            f"Siz ikkalangiz ham mehrni {VALUE_PHRASES[value]} — "
            f"bu kuchli umumiy til; kundalik kichik yordamlar munosabatni mustahkamlaydi."
        )
    phrase = VALUE_PHRASES.get(value, "o‘xshash usulda qadrlanishni xohlaysiz")
    return f"{name_a} va {name_b} ikkalasi ham {phrase}."


PAIR_HANDLERS: dict[str, dict[str, Callable[..., str]]] = {
    "feeling_appreciated": {
        "same": lambda v, a, b: _feeling_appreciated_same(v, a, b),
        "different": lambda va, vb, a, b: _feeling_appreciated_different(va, vb, a, b),
    },
}


def same_choice_line(pair_key: str, value: str, name_a: str, name_b: str) -> str:
    handlers = PAIR_HANDLERS.get(pair_key, {})
    if "same" in handlers:
        return handlers["same"](value, name_a, name_b)
    phrase = VALUE_PHRASES.get(value)
    if phrase:
        return f"{name_a} va {name_b} ikkalasi ham {phrase}."
    return (
        f"{name_a} va {name_b} bu mavzuda o‘xshash yo‘nalishni tanladilar — "
        f"buni mustahkamlash uchun bir-biringizga aytib qo‘ying."
    )


def different_choice_line(
    pair_key: str,
    value_a: str,
    value_b: str,
    name_a: str,
    name_b: str,
) -> str:
    handlers = PAIR_HANDLERS.get(pair_key, {})
    if "different" in handlers:
        return handlers["different"](value_a, value_b, name_a, name_b)
    phrase_a = VALUE_PHRASES.get(value_a, "boshqa ehtiyojni ifodalaysiz")
    phrase_b = VALUE_PHRASES.get(value_b, "boshqa ehtiyojni ifodalaysiz")
    return (
        f"{name_a} {phrase_a}, {name_b} esa {phrase_b}. "
        f"Bu yerda kichik kelishuvlar katta yordam beradi."
    )
