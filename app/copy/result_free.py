WARMTH_SUMMARIES = [
    (
        85,
        "Sizda allaqachon mustahkam poydevor bor. Ko‘p vaziyatlarda bir-biringizni yaxshi tushunasiz — bu juda qimmatli.",
    ),
    (
        70,
        "Sizlar yaqin yo‘nalishdasiz. Bir nechta mayda farqlar bor — ularni suhbat bilan yumshoq yopish oson va tabiiy.",
    ),
    (
        55,
        "Sizda kuchli nuqtalar bor, bir nechta joyda esa yana yaqinlashish imkoniyati bor. Bu normal — har juftlikda shunday bo‘ladi.",
    ),
    (
        0,
        "Sizlar turlicha o‘ylaysiz — bu yomon emas. Bu sizga bir-biringizni chuqurroq eshitish uchun imkoniyat.",
    ),
]


def warmth_summary(score: int) -> str:
    for threshold, text in WARMTH_SUMMARIES:
        if score >= threshold:
            return text
    return WARMTH_SUMMARIES[-1][1]
