"""Telegram bot copy for relationship WebApp flow."""

from __future__ import annotations


def telegram_welcome() -> str:
    return (
        "Assalomu alaykum!\n\n"
        "Juftlik suhbati — bir-biringizni yaxshiroq tushunish uchun hayotiy savollar.\n"
        "Boshlash uchun pastdagi tugmani bosing."
    )


def telegram_link_confirmed() -> str:
    return (
        "✨ Ajoyib!\n\n"
        "Endi juftingiz ham javob bergach, shu yerda xabar olasiz — "
        "natija tayyor bo‘lganda birinchi bo‘lib bilasiz.\n\n"
        "Hozircha tinch kuting yoki juftingizga havola yuboring."
    )


def telegram_link_invalid() -> str:
    return (
        "Bu havola eskirgan yoki noto‘g‘ri.\n\n"
        "Iltimos, veb-sahifadagi taklif bo‘limidan qayta urinib ko‘ring."
    )


def initiator_answers_saved() -> str:
    return (
        "Sizning qismingiz tayyor ✅\n\n"
        "Endi havolani juftingizga yuboring. "
        "U ham 12 ta vaziyatga javob bergach, suhbat natijasi ochiladi."
    )


def invite_partner_welcome() -> str:
    return (
        "Sizni Juftlik suhbatiga taklif qilishdi.\n\n"
        "Turmush o‘rtog‘ingiz o‘z javoblarini belgilab bo‘ldi. "
        "Endi siz ham 12 ta hayotiy vaziyatga javob bering."
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
        "Bu suhbatga allaqachon boshqa ishtirokchi qo‘shilgan.\n"
        "Yangi Juftlik suhbati uchun yangi havola kerak."
    )


def invite_partner_continue() -> str:
    return (
        "Siz allaqachon ushbu Juftlik suhbatiga qo‘shilgansiz.\n"
        "Davom etish uchun tugmani bosing 👇"
    )


def invite_session_complete() -> str:
    return (
        "🎉 Bu suhbat natijasi allaqachon tayyor.\n"
        "Ko‘rish uchun tugmani bosing 👇"
    )


def result_ready_for_initiator() -> str:
    return (
        "🎉 Juftlik suhbati yakunlandi.\n"
        "Ikkalangizning javoblaringiz solishtirildi."
    )


def result_ready_for_partner() -> str:
    return (
        "🎉 Juftlik suhbati yakunlandi.\n"
        "Umumiy natijangiz ochiladi."
    )


def session_ready_notification(partner_name: str, result_url: str) -> tuple[str, str]:
    text = (
        f"Tabriklaymiz!\n\n"
        f"{partner_name} o‘z qismini yakunladi.\n\n"
        f"Sizlarning Juftlik suhbati natijasi tayyor.\n\n"
        f"Ikkingiz ham bir xil hayotiy vaziyatlarga javob berdingiz — "
        f"endi qayerda bir xil va qayerda farqli ekaningizni ko‘ring."
    )
    button = "💬 Natijani ko‘rish"
    return text, button
