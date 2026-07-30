from app.models import Gender, RelationshipStage

SESSION_QUESTION_COUNT = 12

PREMIUM_PRICE_UZS = 9_999


def premium_price_label(amount_uzs: int | None = None) -> str:
    """Foydalanuvchiga ko‘rinadigan premium narx matni."""
    amount = PREMIUM_PRICE_UZS if amount_uzs is None else amount_uzs
    num = f"{amount:,}".replace(",", " ")
    return f"Boshlang‘ich narx — {num} so‘m"

STAGE_LABELS = {
    RelationshipStage.dating: "Endi tanishayapmiz",
    RelationshipStage.newly_married: "Yaqinda oila qurdik",
    RelationshipStage.newly_meeting: "Endi tanishayotganlar",
    RelationshipStage.in_relationship: "Yangi turmush qurganlar",
    RelationshipStage.married: "Turmush qurganlar",
}

STAGE_DESCRIPTIONS = {
    RelationshipStage.dating: "Bir-biringizni chuqurroq bilish uchun",
    RelationshipStage.newly_married: (
        "Oilaviy hayotdagi kutishlaringizni solishtirish uchun"
    ),
    RelationshipStage.newly_meeting: (
        "Bir-biringizning xarakteri va qarashlarini asta-sekin bilib oling."
    ),
    RelationshipStage.in_relationship: (
        "Yangi hayotga moslashishda bir-biringizni yaxshiroq tushuning."
    ),
    RelationshipStage.married: (
        "Kundalik hayotdagi yaqinlik, mas’uliyat va hamkorligingizni ko‘ring."
    ),
}

GENDER_LABELS = {
    Gender.male: "Erkak",
    Gender.female: "Ayol",
}

DIMENSION_LABELS = {
    "responsibility_trust": "Mas'uliyat va ishonch",
    "attention": "E'tibor",
    "respect_attention": "Hurmat va e'tibor",
    "responsibility": "Mas'uliyat",
    "priority_time": "Vaqt va ustuvorlik",
    "money_values": "Pul va qadriyatlar",
    "conflict_style": "Munozara uslubi",
    "family_values": "Oila qadriyatlari",
    "trust_privacy": "Ishonch va maxfiylik",
    "future_vision": "Kelajak tasavvuri",
    "respect_listening": "Tinglash va hurmat",
    "communication_initiative": "Aloqa tashabbusi",
    "emotional_support": "Hissiy qo‘llab-quvvatlash",
    "love_language": "Sevgi tilida ifoda",
    "sensitivity": "Sezgirlik",
    "communication": "Muloqot",
    "attachment": "Bog‘lanish",
    "trust": "Ishonch",
    "openness": "Ochiqlik",
    "boundaries": "Chegaralar",
    "relationship_expectations": "Munosabat kutilmalari",
    "emotional_needs": "Hissiy ehtiyojlar",
    "financial_trust": "Moliyaviy ishonch",
    "appreciation": "Qadrlanish",
    "support": "Qo‘llab-quvvatlash",
    "personal_boundaries": "Shaxsiy chegaralar",
    "future_expectations": "Kelajak kutilmalari",
    "inner_needs": "Ichki ehtiyojlar",
    "attention_and_affection": "E’tibor va mehr",
    "money_and_expenses": "Pul va xarajatlar",
    "household_responsibility": "Uy ishlari",
    "parents_and_relatives": "Ota-ona va qarindoshlar",
    "conflict_resolution": "Kelishmovchilik",
    "future_plans": "Kelajak rejalari",
}

SCENARIO_ORDER = [
    "emotional_support",
    "love_expression",
    "emotional_triggers",
    "conflict_resolution",
    "communication_frequency",
    "emotional_safety",
    "conflict_goal",
    "important_dates",
    "vulnerability",
    "personal_space",
    "future_vision",
    "inner_needs",
]

IN_RELATIONSHIP_SCENARIO_ORDER = [f"newlywed_{i:02d}" for i in range(1, 13)]

# API/debug alias for Yangi turmush qurganlar
STAGE_CATEGORY_CODE = {
    RelationshipStage.dating.value: "dating",
    RelationshipStage.newly_married.value: "newly_married",
    RelationshipStage.newly_meeting.value: "newly_meeting",
    RelationshipStage.in_relationship.value: "newlywed",
    RelationshipStage.married.value: "married",
}

MARRIED_SCENARIO_ORDER = [
    "housework",
    "parenting",
    "money_budget",
    "in_laws",
    "intimacy",
    "work_stress",
    "old_friend",
    "surprise_gift",
    "argument_style",
    "shared_goal",
    "daily_ritual",
    "thank_you",
]

STAGE_SCENARIO_ORDER = {
    RelationshipStage.dating.value: SCENARIO_ORDER,
    RelationshipStage.newly_married.value: IN_RELATIONSHIP_SCENARIO_ORDER,
    RelationshipStage.newly_meeting.value: SCENARIO_ORDER,
    RelationshipStage.in_relationship.value: IN_RELATIONSHIP_SCENARIO_ORDER,
    RelationshipStage.married.value: MARRIED_SCENARIO_ORDER,
}

SCENARIO_DISPLAY_TITLES = {
    "emotional_support": "Hissiy qo‘llab-quvvatlash",
    "love_expression": "Sevgi ifodasi",
    "emotional_triggers": "Ranjitadigan holatlar",
    "conflict_resolution": "Muammoni hal qilish",
    "communication_frequency": "Aloqa chastotasi",
    "emotional_safety": "Xavfsizlik hissi",
    "conflict_goal": "Kelishmovchilik maqsadi",
    "important_dates": "Muhim sanalar",
    "vulnerability": "Ochiq bo‘lish",
    "personal_space": "Shaxsiy erkinlik",
    "future_vision": "Kelajak tasavvuri",
    "inner_needs": "Ichki ehtiyojlar",
    "family_emotional_need": "Oiladagi ehtiyoj",
    "household_responsibility": "Uy ishlari",
    "family_finance": "Oilaviy moliya",
    "silence_interpretation": "Sukut va charchoq",
    "family_boundaries": "Oila chegaralari",
    "feeling_appreciated": "Qadrlanish",
    "support_during_difficulty": "Qiyin paytda yordam",
    "family_future": "Oilaviy kelajak",
    "hidden_emotional_need": "Yashirin ehtiyoj",
    **{f"newlywed_{i:02d}": f"Savol {i}" for i in range(1, 13)},
    "promise_call": "🕗 20:00 da qo‘ng‘iroq",
    "small_attention": "☕ Qahvani eslab qoldi",
    "phone_attention": "📱 Telefoniga qarayverdi",
    "being_late": "⏰ Uchrashuvga kechikdi",
    "friends_plan": "👥 Do‘stlar chaqirdi",
    "first_bill": "💳 Birinchi hisob",
    "different_opinion": "💬 Fikr mos kelmadi",
    "mother_call": "📞 Onasi qo‘ng‘iroq qildi",
    "private_secret": "🤫 Shaxsiy sir",
    "future_talk": "🔮 Kelajak haqida gap",
    "interrupting": "💬 Suhbat paytida",
    "initiative": "📩 Suhbatdagi tashabbus",
    "weekend_plan": "📅 Dam olish rejasi",
    "bad_mood": "😔 Yomon kayfiyat",
    "social_media": "📱 Ijtimoiy tarmoq",
    "money_talk": "💰 Katta xarajat",
    "family_visit": "👨‍👩‍👧 Oila bilan tanishtirish",
    "compliment": "💝 Maqtov va minnat",
    "apology": "🙏 Kichik uzr",
    "future_step": "🏠 Birga yashash",
    "habit_change": "🔄 Kichik odat",
    "support_day": "🤝 Qo‘llab-quvvatlash",
    "jealousy_talk": "💬 Ishonch suhbati",
    "quality_time": "⏳ Birga vaqt",
    "housework": "🧹 Uy ishlari",
    "parenting": "👶 Farzand tarbiyasi",
    "money_budget": "💳 Pul va xarajatlar",
    "in_laws": "🏡 Qarindoshlar tashrifi",
    "intimacy": "💞 Yaqinlik",
    "work_stress": "💼 Ish stressi",
    "old_friend": "👋 Eski tanish",
    "surprise_gift": "🎁 Kichik surpriz",
    "argument_style": "🗣️ Mojaro va sukut",
    "shared_goal": "🎯 Kelajak rejalari",
    "daily_ritual": "☕ Birga vaqt",
    "thank_you": "🌸 Rahmat so‘zi",
}

STAGE_ICONS = {
    RelationshipStage.dating: "🌱",
    RelationshipStage.newly_married: "💍",
    RelationshipStage.newly_meeting: "🌱",
    RelationshipStage.in_relationship: "💞",
    RelationshipStage.married: "💍",
}

SCENARIO_CLOSINGS = {
    "promise_call": "Sizning birinchi fikringiz?",
    "small_attention": "Sizning reaksiyangiz?",
    "phone_attention": "Siz...",
    "being_late": "Siz...",
    "friends_plan": "Siz...",
    "first_bill": "Siz...",
    "different_opinion": "Siz...",
    "mother_call": "Siz...",
    "private_secret": "Siz...",
    "future_talk": "Siz...",
    "interrupting": "",
    "initiative": "",
    "weekend_plan": "Bunday vaziyatda siz…",
    "bad_mood": "Bunday vaziyatda siz…",
    "social_media": "Bunday vaziyatda siz…",
    "money_talk": "Bunday vaziyatda siz…",
    "family_visit": "Bunday vaziyatda siz…",
    "compliment": "Siz...",
    "apology": "Siz...",
    "future_step": "Bunday vaziyatda siz…",
    "habit_change": "Siz...",
    "support_day": "Siz...",
    "jealousy_talk": "Siz...",
    "quality_time": "Siz...",
    "housework": "Bunday vaziyatda siz…",
    "parenting": "Bunday vaziyatda siz…",
    "money_budget": "Bunday vaziyatda siz…",
    "in_laws": "Bunday vaziyatda siz…",
    "intimacy": "Bunday vaziyatda siz…",
    "work_stress": "Bunday vaziyatda siz…",
    "old_friend": "Bunday vaziyatda siz…",
    "surprise_gift": "Siz...",
    "argument_style": "Bunday vaziyatda siz…",
    "shared_goal": "Bunday vaziyatda siz…",
    "daily_ritual": "Bunday vaziyatda siz…",
    "thank_you": "Siz...",
}

SCENARIO_CLOSINGS_MALE = {
    "promise_call": "Siz nima qilasiz?",
    "small_attention": "Siz...",
    "phone_attention": "Siz...",
    "being_late": "Siz...",
    "friends_plan": "Siz...",
    "first_bill": "Siz odatda...",
    "different_opinion": "Siz...",
    "mother_call": "Siz...",
    "private_secret": "Siz...",
    "future_talk": "Siz...",
    "interrupting": "",
    "initiative": "",
    "weekend_plan": "Bunday vaziyatda siz…",
    "bad_mood": "Bunday vaziyatda siz…",
    "social_media": "Bunday vaziyatda siz…",
    "money_talk": "Bunday vaziyatda siz…",
    "family_visit": "Bunday vaziyatda siz…",
    "compliment": "Siz...",
    "apology": "Siz...",
    "future_step": "Bunday vaziyatda siz…",
    "habit_change": "Siz...",
    "support_day": "Siz...",
    "jealousy_talk": "Siz...",
    "quality_time": "Siz...",
    "housework": "Bunday vaziyatda siz…",
    "parenting": "Bunday vaziyatda siz…",
    "money_budget": "Bunday vaziyatda siz…",
    "in_laws": "Bunday vaziyatda siz…",
    "intimacy": "Bunday vaziyatda siz…",
    "work_stress": "Bunday vaziyatda siz…",
    "old_friend": "Bunday vaziyatda siz…",
    "surprise_gift": "Siz...",
    "argument_style": "Bunday vaziyatda siz…",
    "shared_goal": "Bunday vaziyatda siz…",
    "daily_ritual": "Bunday vaziyatda siz…",
    "thank_you": "Siz...",
}

FOOTER_QUOTES = [
    "Har bir kuchli munosabat bir-birini tushunishdan boshlanadi.",
    "Ba’zan bitta samimiy suhbat munosabatni o‘zgartiradi.",
    "Yaqinlik tasodif emas — u kichik qarorlardan o‘sadi.",
    "Tushunish uchun mukammal bo‘lish shart emas, ochiq bo‘lish yetadi.",
    "Eng muhim narsa — bir-biringizni eshitishga vaqt topish.",
]

RESULT_DIMENSION_GROUPS = {
    "trust": {
        "label": "Ishonch",
        "dimensions": [
            "responsibility_trust",
            "trust_privacy",
            "trust",
            "emotional_safety",
            "financial_trust",
        ],
    },
    "communication": {
        "label": "Muloqot",
        "dimensions": [
            "communication_initiative",
            "conflict_style",
            "respect_listening",
            "attention",
            "communication",
            "attachment",
            "silence_interpretation",
            "love_language",
            "emotional_support",
            "sensitivity",
            "openness",
        ],
    },
    "future": {
        "label": "Kelajak",
        "dimensions": [
            "future_vision",
            "future_expectations",
            "relationship_expectations",
            "family_future",
        ],
    },
    "respect": {
        "label": "Hurmat",
        "dimensions": [
            "respect_attention",
            "responsibility",
            "priority_time",
            "money_values",
            "family_values",
            "boundaries",
            "family_boundaries",
            "personal_boundaries",
            "appreciation",
            "support",
            "emotional_needs",
            "inner_needs",
        ],
    },
}

LOADING_MESSAGES = [
    "Javoblaringiz saqlanmoqda...",
    "Bir oz sabr — bu bir daqiqadan kam vaqt oladi",
    "Vaziyatlar juftingiz bilan solishtirish uchun tayyorlanmoqda...",
    "Keyingi qadamga o‘tilmoqda...",
]

PREMIUM_MAP_DIMENSIONS: dict[str, dict[str, object]] = {
    "knowing_each_other": {
        "label": "Bir-birini bilish",
        "dimensions": ["respect_listening", "communication_initiative"],
    },
    "emotional_bond": {
        "label": "Bir-birini his qilish",
        "dimensions": ["attention", "respect_attention"],
    },
    "communication": {
        "label": "Muloqot",
        "dimensions": ["communication_initiative", "respect_listening", "conflict_style"],
    },
    "trust": {
        "label": "Ishonch",
        "dimensions": ["responsibility_trust", "trust_privacy"],
    },
    "care": {
        "label": "G'amxo'rlik",
        "dimensions": ["attention", "responsibility"],
    },
    "future_outlook": {
        "label": "Kelajakka qarash",
        "dimensions": ["future_vision", "family_values"],
    },
    "soft_conflict": {
        "label": "Mojaroni yumshoq hal qilish",
        "dimensions": ["conflict_style"],
    },
}

SEVEN_DAY_EXERCISES = [
    ("10 daqiqa telefonsiz suhbat", "Telefonlarni boshqa xonaga qo'ying. Faqat bir-biringizga quloq tuting."),
    ("Bitta yoqgan fazilat", "Har biringiz bir-biringizda yoqadigan bitta fazilatni ayting."),
    ("Birgalikdagi choy", "Kechki choy yoki kofe — hatto 15 daqiqa ham yetarli."),
    ("«Nima xursand qiladi?»", "«Meni bugun nima xursand qiladi?» deb so'rang va tinglang."),
    ("Kichik surpriz", "Xatcho'p, xabar yoki kichik yordam — katta bo'lishi shart emas."),
    ("«Faqat biz» vaqti", "Dam olish kuniga 2 soatlik birga vaqt rejalashtiring."),
    ("Hafta xulosasi", "«Biz uchun eng yaxshi hafta qaysi edi?» deb so'rang va xulosa qiling."),
]

WEEKLY_REFLECTIONS = [
    (
        "«Bizni yaqinlashtirgan narsa»",
        "O‘tgan haftada sizlarni yaqinlashtirgan bitta kichik lahzani eslang va bir-biringizga ayting.",
    ),
    (
        "«Qanday qo‘llab-quvvatlash kerak?»",
        "«Bu hafta senga qanday yordam berishim mumkin?» deb so‘rang — tinglash ham yaqinlik.",
    ),
    (
        "«Kichik minnatdorchilik»",
        "Har biringiz juftingiz uchun minnatdor bo‘lgan bitta narsani ayting.",
    ),
    (
        "«Kelajakdagi bir kun»",
        "Yaqin kelajakda birgalikda qilishni xohlagan bitta kichik rejani muhokama qiling.",
    ),
]
