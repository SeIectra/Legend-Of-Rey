"""Bolum 11 - "Ayna Salonu". `docs/yapi.md` B11 baglayici.

    ★B11 - Ayna Salonu. Yalnizsin. Golge yaratiklar sadece isikta olur.
    Bulmaca: Aynalari cevirerek isini yaratiklara yonlendir. **Yanki
    sana yalan soyluyor olabilir** - hangi aynanin dogru oldugunu
    kendin bulmalisin.

`docs/gdd.md` 137: *"11 | Ayna Salonu | Isik bulmacasi, Yanki'ya
guvenememe"*.

## Bolum 10'un dersi burada SINANIYOR

B10 yalani ogretti; B11 onunla oynamayi istiyor. Fark su: orada yalan
tek bir secimdi, burada **surekli** - Yanki bulmaca boyunca yorum
yapiyor ve yorumlarinin bir kismi yanlis.

## Bulmaca zinciri

    kaynak (2,5) --saga--> A(10,5)  asagi
                           B(10,12) saga  --> golge yaratiklari
                           C(24,12) yukari --> alici (24,4) -> kapi

Dogru yapilandirma: A="\\", B="\\", C="/".
Baslangic:          A="/",  B="\\", C="\\".

Yani oyuncunun **A ve C**'yi cevirmesi gerekiyor; B zaten dogru.
Yanki'nin yalani tam olarak B: *"ortadakini cevir"* diyor. Dogru olani
bozmaya davet ediyor - bir yalan icin en zarif bicim, cunku
sonrasinda oyuncu "peki hangisi dogruydu" diye butun zinciri yeniden
dusunmek zorunda kaliyor.

## Golge yaratiklari Bolum 3'ten geliyor

`ShadowShambler` zaten yazilmisti ve `scene.light.in_light()` soruyor.
Isin `LightState`'e kaynak yazdigi icin **hicbir sey eklemeye gerek
kalmadi** - dogru sinir Bolum 3'te cizilmis.

## Isaretler

    R oyuncu   g Golge Suruklenen   m Mizrakli   $ sandik   X cikis

Ayna, kaynak ve alici isaret DEGIL - asagidaki sabitler.
"""
from __future__ import annotations

from src.systems.beam import BACKSLASH, RIGHT, SLASH
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


# --- Oda 1: Giris. Kural OGRETILIYOR. ------------------------------------
# Bir golge yaratigi ve **hicbir isik**. Oyuncu vuruyor, hicbir sey
# olmuyor. Ders bir metinle degil, kilicin bosa gitmesiyle veriliyor -
# `shieldbearer.py`'nin ayni ilkesi.
#
# Yaratik da oyuncuyu oldurmuyor (Bolum 3'te tanistilar): tehdit degil
# **bilmece**.
_ROOM1_WIDTH = 20
_r1 = _room(_ROOM1_WIDTH, left_wall=True)
stamp(_r1, 3, 13, "R")
stamp(_r1, 13, 13, "g")
ROOM_1 = finish(_r1)

# --- Oda 2: Ogrenme. Tek ayna, tek yaratik. ------------------------------
# Zincir yok: kaynak, bir ayna, bir yaratik. Oyuncu mekanigi baski
# olmadan cozuyor. `docs/gdd.md` 9: once ogret, sonra sina.
_ROOM2_WIDTH = 22
_r2 = _room(_ROOM2_WIDTH)
stamp(_r2, 15, 13, "g")
ROOM_2 = finish(_r2)

TEACH_EMITTER = (2, 6)
TEACH_MIRROR = (11, 6)       # "/" ise yukari, "\\" ise asagi (dogru olan)

# --- Oda 3: Salon. ★ Zincir + yalan. -------------------------------------
# Genis ve yuksek: uc aynali bir zincirin okunmasi icin yer gerek.
_ROOM3_WIDTH = 30
_r3 = _room(_ROOM3_WIDTH, ceiling=2)
stamp(_r3, 15, 13, "g")
stamp(_r3, 20, 13, "g")
stamp(_r3, 26, 13, "m")      # Mizrakli: bulmacayi baski altinda coz
ROOM_3 = finish(_r3)

HALL_EMITTER = (2, 5)
# (tile_x, tile_y, baslangic_durumu, dogru_durum)
HALL_MIRRORS = (
    (10, 5, SLASH, BACKSLASH),
    (10, 12, BACKSLASH, BACKSLASH),     # ZATEN dogru - Yanki'nin yalani bu
    (24, 12, BACKSLASH, SLASH),
)
HALL_RECEIVER = (24, 4)
# Yanki hangi aynayi isaretliyor: ortadaki (indeks 1) - dogru olani.
LIE_INDEX = 1

# Alici isini alinca acilan kapi.
HALL_DOOR_COLUMN = _ROOM3_WIDTH - 2
HALL_DOOR_ROWS = range(CEILING, FLOOR_TOP)

# --- Oda 4: Cikis. -------------------------------------------------------
_ROOM4_WIDTH = 16
_r4 = _room(_ROOM4_WIDTH, right_wall=True)
stamp(_r4, 6, 13, "$")
stamp(_r4, 12, 13, "X")
ROOM_4 = finish(_r4)


ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4)
LEVEL = parse("bolum-11-ayna-salonu", ROWS)

ROOM_STARTS = (
    ("giris", 0),
    ("ogrenme", _ROOM1_WIDTH),
    ("salon", _ROOM1_WIDTH + _ROOM2_WIDTH),
    ("cikis", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH),
)

_R2 = ROOM_STARTS[1][1]
_R3 = ROOM_STARTS[2][1]

TEACH_EMITTER_TILE = (_R2 + TEACH_EMITTER[0], TEACH_EMITTER[1])
TEACH_MIRROR_TILE = (_R2 + TEACH_MIRROR[0], TEACH_MIRROR[1])
HALL_EMITTER_TILE = (_R3 + HALL_EMITTER[0], HALL_EMITTER[1])
HALL_MIRROR_TILES = tuple(
    (_R3 + x, y, start, correct) for x, y, start, correct in HALL_MIRRORS)
HALL_RECEIVER_TILE = (_R3 + HALL_RECEIVER[0], HALL_RECEIVER[1])
HALL_DOOR_TILE = _R3 + HALL_DOOR_COLUMN

BEAM_DIRECTION = RIGHT
CHEST_GOLD = 80
SECRETS_TOTAL = 1
