def challenge_daily_nudge(day: int, title: str) -> tuple[str, str]:
    text = (
        f"🌱 Bugun {day}-kun — kichik, iliq qadam vaqti!\n\n"
        f"«{title}»\n\n"
        f"Birgalikda 10–15 daqiqa ajrating — bu sizlarni yaqinlashtiradi 💛"
    )
    return text, "Challenge sahifasini ochish"


def challenge_completed_celebration() -> str:
    return (
        "🎉 Ajoyib!\n\n"
        "7 kunlik Relationship Challenge yakunlandi. "
        "Siz allaqachon muhim qadam qo‘ydingiz — endi haftalik mini-tahlillar "
        "sizni yaqinlashtirishda davom etadi 💌"
    )


def weekly_reflection_prompt(week_number: int, prompt: str) -> tuple[str, str]:
    text = (
        f"💬 Hafta {week_number} — mini-tahlil vaqti\n\n"
        f"{prompt}\n\n"
        f"Juftingiz bilan qisqa suhbat qiling — to‘g‘ri javob yo‘q, faqat samimiylik muhim."
    )
    return text, "Challenge sahifasini ochish"


def birthday_reminder(name: str) -> str:
    return (
        f"🎂 Bugun {name} uchun maxsus kun!\n\n"
        f"Kichik tabrik, iliq xabar yoki birga choy — "
        f"munosabat uchun eng chiroyli sovg‘a vaqt va e’tibor 💛"
    )


def anniversary_reminder(years_together: int | None = None) -> str:
    if years_together and years_together > 0:
        return (
            f"💕 Bugun sizlarning {years_together}-yillik yubileyingiz!\n\n"
            f"Bir-biringizga qanday minnatdorchilik bildirishingiz mumkinligini "
            f"o‘ylab ko‘ring — kichik harakat katta yaqinlik keltiradi."
        )
    return (
        "💕 Bugun sizlarning munosabat yubileyingiz!\n\n"
        "Birgalikdagi chiroyli lahzani eslang va juftingizga iliq so‘z ayting 💌"
    )


def new_year_reminder() -> str:
    return (
        "✨ Yangi yil muborak!\n\n"
        "Yangi yilda munosabatingizni yanada mustahkamlash uchun "
        "bitta kichik niyat qo‘ying — masalan, haftada bir marta «faqat biz» vaqti 💛"
    )
