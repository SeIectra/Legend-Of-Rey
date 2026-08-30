"""Bolum 8 - "Ates Basi". `docs/yapi.md` B8 baglayici.

    B8 - Ates Basi. **Dovus yok.** Ates, iki siluet. Rey kolyeyi
    cevirir, Ardo omzundaki yarayi sarar, Rey uzanir.
    Mekanik: **Yanki Rezonansi** burada ogrenilir - Ardo ona sesi silah
    olarak kullanmayi gosterir. Yanki ilk kez Ardo hakkinda fisildar,
    Rey rahatsiz olur.

`docs/gdd.md` 134: *"8 | Ates Basi ★nefes | Rezonans ogrenilir, Yanki
ilk kez Ardo hakkinda konusur"*.

## Nefes bolumu - **tek dusman yok**

`docs/yapi.md` 114: *"Nefes bolumleri (B4, B8, B12) sifir dovus kodu
ister. Sadece dekor + yurumek + panel."* Bolum 4 (Kayit Odasi) ayni
sekilde kuruldu.

Bu bir eksiklik degil bir **ritim**: yedi bolumdur dovusen oyuncu
burada duruyor, oturuyor, bir sey ogreniyor ve bir sey duyuyor.
`docs/gdd.md` 41: nefes bolumleri Yanki kademesini de geri veriyor.

## Dort oda, dort is

    1  ATES      ★ ara sahne: yara sarma, kolye, uzanan el
    2  OGRENME   ilk kristal - rezonans **ogretiliyor**, engel yok
    3  GECIT     kristal yolu kapatiyor + ULASILAMAZ mandal
    4  CIKIS     Yanki ilk kez Ardo hakkinda konusur

Oda 2 ile 3 arasindaki fark `docs/gdd.md` 9'un kurali: once ogret,
sonra sina. Oda 2'de kristali kirmasan da gecebilirsin (ogrenme
serbest); Oda 3'te kirmadan gecemezsin.

## Isaretler

    R oyuncu   $ sandik   X cikis

Kristal, mandal ve ates isaret DEGIL - asagidaki sabitler. Ayni gerekce
Bolum 4'un gunlugu, 5'in vanalari, 6'nin plakalari ve 7'nin catlagi
icin de yazildi: yalniz bir bolumde gecen harf ortak sozlugu sisirir.
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


# --- Oda 1: Ates. Ara sahne burada aciliyor. -----------------------------
# Kucuk ve kapali: bir dinlenme yeri buyuk olmamali. Genis bir oda
# "burada bir sey olacak" der; dar bir oda "burada duruluyor" der.
_ROOM1_WIDTH = 20
_r1 = _room(_ROOM1_WIDTH, left_wall=True)
stamp(_r1, 3, 13, "R")
ROOM_1 = finish(_r1)

FIRE_COLUMN = 11                 # atesin yeri - ara sahne ve isik icin

# --- Oda 2: Ogrenme. Ilk kristal. ----------------------------------------
# Kristal yolu **kapatmiyor** - tavana yakin bir cikintida duruyor.
# Kirmasan da gecebilirsin. `docs/gdd.md` 9: once ogret, sonra sina;
# ogretme odasinda basarisizligin bedeli olmamali.
_ROOM2_WIDTH = 24
_r2 = _room(_ROOM2_WIDTH)
stamp(_r2, 18, 13, "$")          # kristali kiran oyuncuya odul
ROOM_2 = finish(_r2)

TEACH_CRYSTAL = (12, 6)          # havada, ulasilmaz - yalnizca ses varir

# --- Oda 3: Gecit. Kristal + ulasilamaz mandal. -------------------------
# Iki engel, iki ders:
#   * kristal yolu kapatiyor      -> sesi yakina gonder
#   * mandal duvarin ARDINDA      -> sesi ulasamadigin yere gonder
#
# Ikincisi mekanigin asil noktasi: elle yapilabilen bir sey icin sese
# gerek olmazdi.
_ROOM3_WIDTH = 26
_r3 = _room(_ROOM3_WIDTH)
# Kristal sutunu: zeminden tavana kadar degil, gecisi kapatacak kadar.
block(_r3, 9, 9, FLOOR_TOP - 4, FLOOR_TOP - 1)
# Mandal odasi: sagda, duvarla ayrilmis kucuk bir bosluk.
block(_r3, 17, 17, CEILING, FLOOR_TOP - 1)
ROOM_3 = finish(_r3)

GATE_CRYSTAL = (9, FLOOR_TOP - 4)        # yolu kapatan kristal (4 tile)
GATE_CRYSTAL_HEIGHT = 4
LATCH_TILE = (20, FLOOR_TOP - 5)         # duvarin ardinda, ulasilamaz
LATCH_DOOR_COLUMN = 17                   # mandal acilinca bosalan sutun
LATCH_DOOR_ROWS = range(CEILING, FLOOR_TOP - 1)

# --- Oda 4: Cikis. Yanki konusuyor. --------------------------------------
_ROOM4_WIDTH = 18
_r4 = _room(_ROOM4_WIDTH, right_wall=True)
stamp(_r4, 14, 13, "X")
ROOM_4 = finish(_r4)


ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4)
LEVEL = parse("bolum-08-ates-basi", ROWS)

ROOM_STARTS = (
    ("ates", 0),
    ("ogrenme", _ROOM1_WIDTH),
    ("gecit", _ROOM1_WIDTH + _ROOM2_WIDTH),
    ("cikis", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH),
)

_R1 = ROOM_STARTS[0][1]
_R2 = ROOM_STARTS[1][1]
_R3 = ROOM_STARTS[2][1]

FIRE_TILE = (_R1 + FIRE_COLUMN, FLOOR_TOP - 1)
TEACH_CRYSTAL_TILE = (_R2 + TEACH_CRYSTAL[0], TEACH_CRYSTAL[1])
GATE_CRYSTAL_TILE = (_R3 + GATE_CRYSTAL[0], GATE_CRYSTAL[1])
LATCH_TILE_ABS = (_R3 + LATCH_TILE[0], LATCH_TILE[1])
LATCH_DOOR_TILE = _R3 + LATCH_DOOR_COLUMN

CHEST_GOLD = 60
SECRETS_TOTAL = 1
