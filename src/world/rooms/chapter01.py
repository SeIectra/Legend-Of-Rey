"""Bolum 1 - Koy. Oyunun ilk odasi ve prologu.

`docs/yapi.md`: *"Cemo kolyeyi verir. Gece yarik acilir, Cemo cekilir. Elde
sadece kolye."* Mekanik: hareket, saldiri, **Yanki Gorusu**.

## Prolog diyalogsuz

Hicbir replik yok (docs/gdd.md 2). Sira:

    1  Rey uyanir, Cemo yaninda. Cemo'nun basinda kolye balonu.
    2  Cemo Rey'e dogru yurur, kolyeyi verir - balon kolyeye doner.
    3  Yer sarsilir. Zeminde yarik acilir, mor isik.
    4  Cemo yariga dogru **cekilir** - kacmaya calisir, yetismezsin.
    5  Yarik kapanir. Elde sadece kolye.

Adim 4 bilincli olarak **oynanamaz**: oyuncu kosar ama yetismez. Cemo pasif
kurban degil (docs/gdd.md 3) - kacmayi dener, ayagini surur, iz birakir.
Kurtarilamayan bir sey oldugunu oyuncu **deneyerek** ogrenir, ara sahne
izleyerek degil.

## Ziplama zarfi

Her basilabilir kat bir oncekinden en fazla 3 tile yukarida
(`MAX_JUMP_HEIGHT_TILES`). `tests/test_level.py` her kosuda dogruluyor.

## Yanki

Bolumun ucuncu ogretisi Yanki Gorusu ama sistem henuz yok (Gorev 3).
Kanca `ECHO_TUTORIAL_TILE` olarak burada duruyor ve sahne oraya gelindiginde
`on_echo_tutorial()` cagiriyor - sistem gelince govdesi dolacak.
"""
from __future__ import annotations

from src.world.level import parse

# Koy. Gece. Rey evin onunde, Cemo yaninda.
#   R oyuncu   C Cemo   W kilic   s Suruklenen   X cikis   ! Yanki ogretisi
#
# Kilic **yaratiklardan once** duruyor: Rey silahsiz basliyor ve ilk
# yaratigi gorunce kacacak yeri yok. Kilici alma ani boylece bir
# rahatlama oluyor - once ihtiyaci hissettiriyoruz, sonra veriyoruz.
#
# Basamaklar **tam 3 tile** araliklarla: zemin 12 -> 9 -> 6. Ilk halinde
# satir 7 ve 4'te platformlar vardi ve zeminden 5 tile yukaridaydilar -
# hicbir sekilde cikilamiyordu. tools/reachability.py yakaladi.
ROWS: list[str] = [
    "................................................................",
    "................................................................",
    "................................................................",
    "................................................................",
    "................................................................",
    "................................................................",
    "........................####....................................",
    "................................................................",
    "................................................................",
    "....................####....................####................",
    "................................................................",
    "....RC..........................W.........s........s....!......X",
    "################################################################",
    "################################################################",
]

LEVEL = parse("bolum-01-koy", ROWS)

# Yarigin acildigi yer - Cemo oraya cekilir.
RIFT_TILE = (20, 11)

# Yanki Gorusu ogretisinin tetiklendigi tile (Gorev 3'te dolacak).
ECHO_TUTORIAL_TILE = LEVEL.first("trigger")

# Koy susu - evler, cit, kuyu. Sahne dekoru: carpisma yok, yalnizca cizim.
# (tile_x, tile_y, genislik, yukseklik, tip)
SCENERY = (
    (2,  11, 5, 4, "house"),
    (9,  11, 4, 3, "house"),
    (16, 11, 6, 5, "house"),
    (25, 11, 4, 3, "house"),
    (34, 11, 5, 4, "house"),
    (13, 11, 2, 2, "well"),
    (30, 11, 3, 1, "fence"),
    (44, 11, 3, 1, "fence"),
)

# Prolog adimlari: (kare, ad). Kareler **birikimli degil**, her adim kendi
# suresini tasiyor.
PROLOGUE = (
    (70,  "wake"),        # Rey uyanir, Cemo yaninda
    (80,  "gift"),        # Cemo kolyeyi uzatir
    (50,  "taken"),       # Yer sarsilir, yarik acilir
    (120, "chase"),       # Cemo cekilir - kosarsin, yetismezsin
    (60,  "alone"),       # Yarik kapanir, elde kolye
)

# Ogretiler: (tetikleyen kare araligi, dil anahtari). Oyuncu hareket
# etmeye baslayinca birinci, ilk dusmani gorunce ikincisi.
TUTORIAL_MOVE_AFTER = 40
TUTORIAL_ATTACK_AFTER = 260
