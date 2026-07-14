"""Telegram bot copy for relationship WebApp flow."""

from __future__ import annotations


def telegram_welcome() -> str:
    return (
        "Assalomu alaykum! Qadam’ga xush kelibsiz.\n"
        "Munosabatlaringizni yaxshiroq tushunish uchun testni boshlashingiz mumkin."
    )


def telegram_link_confirmed() -> str:
    return (
        "✨ Ajoyib!\n\n"
        "Endi sherigingiz ham javob bergach, shu yerda xabar olasiz — "
        "natijangiz ochilganda birinchi bo‘lib bilasiz.\n\n"
        "Hozircha tinch kuting yoki sherigingizga havola yuboring 💌"
    )


def telegram_link_invalid() -> str:
    return (
        "Bu havola eskirgan yoki noto‘g‘ri.\n\n"
        "Iltimos, veb-sahifadagi taklif bo‘limidan qayta urinib ko‘ring."
    )


def initiator_answers_saved() -> str:
    return (
        "Siz testning birinchi qismini yakunladingiz ✅\n\n"
        "Endi havolani sherigingizga yuboring. "
        "U ham savollarga javob bergach, sizning umumiy natijangiz tayyor bo‘ladi."
    )


def invite_partner_welcome() -> str:
    return (
        "Sizga munosabat testi yuborildi 💌\n\n"
        "Savollarga javob bering. Ikkalangiz ham testni tugatganingizdan keyin "
        "umumiy natija tayyorlanadi."
    )


def invite_self_blocked() -> str:
    return (
        "Bu havola ikkinchi ishtirokchi uchun.\n"
        "Uni boshqa Telegram foydalanuvchisiga yuboring."
    )


def invite_invalid() -> str:
    return (
        "Bu taklif havolasi topilmadi yoki eskirgan.\n"
        "Iltimos, birinchi ishtirokchidan yangi havola so‘rang."
    )


def invite_already_taken() -> str:
    return (
        "Bu testga allaqachon boshqa ishtirokchi qo‘shilgan.\n"
        "Yangi juftlik testi uchun yangi havola kerak."
    )


def invite_partner_continue() -> str:
    return (
        "Siz allaqachon ushbu testga qo‘shilgansiz.\n"
        "Davom etish uchun tugmani bosing 👇"
    )


def invite_session_complete() -> str:
    return (
        "🎉 Bu juftlik testi allaqachon yakunlangan.\n"
        "Natijani ko‘rish uchun tugmani bosing 👇"
    )


def result_ready_for_initiator() -> str:
    return (
        "🎉 Juftlik testi yakunlandi.\n"
        "Ikkalangizning javoblaringiz asosida natija tayyor."
    )


def result_ready_for_partner() -> str:
    return (
        "🎉 Test yakunlandi.\n"
        "Sizlarning umumiy natijangiz tayyor."
    )


def session_ready_notification(partner_name: str, result_url: str) -> tuple[str, str]:
    """Legacy helper kept for older call sites; prefer result_ready_* + web_app."""
    text = (
        f"❤️ Tabriklaymiz!\n\n"
        f"{partner_name} tahlilni yakunladi.\n\n"
        f"Sizlarning umumiy munosabat tahlilingiz tayyor.\n\n"
        f"Ikkingiz ham bir xil hayotiy vaziyatlarga javob berdingiz — "
        f"endi bir-biringizni qanchalik yaqin tushunishingizni ko‘rish vaqti keldi 💛"
    )
    button = "📊 Natijani ko‘rish"
    return text, button
