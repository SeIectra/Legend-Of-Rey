"""Bolum 18 - "Son". `docs/yapi.md` B18 baglayici.

    **B18 - Son.** Yaratik, Yanki'yi kullanarak Cemo'nun sesiyle
    konusur. Rey sesi susturmayi secer - sessizlikte, yardimsiz
    savasir (Ardo'nun butun oyun boyunca oynadigi sekilde).
    Kazanir. Cemo kurtulur. Gun isigi. Rey kolyeyi Cemo'ya geri takar,
    Ardo arkalarinda. Rey'in kafasi ilk kez sessiz.

`docs/ekonomi-uretim.md`: zorluk **9/10** - "Final, yardimsiz". Oyunun
en zoru.

## Uc bolge, ucu de bir sey soyluyor

    1 dip      Zindanin sonu. Dusman yok, yalnizca yol ve sessizlik.
    2 ses      Cemo'nun sesi. Yanki onu GOSTERIYOR ve gosterdigi yalan.
    3 arena    Cagiran. Muhurlu, genis, bos - saklanacak yer yok.

Ilk bolge bilerek bos: on yedi bolumun sonunda oyuncuya bir nefes
borcluyuz ve final bir gurultuyle degil bir **inisle** basliyor.
`docs/gdd.md` 9 nefes bolumlerinin ayni gerekcesi, bir odaya
sikistirilmis hali.

Arena genis ve bos: zorluk 9 saklanmaktan degil **okumaktan** gelmeli
(`docs/derinlestirme.md` 4.2 - ogrenilebilir boss). Sutun arkasina
saklanilan bir final, ogrenilen bir final degildir.

## Neden mesale yok

Butun oyunun isik ekonomisi (B3'ten beri) burada bitiyor: dipte
mesale kalmamis. Isik yalnizca Yanki'dan geliyor - ve oyuncu onu
susturunca arena gercekten kararyor. Susturmanin bedeli bir sayi
degil, **goremiyor olmak**.

## Isaretler

    R oyuncu   X cikis   ! tetikleyici

Cagiran, Cemo ve yemler isaret DEGIL - sahne yerlestiriyor. Ayni
gerekce B6/B9/B17'de de yazildi: yalniz bir bolumde gecen harf ortak
sozlugu sisirir.
"""
from __future__ import annotations

from src.world.level import join_rooms, parse

ROOM_HEIGHT = 18
FLOOR_TOP = 15
CEILING = 2


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


# --- Bolge 1: Dip. Nefes. ----------------------------------------------------
# Dusman yok. Yalnizca yurumek ve inmek. Oyuncu buraya on yedi bolumun
# sonunda geliyor; final bir gurultuyle degil bir sessizlikle acilmali.
_ZONE1_WIDTH = 26
_z1 = _room(_ZONE1_WIDTH, left_wall=True)
stamp(_z1, 3, 14, "R")
stamp(_z1, 20, 14, "!")      # -> InisCinematic
ZONE_1 = finish(_z1)

# --- Bolge 2: Ses. Cemo'yu duyuyorsun. ---------------------------------------
# Burada bir dusman da yok - ama Yanki bir sey gosteriyor ve o sey
# ileride. Oyuncu ona dogru yuruyor. Odanin isi bir dovus degil bir
# **umut**: sonrasinda kirilacak.
_ZONE2_WIDTH = 24
_z2 = _room(_ZONE2_WIDTH)
stamp(_z2, 18, 14, "!")      # -> SesCinematic (yalan aciga cikiyor)
ZONE_2 = finish(_z2)

# --- Bolge 3: Arena. Cagiran. ------------------------------------------------
# Genis ve bos. Sutun yok, siper yok, mesale yok. Zorluk okumaktan
# geliyor.
_ZONE3_WIDTH = 34
_z3 = _room(_ZONE3_WIDTH, right_wall=True)
stamp(_z3, 2, 14, "!")       # -> AdCinematic (boss aciga cikiyor)
stamp(_z3, 30, 14, "X")      # kapanis - boss olunce aciliyor
ZONE_3 = finish(_z3)


ROWS = join_rooms(ZONE_1, ZONE_2, ZONE_3)
LEVEL = parse("bolum-18-son", ROWS)

ZONE_STARTS = (
    ("dip", 0),
    ("ses", _ZONE1_WIDTH),
    ("arena", _ZONE1_WIDTH + _ZONE2_WIDTH),
)

# Arena muhru - Cagiran cikinca kapanan sutun. B6'dan beri ayni desen.
ARENA_SEAL_COLUMN = _ZONE1_WIDTH + _ZONE2_WIDTH + 4
ARENA_SEAL_ROWS = tuple(range(CEILING, FLOOR_TOP))

# Cagiran'in dogdugu yer - arenanin ortasi, havada.
CALLER_TILE = (_ZONE1_WIDTH + _ZONE2_WIDTH + 20, 11)

# Cemo - **gercek olan**. Arenanin sonunda, boss olunce ulasiliyor.
CEMO_TILE = (_ZONE1_WIDTH + _ZONE2_WIDTH + 27, 14)

# Bolge 2'de Yanki'nin gosterdigi yalan: yem burada duruyor.
FALSE_CEMO_TILE = (_ZONE1_WIDTH + 20, 14)

SECRETS_TOTAL = 0

# Sessizlikte bitirmenin odulu.
#
# B15 "hic uyandirmadan", B16 "kaldirarak", B17 "az gecisle" olcuyordu.
# Final **hic diriltmeden** olcuyor: Cagiran'i kac kez geri kaldirdin.
# Susturmayi erken secen oyuncu az, gec secen cok. Ceza yok - odul.
CLEAN_RISES = 2
CLEAN_BONUS = 200
