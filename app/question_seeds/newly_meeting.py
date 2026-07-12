from app.question_seeds._helpers import QuestionSeed, _q

STAGE = "newly_meeting"


def _qn(scenario_id, gender_target, dimension, text, options):
    return _q(scenario_id, gender_target, dimension, text, options, stage=STAGE)


NEWLY_MEETING_QUESTIONS: list[QuestionSeed] = [
    _qn(
        "promise_call",
        "female",
        "responsibility_trust",
        (
            "Yigit sizga:\n"
            "«Bugun soat 20:00 da qo‘ng‘iroq qilaman.»\n"
            "dedi.\n"
            "Lekin 21:30 da:\n"
            "«Uzr, ish chiqib qoldi.»\n"
            "deb yozdi.\n"
            "Sizning birinchi fikringiz?"
        ),
        [
            ("Hayotda shunday bo‘lib turadi.", 4),
            ("Oldinroq yozganida yaxshi bo‘lardi.", 3),
            ("Va’dasiga unchalik amal qilmaydigan odam ekan.", 2),
            ("Ishonchim biroz kamayadi.", 1),
        ],
    ),
    _qn(
        "promise_call",
        "male",
        "responsibility_trust",
        (
            "Siz qizga:\n"
            "«Bugun soat 20:00 da qo‘ng‘iroq qilaman.»\n"
            "dedingiz.\n"
            "Lekin ish chiqib qoldi.\n"
            "Siz nima qilasiz?"
        ),
        [
            ("Darrov xabar beraman.", 4),
            ("Ishim tugagach qo‘ng‘iroq qilaman.", 3),
            ("Keyin uzr so‘rayman.", 2),
            ("Buni katta muammo deb hisoblamayman.", 1),
        ],
    ),
    _qn(
        "small_attention",
        "female",
        "attention",
        (
            "Bir hafta oldin siz:\n"
            "«Qahvani yoqtirmayman.»\n"
            "degandingiz.\n"
            "Keyingi uchrashuvda u buni eslab qoldi.\n"
            "Sizning reaksiyangiz?"
        ),
        [
            ("Mayda narsalarni eslab qolishi menga juda yoqadi.", 4),
            ("Yoqimli holat.", 3),
            ("Hayron bo‘laman.", 2),
            ("Bunga unchalik ahamiyat bermayman.", 1),
        ],
    ),
    _qn(
        "small_attention",
        "male",
        "attention",
        (
            "Bir hafta oldin qiz:\n"
            "«Qahvani yoqtirmayman.»\n"
            "degandi.\n"
            "Keyingi uchrashuvda ichimlik buyurtma qilayotganda siz..."
        ),
        [
            ("Buni eslab, unga choy taklif qilaman.", 4),
            ("Esimda bo‘lsa, albatta e’tibor beraman.", 3),
            ("O‘sha paytda o‘zidan so‘rayman.", 2),
            ("Bunday mayda narsalarni eslab yurmayman.", 1),
        ],
    ),
    _qn(
        "phone_attention",
        "female",
        "respect_attention",
        "Suhbat davomida u telefoniga tez-tez qarab turdi.\nSiz...",
        [
            ("Balki muhim ishidir deb o‘ylayman.", 4),
            ("Kim yozayotganiga qiziqaman.", 3),
            ("O‘zimni noqulay his qilaman.", 2),
            ("Keyin bu haqda gaplashaman.", 1),
        ],
    ),
    _qn(
        "phone_attention",
        "male",
        "respect_attention",
        "Suhbat paytida telefoningizga muhim xabar keldi.\nSiz...",
        [
            ("Telefonni chetga qo‘yaman.", 4),
            ("Uzr so‘rab, tez javob beraman.", 3),
            ("Vaqti-vaqti bilan tekshirib turaman.", 2),
            ("Telefonimga qarashni muammo deb bilmayman.", 1),
        ],
    ),
    _qn(
        "being_late",
        "female",
        "responsibility",
        "Yigit uchrashuvga 30 daqiqa kech qoldi.\nSiz...",
        [
            ("Tushunaman, bo‘lib turadi.", 4),
            ("Sababini bilishni xohlayman.", 3),
            ("Xafa bo‘laman.", 2),
            ("Bu menga hurmatsizlikdek tuyuladi.", 1),
        ],
    ),
    _qn(
        "being_late",
        "male",
        "responsibility",
        "Uchrashuvga kech qolayotganingizni bildingiz.\nSiz...",
        [
            ("Oldindan yozaman.", 4),
            ("Yetib borgach tushuntiraman.", 3),
            ("Faqat uzr so‘rayman.", 2),
            ("20-30 daqiqa katta muammo emas deb o‘ylayman.", 1),
        ],
    ),
    _qn(
        "friends_plan",
        "female",
        "priority_time",
        (
            "Bugun uchrashishga kelishgansiz.\n"
            "Yigit:\n"
            "«Do‘stlarim chaqirib qoldi. Bugun bora olmayman.»\n"
            "dedi.\n"
            "Siz..."
        ),
        [
            ("Tushunaman.", 4),
            ("Oldindan aytgani yaxshi bo‘lardi.", 3),
            ("Men bilan uchrashuvni muhim deb bilmaganiga xafa bo‘laman.", 2),
            ("Endi tashabbusni undan kutaman.", 1),
        ],
    ),
    _qn(
        "friends_plan",
        "male",
        "priority_time",
        "Do‘stlaringiz sizni chaqirdi.\nLekin qiz bilan ham uchrashuv rejangiz bor.\nSiz...",
        [
            ("Avval qiz bilan kelishilgan rejani bajaraman.", 4),
            ("Vaziyatni tushuntirib, boshqa vaqt taklif qilaman.", 3),
            ("Do‘stlarim bilan ketaman, keyin unga yozaman.", 2),
            ("Kim birinchi chaqirgan bo‘lsa, o‘sha reja qoladi.", 1),
        ],
    ),
    _qn(
        "first_bill",
        "female",
        "money_values",
        (
            "Uchrashuv oxirida hisob keldi.\n"
            "Yigit:\n"
            "«Hisobni ikkalamiz bo‘lib to‘laylik.»\n"
            "dedi.\n"
            "Siz..."
        ),
        [
            ("Men uchun bu normal.", 4),
            ("Vaziyatga qarayman.", 3),
            ("Birinchi uchrashuvda yigit to‘lagani ma’qul.", 2),
            ("Bu meni noqulay qiladi.", 1),
        ],
    ),
    _qn(
        "first_bill",
        "male",
        "money_values",
        "Uchrashuv oxirida hisob keldi.\nSiz odatda...",
        [
            ("O‘zim to‘layman.", 4),
            ("Vaziyatga qarayman.", 3),
            ("Bo‘lib to‘lashni taklif qilaman.", 2),
            ("Qizning fikrini so‘rayman.", 1),
        ],
    ),
    _qn(
        "different_opinion",
        "female",
        "conflict_style",
        "Suhbatda fikringiz bir xil chiqmadi.\nYigitning qaysi munosabati sizga ma’qul?",
        [
            ("Tinch gaplashsa.", 4),
            ("Hazil bilan vaziyatni yumshatsa.", 3),
            ("Ovozini ko‘tarmasdan o‘z fikrida tursa.", 2),
            ("Jim bo‘lib qolsa.", 1),
        ],
    ),
    _qn(
        "different_opinion",
        "male",
        "conflict_style",
        "Suhbatda qiz bilan fikringiz bir xil chiqmadi.\nSiz...",
        [
            ("Tinch gaplashaman.", 4),
            ("Biroz tanaffus qilib, keyin gaplashaman.", 3),
            ("O‘z fikrimni himoya qilaman.", 2),
            ("Mavzuni yopib qo‘yaman.", 1),
        ],
    ),
    _qn(
        "mother_call",
        "female",
        "family_values",
        "Uchrashuv vaqtida uning onasi qo‘ng‘iroq qildi.\nSiz...",
        [
            ("Bemalol javob bersin.", 4),
            ("Mendan uzr so‘rab javob bersa yaxshi.", 3),
            ("Keyinroq javob bersa ham bo‘lardi.", 2),
            ("Bu holat menga yoqmaydi.", 1),
        ],
    ),
    _qn(
        "mother_call",
        "male",
        "family_values",
        "Uchrashuv vaqtida onangiz qo‘ng‘iroq qildi.\nSiz...",
        [
            ("Qizdan uzr so‘rab, qisqa javob beraman.", 4),
            ("Keyinroq qayta qo‘ng‘iroq qilaman.", 3),
            ("Tez javob berib olaman.", 2),
            ("Vaziyatga qarayman.", 1),
        ],
    ),
    _qn(
        "private_secret",
        "female",
        "trust_privacy",
        (
            "Siz unga faqat ikkalangiz biladigan gapni aytdingiz.\n"
            "Keyinroq dugonangiz ham shu gapni bilishini bildingiz.\n"
            "Siz..."
        ),
        [
            ("Darrov undan so‘rayman.", 4),
            ("Avval aniqlayman.", 3),
            ("Ishonchim kamayadi.", 2),
            ("Juda xafa bo‘laman.", 1),
        ],
    ),
    _qn(
        "private_secret",
        "male",
        "trust_privacy",
        "Qiz sizga shaxsiy gapini aytdi.\nSiz...",
        [
            ("Hech kimga aytmayman.", 4),
            ("Juda yaqin odamimga aytishim mumkin deb o‘ylayman.", 2),
            ("Muhim bo‘lmasa aytib yuborishim mumkin.", 1),
            ("Sir saqlashga harakat qilaman.", 3),
        ],
    ),
    _qn(
        "future_talk",
        "female",
        "future_vision",
        (
            "Yigit sizdan:\n"
            "«Kelajak haqida qanday o‘ylaysiz?»\n"
            "deb so‘radi.\n"
            "Siz..."
        ),
        [
            ("Bu savol menga yoqadi.", 4),
            ("Hali bu mavzu uchun ertaroq deb o‘ylayman.", 3),
            ("Keyinroq gaplashgan ma’qul.", 2),
            ("Bunday savol meni noqulay qiladi.", 1),
        ],
    ),
    _qn(
        "future_talk",
        "male",
        "future_vision",
        "Siz qizdan kelajak haqida so‘ramoqchisiz.\nSiz...",
        [
            ("Bu muhim mavzu deb hisoblayman.", 4),
            ("Bir oz tanigach so‘rayman.", 3),
            ("Hozircha erta deb o‘ylayman.", 2),
            ("Umuman shoshilmayman.", 1),
        ],
    ),
    _qn(
        "interrupting",
        "female",
        "respect_listening",
        "Suhbatdoshingiz o‘z fikrini aytayotganida siz odatda…",
        [
            ("Gapini tugatgunicha diqqat bilan tinglayman.", 4),
            ("Tinglab, keyin aniqlashtiruvchi savol beraman.", 3),
            ("Fikrimni aytish uchun tezroq suhbatga qo‘shilaman.", 2),
            ("Ko‘pincha gapini tugatmasidan fikrimni aytib yuboraman.", 1),
        ],
    ),
    _qn(
        "interrupting",
        "male",
        "respect_listening",
        "Suhbatdoshingiz o‘z fikrini aytayotganida siz odatda…",
        [
            ("Gapini tugatgunicha diqqat bilan tinglayman.", 4),
            ("Tinglab, keyin aniqlashtiruvchi savol beraman.", 3),
            ("Fikrimni aytish uchun tezroq suhbatga qo‘shilaman.", 2),
            ("Ko‘pincha gapini tugatmasidan fikrimni aytib yuboraman.", 1),
        ],
    ),
    _qn(
        "initiative",
        "female",
        "communication_initiative",
        (
            "So‘nggi paytlarda suhbatni ko‘pincha tanishayotgan insoningiz "
            "boshlab bermoqda. Siz odatda…"
        ),
        [
            ("Men ham muntazam ravishda birinchi bo‘lib yozaman.", 4),
            ("Ba’zan o‘zim yozaman, ba’zan undan xabar kutaman.", 3),
            ("Ko‘pincha u yozishini kutaman, keyin javob beraman.", 2),
            ("O‘zim birinchi yozishga deyarli ehtiyoj sezmayman.", 1),
        ],
    ),
    _qn(
        "initiative",
        "male",
        "communication_initiative",
        (
            "So‘nggi paytlarda suhbatni ko‘pincha tanishayotgan insoningiz "
            "boshlab bermoqda. Siz odatda…"
        ),
        [
            ("Men ham muntazam ravishda birinchi bo‘lib yozaman.", 4),
            ("Ba’zan o‘zim yozaman, ba’zan undan xabar kutaman.", 3),
            ("Ko‘pincha u yozishini kutaman, keyin javob beraman.", 2),
            ("O‘zim birinchi yozishga deyarli ehtiyoj sezmayman.", 1),
        ],
    ),
]
