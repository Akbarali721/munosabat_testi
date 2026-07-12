from app.models import Gender


def spouse_label_for_gender(gender: Gender | None) -> str:
    if gender == Gender.male:
        return "ayolingiz"
    if gender == Gender.female:
        return "eringiz"
    return "turmush o‘rtog‘ingiz"


def spouse_label_possessive(gender: Gender | None) -> str:
    if gender == Gender.male:
        return "ayolingizning"
    if gender == Gender.female:
        return "eringizning"
    return "turmush o‘rtog‘ingizning"


def spouse_label_dative(gender: Gender | None) -> str:
    if gender == Gender.male:
        return "ayolingizga"
    if gender == Gender.female:
        return "eringizga"
    return "turmush o‘rtog‘ingizga"


def spouse_label_with(gender: Gender | None) -> str:
    if gender == Gender.male:
        return "ayolingiz bilan"
    if gender == Gender.female:
        return "eringiz bilan"
    return "turmush o‘rtog‘ingiz bilan"


def apply_spouse_labels(text: str, gender: Gender | None) -> str:
    label = spouse_label_for_gender(gender)
    capitalized = label[:1].upper() + label[1:] if label else label
    possessive = spouse_label_possessive(gender)
    dative = spouse_label_dative(gender)
    with_phrase = spouse_label_with(gender)
    return (
        text.replace("{spouse_label.capitalize()}", capitalized)
        .replace("{spouse_label_cap}", capitalized)
        .replace("{spouse_dative}", dative)
        .replace("{spouse_with}", with_phrase)
        .replace("{spouse_label}ning", possessive)
        .replace("{spouse_label}", label)
    )
