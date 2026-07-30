"""Yangi turmush qurganlar — juftlik savollari (12 × 2)."""

from app.question_seeds._helpers import QuestionSeed, _q

STAGE = "in_relationship"


def _pair(order: int) -> str:
    return f"newlywed_{order:02d}"


def _qi(
    scenario_id: str,
    gender_target: str,
    dimension: str,
    text: str,
    option_specs: list[tuple[str, str]],
    *,
    question_code: str | None = None,
) -> QuestionSeed:
    return _q(
        scenario_id,
        gender_target,
        dimension,
        text,
        option_specs,
        stage=STAGE,
        question_code=question_code,
    )


def _male(order: int, dimension: str, text: str, option_specs: list[tuple[str, str]]) -> QuestionSeed:
    return _qi(
        _pair(order),
        "male",
        dimension,
        text,
        option_specs,
        question_code=f"newlywed_male_{order:02d}",
    )


IN_RELATIONSHIP_QUESTIONS: list[QuestionSeed] = [
    # --- Female (same pair_key order; texts unchanged for partner flow) ---
    _qi(
        _pair(1),
        "female",
        "emotional_needs",
        "Oilamizda o‘zingni baxtli his qilishing uchun mendan eng ko‘p nimani kutasan?",
        [
            ("Senga vaqt va e’tibor ajratishimni", "time_attention"),
            ("Seni tushunib, tinglashimni", "listening_understanding"),
            ("Mas’uliyatni sen bilan bo‘lishishimni", "shared_responsibility"),
            ("Mehrlimni ochiq ko‘rsatishimni", "open_affection"),
        ],
        question_code="newlywed_female_01",
    ),
    _qi(
        _pair(2),
        "female",
        "emotional_support",
        "Xafa bo‘lganingda men qanday yo‘l tutishimni xohlaysan?",
        [
            ("Avval seni tinchgina tinglashimni", "quiet_listening"),
            ("Nima bo‘lganini so‘rab, yechim izlashimni", "problem_solving"),
            ("Senga mehr ko‘rsatib, yoningda qolishimni", "affection_presence"),
            ("Tinchlanishing uchun biroz vaqt berishimni", "give_space"),
        ],
        question_code="newlywed_female_02",
    ),
    _qi(
        _pair(3),
        "female",
        "financial_trust",
        "Oilaviy xarajatlar haqida qanday yo‘l tutishimizni istaysan?",
        [
            ("Barcha daromad va xarajatlarni ochiq gaplashishimizni", "open_finances"),
            ("Asosiy xarajatlarni birga rejalashtirishimizni", "plan_expenses"),
            ("Har birimizda shaxsiy pul ham bo‘lishini", "personal_money"),
            ("Moliyaviy mas’uliyatni asosan sen boshqarishingni", "partner_manages"),
        ],
        question_code="newlywed_female_03",
    ),
    _qi(
        _pair(4),
        "female",
        "financial_trust",
        "Turmush o‘rtog‘ing sen bilan maslahatlashmasdan katta xarajat qilsa, qanday munosabat bildirasiz?",
        [
            ("Avval sababini xotirjam so‘raysan", "ask_calmly"),
            ("Buni noto‘g‘ri deb, darhol e’tiroz bildirasiz", "object_immediately"),
            ("Bir marta bo‘lsa, jiddiy muammo qilmaysiz", "one_time_ok"),
            ("Keyingi safar uchun birgalikda qoida belgilaysiz", "set_rule_together"),
        ],
        question_code="newlywed_female_04",
    ),
    _qi(
        _pair(5),
        "female",
        "responsibility",
        "Uy ishlarini qanday tashkil qilishimiz senga to‘g‘ri tuyuladi?",
        [
            ("Vazifalarni oldindan bo‘lib olishimiz", "divided_tasks"),
            ("Kimning vaqti bo‘lsa, o‘sha bajarishi", "flexible_time"),
            ("Bir-birimizga aytmasdan ham yordam berishimiz", "spontaneous_help"),
            ("Har kim o‘ziga qulay bo‘lgan ishni bajarishi", "preferred_tasks"),
        ],
        question_code="newlywed_female_05",
    ),
    _qi(
        _pair(6),
        "female",
        "responsibility",
        "Uy ishlarini bajarishga ulgurmasang, turmush o‘rtog‘ing qanday yo‘l tutishini kutasan?",
        [
            ("Imkon bo‘lsa, yordam bersin", "help_if_can"),
            ("Nima sabab bo‘lganini so‘rasin", "ask_why"),
            ("Bu sening mas’uliyating deb hisoblasin", "your_duty"),
            ("Ishlarni keyinroq birga bajarishni taklif qilsin", "postpone_together"),
        ],
        question_code="newlywed_female_06",
    ),
    _qi(
        _pair(7),
        "female",
        "boundaries",
        "Oilangizdagi kelishmovchiliklarni ota-onaga aytish haqida qanday fikrdasan?",
        [
            ("Odatda er-xotin o‘zi hal qilishi kerak", "couple_resolves"),
            ("Faqat jiddiy vaziyatda ota-onadan maslahat olish mumkin", "serious_only"),
            ("Ota-onadan hech narsani yashirmaslik kerak", "no_secrets"),
            ("Kimga aytilishi vaziyatga bog‘liq", "depends_situation"),
        ],
        question_code="newlywed_female_07",
    ),
    _qi(
        _pair(8),
        "female",
        "boundaries",
        "Turmush o‘rtog‘ing bilan onangiz yoki qarindoshlaringiz o‘rtasida tushunmovchilik bo‘lsa, qanday yo‘l tutasiz?",
        [
            ("Ikkala tomonni ham xotirjam tinglaysiz", "listen_both"),
            ("Avvalo turmush o‘rtog‘ingizni himoya qilasiz", "protect_spouse"),
            ("Avvalo ota-onangizning fikrini hurmat qilasiz", "respect_parents"),
            ("Ularni o‘zaro gaplashtirib, murosaga keltirasiz", "mediate"),
        ],
        question_code="newlywed_female_08",
    ),
    _qi(
        _pair(9),
        "female",
        "conflict_style",
        "Turmush o‘rtog‘ingiz bilan kelishmovchilik yuz bersa, odatda nima qilasiz?",
        [
            ("Darhol gaplashib, muammoni hal qilishga harakat qilasiz", "talk_now"),
            ("Avval tinchlanish uchun biroz vaqt olasiz", "cool_down"),
            ("U birinchi bo‘lib gap boshlashini kutasiz", "wait_partner"),
            ("Mojaro kattalashmasligi uchun mavzuni yopasiz", "drop_topic"),
        ],
        question_code="newlywed_female_09",
    ),
    _qi(
        _pair(10),
        "female",
        "conflict_style",
        "Turmush o‘rtog‘ingiz sizni xafa qilganini aytsa, birinchi munosabatingiz qanday bo‘ladi?",
        [
            ("Uni bo‘lmasdan tinglaysiz", "listen_first"),
            ("Nima uchun bunday qilganingizni tushuntirasiz", "explain_why"),
            ("Siz ham nimadan xafa bo‘lganingizni aytasiz", "share_hurt"),
            ("Vaziyat tinchgach gaplashishni taklif qilasiz", "talk_when_calm"),
        ],
        question_code="newlywed_female_10",
    ),
    _qi(
        _pair(11),
        "female",
        "future_expectations",
        "Oilaviy kelajak uchun reja tuzishda eng muhim narsa nima?",
        [
            ("Er-xotinning maqsadlarini birgalikda kelishib olish", "align_goals"),
            ("Moliyaviy barqarorlikka erishish", "financial_stability"),
            ("Uy va farzand masalasini oldindan rejalashtirish", "home_children_plan"),
            ("Vaziyatga qarab yashash, ortiqcha reja qilmaslik", "flexible_life"),
        ],
        question_code="newlywed_female_11",
    ),
    _qi(
        _pair(12),
        "female",
        "future_expectations",
        "Ishingiz yoki daromadingiz sabab oilaga kamroq vaqt ajratayotganingizni sezsangiz, nima qilasiz?",
        [
            ("Turmush o‘rtog‘ingiz bilan ochiq gaplashasiz", "open_talk"),
            ("Bo‘sh kunlarda buning o‘rnini to‘ldirishga harakat qilasiz", "make_up_time"),
            ("Oilangiz ishlayotganingizni tushunishini kutasiz", "expect_understanding"),
            ("Ish va oilaga ajratiladigan vaqtni qayta rejalashtirasiz", "rebalance_time"),
        ],
        question_code="newlywed_female_12",
    ),
    # --- Male (Yangi turmush qurganlar — respondent erkak) ---
    _male(
        1,
        "attention_and_affection",
        "Ishdan charchab uyga kelganingizda, turmush o‘rtog‘ingizdan eng ko‘p nimani kutasiz?",
        [
            ("Meni iliq kutib olib, holimni so‘rashini", "warm_welcome"),
            ("Biroz tinch qolishimga imkon berishini", "quiet_rest"),
            ("Ovqat yoki boshqa amaliy g‘amxo‘rlik ko‘rsatishini", "practical_care"),
            ("Yonimda o‘tirib, kunim qanday o‘tganini tinglashini", "listen_about_day"),
        ],
    ),
    _male(
        2,
        "attention_and_affection",
        "Turmush o‘rtog‘ingiz sizga mehrini qanday ko‘rsatsa, buni ko‘proq his qilasiz?",
        [
            ("Menga iliq gaplar aytsa", "warm_words"),
            ("Men uchun foydali biror ish qilsa", "helpful_act"),
            ("Men bilan ko‘proq vaqt o‘tkazsa", "quality_time"),
            ("Meni quchoqlab, yaqinlik ko‘rsatsa", "physical_affection"),
        ],
    ),
    _male(
        3,
        "money_and_expenses",
        "Oiladagi katta xarajatlar qanday hal qilinishi kerak deb o‘ylaysiz?",
        [
            ("Er-xotin oldindan maslahatlashib hal qilishi kerak", "decide_together"),
            ("Asosan pul topayotgan tomon qaror qilishi kerak", "earner_decides"),
            ("Har kim o‘z pulini o‘zi boshqarishi kerak", "separate_money"),
            ("Vaziyatga qarab, kim yaxshi tushunsa, o‘sha qaror qilishi kerak", "situational"),
        ],
    ),
    _male(
        4,
        "money_and_expenses",
        "Turmush o‘rtog‘ingiz siz bilan maslahatlashmasdan katta xarajat qilsa, qanday munosabat bildirasiz?",
        [
            ("Avval sababini xotirjam so‘rayman", "ask_calmly"),
            ("Buni noto‘g‘ri deb, darhol e’tiroz bildiraman", "object_immediately"),
            ("Bir marta bo‘lsa, jiddiy muammo qilmayman", "one_time_ok"),
            ("Keyingi safar uchun birgalikda qoida belgilayman", "set_rule_together"),
        ],
    ),
    _male(
        5,
        "household_responsibility",
        "Uy ishlari er-xotin o‘rtasida qanday taqsimlanishi kerak?",
        [
            ("Ikkalasi ham imkoniyatiga qarab bajarishi kerak", "shared_by_ability"),
            ("Har kimning doimiy vazifasi bo‘lishi kerak", "fixed_roles"),
            ("Uy ishlarining asosiy qismi ayolning vazifasi", "traditional_split"),
            ("Kim bo‘sh bo‘lsa, o‘sha bajarishi kerak", "whoever_free"),
        ],
    ),
    _male(
        6,
        "household_responsibility",
        "Turmush o‘rtog‘ingiz uy ishlarini bajarishga ulgurmasa, siz qanday yo‘l tutasiz?",
        [
            ("Imkonim bo‘lsa, yordam beraman", "help_if_can"),
            ("Nima sabab bo‘lganini so‘rayman", "ask_why"),
            ("Bu uning mas’uliyati deb hisoblayman", "their_duty"),
            ("Ishlarni keyinroq birga bajarishni taklif qilaman", "postpone_together"),
        ],
    ),
    _male(
        7,
        "parents_and_relatives",
        "Oilangizdagi kelishmovchiliklarni ota-onaga aytish haqida qanday fikrdasiz?",
        [
            ("Odatda er-xotin o‘zi hal qilishi kerak", "couple_resolves"),
            ("Faqat jiddiy vaziyatda ota-onadan maslahat olish mumkin", "serious_only"),
            ("Ota-onadan hech narsani yashirmaslik kerak", "no_secrets"),
            ("Kimga aytilishi vaziyatga bog‘liq", "depends_situation"),
        ],
    ),
    _male(
        8,
        "parents_and_relatives",
        "Turmush o‘rtog‘ingiz bilan onangiz yoki qarindoshlaringiz o‘rtasida tushunmovchilik bo‘lsa, qanday yo‘l tutasiz?",
        [
            ("Ikkala tomonni ham xotirjam tinglayman", "listen_both"),
            ("Avvalo turmush o‘rtog‘imni himoya qilaman", "protect_spouse"),
            ("Avvalo ota-onamning fikrini hurmat qilaman", "respect_parents"),
            ("Ularni o‘zaro gaplashtirib, murosaga keltiraman", "mediate"),
        ],
    ),
    _male(
        9,
        "conflict_resolution",
        "Turmush o‘rtog‘ingiz bilan kelishmovchilik yuz bersa, odatda nima qilasiz?",
        [
            ("Darhol gaplashib, muammoni hal qilishga harakat qilaman", "talk_now"),
            ("Avval tinchlanish uchun biroz vaqt olaman", "cool_down"),
            ("U birinchi bo‘lib gap boshlashini kutaman", "wait_partner"),
            ("Mojaro kattalashmasligi uchun mavzuni yopaman", "drop_topic"),
        ],
    ),
    _male(
        10,
        "conflict_resolution",
        "Turmush o‘rtog‘ingiz sizni xafa qilganini aytsa, birinchi munosabatingiz qanday bo‘ladi?",
        [
            ("Uni bo‘lmasdan tinglayman", "listen_first"),
            ("Nima uchun bunday qilganimni tushuntiraman", "explain_why"),
            ("Men ham nimadan xafa bo‘lganimni aytaman", "share_hurt"),
            ("Vaziyat tinchgach gaplashishni taklif qilaman", "talk_when_calm"),
        ],
    ),
    _male(
        11,
        "future_plans",
        "Oilaviy kelajak uchun reja tuzishda eng muhim narsa nima?",
        [
            ("Er-xotinning maqsadlarini birgalikda kelishib olish", "align_goals"),
            ("Moliyaviy barqarorlikka erishish", "financial_stability"),
            ("Uy va farzand masalasini oldindan rejalashtirish", "home_children_plan"),
            ("Vaziyatga qarab yashash, ortiqcha reja qilmaslik", "flexible_life"),
        ],
    ),
    _male(
        12,
        "future_plans",
        "Ishingiz yoki daromadingiz sabab oilaga kamroq vaqt ajratayotganingizni sezsangiz, nima qilasiz?",
        [
            ("Turmush o‘rtog‘im bilan ochiq gaplashaman", "open_talk"),
            ("Bo‘sh kunlarda buning o‘rnini to‘ldirishga harakat qilaman", "make_up_time"),
            ("Oilam uchun ishlayotganimni tushunishini kutaman", "expect_understanding"),
            ("Ish va oilaga ajratiladigan vaqtni qayta rejalashtiraman", "rebalance_time"),
        ],
    ),
]
