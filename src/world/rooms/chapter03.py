"""Bolum 3 - "Mesale Mahzeni". docs/bolum-03.md baglayici.

## Isaretler (world/level.py MARKERS'a ek olarak)

    R oyuncu   s Suruklenen   t Tirmanan   g Golge Suruklenen
    N Mum Bekcisi   $ sandik   M mini-boss   B kirilabilir duvar   X cikis

## Isik - meselenin ozeti

`TORCHES` (chapter02'deki gibi) artik salt dekor degil: her giris
`[tile_x, tile_y, lit]` **mutable** bir liste - oyuncu meshale ile
yakinca/firlatinca `lit` calisma zamaninda degisiyor. `Chapter03Scene`
bunlari `LightState`e besliyor. Konumlari zeminden bagimsiz (duvara/tavana
asili dekoratif isaretler - `cave_backdrop.draw_torches` cizer), yani
erisilebilirlik dogrulayicisini hic ilgilendirmiyor.

## Odalar kod ile insa ediliyor, elle ASCII sayilmiyor

`_room()` duz bir tuval acar (taban/tavan/duvar), `stamp()` tek tek
karakter yerlestirir. Genislik hatasi (chapter02'deki gibi elle sayarken
kayma) boylece yapisal olarak imkansiz.

## Mum Bekcisi'nin gizli odasi - AYRI BLOK DEGIL

Ilk denemede Oda 3-A'yi chapter02'deki gibi ayri bir blok olarak
`join_rooms`a eklemistim (Oda 3 ile Oda 4 arasina). Bu **yanlisti**:
`join_rooms` bloklari yan yana ekliyor, dallanma yok - araya giren blok
ana yolun **uzerinden gecmesi gerektigi** sutunlari da kapsiyor, ve o
blogun sag duvari varsa ana yol tamamen kesiliyor (Oda 4 ve sonrasi
erisilemez hale geliyordu - `tools/reachability.py` bunu hemen yakaladi).
Chapter02 bunu **ayni sutun araliginda iki kat** ile cozuyor (ana koridor
asagida, gizli oda yukarida). Ayni sey yerine burada daha basit bir yol
seciliyor: gizli oda Oda 3'un **kendi blogu icinde** ust tarafta bir
cep - ayri blok yok, ana zemin (satir 14) Oda 3 boyunca hic kesilmiyor.
"""
from __future__ import annotations

from src.world.level import join_rooms, parse

ROOM_HEIGHT = 16          # Butun odalar 16 satir (chapter02.py ile ayni)
FLOOR_TOP = 14            # Zemin satir 14 - basilabilir satir 13


def _room(width: int, ceiling: int = 4, floor: int = FLOOR_TOP,
          left_wall: bool = False, right_wall: bool = False) -> list[list[str]]:
    """Duz bir oda tuvali: `ceiling` satir tavan, `floor`den asagisi zemin.

    Zemin (satir >= floor) **butun genislik boyunca kesintisiz** - odalar
    arasi gecis hep bu satirdan. `left_wall`/`right_wall` yalnizca ilk/son
    odada disariya tasmayi onlemek icin; ara odalarda kullanilmaz (aksi
    halde ana yolu keser).
    """
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


def finish(rows: list[list[str]]) -> list[str]:
    return ["".join(row) for row in rows]


# --- Oda 1: Isigin Kurali. Tavan 4 satir, zemin 14. ----------------------
# Iki Suruklenen isik dairesinin disinda - oyuncu onlari duyar, gormez
# (docs/bolum-03.md: "ilk gercek gerilim ani").
_r1 = _room(26, left_wall=True)
stamp(_r1, 2, 13, "R")
stamp(_r1, 14, 13, "s")
stamp(_r1, 22, 13, "s")
ROOM_1 = finish(_r1)

# --- Oda 2: Karanlik Gecis. Sadece tasinan mesale aydinlatir. ------------
# Duz zemin - tehlike platformdan degil karanliktan geliyor (docs: "isik
# daireis 3 tile, oda 20 tile"). Sonu sandik (35 altin).
_r2 = _room(30)
stamp(_r2, 27, 13, "$")
ROOM_2 = finish(_r2)

# --- Oda 3: Yuvalar Bulmacasi + gizli Mum Bekcisi cebi. ------------------
# Bes yuva (TORCHES, asagida) duvara/tavana asili - zemine dokunmuyor, hepsi
# sonuk baslar. Uc Tirmanan tavanda, isik yaklasinca kacar
# (climber.py::_fleeing_light). Sag tarafta kirilabilir duvarin ardinda
# kucuk bir cep: Mum Bekcisi + gizli sandik (70 altin). Cebin zemini ana
# zeminden yalnizca 2 tile yukarida - tek ziplamayla erisilir
# (`MAX_JUMP_HEIGHT_TILES=3`, `tools/reachability.py` bunu dogruluyor). Ana
# zemin (satir 14) odanin sonuna kadar kesintisiz - cep ona **kesmiyor**,
# sadece uzerine biniyor.
_r3 = _room(34, ceiling=3)
stamp(_r3, 4, 4, "t")
stamp(_r3, 24, 4, "t")
stamp(_r3, 16, 12, "t")
# Gizli cep: sutun 27-33, satir 4-11. Ic hacim 28-31 x 4-10, zemini satir 11.
#
# **Kritik:** cep satir 12/13'e HIC dokunmuyor - ana koridorun zemini
# (satir 14) boyunca oyuncunun bas hizasi tam olarak bu iki satirdir
# (govde 2 tile). Ilk denemede cebi satir 12'ye kadar indirmistim ve ana
# koridor cebin **altindan** gectigi icin oyuncu orada tavana carpip
# gecemiyordu - `tools/reachability.py` butun Oda 4'ten sonrasini
# "ulasilamaz" diye isaretleyince fark edildi.
for col in range(27, 33):
    for row in range(4, 12):
        stamp(_r3, col, row, "#")
for col in range(28, 32):
    for row in range(4, 11):
        stamp(_r3, col, row, ".")
# Giris - iki tile yukseklikte (oyuncu govdesi 2 tile), ana zeminden tek
# ziplamayla erisilir (climb = 14-11 = 3, tam sinirda).
stamp(_r3, 27, 9, "B")
stamp(_r3, 27, 10, "B")
stamp(_r3, 29, 10, "N")
stamp(_r3, 31, 10, "$")
ROOM_3 = finish(_r3)

# --- Oda 4: Surunen Karanlik. Sconce yok - sadece tasinan isik. ----------
_r4 = _room(28)
for col in (2, 8, 18, 25):
    stamp(_r4, col, 13, "g")
ROOM_4 = finish(_r4)

# --- Oda 5: MOR ALEV. Kaide odanin ortasinda (kod tarafinda cizilir). ----
ROOM_5 = finish(_room(26))

# --- Oda 6: Alev Sinavi. Ruzgar meshaleyi sonduruyor (Mor Alev etkilenmez,
# Chapter03Scene isik yaricapini WIND_ZONES'a gore sadece "meshale" icin
# sifirlar). Duz zemin - tehlike ruzgardan geliyor, platformdan degil.
ROOM_6 = finish(_room(30))

# --- Oda 7: SONMUS OLAN. Genis arena, ortada mangal. ---------------------
_r7 = _room(36, right_wall=True)
stamp(_r7, 10, 13, "M")
stamp(_r7, 33, 13, "X")
ROOM_7 = finish(_r7)

ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4, ROOM_5, ROOM_6, ROOM_7)

LEVEL = parse("bolum-03-mesale-mahzeni", ROWS)

# Oda sinirlari - tetikleyiciler ve anlatim icin. (ad, baslangic tile)
_WIDTHS = (26, 30, 34, 28, 26, 30, 36)
_starts = []
_acc = 0
for _name, _width in zip(
        ("isigin_kurali", "karanlik_gecis", "yuvalar_bulmacasi",
         "surunen_karanlik", "mor_alev", "alev_sinavi", "sonmus_olan"),
        _WIDTHS):
    _starts.append((_name, _acc))
    _acc += _width
ROOM_STARTS = tuple(_starts)

_room1_start = ROOM_STARTS[0][1]
_room3_start = ROOM_STARTS[2][1]
_room6_start = ROOM_STARTS[5][1]
_room7_start = ROOM_STARTS[6][1]

# Mum Bekcisi'nin gizli cebi - mutlak sutun araligi (Oda 3'un kendi blogu
# icindeki yerel 27-33 araliginin karsiligi).
SECRET_POCKET_ABS_COLUMNS = (_room3_start + 27, _room3_start + 33)
SECRET_WALL_MIN_COLUMN = SECRET_POCKET_ABS_COLUMNS[0]

# --- Mesale yuvalari - `[tile_x, tile_y, lit]`, MUTABLE ------------------
# `tile_y`: tavanin altindaki ilk bos satir (cave_backdrop.draw_torches
# sozlesmesi). Oda 1 tek yanik mesaleyle basliyor; Oda 2 ve 4 hicbir sabit
# isik yok - yalnizca tasinan mesale/Mor Alev aydinlatiyor (docs).
TORCHES: list[list] = [
    [_room1_start + 4, 4, True],                  # Oda 1 - "biri yaniyor"
    [_room1_start + 20, 4, False],
    # Oda 3 - bes yuva, hepsi sonuk baslar (bulmaca). Zemine dokunmuyorlar.
    [_room3_start + 6, 3, False],
    [_room3_start + 26, 3, False],
    [_room3_start + 8, 7, False],
    [_room3_start + 21, 7, False],
    [_room3_start + 4, 10, False],
    # Mum Bekcisi'nin cebi - sicak/aydinlik, o zaten orada.
    [_room3_start + 29, 5, True],
    # Oda 6 - alev sinavi, birkac sabit nokta (ruzgarin olmadigi koseler).
    [_room6_start + 4, 4, True],
    [_room6_start + 22, 4, True],
    # Oda 7 - arena, kenarlarda birkac sabit mesale.
    [_room7_start + 4, 4, True],
    [_room7_start + 30, 4, True],
]

# Oda 3'un bulmacasi: bes yuvanin **hepsi** yaninca gizli kapi acilir
# (docs: sira onemli degil). TORCHES listesindeki indeksler.
ROOM3_SOCKET_INDICES = (2, 3, 4, 5, 6)

# Oda 6'daki ruzgarli sutun araliklari - sıradan mesaleyi (Mor Alev degil)
# etkiler. (baslangic, bitis) tile sutunu, mutlak.
WIND_ZONES = ((_room6_start + 6, _room6_start + 14),
             (_room6_start + 18, _room6_start + 26))

# Mor Alev kaidesinin konumu (Oda 5).
PURPLE_FLAME_TILE = (ROOM_STARTS[4][1] + 13, 13)

# Mangal (Oda 7).
BRAZIER_TILE = (_room7_start + 18, 13)
