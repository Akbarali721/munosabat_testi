"""Copy variants for the free + premium result experience."""

# Score bands: high / mid / low — used with dimension + alignment
STRENGTH_BY_DIMENSION = {
    "conflict_style": {
        "high_similar": (
            "Javoblaringizga ko‘ra, ikkalangiz ham muammo chiqqanda munosabatni "
            "saqlab qoladigan yechim izlashga moyilsiz — bu sizlarning kuchli tomoningiz."
        ),
        "mid_similar": (
            "Muammo chiqqanda ikkalangiz ham munosabatni saqlashga intilasiz. "
            "Bu yaxshi poydevor — ba’zan esa tezroq ochiq gaplashish yanada yordam beradi."
        ),
        "low_similar": (
            "Ikkalangiz ham qiyin vaziyatda bir xil yo‘nalishda harakat qilasiz — "
            "bu farqlarga qaramay mustahkam nuqta."
        ),
        "high_different": (
            "Umuman yaqin ekansiz, lekin mojaro uslubingizda farq bor. "
            "Shunga qaramay, yechim izlashga intilishingiz kuchli tomon."
        ),
        "default": (
            "Javoblaringizga ko‘ra, ikkalangiz ham muammo chiqqanda munosabatni "
            "saqlab qoladigan yechim izlashga moyilsiz."
        ),
    },
    "communication_initiative": {
        "high_similar": (
            "Javoblaringizga ko‘ra, bir-biringiz bilan gaplashishni boshlash va "
            "muloqotni davom ettirish sizlarda kuchli tomon."
        ),
        "mid_similar": (
            "Muloqotda tashabbus ko‘rsatishda fikrlaringiz yaqin — "
            "bu juftlikni birga tutib turadigan kuchli jihat."
        ),
        "default": (
            "Javoblaringizga ko‘ra, bir-biringiz bilan gaplashishni boshlash "
            "sizlarning kuchli yo‘nalishingiz."
        ),
    },
    "attention": {
        "high_similar": (
            "Javoblaringizga ko‘ra, e’tibor va mayda g‘amxo‘rlik sizlar uchun "
            "tabiiy yaqinlik manbai."
        ),
        "default": (
            "Javoblaringizga ko‘ra, e’tibor bildirishi sizlarning kuchli tomoningiz."
        ),
    },
    "trust_privacy": {
        "default": (
            "Javoblaringizga ko‘ra, ishonch va shaxsiy chegaralarni hurmat qilish "
            "sizlarda mustahkam poydevor."
        ),
    },
    "responsibility": {
        "default": (
            "Javoblaringizga ko‘ra, kundalik mas’uliyatni birga ko‘tarish "
            "sizlarning kuchli tomoningiz."
        ),
    },
    "responsibility_trust": {
        "default": (
            "Javoblaringizga ko‘ra, ishonch va mas’uliyat masalasida "
            "bir-biringizga tayanish sizlarda kuchli."
        ),
    },
    "future_vision": {
        "default": (
            "Javoblaringizga ko‘ra, kelajak haqida birga o‘ylash va reja qilish "
            "sizlarda yaqin yo‘nalish."
        ),
    },
    "family_values": {
        "default": (
            "Javoblaringizga ko‘ra, oila va qarindoshlar mavzusida bir-biringizni "
            "tushunishga intilasiz."
        ),
    },
    "money_values": {
        "default": (
            "Javoblaringizga ko‘ra, pul va xarajatlar bo‘yicha ochiq gaplashishga "
            "tayyorlik sizlarda bor."
        ),
    },
    "respect_attention": {
        "default": (
            "Javoblaringizga ko‘ra, hurmat va e’tibor bildirishi sizlarning "
            "kuchli tomoningiz."
        ),
    },
    "respect_listening": {
        "default": (
            "Javoblaringizga ko‘ra, bir-biringizni tinglashga intilish "
            "sizlarda kuchli."
        ),
    },
    "priority_time": {
        "default": (
            "Javoblaringizga ko‘ra, birga vaqt ajratish sizlar uchun "
            "muhim va yaqin yo‘nalish."
        ),
    },
}

STRENGTH_DEFAULT = (
    "Javoblaringizga ko‘ra, bir-biringizni tushunishga intilish "
    "sizlarning asosiy kuchli tomoningiz."
)

STRENGTH_HIGH_ALIGN = (
    "Ko‘p vaziyatlarda fikrlaringiz yaqin — bu juftlik uchun mustahkam "
    "poydevor. Ayniqsa «{area}» yo‘nalishida bir xil yo‘l tutasiz."
)

STRENGTH_MID = (
    "Sizda aniq kuchli nuqta bor: «{area}» bo‘yicha bir-biringizni "
    "yaxshi tushunasiz. Boshqa joylarda esa yumshoq suhbat foydali."
)

STRENGTH_LOW = (
    "Umuman farqlaringiz bo‘lsa-da, «{area}» sizlarni birlashtiradigan "
    "nuqta. Shu yeridan yaqinlashishni boshlash oson."
)

DIFF_BY_DIMENSION = {
    "conflict_style": {
        "high_gap": (
            "Biringiz muammoni darhol gaplashishni xohlaydi, ikkinchingiz esa "
            "avval tinchlanishga ehtiyoj sezadi."
        ),
        "mid_gap": (
            "Mojaro paytida tempingiz biroz farq qiladi — biri tezroq ochiladi, "
            "ikkinchisi biroz vaqt oladi."
        ),
        "small_gap": (
            "Munozara uslubingizda mayda farq bor — lekin ikkalangiz ham "
            "yechimga intilasiz."
        ),
        "default": (
            "Biringiz muammoni darhol gaplashishni xohlaydi, ikkinchingiz esa "
            "avval tinchlanishga ehtiyoj sezadi."
        ),
    },
    "communication_initiative": {
        "default": (
            "Biringiz suhbatni tezroq boshlashga moyil, ikkinchingiz esa "
            "avval ichida tartibga solishni afzal ko‘radi."
        ),
    },
    "attention": {
        "default": (
            "E’tibor bildirishi uslubingizda farq bor — biringiz ochiqroq, "
            "ikkinchingiz esa jimroq yo‘l tutadi."
        ),
    },
    "money_values": {
        "default": (
            "Pul va xarajatlar bo‘yicha ustuvorliklaringiz biroz farq qiladi — "
            "bu ochiq suhbatni talab qiladi."
        ),
    },
    "future_vision": {
        "default": (
            "Kelajak rejalari bo‘yicha tempingiz farq qiladi — biringiz tezroq, "
            "ikkinchingiz ehtiyotkorroq."
        ),
    },
    "family_values": {
        "default": (
            "Oila va qarindoshlar mavzusida qarashlaringiz bir xil emas — "
            "bu yumshoq kelishuvni talab qiladi."
        ),
    },
    "trust_privacy": {
        "default": (
            "Ishonch va shaxsiy chegaralar bo‘yicha kutishlaringiz biroz farq qiladi."
        ),
    },
    "responsibility": {
        "default": (
            "Mas’uliyatni taqsimlash haqidagi kutishlaringizda farq seziladi."
        ),
    },
    "responsibility_trust": {
        "default": (
            "Ishonch va mas’uliyat kutishlaringizda farq bor — "
            "aniq suhbat bu joyda juda foydali."
        ),
    },
    "respect_listening": {
        "default": (
            "Tinglash uslubingizda farq seziladi — biri chuqurroq eshitishni, "
            "ikkinchisi tezroq javob berishni afzal ko‘radi."
        ),
    },
    "respect_attention": {
        "default": (
            "Hurmat va e’tibor bildirishi uslubingiz biroz farq qiladi."
        ),
    },
    "priority_time": {
        "default": (
            "Birga vaqtni qanday o‘tkazish haqidagi kutishlaringizda farq bor."
        ),
    },
}

DIFF_DEFAULT = (
    "Ba’zi vaziyatlarda reaksiyangiz farq qiladi — bu yomon emas, "
    "balki bir-biringizni chuqurroq eshitish uchun imkoniyat."
)

DIFF_SMALL = (
    "Farqlaringiz unchalik katta emas. «{area}» bo‘yicha biroz boshqacha "
    "his qilasiz — bu suhbat uchun yumshoq mavzu."
)

DIFF_HIGH_SCORE = (
    "Umuman yaxshi tushunasiz, lekin «{area}» da qarashlaringiz ajraladi — "
    "shu mavzuni ochiq muhokama qilish yanada yaqinlashtiradi."
)

COMM_HIGH = (
    "Ikkalangiz ham bir-biringizni tushunishga harakat qilasiz va "
    "muloqotni ochiq saqlashga moyilsiz."
)
COMM_MID = (
    "Ikkalangiz ham bir-biringizni tushunishga harakat qilasiz, lekin "
    "ehtiyojlarni har doim ham aniq ifodalamaysiz."
)
COMM_LOW = (
    "Sizlar bir-biringizni tinglashni xohlaysiz, lekin ba’zan suhbat "
    "kechikadi yoki to‘liq ochilmaydi — bu o‘zgarishi mumkin."
)
COMM_SIMILAR = (
    "Muloqotda uslublaringiz o‘xshash — bu sizlarga bir tilni topishni osonlashtiradi."
)
COMM_DIFFERENT = (
    "Muloqot tempingiz farq qiladi: biri tezroq ochiladi, ikkinchisi ehtiyotkorroq. "
    "Ikkalasini hurmat qilish yaqinlashtiradi."
)

TIP_BY_DIMENSION = {
    "conflict_style": (
        "Bugun 10 daqiqa telefonlarni chetga qo‘yib, bir-biringizdan: "
        "«Oxirgi paytda mendan nimani ko‘proq kutyapsan?» deb so‘rang."
    ),
    "attention": (
        "Bugun juftingizga bitta aniq minnatdorchilik ayting — "
        "nima uchun ekanini ham qo‘shib."
    ),
    "communication_initiative": (
        "Bugun suhbatni siz boshlang: «Bugun sen haqingda nima bilishim "
        "mumkin?» deb so‘rang va tinglang."
    ),
    "future_vision": (
        "Bugun 15 daqiqada bitta umumiy maqsadni ayting — "
        "hatto kichik bo‘lsa ham."
    ),
    "money_values": (
        "Bugun bir xarajat haqida tinch gaplashib, ikkalangizga mos "
        "yechim toping."
    ),
    "respect_listening": (
        "Bugun juftingiz gapirganda 2 daqiqa faqat tinglang — "
        "maslahat bermasdan, faqat eshiting."
    ),
    "responsibility": (
        "Bugun bitta kundalik ishni birga bo‘lib oling va "
        "kim nima qilishini oldindan ayting."
    ),
    "priority_time": (
        "Bugun 20 daqiqalik «faqat biz» vaqtini belgilang — "
        "telefonlarsiz."
    ),
    "trust_privacy": (
        "Bugun bir-biringizdan: «Menga ishonchingni nima kuchaytiradi?» "
        "deb so‘rang."
    ),
    "family_values": (
        "Bugun oila mavzusida bitta yumshoq savol bering: "
        "«Bu hafta oila uchun nima muhim?»"
    ),
}

TIP_DEFAULT = (
    "Bugun 10 daqiqa telefonlarni chetga qo‘yib, bir-biringizdan: "
    "«Oxirgi paytda mendan nimani ko‘proq kutyapsan?» deb so‘rang."
)

# Personal style keys inferred from answer weights
STYLE_LABELS = {
    "listening": "tinglash",
    "compromise": "murosaga kelish",
    "practical": "amaliy yechim",
    "responsibility": "mas’uliyat olish",
    "withdrawal": "hissiy chekinish",
    "delay": "muammoni kechiktirish",
    "control": "nazorat qilish",
    "self_justify": "o‘zini oqlash",
    "open_comm": "ochiq muloqot",
    "intimacy": "yaqinlikka ehtiyoj",
}

PERSONAL_COMBOS = {
    ("practical", "responsibility"): (
        "{name}, javoblaringizda muammoga amaliy yechim topish va mas’uliyatni "
        "o‘z zimmangizga olishga moyillik ko‘rinadi. Ba’zan esa hislarni muhokama "
        "qilishdan oldin yechim taklif qilishga shoshilishingiz mumkin."
    ),
    ("responsibility", "practical"): (
        "{name}, javoblaringizda mas’uliyat olish va amaliy yechimga intilish "
        "kuchli. Ba’zan esa avval hislarni eshitish — keyin yechim yanada samarali."
    ),
    ("intimacy", "open_comm"): (
        "{name}, javoblaringizda hissiy yaqinlik va ochiq muloqotga ehtiyoj "
        "kuchliroq ko‘rinadi. Siz uchun faqat yechim emas, avval tinglanish "
        "va tushunilish ham muhim."
    ),
    ("open_comm", "intimacy"): (
        "{name}, javoblaringizda ochiq muloqot va hissiy yaqinlikka ehtiyoj "
        "seziladi. Gaplashish siz uchun yaqinlikning muhim qismi."
    ),
    ("listening", "compromise"): (
        "{name}, javoblaringizda tinglash va murosaga kelishga moyillik "
        "ko‘rinadi. Ba’zan o‘z ehtiyojingizni ham aniq aytish yanada "
        "yaqinlashtiradi."
    ),
    ("compromise", "listening"): (
        "{name}, javoblaringizda murosa va tinglash uslubi kuchli. "
        "Bu munosabatni saqlaydi — o‘zingizni ham ochiq ifodalash esa to‘ldiradi."
    ),
    ("withdrawal", "delay"): (
        "{name}, javoblaringizda qiyin paytda biroz chekinish yoki masalani "
        "keyinga qoldirish moyilligi seziladi. Tinchlanish foydali — keyin "
        "qaytib gaplashish esa yanada yaqinlashtiradi."
    ),
    ("delay", "withdrawal"): (
        "{name}, javoblaringizda ba’zi masalalarni keyinga surish va jim "
        "qolish moyilligi ko‘rinadi. Vaqt foydali — lekin aniq qaytish muhim."
    ),
}

PERSONAL_PRIMARY = {
    "listening": (
        "{name}, javoblaringizda tinglash va tushunishga intilish kuchliroq "
        "ko‘rinadi. Siz uchun avval eshitilish — keyin yechim muhim."
    ),
    "compromise": (
        "{name}, javoblaringizda murosaga kelish va munosabatni saqlash "
        "moyilligi ko‘rinadi. Ba’zan o‘z ehtiyojingizni ham ochiq aytish "
        "yanada yaqinlashtiradi."
    ),
    "practical": (
        "{name}, javoblaringizda muammoga amaliy yechim topishga moyillik "
        "ko‘rinadi. Ba’zan hislarni muhokama qilishdan oldin yechim taklif "
        "qilishga shoshilishingiz mumkin."
    ),
    "responsibility": (
        "{name}, javoblaringizda mas’uliyatni o‘z zimmangizga olishga "
        "moyillik ko‘rinadi. Bu kuchli tomon — lekin ba’zan yukni bo‘lishish "
        "ham muhim."
    ),
    "withdrawal": (
        "{name}, javoblaringizda qiyin paytda biroz chekinish yoki jim "
        "qolish moyilligi seziladi. Tinchlanish foydali — keyin qaytib "
        "gaplashish esa yanada yaqinlashtiradi."
    ),
    "delay": (
        "{name}, javoblaringizda ba’zi masalalarni keyinga qoldirish "
        "moyilligi ko‘rinadi. Vaqt foydali bo‘lishi mumkin — lekin muhim "
        "suhbatni uzoqqa cho‘zmaslik yaxshiroq."
    ),
    "control": (
        "{name}, javoblaringizda vaziyatni o‘zingiz boshqarishga intilish "
        "seziladi. Bu mas’uliyat belgisidir — ba’zan esa juftingizga "
        "ham qaror berish joy ochish yaqinlashtiradi."
    ),
    "self_justify": (
        "{name}, javoblaringizda o‘z pozitsiyangizni himoya qilish "
        "kuchliroq ko‘rinadi. Bu tabiiy — tinglash bilan birga kelganda "
        "yanada samarali."
    ),
    "open_comm": (
        "{name}, javoblaringizda ochiq muloqotga ehtiyoj kuchliroq "
        "ko‘rinadi. Siz uchun gaplashish — yaqinlikning bir qismi."
    ),
    "intimacy": (
        "{name}, javoblaringizda hissiy yaqinlik va e’tiborga ehtiyoj "
        "kuchliroq ko‘rinadi. Siz uchun faqat yechim emas, avval "
        "tinglanish va tushunilish ham muhim."
    ),
}

PERSONAL_SECONDARY = {
    "listening": "Shu bilan birga, tinglash uslubingiz juftlikni yumshoq tutadi.",
    "compromise": "Murosaga tayyorligingiz munosabatni saqlab qolishga yordam beradi.",
    "practical": "Amaliy yondashuvingiz kundalik hayotda foydali.",
    "responsibility": "Mas’uliyatli bo‘lishingiz ishonchni oshiradi.",
    "withdrawal": "Ba’zan jimlik himoya — lekin keyin qaytish muhim.",
    "delay": "Vaqt olish foydali, lekin aniq muddat bilan yaxshiroq.",
    "control": "Nazorat o‘rniga birga qaror qilish yaqinlashtiradi.",
    "self_justify": "O‘zingizni tushuntirish — ochiqlikning bir ko‘rinishi.",
    "open_comm": "Ochiq gapirish istagingiz juftlik uchun qimmatli.",
    "intimacy": "Yaqinlikka ehtiyojingiz munosabatni jonlantiradi.",
}

PREMIUM_TEASER_LINES = [
    "Javoblaringiz asosida 3 ta aniq kuchli jihat tayyorlandi…",
    "Kelishmovchilik boshlanadigan 2 ta nuqta aniqlangan…",
    "Birinchi sherikning munosabat uslubi tahlil qilindi…",
    "Ikkinchi sherikning munosabat uslubi tahlil qilindi…",
    "Aytilmagan ehtiyojlaringiz ochib beriladi…",
    "Sizlarga mos 5 ta shaxsiy tavsiya kutmoqda…",
    "7 kunlik kichik yaqinlashuv rejasi tayyor…",
]

PREMIUM_LEAD = (
    "Ko‘p juftliklar muammoni bilmagani uchun emas, uni qanday gaplashishni "
    "bilmagani uchun uzoqlashadi. To‘liq tahlil sizga suhbatni nimadan "
    "boshlashni va bir-biringizga qanday yaqinlashishni ko‘rsatadi."
)

PREMIUM_SUBLEAD = (
    "Natijani alohida emas, birga o‘qing. Ayrim xulosalar siz ilgari "
    "gaplashmagan mavzuni ochishi mumkin."
)

PREMIUM_BLOCK_TITLES = [
    "Sizlarning 3 ta kuchli jihatingiz",
    "Kelishmovchilik boshlanadigan 2 ta asosiy nuqta",
    "{name_a}ning munosabatdagi uslubi",
    "{name_b}ning munosabatdagi uslubi",
    "Bir-biringizdan kutayotgan, lekin aytmayotgan ehtiyojlaringiz",
    "Sizlar uchun 5 ta shaxsiy tavsiya",
    "7 kunlik kichik yaqinlashuv rejasi",
]

PREMIUM_STRENGTH_TEMPLATES = {
    "aligned": (
        "«{area}» da ikkalangiz ham bir xil yo‘nalishdasiz — "
        "bu juftlikning mustahkam tomoni."
    ),
    "close": (
        "«{area}» bo‘yicha qarashlaringiz yaqin — "
        "kichik farqlar suhbat bilan yumshoq yopiladi."
    ),
    "score_high": (
        "Umuman yaxshi tushunishingiz «{area}» da ham ko‘rinadi — "
        "shu yo‘nalishni saqlab qoling."
    ),
}

PREMIUM_GAP_TEMPLATES = {
    "high": (
        "«{area}» — kelishmovchilik eng ko‘p shu yerda boshlanishi mumkin. "
        "{higher} bu yerda faoliroq, {lower} esa boshqacha yo‘l tutadi."
    ),
    "mid": (
        "«{area}» da tempingiz farq qiladi. "
        "Avval bir-biringizni eshitib, keyin yechim izlash foydali."
    ),
    "soft": (
        "«{area}» bo‘yicha mayda farq bor — "
        "bu yomon emas, balki ochiq suhbat uchun imkoniyat."
    ),
}
