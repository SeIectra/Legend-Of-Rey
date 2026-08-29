"""Bolum 5 - "Sular". `docs/yapi.md` B5 baglayici.

    B5 - Sular. Su basmis mahzen. Vana mekanigi.
    Bulmaca: Suyu yukselt -> yuzerek ust kata gec -> suyu indir ->
    alttaki kapiyi ac. Klasik ama calisir.

## Bulmaca dort adim, her adim BIR sey ogretiyor

    1. Vana 1 (zeminde)   suyu YUKSELTIR   -> "vana suyu degistiriyor"
    2. Yuzerek ust kata   yeni erisim      -> "su bir merdiven"
    3. Vana 2 (ust katta) suyu INDIRIR     -> "su geri de alinabilir"
    4. Savak acilir       alt gecit        -> "seviyenin kendisi anahtar"

Ucuncu adim kritik: oyuncu suyu indirirken **kendisi de asagi iniyor**.
Yani cozumun bedeli konumunu kaybetmek. Bu istemsiz degil - bulmacanin
bir karar olmasini saglayan sey bu.

## Savak: su yuksekken KAPALI

Alt gecidi bir samandirali savak kapatiyor (`src/scenes/chapter05.py`
`_update_sluice`). Su yukselince samandira kalkiyor ve kapak iniyor;
su cekilince kapak aciliyor. Mekanik bir sebep - "kapi suyun altinda
kaliyor" demek bogulma sistemi gerektirirdi, oyunda yok.

Bu ayni zamanda kilidi de kuruyor: oyuncu suyu indirmeden cikamiyor,
yani Vana 2'ye ulasmak ZORUNDA. Bulmacanin atlanamamasi buradan geliyor
(Bolum 2/3'te boss atlanabiliyordu - o ders `keydoor.py`'ye yazildi,
burada tasarima gomulu).

## Isaretler

    R oyuncu   $ sandik   X cikis   s Suruklenen

Su seviyesi, savak ve ust kat isaret DEGIL - asagidaki sabitler.
`level.MARKERS`'a butun bolumler icin harf eklemek ortak sozlugu
yalnizca bu bolum icin sisirirdi (Bolum 4'te ayni gerekce).

## Dusman: tek Suruklenen, SUDAN UZAK

`docs/gdd.md` 7 Katman 1 hala gecerli (B1-B6). Ama su bir **bulmaca**,
dovus alani degil: tek dusman ilk odada, suyun hic ulasmadigi yerde.
Suda dovusmek hem okunmaz (kaldirma kuvveti kaçinmayi bozar) hem de
bolumun soruşunu ("seviyeyi nasil kullanirim") boğar.
"""
from __future__ import annotations

from src.config import TILE_SIZE
from src.world.level import join_rooms, parse

ROOM_HEIGHT = 16
FLOOR_TOP = 14


def _room(width: int, ceiling: int = 3, floor: int = FLOOR_TOP,
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
    """Dikdortgen kutle. Ust kat ve savak yuvasi bununla kuruluyor."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            rows[y][x] = "#"


def finish(rows: list[list[str]]) -> list[str]:
    return ["".join(row) for row in rows]


# --- Oda 1: Esik. Kuru. Tek dusman. --------------------------------------
# Su HENUZ yok - oyuncu once bolumun kuru halini goruyor ki sonraki
# odada suyun ne degistirdigini karsilastirabilsin.
_r1 = _room(24, left_wall=True)
stamp(_r1, 2, 13, "R")
stamp(_r1, 17, 13, "s")
ROOM_1 = finish(_r1)

# --- Oda 2: Vana Odasi. Bulmacanin tamami burada. ------------------------
# Genislik 40: ust kat, savak yuvasi ve iki vana arasinda yuruyecek yer
# olmali. Dar olsaydi bulmaca "bak ve bas" olurdu, "gez ve anla" degil.
_ROOM2_WIDTH = 40
_r2 = _room(_ROOM2_WIDTH, ceiling=2)

# Ust kat: sag ustte bir platform. Zeminden 8 tile yukarida - ziplama
# zarfi 3 tile, yani KESINLIKLE ziplanarak cikilamaz. Tek yol yuzmek.
UPPER_FLOOR_ROW = 6
block(_r2, 26, _ROOM2_WIDTH - 1, UPPER_FLOOR_ROW, UPPER_FLOOR_ROW)

# Vana 1 zeminde solda, Vana 2 ust katta. **Isaret DEGIL** - haritaya
# `v` damgalamak `level.MARKERS`'a butun bolumler icin yeni bir harf
# eklemek demekti; vana yalnizca bu bolumde var. Bolum 3'un Mor Alev
# kaidesi ve Bolum 4'un gunlugu ayni gerekceyle sabit.
VALVE_LOW = (8, 13)
VALVE_HIGH = (33, UPPER_FLOOR_ROW - 1)

# Savak yuvasi: alt gecidin agzi. Kapak sahne tarafindan aciliyor/
# kapaniyor (`SLUICE_COLUMN`), oda verisinde YUVA acik biraktik -
# baslangicta su alcak, yani kapak acik.
SLUICE_COLUMN = 20
SLUICE_ROWS = range(11, FLOOR_TOP)
ROOM_2 = finish(_r2)

# --- Oda 3: Alt Gecit. Savagin ardi - cikis. -----------------------------
_r3 = _room(20, right_wall=True)
stamp(_r3, 6, 13, "$")
stamp(_r3, 16, 13, "X")
ROOM_3 = finish(_r3)


ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3)
LEVEL = parse("bolum-05-sular", ROWS)

ROOM_STARTS = (
    ("esik", 0),
    ("vana_odasi", len(ROOM_1[0])),
    ("alt_gecit", len(ROOM_1[0]) + _ROOM2_WIDTH),
)

# --- Su -------------------------------------------------------------------
# Sutunlar birlestirilmis haritada kayiyor - Oda 2'nin basi kadar oteleniyor.
_R2 = ROOM_STARTS[1][1]
VALVE_LOW_TILE = (_R2 + VALVE_LOW[0], VALVE_LOW[1])
VALVE_HIGH_TILE = (_R2 + VALVE_HIGH[0], VALVE_HIGH[1])
SLUICE_TILE_COLUMN = _R2 + SLUICE_COLUMN

# Su seviyeleri (dunya piksel, y). **Kucuk y = yuksek su.**
# Alcak: zeminin hemen ustu - bulmaca baslarken su neredeyse yok.
WATER_LOW = FLOOR_TOP * TILE_SIZE - TILE_SIZE
# Yuksek: ust katin bir tile ustune kadar. Oyuncu yuzerek platforma
# CIKABILMELI ama platform su altinda KALMAMALI - yoksa uzerinde
# duramaz ve vanaya basamaz.
WATER_HIGH = (UPPER_FLOOR_ROW - 1) * TILE_SIZE
# Savak bu seviyenin uzerinde su varken KAPALI.
SLUICE_CLOSE_LEVEL = (FLOOR_TOP - 4) * TILE_SIZE

SECRETS_TOTAL = 1
CHEST_GOLD = 35
