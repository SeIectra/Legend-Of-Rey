"""Bolum 9 - "Can Kulesi". `docs/yapi.md` B9 baglayici.

    ★B9 - Can Kulesi. **Dikey bolum.**
    Bulmaca: Rezonans ile uc cani dogru sirada calmak. Sira ipucu
    duvardaki freskte.
    Mekanik: **Team-up firlatma** - Ardo seni platformlara firlatir.

`docs/gdd.md` 155 (romantik yay): *"B9 | Guven | Firlatma - kendini
ona birakiyorsun."*

## Ilk DIKEY bolum - odalar y'ye gore

Sekiz bolumdur haritalar yatay: `join_rooms` odalari yan yana
diziyor ve `_room_at(x)` sutuna bakiyor. Kule oyle kurulamaz.

Burada tek bir uzun harita var (26 x 48 tile = uc ekran boyu) ve
"oda" kavraminin yerini **kat** aliyor. `chapter09.py` `_floor_at(y)`
ile satira bakiyor. Ayni fikir, doksan derece donmus.

## Katlar arasi mesafe firlatmayi ZORUNLU kiliyor

Ziplama 3.8 tile (`PLAYER_JUMP_SPEED`), katlar arasi 8 tile. Yani
kimse tek basina tirmanamaz - kulenin tamami "birlikte" demek.

Tek istisna **taban kat**: orada ziplayarak ulasilan bir cikinti var
ve firlatma orada ogretiliyor. `docs/gdd.md` 9: once ogret, sonra
sina.

## Isaretler

    R oyuncu   $ sandik   X cikis

Canlar, fresk ve platformlar isaret DEGIL - asagidaki sabitler. Ayni
gerekce her bolumde yazildi: yalniz bir bolumde gecen harf ortak
sozlugu sisirir.
"""
from __future__ import annotations

from src.world.level import parse

WIDTH = 26
HEIGHT = 48

# Katlarin zemin satirlari - **asagidan yukari**. Aralarinda 8 tile
# var: ziplama 3.8, yani firlatmasiz gecilmiyor.
FLOOR_ROWS = (45, 37, 29, 21, 13)
# Kat adlari, ayni sirada. `chapter09.py` bunlari `_floor_at` ile
# okuyor.
FLOOR_NAMES = ("taban", "ilk_can", "orta", "ikinci_can", "tepe")


def _blank() -> list[list[str]]:
    """Bos kule govdesi: yanlarda duvar, icerisi hava."""
    rows: list[list[str]] = []
    for y in range(HEIGHT):
        row = ["." for _ in range(WIDTH)]
        row[0] = row[1] = "#"
        row[-1] = row[-2] = "#"
        if y < 2 or y >= HEIGHT - 2:
            row = ["#"] * WIDTH
        rows.append(row)
    return rows


def stamp(rows: list[list[str]], x: int, y: int, char: str) -> None:
    rows[y][x] = char


def slab(rows: list[list[str]], x0: int, x1: int, y: int) -> None:
    """Yatay zemin dilimi."""
    for x in range(x0, x1 + 1):
        rows[y][x] = "#"


def solid(rows: list[list[str]], x0: int, x1: int, y0: int, y1: int) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            rows[y][x] = "#"


_r = _blank()

# --- Katlar --------------------------------------------------------------
# Her kat bir zemin dilimi + yukari gecis icin bir **acikilik**. Acikilik
# bilerek dar (4 tile): firlatilan kisi nisan almak zorunda, kule bir
# koridor degil.
GAPS = ((16, 20), (5, 9), (16, 20), (5, 9))

for index, row in enumerate(FLOOR_ROWS):
    if index == 0:
        slab(_r, 2, WIDTH - 3, row)          # taban tam dolu
        continue
    left, right = GAPS[index - 1]
    slab(_r, 2, left - 1, row)
    slab(_r, right + 1, WIDTH - 3, row)

# --- Taban kat: firlatma OGRETILIYOR -------------------------------------
# Ziplayarak cikilan bir cikinti (3 tile) ve firlatmayla cikilan bir
# cikinti (7 tile). Ikisi yan yana: fark oyuncunun gozunun onunde.
slab(_r, 6, 9, FLOOR_ROWS[0] - 3)            # ziplanabilir
slab(_r, 12, 15, FLOOR_ROWS[0] - 7)          # yalnizca firlatmayla

stamp(_r, 4, FLOOR_ROWS[0] - 1, "R")
stamp(_r, 8, FLOOR_ROWS[0] - 4, "$")         # ziplama odulu

# --- Fresk: sira ipucu ---------------------------------------------------
# Taban katta ve **girisin karsisinda**: oyuncu daha ilk adimda
# goruyor. Bulmacayi cozerken geri inmek zorunda kalmasin.
FRESCO_TILE = (20, FLOOR_ROWS[0] - 4)

# --- Canlar --------------------------------------------------------------
# Uc kat, uc can. Numaralari **konumdan bagimsiz**: freskteki sira
# 2 -> 0 -> 1, yani oyuncu en usttekini once calamiyor. Kule
# yukari-asagi-yukari geziliyor ve "dikey bolum" bir tirmanis degil bir
# **dolasma** oluyor.
BELL_TILES = (
    (7, FLOOR_ROWS[1] - 3),      # index 0 - ikinci calinacak
    (19, FLOOR_ROWS[3] - 3),     # index 1 - son calinacak
    (7, FLOOR_ROWS[2] - 3),      # index 2 - ILK calinacak
)
BELL_ORDER = (2, 0, 1)

# --- Tepe: cikis ---------------------------------------------------------
# Kapi bulmacayi cozene kadar KATI. `chapter09.py` aciyor.
EXIT_DOOR_COLUMN = 21
EXIT_DOOR_ROWS = range(FLOOR_ROWS[4] - 4, FLOOR_ROWS[4])
solid(_r, EXIT_DOOR_COLUMN, EXIT_DOOR_COLUMN,
      EXIT_DOOR_ROWS.start, EXIT_DOOR_ROWS.stop - 1)
stamp(_r, 23, FLOOR_ROWS[4] - 1, "X")

ROWS = ["".join(row) for row in _r]
LEVEL = parse("bolum-09-can-kulesi", ROWS)

CHEST_GOLD = 70
SECRETS_TOTAL = 1
