from app.question_seeds._helpers import QuestionSeed, _q

STAGE = "married"

_HOUSEWORK_TEXT_MALE = (
    "Bugun uyda qilinadigan ishlar juda ko‘p. Ayolingiz kun bo‘yi uy ishlari bilan "
    "band bo‘lib, charchagan. Siz ham ishdan charchab keldingiz."
)
_HOUSEWORK_OPTIONS_MALE = [
    ("Charchagan bo‘lsam ham, undan qaysi ishda yordam kerakligini so‘rayman.", 4),
    ("Biroz dam olgach, ishlarni birgalikda tugatishni taklif qilaman.", 3),
    ("Ikkalamiz ham charchaganimiz uchun ishlarni keyinga qoldirishni aytaman.", 2),
    ("Uy ishlarini uning vazifasi deb hisoblab, aralashmayman.", 1),
]

_HOUSEWORK_TEXT_FEMALE = (
    "Bugun uyda qilinadigan ishlar juda ko‘p. Siz kun bo‘yi uy ishlari bilan band "
    "bo‘lib, charchadingiz. Eringiz ham ishdan charchab keldi."
)
_HOUSEWORK_OPTIONS_FEMALE = [
    ("Charchaganimni ochiq aytib, undan aniq bir ishda yordam so‘rayman.", 4),
    ("Biroz dam olgach, ishlarni birgalikda tugatishni taklif qilaman.", 3),
    ("Hech narsa demay, barcha ishlarni o‘zim davom ettiraman.", 2),
    ("U yordam taklif qilmaganidan ranjib, keskin gapiraman.", 1),
]

_PARENTING_TEXT = (
    "Farzandingiz kelishilgan qoidaga amal qilmadi. Siz qattiqroq chora kerak deb "
    "o‘ylaysiz, {spouse_label} esa unga avval tushuntirish kerakligini aytadi."
)
_PARENTING_OPTIONS = [
    (
        "Farzand oldida tortishmay, keyin alohida gaplashib umumiy qarorga kelamiz.",
        4,
    ),
    (
        "Hozircha uning taklifini qabul qilib, keyin bu qoida haqida yana gaplashamiz.",
        3,
    ),
    ("Farzandga o‘zim to‘g‘ri deb bilgan usulda munosabat qilaman.", 2),
    ("Bu masalani turmush o‘rtog‘im hal qilsin deb chetga chiqaman.", 1),
]

_MONEY_BUDGET_TEXT = (
    "Bu oy kutilmagan xarajat chiqdi. {spouse_label_cap} zarur deb hisoblagan bir "
    "narsani hozir sotib olmoqchi. Siz esa pulni tejash kerak deb o‘ylaysiz."
)
_MONEY_BUDGET_OPTIONS = [
    ("Avval nima uchun bu narsa muhimligini so‘rab, birga qaror qilaman.", 4),
    (
        "Hozir pul yetishmasligini tushuntirib, xaridni aniqroq muddatga "
        "qoldirishni taklif qilaman.",
        3,
    ),
    ("Tortishuv chiqmasligi uchun rozi bo‘laman, lekin ichimda ranjib qolaman.", 2),
    ("Pul bo‘yicha oxirgi qarorni men qilaman deb hisoblayman.", 1),
]

_IN_LAWS_TEXT = (
    "Siz turmush o‘rtog‘ingiz bilan alohida yashaysiz. Ota-onangiz yoki yaqin "
    "qarindoshlaringiz bir necha kunga mehmonga kelishni rejalashtirdi. "
    "{spouse_label_cap} hozir bunga to‘liq rozi emas."
)
_IN_LAWS_OPTIONS = [
    ("Avval nima sababdan rozi emasligini tinglab, keyin birga qaror qilaman.", 4),
    (
        "Tashrif muddatini yoki vaqtini o‘zgartirib, ikkalamizga mos yechim "
        "taklif qilaman.",
        3,
    ),
    (
        "Qarindoshlarim xafa bo‘lmasligi uchun turmush o‘rtog‘im rozi bo‘lmasa "
        "ham tashrifni qabul qilaman.",
        2,
    ),
    ("Kelishmovchilik chiqmasligi uchun qarorni turmush o‘rtog‘imga qoldiraman.", 1),
]

_INTIMACY_TEXT = (
    "{spouse_label_cap} oxirgi paytda sizdan yaqinlik va e’tibor "
    "kamayganini his qilayotganini aytdi."
)
_INTIMACY_OPTIONS = [
    ("Nimalar yetishmayotganini so‘rab, uni diqqat bilan tinglayman.", 4),
    (
        "Oxirgi paytdagi bandligimni tushuntirib, unga vaqt ajratish uchun "
        "aniq reja qilaman.",
        3,
    ),
    ("Bu vaqtinchalik holat, o‘z-o‘zidan o‘tib ketadi deb o‘ylayman.", 2),
    (
        "Men ham charchayotganimni aytib, bu gapni ortiqcha talab deb qabul qilaman.",
        1,
    ),
]

_WORK_STRESS_TEXT = (
    "Ishdagi bosim sabab uyga asabiy qaytdingiz va {spouse_dative} "
    "qo‘polroq gapirib yubordingiz."
)
_WORK_STRESS_OPTIONS = [
    (
        "Xato qilganimni tan olib, uzr so‘rayman va nega asabiylashganimni "
        "tushuntiraman.",
        4,
    ),
    ("Avval biroz tinchlanaman, keyin bu holat haqida u bilan gaplashaman.", 3),
    ("Ishdagi bosimni bilganidan keyin meni tushunishi kerak deb o‘ylayman.", 2),
    ("Gapni cho‘zmaslik uchun jim bo‘lib, undan uzoqlashaman.", 1),
]

_OLD_FRIEND_TEXT = (
    "Suhbat davomida qarama-qarshi jinsdagi eski tanishingiz haqida gapirdingiz. "
    "{spouse_label_cap} bundan noqulay bo‘lganini aytdi."
)
_OLD_FRIEND_OPTIONS = [
    (
        "Nima sababdan noqulay bo‘lganini so‘rab, uning hislarini diqqat bilan "
        "tinglayman.",
        4,
    ),
    (
        "U inson bilan munosabatim qandayligini ochiq tushuntirib, shubha "
        "qolmasligiga harakat qilaman.",
        3,
    ),
    (
        "Bunda hech qanday muammo yo‘q deb, uning xavotirini ortiqcha deb "
        "hisoblayman.",
        2,
    ),
    ("Kelishmovchilik chiqmasligi uchun mavzuni yopaman, lekin izoh bermayman.", 1),
]

_ARGUMENT_STYLE_TEXT = (
    "Muhim bir masala ustida tortishib qoldingiz. Jahlingiz chiqib, "
    "{spouse_dative} ovozingizni balandlatdingiz. Shundan keyin u siz bilan "
    "gaplashmay qo‘ydi."
)
_ARGUMENT_STYLE_OPTIONS = [
    (
        "Avval tinchlanib, ovozimni balandlatganim uchun uzr so‘rayman va "
        "suhbatni davom ettirishga harakat qilaman.",
        4,
    ),
    (
        "Unga biroz vaqt beraman, keyin qachon gaplashishga tayyorligini "
        "so‘rayman.",
        3,
    ),
    (
        "Men birinchi bo‘lib gap boshlamayman — o‘zi tinchlangach kelishini "
        "kutaman.",
        2,
    ),
    (
        "Uning sukutidan jahlim chiqib, men ham ataylab gaplashmay qo‘yaman.",
        1,
    ),
]

_SHARED_GOAL_TEXT = (
    "So‘nggi paytda uy-joy, jamg‘arma, farzandlar yoki ish bilan bog‘liq "
    "kelajak rejalaringiz haqida jiddiy gaplashmagansiz. {spouse_label_cap} "
    "bu noaniqlikdan xavotir olayotganini aytdi."
)
_SHARED_GOAL_OPTIONS = [
    (
        "Uning nimalardan xavotir olayotganini tinglab, kelajak rejamizni "
        "birga muhokama qilaman.",
        4,
    ),
    (
        "Hozir amalga oshirishimiz mumkin bo‘lgan bitta maqsadni tanlab, "
        "aniq qadam belgilashni taklif qilaman.",
        3,
    ),
    (
        "Hozir vaziyat noaniq ekanini aytib, bu suhbatni keyinga qoldiraman.",
        2,
    ),
    (
        "Kelajak bo‘yicha o‘z rejam borligini aytib, undan menga ishonishini "
        "kutaman.",
        1,
    ),
]

_DAILY_RITUAL_TEXT = (
    "Oldin siz {spouse_with} kechqurun birga choy ichar yoki qisqa sayrga "
    "chiqardingiz. So‘nggi paytda bandlik sabab bu odat to‘xtab qoldi. "
    "{spouse_label_cap} buni sog‘inganini aytdi."
)
_DAILY_RITUAL_OPTIONS = [
    (
        "Bugunoq vaqt topib, birga choy ichish yoki sayr qilishni taklif qilaman.",
        4,
    ),
    (
        "Hafta davomida ikkalamizga qulay bo‘lgan aniq vaqtni belgilashni "
        "taklif qilaman.",
        3,
    ),
    (
        "Hozir ishlar ko‘pligini aytib, bo‘sh vaqt paydo bo‘lganda qaytamiz "
        "deb o‘ylayman.",
        2,
    ),
    (
        "Bunday kichik odatlar munosabat uchun unchalik muhim emas deb "
        "hisoblayman.",
        1,
    ),
]


def _qm(scenario_id, gender_target, dimension, text, options):
    return _q(scenario_id, gender_target, dimension, text, options, stage=STAGE)


MARRIED_QUESTIONS: list[QuestionSeed] = [
    _qm("housework", "female", "responsibility", _HOUSEWORK_TEXT_FEMALE, _HOUSEWORK_OPTIONS_FEMALE),
    _qm("housework", "male", "responsibility", _HOUSEWORK_TEXT_MALE, _HOUSEWORK_OPTIONS_MALE),
    _qm("parenting", "female", "family_values", _PARENTING_TEXT, _PARENTING_OPTIONS),
    _qm("parenting", "male", "family_values", _PARENTING_TEXT, _PARENTING_OPTIONS),
    _qm("money_budget", "female", "money_values", _MONEY_BUDGET_TEXT, _MONEY_BUDGET_OPTIONS),
    _qm("money_budget", "male", "money_values", _MONEY_BUDGET_TEXT, _MONEY_BUDGET_OPTIONS),
    _qm("in_laws", "female", "family_values", _IN_LAWS_TEXT, _IN_LAWS_OPTIONS),
    _qm("in_laws", "male", "family_values", _IN_LAWS_TEXT, _IN_LAWS_OPTIONS),
    _qm("intimacy", "female", "attention", _INTIMACY_TEXT, _INTIMACY_OPTIONS),
    _qm("intimacy", "male", "attention", _INTIMACY_TEXT, _INTIMACY_OPTIONS),
    _qm(
        "work_stress",
        "female",
        "respect_attention",
        _WORK_STRESS_TEXT,
        _WORK_STRESS_OPTIONS,
    ),
    _qm(
        "work_stress",
        "male",
        "respect_attention",
        _WORK_STRESS_TEXT,
        _WORK_STRESS_OPTIONS,
    ),
    _qm("old_friend", "female", "trust_privacy", _OLD_FRIEND_TEXT, _OLD_FRIEND_OPTIONS),
    _qm("old_friend", "male", "trust_privacy", _OLD_FRIEND_TEXT, _OLD_FRIEND_OPTIONS),
    _qm(
        "surprise_gift",
        "female",
        "attention",
        "Uzoq vaqtdan beri kichik surpriz yoki e’tibor bo‘lmadi.\nSiz...",
        [
            ("O‘zimga kerak bo‘lsa, tinch aytyapman.", 4),
            ("Kutaman — band bo‘lishi mumkin.", 3),
            ("Ichimda biroz xafa bo‘laman.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
    _qm(
        "surprise_gift",
        "male",
        "attention",
        (
            "Uzoq vaqtdan beri {spouse_label}ga kichik surpriz\n"
            "yoki e’tibor bildirmadingiz.\n"
            "Siz..."
        ),
        [
            ("Bugun kichik e’tibor yoki surpriz qilaman.", 4),
            ("Hafta oxiriga maxsus reja qilaman.", 3),
            ("Bu mayda narsa deb o‘ylayman.", 2),
            ("U tushunadi deb bilaman.", 1),
        ],
    ),
    _qm(
        "argument_style",
        "female",
        "conflict_style",
        _ARGUMENT_STYLE_TEXT,
        _ARGUMENT_STYLE_OPTIONS,
    ),
    _qm(
        "argument_style",
        "male",
        "conflict_style",
        _ARGUMENT_STYLE_TEXT,
        _ARGUMENT_STYLE_OPTIONS,
    ),
    _qm(
        "shared_goal",
        "female",
        "future_vision",
        _SHARED_GOAL_TEXT,
        _SHARED_GOAL_OPTIONS,
    ),
    _qm(
        "shared_goal",
        "male",
        "future_vision",
        _SHARED_GOAL_TEXT,
        _SHARED_GOAL_OPTIONS,
    ),
    _qm(
        "daily_ritual",
        "female",
        "communication_initiative",
        _DAILY_RITUAL_TEXT,
        _DAILY_RITUAL_OPTIONS,
    ),
    _qm(
        "daily_ritual",
        "male",
        "communication_initiative",
        _DAILY_RITUAL_TEXT,
        _DAILY_RITUAL_OPTIONS,
    ),
    _qm(
        "thank_you",
        "female",
        "respect_attention",
        "Kundalik kichik yordam uchun «rahmat» kam eshitiladi.\nSiz...",
        [
            ("Kerak bo‘lsa, tinch aytaman — minnatdorchilik muhim.", 4),
            ("Qilayotgan ishlarini qadrlayman deb aytaman.", 3),
            ("Ichimda biroz xafa bo‘laman.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
    _qm(
        "thank_you",
        "male",
        "respect_attention",
        (
            "{spouse_label.capitalize()} kundalik kichik ishlar qiladi,\n"
            "lekin siz kamdan-kam «rahmat» deysiz.\n"
            "Siz..."
        ),
        [
            ("Bugundan boshlab ko‘proq minnatdorlik bildiraman.", 4),
            ("Kichik «rahmat» aytishni odat qilaman.", 3),
            ("Bu kundalik ish — aytish shart emas deb o‘ylayman.", 2),
            ("Hozircha bilmayman.", 1),
        ],
    ),
]
