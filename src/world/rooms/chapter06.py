"""Bolum 6 - "ARDO". Katman 1'in finali. `docs/yapi.md` B6 baglayici.

    B6 - ARDO. Rey kosede sikisir, uc yaratik. Golge yukaridan duser,
    ucunu bicer. Bakisma, soru isareti balonu.
    Mekanik: Ilk team-up dovusu + agirlik plakalari (ikisi ayri plakada
    durmali - beraberlik mekanige giriyor).

`docs/gdd.md` 10: *"6 | ARDO | Havali giris, ilk team-up, **BOSS 1**"*.

## Dort oda, dort is

    1  KOSE        oyuncu sikisir - yoldas gelir (sinematik)
    2  ILK BERABER birlikte dovus; yoldas ne yaptigini gosterir
    3  PLAKA ODASI bulmaca OGRETILIR - dovussuz, sakin
    4  ARENA       BOSS 1; plakalar burada SINAV oluyor

`docs/gdd.md` 9'un kurali: *"yeni mekanik + eski mekanik = yeni
bulmaca"*. Oda 3 plakayi sakin bir yerde ogretiyor, Oda 4 onu dovusun
ortasina koyuyor. Ogret, sonra sina - ayni yerde ikisi birden olmaz.

## Yoldas kim?

`docs/gdd.md` 3, kanon: *"Secmedigin, ara sahnelerde havali girisi yapan
taraf olur."* Yani Rey oynuyorsan Ardo geliyor, Ardo oynuyorsan Rey.
Tek kaynak: `companion.other_character()`.

## Isaretler

    R oyuncu   s Suruklenen   t Tirmanan   b Sismek   $ sandik   X cikis

Plakalar, kapi sutunu ve boss dogum yeri isaret DEGIL - asagidaki
sabitler. `level.MARKERS`'a yalnizca bu bolumde gecen harfler eklemek
ortak sozlugu sisirirdi (ayni gerekce Bolum 4'un gunlugu ve Bolum 5'in
vanalari icin de yazildi).
"""
from __future__ import annotations

from src.config import TILE_SIZE
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


# --- Oda 1: Kose. Oyuncu sikisir. ----------------------------------------
# **Cikmaz sokak, bilerek.** Sag ucu duvar: oyuncu kosede, uc yaratik
# onunde. `docs/yapi.md`: *"Rey kosede sikisir, uc yaratik."* Kacacak yer
# olsaydi sahne calismazdi - sikismanin GERCEK olmasi gerekiyor.
#
# Duvar sinematik bitince aciliyor (`chapter06.py` `_open_corner`): yoldas
# geldiginde yol da aciliyor, yani kurtarilmanin somut bir karsiligi var.
_r1 = _room(26, left_wall=True, right_wall=True)
stamp(_r1, 20, 13, "R")
stamp(_r1, 14, 13, "s")
stamp(_r1, 16, 13, "s")
stamp(_r1, 11, 13, "b")
ROOM_1 = finish(_r1)

CORNER_WALL_COLUMN = 25          # sinematik bitince aciliyor
CORNER_WALL_ROWS = range(CEILING, FLOOR_TOP)

# --- Oda 2: Ilk Beraber. Yoldas ne yaptigini gosterir. -------------------
# Dusman sayisi bilerek fazla (5): oyuncu **tek basina zorlanacagi** bir
# kalabalikla karsilasmali ki yoldasin varligi bir sayi degil bir HIS
# olsun. Yoldas dusmani temizlemiyor, mesgul ediyor (`companion.py`).
_r2 = _room(30)
for column in (6, 9, 18, 22):
    stamp(_r2, column, 13, "s")
stamp(_r2, 14, 4, "t")           # tavandan biri - Tirmanan hatirlatmasi
ROOM_2 = finish(_r2)

# --- Oda 3: Plaka Odasi. Bulmaca OGRETILIYOR - dovus yok. ---------------
# Sakin bir oda: iki plaka, arada bir kapi. Dusman yok ki oyuncu mekanigi
# baski altinda degil rahatca cozsun. `docs/gdd.md` 9: once ogret.
#
# Plakalar **birbirinden uzak** (8 tile): tek kisinin ikisine birden
# basmasi fiziksel olarak imkansiz olmali, yoksa bulmaca "kos ve bas"a
# duser ve beraberlik anlamsizlasir.
_ROOM3_WIDTH = 26
_r3 = _room(_ROOM3_WIDTH)
stamp(_r3, 6, 13, "$")
ROOM_3 = finish(_r3)

TEACH_PLATE_A = (10, FLOOR_TOP)
TEACH_PLATE_B = (18, FLOOR_TOP)
TEACH_GATE_COLUMN = 24
TEACH_GATE_ROWS = range(CEILING, FLOOR_TOP)

# --- Oda 4: Arena. BOSS 1 + plakalar SINAV. ------------------------------
# Genis (36 tile): boss'un radyal patlamasindan kacacak yer olmali, ve
# oyuncunun plakalar arasinda kosacagi mesafe gercek bir bedel olmali.
#
# Tavan yuksek (ceiling 2): boss tavana tirmanip dusuyor (Faz 1), o
# hareket icin dikey alan gerek.
_ROOM4_WIDTH = 36
_r4 = _room(_ROOM4_WIDTH, ceiling=2, right_wall=True)
stamp(_r4, 32, 13, "X")
ROOM_4 = finish(_r4)

BOSS_SPAWN_TILE = (20, 13)
ARENA_PLATE_A = (5, FLOOR_TOP)
ARENA_PLATE_B = (29, FLOOR_TOP)
# Arenanin GIRISI - boss uyaninca kapaniyor (Bolum 2/3'un dersi:
# boss atlanabilmemeli).
ARENA_DOOR_COLUMN = 1
ARENA_DOOR_ROWS = range(2, FLOOR_TOP)


ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4)
LEVEL = parse("bolum-06-ardo", ROWS)

ROOM_STARTS = (
    ("kose", 0),
    ("ilk_beraber", len(ROOM_1[0])),
    ("plaka_odasi", len(ROOM_1[0]) + len(ROOM_2[0])),
    ("arena", len(ROOM_1[0]) + len(ROOM_2[0]) + _ROOM3_WIDTH),
)

# Sutunlar birlestirilmis haritada kayiyor.
_R1 = ROOM_STARTS[0][1]
_R2 = ROOM_STARTS[1][1]
_R3 = ROOM_STARTS[2][1]
_R4 = ROOM_STARTS[3][1]

CORNER_WALL_TILE = _R1 + CORNER_WALL_COLUMN
TEACH_PLATE_A_TILE = (_R3 + TEACH_PLATE_A[0], TEACH_PLATE_A[1])
TEACH_PLATE_B_TILE = (_R3 + TEACH_PLATE_B[0], TEACH_PLATE_B[1])
TEACH_GATE_TILE = _R3 + TEACH_GATE_COLUMN
ARENA_PLATE_A_TILE = (_R4 + ARENA_PLATE_A[0], ARENA_PLATE_A[1])
ARENA_PLATE_B_TILE = (_R4 + ARENA_PLATE_B[0], ARENA_PLATE_B[1])
ARENA_DOOR_TILE = _R4 + ARENA_DOOR_COLUMN
BOSS_SPAWN = (_R4 + BOSS_SPAWN_TILE[0], BOSS_SPAWN_TILE[1])

BOSS_GOLD = 120
CHEST_GOLD = 45
SECRETS_TOTAL = 1
