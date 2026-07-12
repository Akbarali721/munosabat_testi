from app.question_seeds._helpers import QuestionSeed, _q

STAGE = "in_relationship"


def _qi(scenario_id, gender_target, dimension, text, options):
    return _q(scenario_id, gender_target, dimension, text, options, stage=STAGE)


IN_RELATIONSHIP_QUESTIONS: list[QuestionSeed] = [
    _qi(
        "weekend_plan",
        "female",
        "priority_time",
        (
            "Dam olish kuni sevgan insoningiz bilan film ko‘rishni "
            "oldindan kelishgansiz.\n"
            "Shu kuni do‘stlaringiz ham anchadan beri rejalashtirgan "
            "uchrashuvga chaqirdi."
        ),
        [
            ("Oldindan kelishilgan rejani saqlab, sevgan insonim bilan vaqt o‘tkazaman.", 4),
            ("Vaziyatni ochiq tushuntirib, ikkalamizga mos boshqa vaqtni kelishaman.", 3),
            ("Do‘stlarim bilan boraman va bu haqda keyinroq aytaman.", 2),
            ("Qaysi reja menga qiziqroq bo‘lsa, o‘shani tanlayman.", 1),
        ],
    ),
    _qi(
        "weekend_plan",
        "male",
        "priority_time",
        (
            "Dam olish kuni sevgan insoningiz bilan film ko‘rishni "
            "oldindan kelishgansiz.\n"
            "Shu kuni do‘stlaringiz ham anchadan beri rejalashtirgan "
            "uchrashuvga chaqirdi."
        ),
        [
            ("Oldindan kelishilgan rejani saqlab, sevgan insonim bilan vaqt o‘tkazaman.", 4),
            ("Vaziyatni ochiq tushuntirib, ikkalamizga mos boshqa vaqtni kelishaman.", 3),
            ("Do‘stlarim bilan boraman va bu haqda keyinroq aytaman.", 2),
            ("Qaysi reja menga qiziqroq bo‘lsa, o‘shani tanlayman.", 1),
        ],
    ),
    _qi(
        "bad_mood",
        "female",
        "attention",
        (
            "Kunning oxirida kayfiyatingiz tushib, uyingizga qaytdingiz.\n"
            "Sevgan insoningiz sizdagi o‘zgarishni sezib, nima bo‘lganini so‘radi.\n"
            "Siz esa hozir bu haqda gaplashishga tayyor emassiz."
        ),
        [
            (
                "Hozir gaplashishga tayyor emasligimni muloyim aytib, "
                "keyinroq tushuntirishimni bildiraman.",
                4,
            ),
            ("Biroz tinchlangach, nima bo‘lganini ochiq aytib beraman.", 3),
            ("Hech narsa bo‘lmaganini aytib, o‘zimni undan uzoq tutaman.", 2),
            ("U qayta-qayta so‘raganidan asabiylashib, keskin javob beraman.", 1),
        ],
    ),
    _qi(
        "bad_mood",
        "male",
        "attention",
        (
            "Kunning oxirida kayfiyatingiz tushib, uyingizga qaytdingiz.\n"
            "Sevgan insoningiz sizdagi o‘zgarishni sezib, nima bo‘lganini so‘radi.\n"
            "Siz esa hozir bu haqda gaplashishga tayyor emassiz."
        ),
        [
            (
                "Hozir gaplashishga tayyor emasligimni muloyim aytib, "
                "keyinroq tushuntirishimni bildiraman.",
                4,
            ),
            ("Biroz tinchlangach, nima bo‘lganini ochiq aytib beraman.", 3),
            ("Hech narsa bo‘lmaganini aytib, o‘zimni undan uzoq tutaman.", 2),
            ("U qayta-qayta so‘raganidan asabiylashib, keskin javob beraman.", 1),
        ],
    ),
    _qi(
        "social_media",
        "female",
        "trust_privacy",
        (
            "Qarama-qarshi jinsdagi eski tanishingiz sizga ijtimoiy tarmoq "
            "orqali yozdi.\n"
            "Sevgan insoningiz telefondagi xabarni tasodifan ko‘rib, "
            "bu suhbatdan noqulay bo‘lganini aytdi."
        ),
        [
            (
                "Yozishma nima haqida ekanini ochiq tushuntirib, "
                "uning xavotirini tinglayman.",
                4,
            ),
            (
                "Bu oddiy suhbat ekanini tushuntirib, kelajakda bunday "
                "holatlarda bir-birimizga qanday chegara qo‘yishimizni kelishaman.",
                3,
            ),
            (
                "Hech qanday yomon niyat yo‘qligini aytib, "
                "uning xavotirini ortiqcha deb hisoblayman.",
                2,
            ),
            (
                "Telefonim shaxsiy ekanini aytib, yozishmalarimni "
                "tushuntirishga majbur emasman deb o‘ylayman.",
                1,
            ),
        ],
    ),
    _qi(
        "social_media",
        "male",
        "trust_privacy",
        (
            "Qarama-qarshi jinsdagi eski tanishingiz sizga ijtimoiy tarmoq "
            "orqali yozdi.\n"
            "Sevgan insoningiz telefondagi xabarni tasodifan ko‘rib, "
            "bu suhbatdan noqulay bo‘lganini aytdi."
        ),
        [
            (
                "Yozishma nima haqida ekanini ochiq tushuntirib, "
                "uning xavotirini tinglayman.",
                4,
            ),
            (
                "Bu oddiy suhbat ekanini tushuntirib, kelajakda bunday "
                "holatlarda bir-birimizga qanday chegara qo‘yishimizni kelishaman.",
                3,
            ),
            (
                "Hech qanday yomon niyat yo‘qligini aytib, "
                "uning xavotirini ortiqcha deb hisoblayman.",
                2,
            ),
            (
                "Telefonim shaxsiy ekanini aytib, yozishmalarimni "
                "tushuntirishga majbur emasman deb o‘ylayman.",
                1,
            ),
        ],
    ),
    _qi(
        "money_talk",
        "female",
        "money_values",
        (
            "Siz o‘zingiz uchun ancha qimmat narsa sotib olmoqchisiz.\n"
            "Bu qaror sizning byudjetingizga ta’sir qilishi mumkin, lekin "
            "bu haqda sevgan insoningiz bilan hali gaplashmagansiz."
        ),
        [
            ("Avval bu xarid nega muhimligini aytib, uning fikrini so‘rayman.", 4),
            (
                "Xarid qilishdan oldin o‘zim uchun ham, munosabatimiz uchun "
                "ham to‘g‘ri vaqtmi, shuni birga muhokama qilaman.",
                3,
            ),
            ("Avval sotib olib, keyin vaziyatni tushuntiraman.", 2),
            ("Bu mening shaxsiy pulim va qarorim deb hisoblayman.", 1),
        ],
    ),
    _qi(
        "money_talk",
        "male",
        "money_values",
        (
            "Siz o‘zingiz uchun ancha qimmat narsa sotib olmoqchisiz.\n"
            "Bu qaror sizning byudjetingizga ta’sir qilishi mumkin, lekin "
            "bu haqda sevgan insoningiz bilan hali gaplashmagansiz."
        ),
        [
            ("Avval bu xarid nega muhimligini aytib, uning fikrini so‘rayman.", 4),
            (
                "Xarid qilishdan oldin o‘zim uchun ham, munosabatimiz uchun "
                "ham to‘g‘ri vaqtmi, shuni birga muhokama qilaman.",
                3,
            ),
            ("Avval sotib olib, keyin vaziyatni tushuntiraman.", 2),
            ("Bu mening shaxsiy pulim va qarorim deb hisoblayman.", 1),
        ],
    ),
    _qi(
        "family_visit",
        "female",
        "family_values",
        (
            "Munosabatingiz jiddiylashib boryapti.\n"
            "Sevgan insoningiz sizni yaqinlari bilan tanishtirmoqchi, "
            "lekin siz hali bunga tayyor emassiz."
        ),
        [
            (
                "Nega hozir tayyor emasligimni ochiq tushuntirib, "
                "keyinroq aniq vaqt taklif qilaman.",
                4,
            ),
            (
                "U uchun bu muhimligini tushunib, o‘zimdagi xavotirni aytib, "
                "birga qaror qilaman.",
                3,
            ),
            (
                "Uni xafa qilmaslik uchun rozi bo‘laman, "
                "lekin ichimda noqulaylik qoladi.",
                2,
            ),
            ("Bunday tanishtirishga hali erta deb, mavzuni yopaman.", 1),
        ],
    ),
    _qi(
        "family_visit",
        "male",
        "family_values",
        (
            "Munosabatingiz jiddiylashib boryapti.\n"
            "Sevgan insoningiz sizni yaqinlari bilan tanishtirmoqchi, "
            "lekin siz hali bunga tayyor emassiz."
        ),
        [
            (
                "Nega hozir tayyor emasligimni ochiq tushuntirib, "
                "keyinroq aniq vaqt taklif qilaman.",
                4,
            ),
            (
                "U uchun bu muhimligini tushunib, o‘zimdagi xavotirni aytib, "
                "birga qaror qilaman.",
                3,
            ),
            (
                "Uni xafa qilmaslik uchun rozi bo‘laman, "
                "lekin ichimda noqulaylik qoladi.",
                2,
            ),
            ("Bunday tanishtirishga hali erta deb, mavzuni yopaman.", 1),
        ],
    ),
    _qi(
        "compliment",
        "female",
        "attention",
        "Uzoq vaqt maqtov yoki minnatdorchilik eshitmadingiz.\nSiz...",
        [
            ("O‘zimga kerak bo‘lsa, tinch aytyapman.", 4),
            ("Kutaman — u band bo‘lishi mumkin.", 3),
            ("Ichimda biroz xafa bo‘laman.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
    _qi(
        "compliment",
        "male",
        "attention",
        (
            "Sherigingiz siz uchun ko‘p narsa qiladi,\n"
            "lekin uzoq vaqtdan beri minnatdorchilik bildirmadingiz.\n"
            "Siz..."
        ),
        [
            ("Bugundan boshlab e’tibor qarataman.", 4),
            ("Kichik surpriz yoki maqtov aytaman.", 3),
            ("Bu mayda narsa deb o‘ylayman.", 2),
            ("U tushunadi deb bilaman, aytmasam ham.", 1),
        ],
    ),
    _qi(
        "apology",
        "female",
        "conflict_style",
        "Kichik xato uchun sherigingiz uzr so‘radi.\nSiz...",
        [
            ("Qabul qilaman — davom etamiz.", 4),
            ("Uzr yetadi, lekin nima uchun bo‘lganini ham gaplashamiz.", 3),
            ("Hali biroz og‘riq bor.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
    _qi(
        "apology",
        "male",
        "conflict_style",
        "Kichik xato qildingiz — uzr so‘ramoqchisiz.\nSiz...",
        [
            ("Samimiy uzr so‘rayman va nima o‘zgartirishni aytaman.", 4),
            ("Qisqa uzr yetarli deb bilaman.", 3),
            ("Vaqt o‘tsin, o‘zi tushunadi deb o‘ylayman.", 2),
            ("Bu katta xato emas — uzr kerak emas.", 1),
        ],
    ),
    _qi(
        "future_step",
        "female",
        "future_vision",
        (
            "Turmush qurganingizga hali ko‘p bo‘lmagan.\n"
            "{spouse_label_cap} kechqurun siz bilan birga vaqt o‘tkazishni xohlaydi, "
            "siz esa kun oxirida biroz yolg‘iz qolib dam olishga ehtiyoj sezasiz."
        ),
        [
            (
                "Hozir biroz dam olishim kerakligini tushuntirib, "
                "keyin birga vaqt o‘tkazishni taklif qilaman.",
                4,
            ),
            (
                "Uning istagini ham tinglab, ikkalamizga mos "
                "kundalik tartibni kelishib olaman.",
                3,
            ),
            (
                "Hech narsa tushuntirmay, telefonim yoki boshqa "
                "mashg‘ulot bilan band bo‘lib qolaman.",
                2,
            ),
            (
                "Meni o‘zi tushunishi kerak deb o‘ylab, "
                "e’tibor talab qilganidan asabiylashaman.",
                1,
            ),
        ],
    ),
    _qi(
        "future_step",
        "male",
        "future_vision",
        (
            "Turmush qurganingizga hali ko‘p bo‘lmagan.\n"
            "{spouse_label_cap} kechqurun siz bilan birga vaqt o‘tkazishni xohlaydi, "
            "siz esa kun oxirida biroz yolg‘iz qolib dam olishga ehtiyoj sezasiz."
        ),
        [
            (
                "Hozir biroz dam olishim kerakligini tushuntirib, "
                "keyin birga vaqt o‘tkazishni taklif qilaman.",
                4,
            ),
            (
                "Uning istagini ham tinglab, ikkalamizga mos "
                "kundalik tartibni kelishib olaman.",
                3,
            ),
            (
                "Hech narsa tushuntirmay, telefonim yoki boshqa "
                "mashg‘ulot bilan band bo‘lib qolaman.",
                2,
            ),
            (
                "Meni o‘zi tushunishi kerak deb o‘ylab, "
                "e’tibor talab qilganidan asabiylashaman.",
                1,
            ),
        ],
    ),
    _qi(
        "habit_change",
        "female",
        "respect_listening",
        (
            "Siz aytgan kichik odatini (masalan, tartibsizlik)\n"
            "u o‘zgartirmadi.\n"
            "Siz..."
        ),
        [
            ("Yana bir bor muloyim gaplashaman.", 4),
            ("Kuzataman — vaqt kerak bo‘lishi mumkin.", 3),
            ("Biroz charchagan his qilaman.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
    _qi(
        "habit_change",
        "male",
        "respect_listening",
        "Sherigingiz sizdan kichik o‘zgarish so‘radi — siz hali qilmadingiz.\nSiz...",
        [
            ("Eslab, o‘zgartirishga harakat qilaman.", 4),
            ("Band edim — tez orada qilaman.", 3),
            ("Bu unchalik muhim emas deb o‘ylayman.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
    _qi(
        "support_day",
        "female",
        "attention",
        (
            "Qiyin kuningizda sherigingiz qo‘llab-quvvatlash o‘rniga\n"
            "maslahat berdi.\n"
            "Siz..."
        ),
        [
            ("«Hozir faqat eshitish kerak» deb tinch aytaman.", 4),
            ("Ikkalasini ham qadrlayman — lekin tinglash muhimroq.", 3),
            ("Biroz xafa bo‘laman.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
    _qi(
        "support_day",
        "male",
        "attention",
        "Sherigingiz qiyin kun o‘tkazdi — siz yechim taklif qildingiz.\nSiz...",
        [
            ("Avval tinglayman, keyin maslahat beraman.", 4),
            ("Qo‘llab-quvvatlash uchun yonida turaman.", 3),
            ("Muammoni hal qilish yaxshiroq deb o‘ylayman.", 2),
            ("U o‘zi hal qiladi deb bilaman.", 1),
        ],
    ),
    _qi(
        "jealousy_talk",
        "female",
        "trust_privacy",
        "Qiziquv yoki revnak haqida gap ochildi.\nSiz...",
        [
            ("Ochiq va tinch gaplashaman.", 4),
            ("His-tuyg‘ularimni aytyapman — hukm qilmayman.", 3),
            ("Bu mavzuni yoqtirmayman, lekin gap bor.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
    _qi(
        "jealousy_talk",
        "male",
        "trust_privacy",
        "Sherigingiz sizda qiziquv bor-yo‘qligini so‘radi.\nSiz...",
        [
            ("Samimiy va tinch javob beraman.", 4),
            ("Bu normal savol deb qabul qilaman.", 3),
            ("Bu menga yoqmaydi deb o‘ylayman.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
    _qi(
        "quality_time",
        "female",
        "priority_time",
        "Bir hafta «bandman» deb o‘tdi — siz uchun vaqt topilmadi.\nSiz...",
        [
            ("Tushunaman, lekin birga vaqt kerak deb aytaman.", 4),
            ("Kichik uchrashuv taklif qilaman.", 3),
            ("O‘zimga vaqt ajrataman — kutaman.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
    _qi(
        "quality_time",
        "male",
        "priority_time",
        "Bir haftadan beri band edingiz — sherigingiz uchun vaqt kam.\nSiz...",
        [
            ("Bu hafta maxsus vaqt ajrataman.", 4),
            ("Qisqa uchrashuv yoki qo‘ng‘iroq qilaman.", 3),
            ("Ish tugagach ko‘ramiz deb o‘ylayman.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
]
