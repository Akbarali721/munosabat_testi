DIMENSION_TRAITS: dict[str, list[str]] = {
    "responsibility_trust": [
        "Va'dalaringizga amal qilishga harakat qilasiz",
        "Ishonchli va barqaror bo‘lishga intilasiz",
        "Mas'uliyatni jiddiy qabul qilasiz",
    ],
    "attention": [
        "Kichik e'tiborlarni qadrlaysiz",
        "Sherigingiz kayfiyatini sezib turasiz",
        "Mehr va g'amxo'rlik ko'rsatishga tayyorsiz",
    ],
    "respect_attention": [
        "Hurmat bilan munosabatda bo‘lishni xohlaysiz",
        "Yonida bo‘lishga vaqt ajratishga harakat qilasiz",
        "E'tiborli va muloyim bo‘lishga intilasiz",
    ],
    "responsibility": [
        "Mas'uliyatni o'z zimmangizga olasiz",
        "Kelishilgan narsalarga rioya qilishga harakat qilasiz",
        "Ishonch uyg'otadigan qadamlar qo'yasiz",
    ],
    "priority_time": [
        "Birga vaqt o'tkazishni qadrlaysiz",
        "Munosabatni ustuvor deb bilasiz",
        "Rejalarni birga muhokama qilishga ochiqsiz",
    ],
    "money_values": [
        "Moliyaviy masalalarda ochiq bo‘lishga tayyorsiz",
        "Kelajak uchun o'ylab qaror qilasiz",
        "Qadriyatlaringizni hurmat qilasiz",
    ],
    "conflict_style": [
        "Mojaroda tinchlikni saqlashga harakat qilasiz",
        "Uzr so'rash va yarashishni muhim deb bilasiz",
        "Gapni yumshoq yopishga intilasiz",
    ],
    "family_values": [
        "Oila qadriyatlarini hurmat qilasiz",
        "Yaqinlaringiz bilan munosabatni muhim deb bilasiz",
        "Muvozanat topishga harakat qilasiz",
    ],
    "trust_privacy": [
        "Ishonchni qadrlaysiz",
        "Shaxsiy chegaralarni hurmat qilasiz",
        "Ochiq va samimiy bo‘lishga tayyorsiz",
    ],
    "future_vision": [
        "Kelajak haqida o'ylashga tayyorsiz",
        "Umumiy orzular haqida gaplashishga ochiqsiz",
        "Birga rivojlanishni xohlaysiz",
    ],
    "respect_listening": [
        "Tinglashga vaqt ajratishga harakat qilasiz",
        "Sherigingiz fikrini qadrlaysiz",
        "Hurmat bilan javob berasiz",
    ],
    "communication_initiative": [
        "Aloqada bo‘lishga tashabbus ko'rsatasiz",
        "Gaplashishdan qochmay qolmaslikka harakat qilasiz",
        "Munosabatni jonli tutishni xohlaysiz",
    ],
}

DEFAULT_TRAITS = [
    "Munosabatni yaxshilashga ochiq bo‘lishingiz",
    "Bir-biringizni tushunishga harakat qilasiz",
    "Samimiy va iliq munosabatda bo‘lishni xohlaysiz",
]

STRENGTH_TEMPLATES = [
    "Ko‘p hayotiy vaziyatlarda bir-biringizni yaxshi tushunasiz — bu sizlarning «ishonchli qayig'ingiz».",
    "{areas} kabi mavzularda yaqin yo‘nalishdasiz — bu sizlarning kuchli tomoningiz.",
    "Sizda allaqachon mustahkam poydevor bor — kundalik hayotda bir-biringizga yaqinsiz.",
]

SOFT_GROWTH_DEFAULT = (
    "Hozircha alohida e'tibor kerak bo'lgan jihat ko'rinmadi — bu ham yaxshi xabar."
)

SOFT_GROWTH_TEMPLATE = (
    "Ba'zi mavzularda ({areas}) oldindan ochiqroq suhbat qilish yanada qulay bo'lishi mumkin. "
    "Bu sizni uzoqlashtirmaydi — aksincha, yaqinlashtiradi."
)

WEEKLY_ACTIONS_BY_DIMENSION: dict[str, str] = {
    "priority_time": "Dam olish kunini birga rejalashtiring — hatto 2 soatlik «faqat biz» vaqti ham yetarli.",
    "attention": "Har kuni bitta minnatdorchilik gapiring — «bugun nimaga rahmat» deb so'rang.",
    "respect_attention": "10 daqiqa telefonsiz suhbat qiling — faqat bir-biringizga quloq tuting.",
    "responsibility": "Kichik va'dalarni yozib qo'ying va birga bajaring.",
    "money_values": "Katta xarajatdan oldin «birga qaror» qoidasini qo'ying.",
    "conflict_style": "Mojarodan keyin 24 soat ichida tinch gapiring — hukm emas, tushunish uchun.",
    "family_values": "Yaqinlar bilan bog'liq rejani oldindan birga kelishing.",
    "trust_privacy": "Ishonch haqida ochiq suhbat qiling — savol bering, hukm qilmang.",
    "future_vision": "3 ta umumiy orzu yoki maqsadni yozib qo'ying — katta bo'lishi shart emas.",
    "respect_listening": "Gapirayotganda to'xtab, «to'g'ri tushundimmi?» deb so'rang.",
    "communication_initiative": "Bu hafta bir marta birinchi bo'lib yozing yoki qo'ng'iroq qiling.",
    "responsibility_trust": "Kichik va'dangizni bugun bajaring — bu ishonchni mustahkamlaydi.",
}

DEFAULT_WEEKLY_ACTIONS = [
    "Xotirjam vaqt ajratib, hozir munosabatda sizga nima muhimligini bir-biringiz bilan ulashing.",
    "Yaxshi mos kelgan bitta vaziyatni tanlang va qiyin mavzularni shu usulda muhokama qiling.",
    "«Bugun nimaga minnatdorman?» deb so'rang — kichik savol, katta ta'sir.",
]
