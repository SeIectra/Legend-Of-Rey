"""Bolum 10 - "Ayrilik". `docs/yapi.md` B10 baglayici.

    B10 - Ayrilik. Yol ikiye ayrilir. Yalniz devam. Yanki yukselir,
    yorum yapmaya baslar, **ilk kez yanlis bilgi verip seni tuzaga
    sokar.**
    Mekanik: Zorluk sicramasi. Yanki'ya guvenmeme dersi.

`docs/gdd.md` 136: *"10 | Ayrilik | Yalnizlik, **Yanki ilk kez yalan
soyler**"*.

## Yalan bir SECIM olmali

Bir ara sahnede "Yanki yalan soyledi" demek kolay ve degersiz olurdu.
Burada yalan oynanisin icinde:

    Oda 3'te iki yol var. Yanki ustteki icin *"buradan"* diyor.
    Ustteki tuzak. Alttaki guvenli - ama oraya inmek icin Bolum 9'da
    ogrendigin firlatmayi... kullanamiyorsun, cunku YALNIZSIN.

Alt yol bunun yerine **kendi becerini** istiyor: dar bir cikinti
dizisi, ziplama zarfinin sinirinda. Yani ders sudur - Yanki'nin kolay
yolu bedelli, kendi yolun zahmetli.

Iki yol da devam ediyor. Tuzak **oldurmuyor**, pahali: hasar ve bir
dovus. Bir oyuncuyu "yanlis" bir secim yuzunden bolum basina
gondermek dersi ogretmez, yalnizca kizdirir.

## Zorluk sicramasi

`docs/yapi.md` B10: *"Zorluk sicramasi."* Yoldas yok ve **Mizrakli**
burada tanitiliyor (Katman 2'nin ikinci uyesi). Iki yeni sey ayni
anda: yalnizlik ve uzun menzil.

## Isaretler

    R oyuncu   k Kalkanli   m Mizrakli   s Suruklenen   $ sandik   X cikis
"""
from __future__ import annotations

from src.world.level import join_rooms, parse

ROOM_HEIGHT = 16
FLOOR_TOP = 14
CEILING = 3


def _room(width: int, ceiling: int = CEILING, floor: int = FLOOR_TOP,
          left_wall: bool = False, right_wall: bool = False) -> list[list[str]]:
    rows: list[list[str]] = []
    for y in range(ROOM_HEIGHT):
        if y < ceiling or y >= floor:
            row = ["#"] * width
        else:
            row = ["."] * width
            if left_wall:
                row[0] = "#"
            if right_wall:
                row[-1] = "#"
        rows.append(row)
    return rows


def stamp(rows: list[list[str]], x: int, y: int, char: str) -> None:
    rows[y][x] = char


def block(rows: list[list[str]], x0: int, x1: int, y0: int, y1: int) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            rows[y][x] = "#"


def carve(rows: list[list[str]], x0: int, x1: int, y0: int, y1: int) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            rows[y][x] = "."


def finish(rows: list[list[str]]) -> list[str]:
    return ["".join(row) for row in rows]


# --- Oda 1: Ayrilik. Yoldas gidiyor. -------------------------------------
# Dovus yok: ayrilik bir an, bir sinav degil. Odanin sonunda yol ikiye
# ayriliyor ve ara sahne orada aciliyor.
_ROOM1_WIDTH = 22
_r1 = _room(_ROOM1_WIDTH, left_wall=True)
stamp(_r1, 3, 13, "R")
ROOM_1 = finish(_r1)

SPLIT_COLUMN = 17            # yollarin ayrildigi yer - ara sahne burada

# --- Oda 2: Yalniz. Zorluk sicramasi. ------------------------------------
# Iki Mizrakli + bir Kalkanli. Yoldas yokken ilk gercek sinav; Mizrakli
# da burada taniticiliyor, yani iki yeni sey ayni anda: yalnizlik ve
# uzun menzil.
#
# Odanin genis olmasi sart (32 tile): Mizrakli'nin mekanigi mesafe ve
# dar bir odada mesafe diye bir sey yok.
_ROOM2_WIDTH = 32
_r2 = _room(_ROOM2_WIDTH)
stamp(_r2, 9, 13, "m")
stamp(_r2, 20, 13, "k")
stamp(_r2, 27, 13, "m")
ROOM_2 = finish(_r2)

# --- Oda 3: Catal. ★ Yalan burada. ---------------------------------------
# Iki yol:
#   UST   - Yanki'nin gosterdigi. Genis, kolay, duz. **Tuzak.**
#   ALT   - dar cikintilar, ziplama zarfinin sinirinda. Guvenli.
#
# Ustteki bilerek **davetkar**: genis ve duz. Yanki'nin yalani ancak
# inandirici oldugunda ders olur.
_ROOM3_WIDTH = 30
_r3 = _room(_ROOM3_WIDTH, ceiling=1)

# Iki yolu ayiran orta duvar (satir 8).
block(_r3, 8, _ROOM3_WIDTH - 1, 8, 8)

# **Sag duvar**: alt yolun cikisi yalnizca cikintilardan gecerek
# ulasilan bir delik. Olmasaydi oyuncu zeminden duz yuruyup gecerdi ve
# "catal" diye bir sey kalmazdi - ilk surumde tam olarak oyle oldu.
block(_r3, _ROOM3_WIDTH - 3, _ROOM3_WIDTH - 1, 9, 13)
carve(_r3, _ROOM3_WIDTH - 3, _ROOM3_WIDTH - 1, 10, 11)   # cikis deligi

# Ust yol: duvarin ustunde, **genis ve duz**. Yanki'nin gosterdigi yol
# davetkar olmali, yoksa yalan inandirici olmaz.
carve(_r3, 8, _ROOM3_WIDTH - 1, 2, 7)

# Ust yola cikis: girisin sagindaki basamaklar.
block(_r3, 5, 6, 12, 13)
block(_r3, 7, 7, 10, 13)

# Alt yol: cukur + uzerinde dort cikinti. **Iki gecerli cozum**:
#
#   cikintilardan atla  - beceri. Hizli, dovussuz.
#   cukurdan yuru       - dovus. Yavas ama garantili.
#
# Ikisi de zahmetli ve ikisi de gecerli; Kalkanli'nin iki cozumuyle
# ayni ilke (`shieldbearer.py`): oyuncunun kendi cozumunu bulmasi,
# verilen cozumu uygulamasindan iyi hissettiriyor.
#
# Cukurdan cikilabiliyor (2-3 tile) - bir yanlis adim bolumu bastan
# oynatmamali.
carve(_r3, 9, _ROOM3_WIDTH - 4, 12, 13)          # cukur
for column, row in ((11, 11), (15, 12), (19, 11), (23, 12)):
    block(_r3, column, column + 1, row, row)
stamp(_r3, 17, 13, "m")                          # cukurun bekcisi
ROOM_3 = finish(_r3)

UPPER_ROW = 7                # Yanki'nin gosterdigi yol (tuzak)
LOWER_ROW = 13               # kendi yolun
# Tuzak: ust yolun ortasinda zemin cokuyor.
TRAP_COLUMNS = range(16, 22)
TRAP_ROW = 8

# --- Oda 4: Ders. Iki yol birlesiyor. ------------------------------------
# Tuzaktan dusen de, alt yoldan gelen de buraya cikiyor. Yanki burada
# konusuyor - ve **ozur dilemiyor**.
_ROOM4_WIDTH = 24
_r4 = _room(_ROOM4_WIDTH, right_wall=True)
stamp(_r4, 6, 13, "s")
stamp(_r4, 14, 13, "m")
stamp(_r4, 19, 13, "$")
stamp(_r4, 21, 13, "X")
ROOM_4 = finish(_r4)


ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4)
LEVEL = parse("bolum-10-ayrilik", ROWS)

ROOM_STARTS = (
    ("ayrilik", 0),
    ("yalniz", _ROOM1_WIDTH),
    ("catal", _ROOM1_WIDTH + _ROOM2_WIDTH),
    ("ders", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH),
)

_R1 = ROOM_STARTS[0][1]
_R3 = ROOM_STARTS[2][1]

SPLIT_TILE = _R1 + SPLIT_COLUMN
TRAP_TILES = range(_R3 + TRAP_COLUMNS.start, _R3 + TRAP_COLUMNS.stop)
# Yanki'nin isaretledigi nokta - ust yolun girisi.
LURE_TILE = (_R3 + 10, UPPER_ROW)
# Alt yolun ilk cikintisi - "kendi yolun" buradan basliyor.
HONEST_TILE = (_R3 + 11, 12)

CHEST_GOLD = 75
SECRETS_TOTAL = 1
