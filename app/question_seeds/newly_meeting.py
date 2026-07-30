"""Endi tanishayotganlar — juftlik savollari (12 × 2)."""

from app.question_seeds._helpers import QuestionSeed, _q

STAGE = "newly_meeting"


def _qn(
    scenario_id: str,
    gender_target: str,
    dimension: str,
    text: str,
    option_specs: list[tuple[str, str]],
) -> QuestionSeed:
    return _q(scenario_id, gender_target, dimension, text, option_specs, stage=STAGE)


NEWLY_MEETING_QUESTIONS: list[QuestionSeed] = [
    _qn(
        "emotional_support",
        "male",
        "emotional_support",
        "Xafa bo‘lganingda yaqin insoningdan nimani ko‘proq kutasan?",
        [
            ("Meni tinchgina tinglashini", "listening"),
            ("Menga maslahat berishini", "problem_solving"),
            ("Meni quchoqlab, yonimda bo‘lishini", "affection"),
            ("Biroz vaqt yolg‘iz qoldirishini", "space"),
        ],
    ),
    _qn(
        "emotional_support",
        "female",
        "emotional_support",
        "Xafa bo‘lganingda mendan nimani ko‘proq kutasan?",
        [
            ("Seni tinchgina tinglashimni", "listening"),
            ("Muammoni hal qilishga yordam berishimni", "problem_solving"),
            ("Yoningda bo‘lib, mehr ko‘rsatishimni", "affection"),
            ("Biroz vaqt yolg‘iz qoldirishimni", "space"),
        ],
    ),
    _qn(
        "love_expression",
        "male",
        "love_language",
        "Senga insonning sevgisi ko‘proq nimada bilinadi?",
        [
            ("Menga vaqt ajratishida", "time"),
            ("Chiroyli so‘zlar aytishida", "words"),
            ("Amalda yordam berishida", "acts_of_service"),
            ("Mayda narsalarni eslab qolishida", "remembering"),
        ],
    ),
    _qn(
        "love_expression",
        "female",
        "love_language",
        "Mening sevgimni ko‘proq nimada his qilasan?",
        [
            ("Senga vaqt ajratganimda", "time"),
            ("Hislarimni so‘z bilan aytganimda", "words"),
            ("Amalda yordam berganimda", "acts_of_service"),
            ("Sen haqingdagi mayda narsalarni eslab qolganimda", "remembering"),
        ],
    ),
    _qn(
        "emotional_triggers",
        "male",
        "sensitivity",
        "Munosabatda seni eng ko‘p nima ranjitadi?",
        [
            ("Beparvolik", "indifference"),
            ("Yolg‘on gapirish", "dishonesty"),
            ("Meni boshqalar bilan solishtirish", "comparison"),
            ("Hislarimni jiddiy qabul qilmaslik", "invalidation"),
        ],
    ),
    _qn(
        "emotional_triggers",
        "female",
        "sensitivity",
        "Munosabatimizda seni eng ko‘p nima ranjitishi mumkin?",
        [
            ("Senga befarq bo‘lib qolishim", "indifference"),
            ("Rostini aytmasligim", "dishonesty"),
            ("Seni boshqa yigitlar bilan solishtirishim", "comparison"),
            ("Hislaringni jiddiy qabul qilmasligim", "invalidation"),
        ],
    ),
    _qn(
        "conflict_resolution",
        "male",
        "communication",
        "Biror muammo bo‘lsa, uni qanday hal qilishni afzal ko‘rasan?",
        [
            ("Darhol ochiq gaplashishni", "talk_immediately"),
            ("Avval o‘ylab, keyin gaplashishni", "think_then_talk"),
            ("Qarshi tomon birinchi bo‘lib gap boshlashini", "partner_starts"),
            ("Vaqt o‘tishi bilan o‘zi hal bo‘lishini", "wait_it_out"),
        ],
    ),
    _qn(
        "conflict_resolution",
        "female",
        "communication",
        "Oramizda muammo paydo bo‘lsa, uni qanday hal qilishni xohlaysan?",
        [
            ("Darhol ochiq gaplashishni", "talk_immediately"),
            ("Avval o‘ylab, keyin gaplashishni", "think_then_talk"),
            ("Men birinchi bo‘lib gap boshlashimni", "partner_starts"),
            ("Biroz vaqt o‘tib, vaziyat tinchishini", "wait_it_out"),
        ],
    ),
    _qn(
        "communication_frequency",
        "male",
        "attachment",
        "Yaqin insoning band bo‘lib, kun davomida kam yozsa, sen nima deb o‘ylaysan?",
        [
            ("Ishlari ko‘p ekanini tushunaman", "understand_busy"),
            ("Menga qiziqishi kamaygan deb xavotirlanaman", "fear_losing_interest"),
            ("O‘zim birinchi bo‘lib yozaman", "initiate_contact"),
            ("Men ham ataylab yozmay turaman", "mirror_distance"),
        ],
    ),
    _qn(
        "communication_frequency",
        "female",
        "attachment",
        "Men band bo‘lib, kun davomida kam yozsam, qanday munosabat bildirasan?",
        [
            ("Ishlarim ko‘pligini tushunasan", "understand_busy"),
            ("Senga qiziqishim kamaygan deb xavotirlanasan", "fear_losing_interest"),
            ("O‘zing birinchi bo‘lib yozasan", "initiate_contact"),
            ("Sen ham ataylab yozmay turasan", "mirror_distance"),
        ],
    ),
    _qn(
        "emotional_safety",
        "male",
        "trust",
        "O‘zingni munosabatda qachon xavfsiz his qilasan?",
        [
            ("Menga doimo rost gapirilganda", "honesty"),
            ("Hislar haqida ochiq gaplashilganda", "open_talk"),
            ("Va’dalar bajarilganda", "reliability"),
            ("Qanday holatda bo‘lsam ham qabul qilinganimda", "unconditional"),
        ],
    ),
    _qn(
        "emotional_safety",
        "female",
        "trust",
        "Munosabatimizda o‘zingni qachon xavfsiz his qilasan?",
        [
            ("Men senga doimo rost gapirganimda", "honesty"),
            ("Hislarimiz haqida ochiq gaplashganimizda", "open_talk"),
            ("Bergan va’dalarimni bajarganimda", "reliability"),
            ("Seni qanday bo‘lsang, shunday qabul qilganimda", "unconditional"),
        ],
    ),
    _qn(
        "conflict_goal",
        "male",
        "conflict_style",
        "Sevgan insoning bilan kelishmovchilik bo‘lsa, senga nima muhimroq?",
        [
            ("Kim haq ekanini aniqlash", "being_right"),
            ("Bir-birimizni tushunish", "understanding"),
            ("Tezroq yarashib olish", "quick_reconcile"),
            ("Bunday holat boshqa takrorlanmasligi", "prevent_repeat"),
        ],
    ),
    _qn(
        "conflict_goal",
        "female",
        "conflict_style",
        "Oramizda kelishmovchilik bo‘lsa, sen uchun nima muhimroq?",
        [
            ("Kim haq ekanini aniqlash", "being_right"),
            ("Bir-birimizni tushunish", "understanding"),
            ("Tezroq yarashib olish", "quick_reconcile"),
            ("Bu holat boshqa takrorlanmasligi", "prevent_repeat"),
        ],
    ),
    _qn(
        "important_dates",
        "male",
        "attention",
        "Yaqin insoning sen uchun muhim sanani unutib qo‘ysa, qanday his qilasan?",
        [
            ("Juda xafa bo‘laman", "very_hurt"),
            ("Sababini so‘rab, tushunishga harakat qilaman", "ask_why"),
            ("Muhim emasdek ko‘rsataman, lekin ichimda qoladi", "hide_hurt"),
            ("Sanalardan ko‘ra kundalik munosabat muhim deb hisoblayman", "daily_over_dates"),
        ],
    ),
    _qn(
        "important_dates",
        "female",
        "attention",
        "Men sen uchun muhim sanani unutib qo‘ysam, qanday yo‘l tutasan?",
        [
            ("Juda qattiq xafa bo‘lasan", "very_hurt"),
            ("Sababini so‘rab, tushunishga harakat qilasan", "ask_why"),
            ("Muhim emasdek ko‘rsatasan, lekin ichingda qoladi", "hide_hurt"),
            ("Sanalardan ko‘ra kundalik munosabat muhim deb hisoblaysan", "daily_over_dates"),
        ],
    ),
    _qn(
        "vulnerability",
        "male",
        "openness",
        "Qiyin vaziyatga tushganingda odatda nima qilasan?",
        [
            ("Yaqin insonim bilan bo‘lishaman", "share_openly"),
            ("Hammasini o‘zim hal qilishga harakat qilaman", "handle_alone"),
            ("Faqat eng ishongan odamimga aytaman", "trusted_only"),
            ("Muammoni ichimda saqlayman", "keep_inside"),
        ],
    ),
    _qn(
        "vulnerability",
        "female",
        "openness",
        "Qiyin vaziyatga tushganingda odatda qanday yo‘l tutasan?",
        [
            ("Men bilan ochiq bo‘lishasan", "share_openly"),
            ("Muammoni o‘zing hal qilishga harakat qilasan", "handle_alone"),
            ("Faqat juda ishonganingdagina menga aytasan", "trusted_only"),
            ("Muammoni ichingda saqlaysan", "keep_inside"),
        ],
    ),
    _qn(
        "personal_space",
        "male",
        "boundaries",
        "Munosabatda shaxsiy erkinlik haqida qanday fikrdasan?",
        [
            ("Har kimning o‘z vaqti va do‘stlari bo‘lishi kerak", "independence"),
            ("Ko‘p vaqtni birga o‘tkazish kerak", "togetherness"),
            ("Erkinlik bo‘lishi kerak, lekin hamma narsani aytib turish lozim", "informed_freedom"),
            ("Bu insonlar o‘rtasidagi ishonchga bog‘liq", "trust_based"),
        ],
    ),
    _qn(
        "personal_space",
        "female",
        "boundaries",
        "Munosabatda shaxsiy erkinlik haqida qanday fikrdasan?",
        [
            ("Har birimizning o‘z vaqtimiz va do‘stlarimiz bo‘lishi kerak", "independence"),
            ("Ko‘proq vaqtni birga o‘tkazishimiz kerak", "togetherness"),
            ("Erkinlik bo‘lishi kerak, lekin hamma narsani aytib turish lozim", "informed_freedom"),
            ("Bu o‘rtamizdagi ishonchga bog‘liq", "trust_based"),
        ],
    ),
    _qn(
        "future_vision",
        "male",
        "relationship_expectations",
        "Kelajakdagi munosabatingni qanday tasavvur qilasan?",
        [
            ("Tinch va barqaror", "calm_stable"),
            ("Romantik va hislarga boy", "romantic"),
            ("Birgalikda rivojlanadigan", "growing_together"),
            ("Erkin, lekin bir-birini qo‘llab-quvvatlaydigan", "supportive_freedom"),
        ],
    ),
    _qn(
        "future_vision",
        "female",
        "relationship_expectations",
        "Kelajakdagi munosabatimizni qanday tasavvur qilasan?",
        [
            ("Tinch va barqaror", "calm_stable"),
            ("Romantik va hislarga boy", "romantic"),
            ("Birgalikda rivojlanadigan", "growing_together"),
            ("Erkin, lekin bir-birini qo‘llab-quvvatlaydigan", "supportive_freedom"),
        ],
    ),
    _qn(
        "inner_needs",
        "male",
        "emotional_needs",
        "Seni chin dildan tushunishlari uchun inson nimani bilishi kerak?",
        [
            ("Men hislarimni har doim ham ayta olmasligimni", "hard_to_express"),
            ("Ba’zan menga ko‘proq e’tibor kerakligini", "needs_attention"),
            ("Men kuchli ko‘rinsam ham, ichimda xavotirlarim borligini", "hidden_worry"),
            ("Menga so‘zlardan ko‘ra munosabat va harakat muhimligini", "actions_over_words"),
        ],
    ),
    _qn(
        "inner_needs",
        "female",
        "emotional_needs",
        "Seni chin dildan tushunishim uchun nimani bilishim kerak?",
        [
            ("Hislaringni har doim ham ochiq ayta olmasligingni", "hard_to_express"),
            ("Ba’zan senga ham ko‘proq e’tibor kerakligini", "needs_attention"),
            ("Kuchli ko‘rinsang ham, ichingda xavotirlaring borligini", "hidden_worry"),
            ("Senga so‘zlardan ko‘ra munosabat va harakat muhimligini", "actions_over_words"),
        ],
    ),
]
