"""Bolum 14 - "Yanki'nin Kaynagi". `docs/yapi.md` B14 baglayici.

    B14 - Yanki'nin Kaynagi. Rey anlar: **Yanki lanet degil, asagidaki
    seyin sesi.** Hep yardim ediyordu cunku onu cagiriyordu.
    *Mekanik:* Yanki tersine doner - actiginda dusmanlar da seni gorur.

`docs/gdd.md` 10: *"14 | Yanki'nin Kaynagi | Twist, **BOSS 3**, Yanki
tersine doner"*. `docs/ekonomi-uretim.md`: zorluk **7/10**.

## Katman 3 BURADA basliyor

`docs/gdd.md` 7: *"Katman 3 - Derin Zindan (B14-B18) - Yanki'nin
Cocuklari. Soru: yardimci sisteminin ihanetiyle yuzles."* Ucu de bu
bolumde ilk kez sahneye cikiyor ve **her biri kendi odasinda** -
ayni desen Katman 2'nin acilisinda (B7) da kullanildi.

    Oda 2  SESSIZ       arac EKSIK      Yanki onu gostermiyor
    Oda 4  YANKILAYAN   arac KIRLI      sahte isaret veriyor
    Oda 5  BOLUNEN      BECERI aleyhine combo cogaltiyor

Sirasi tesadufi degil: once aracin eksigi, sonra yalani, en sonda
oyuncunun kendi ustaligi. Ve ucunun de atasi Oda 6'da.

## Donus noktasi ODANIN ORTASINDA

Oda 1-2 eski sozlesmeyle oynaniyor: Yanki'yi ac, bak, ilerle. Ara
sahne 2'den (Kaynak) sonra **ayni tus odayi uyandiriyor**. Bir
mekanigi once son kez ogretip sonra kirmak, bastan kirmaktan cok daha
etkili - oyuncunun refleksi taze olmali ki ihanet hissedilsin.

## Isaretler

    R oyuncu   n Sessiz   y Yankilayan   p Bolunen   s Suruklenen
    O Kaynak (BOSS 3)   $ sandik   X cikis   ! tetikleyici
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


def finish(rows: list[list[str]]) -> list[str]:
    return ["".join(row) for row in rows]


# --- Oda 1: Inis. ESKI sozlesme, son kez. ------------------------------------
# Tanidik dusmanlar (Suruklenen), tanidik cozum: Yanki'yi ac, bak,
# ilerle. Bu oda hicbir sey ogretmiyor - **hatirlatiyor**. Ihanetin
# hissedilmesi icin refleksin taze olmasi gerek.
_ROOM1_WIDTH = 22
_r1 = _room(_ROOM1_WIDTH, left_wall=True)
stamp(_r1, 3, 13, "R")
stamp(_r1, 12, 13, "s")
stamp(_r1, 17, 13, "s")
ROOM_1 = finish(_r1)

# --- Oda 2: Sessiz. Aracin ILK eksigi. ---------------------------------------
# Yanki aciliyor, oda bos gorunuyor - ve bos degil. Ders bir metinle
# degil vurulmakla veriliyor (`shieldbearer.py` ve `shadow_shambler.py`
# ile ayni ilke).
#
# Iki tane: biri kaza olabilirdi, ikisi bir KURAL.
_ROOM2_WIDTH = 24
_r2 = _room(_ROOM2_WIDTH)
stamp(_r2, 8, 13, "n")
stamp(_r2, 18, 13, "n")
stamp(_r2, 21, 13, "!")      # ara sahne 2 tetikleyicisi ("Kaynak")
ROOM_2 = finish(_r2)

# --- Oda 3: Ters. Yeni sozlesme OGRETILIYOR. ---------------------------------
# Ara sahneden sonraki ilk oda. Uc Suruklenen uyuyor; Yanki'yi acan
# oyuncu ucunu birden uyandiriyor.
#
# Dusmanlar bilerek ZAYIF: bu oda cezalandirmiyor, **gosteriyor**.
# Yeni kuralin ilk ornegi olumcul olsaydi oyuncu ne oldugunu
# anlamadan olurdu.
_ROOM3_WIDTH = 26
_r3 = _room(_ROOM3_WIDTH)
stamp(_r3, 9, 13, "s")
stamp(_r3, 15, 13, "s")
stamp(_r3, 21, 13, "s")
ROOM_3 = finish(_r3)

# --- Oda 4: Yankilayan. Arac artik KIRLI. ------------------------------------
# Sessiz eksiltiyordu, bu kirletiyor: Yanki gosteriyor ama gosterdigi
# sey yalan. Ve artik acmanin bir de bedeli var - yani oyuncu "bakayim
# mi" sorusunu iki kere soruyor.
_ROOM4_WIDTH = 24
_r4 = _room(_ROOM4_WIDTH)
stamp(_r4, 10, 13, "y")
stamp(_r4, 19, 13, "n")      # Sessiz'le birlikte: eksik + kirli
stamp(_r4, 6, 13, "$")       # gizli sandik
ROOM_4 = finish(_r4)

# --- Oda 5: Bolunen. Kendi becerin. ------------------------------------------
# Katman 3'un ucuncu ihaneti. Ders "combo yapma" degil "combo'yu
# BITIR" - bitirici vurus bolmuyor (`splitter.py`).
_ROOM5_WIDTH = 24
_r5 = _room(_ROOM5_WIDTH)
stamp(_r5, 9, 13, "p")
stamp(_r5, 17, 13, "y")
stamp(_r5, 22, 13, "!")      # boss ara sahnesi tetikleyicisi
ROOM_5 = finish(_r5)

# --- Oda 6: BOSS 3 arenasi. --------------------------------------------------
# Genis ve yuksek: Kaynak 29x73 piksel (oyunun en buyugu), feryati
# yonsuz ve 58 piksel menzilli, sahte suretleri 90 piksel oteye
# cikiyor. Dar bir odada hicbiri okunmazdi.
_ROOM6_WIDTH = 32
_r6 = _room(_ROOM6_WIDTH, ceiling=2, right_wall=True)
stamp(_r6, 20, 13, "O")      # Kaynak
stamp(_r6, 29, 13, "X")      # cikis - boss olunce aciliyor
ROOM_6 = finish(_r6)


ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4, ROOM_5, ROOM_6)
LEVEL = parse("bolum-14-kaynak", ROWS)

ROOM_STARTS = (
    ("inis", 0),
    ("sessiz", _ROOM1_WIDTH),
    ("ters", _ROOM1_WIDTH + _ROOM2_WIDTH),
    ("yankilayan", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH),
    ("bolunen", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH + _ROOM4_WIDTH),
    ("arena", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH + _ROOM4_WIDTH
     + _ROOM5_WIDTH),
)

# Ihanetin basladigi oda. Bundan **once** eski sozlesme, sonra yeni.
BETRAYAL_ROOM = "ters"

CHEST_GOLD = 110
SECRETS_TOTAL = 1
