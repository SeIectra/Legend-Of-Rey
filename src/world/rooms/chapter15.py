"""Bolum 15 - "Sessizlik". `docs/yapi.md` B15 baglayici.

    ★B15 - Sessizlik. Yanki'yi **kapali oynamak zorundasin.** Uyuyan
    suru. Kosarsan uyanirlar.
    *Bulmaca:* Gurultu kaynaklarini (dusen tas, can, su damlasi)
    kullanarak dikkat dagitma. **Tamamen dovussuz gecilebilir - ve
    daha iyi odul verir.**

`docs/gdd.md` 10: *"15 | Sessizlik | Gizlilik bolumu, dovussuz
gecilebilir"*. `docs/ekonomi-uretim.md`: zorluk **4/10** - B14
zirvesinden sonraki dusus.

## Bolum 14 bu bolumu zaten kurdu

*"Yanki'yi kapali oynamak zorundasin"* cumlesi burada yazilmadi -
B14'te yazildi. `sense_betrayed` bayragi yuzunden duyuyu acmak
menzildeki herkesi uyandiriyor ve mekanizma `PlayScene`de. Bu bolum
o kurali **oynatiyor**, yeniden kurmuyor.

Iki bolum tek yay: biri araci elinden aldi, oteki onsuz yasamayi
ogretiyor.

## Bulmacanin tek cumlesi

Rezonans (B8) bir **uzaktan ses**. On iki bolumdur kapi aciyordu;
burada dikkat dagitiyor - `docs/gdd.md` 9: *yeni mekanik + eski
mekanik = yeni bulmaca.*

Ve darbenin **kendi sesi var** (`NOISE_RESONATE`). Bulmacayi kuran
sey bu: yeterince uzak dur ki kendi darbeni duymasinlar, yeterince
yakin dur ki cana ulassin.

## Oda sirasi

    1 uyku      OGRETME. Tek uyuyan, can yok, tehlike yok.
    2 can       Dikkat dagitma ogretiliyor: bir uyuyan, bir can.
    3 suru      Ilk sinav - uc uyuyan, iki can.
    4 damla     Kendi kendine calan kaynak: RITIM, tetikleme degil.
    5 dar       Zirve: yaninda yurumek zorunda oldugun koridor.
    6 cikis     Sayim ve cikis.

Oda 4 bilerek farkli: oteki odalarda sesi **sen** cikariyorsun,
orada ses zaten var ve sen ona uyuyorsun. Ayni mekanigin iki yuzu -
tek bir fikri bes oda tekrarlamak yorardi.

## Isaretler

    R oyuncu   s uyuyan Suruklenen   n uyuyan Sessiz
    h can (calinabilir)   H damla (kendi calar)
    $ sandik   X cikis   ! tetikleyici

Uyku isaret DEGIL: `SLEEPERS` asagida sutun araligiyla veriliyor ve
`chapter15.py` odaya girerken uyguluyor. Ayri bir harf ("uyuyan
Suruklenen") ortak sozlugu sisirirdi - dusman ayni dusman, degisen
sey sahnenin ona verdigi durum.
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


# --- Oda 1: Uyku. OGRETME, tehlikesiz. ---------------------------------------
# Tek bir uyuyan ve bol yer. Oyuncu yuruyerek yanindan gecebiliyor,
# kosarsa uyandiriyor - ve uyandirinca da bir sey kaybetmiyor, cunku
# burada gecilecek dar bir yer yok.
#
# `docs/gdd.md` 9: once ogret, sonra sina. Ilk ders **bedelsiz**
# olmali, yoksa oyuncu neyi yanlis yaptigini anlamadan cezalandirilir.
_ROOM1_WIDTH = 24
_r1 = _room(_ROOM1_WIDTH, left_wall=True)
stamp(_r1, 3, 13, "R")
stamp(_r1, 14, 13, "s")
ROOM_1 = finish(_r1)

# --- Oda 2: Can. Dikkat dagitma ogretiliyor. ---------------------------------
# Uyuyan **gecidin ustunde**: yanindan gecmek mumkun ama dar, ve
# yurumek sart. Can uzakta, ters yonde - yani cali ve suru oraya
# baksin.
#
# Can gecidin OTESINDE degil GERISINDE: uyuyani oyuncunun geldigi
# yone cekiyor, oyuncu de onun birakugi bosluktan geciyor. Ileriye
# koysaydik dikkat dagitmak dusmani hedefe dogru iterdi.
_ROOM2_WIDTH = 26
_r2 = _room(_ROOM2_WIDTH)
stamp(_r2, 16, 13, "s")
stamp(_r2, 4, 6, "h")
ROOM_2 = finish(_r2)

# --- Oda 3: Suru. Ilk sinav. -------------------------------------------------
# Uc uyuyan, iki can. Tek bir can yetmiyor: biri suruyu bir yana
# cekiyor, oteki obur yana. Oyuncu ikisini **sirayla** kullanmak
# zorunda.
_ROOM3_WIDTH = 30
_r3 = _room(_ROOM3_WIDTH)
stamp(_r3, 9, 13, "s")
stamp(_r3, 17, 13, "s")
stamp(_r3, 24, 13, "s")
stamp(_r3, 3, 5, "h")
stamp(_r3, 27, 5, "h")
stamp(_r3, 13, 13, "$")      # gizli sandik - suru arasinda
ROOM_3 = finish(_r3)

# --- Oda 4: Damla. Ses zaten var. --------------------------------------------
# Kendi kendine calan bir su damlasi. Oyuncu tetiklemiyor, **ritmine
# uyuyor**: damla dustugu an suru oraya bakiyor ve oyuncunun kendi
# ayak sesi o gurultunun altinda kayboluyor.
#
# Ayni mekanigin ikinci yuzu. Tek fikri bes oda tekrarlamak yorardi.
_ROOM4_WIDTH = 28
_r4 = _room(_ROOM4_WIDTH)
stamp(_r4, 11, 13, "s")
stamp(_r4, 20, 13, "n")      # uyuyan Sessiz - Yanki'nin gostermedigi
stamp(_r4, 15, 4, "H")       # damla, tavanda
ROOM_4 = finish(_r4)

# --- Oda 5: Dar. Zirve. ------------------------------------------------------
# Iki uyuyan arasinda iki tile'lik bir gecit. Can YOK - dikkat
# dagitacak bir sey yok, tek cozum **yurumek**. Bolumun butun dersi
# burada tek harekete iniyor.
_ROOM5_WIDTH = 24
_r5 = _room(_ROOM5_WIDTH)
stamp(_r5, 8, 13, "s")
stamp(_r5, 11, 13, "n")
stamp(_r5, 15, 13, "s")
stamp(_r5, 21, 13, "!")      # bolum sonu ara sahnesi
ROOM_5 = finish(_r5)

# --- Oda 6: Cikis. -----------------------------------------------------------
_ROOM6_WIDTH = 16
_r6 = _room(_ROOM6_WIDTH, right_wall=True)
stamp(_r6, 12, 13, "X")
ROOM_6 = finish(_r6)


ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4, ROOM_5, ROOM_6)
LEVEL = parse("bolum-15-sessizlik", ROWS)

ROOM_STARTS = (
    ("uyku", 0),
    ("can", _ROOM1_WIDTH),
    ("suru", _ROOM1_WIDTH + _ROOM2_WIDTH),
    ("damla", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH),
    ("dar", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH + _ROOM4_WIDTH),
    ("cikis", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH + _ROOM4_WIDTH
     + _ROOM5_WIDTH),
)

# Damlanin calma araligi (kare). Yaklasik dort saniye: oyuncunun bir
# sonraki damlayi **bekleyecek** kadar sabri olmali ama beklemek
# angarya olmamali.
DRIP_INTERVAL = 240

CHEST_GOLD = 85
SECRETS_TOTAL = 1
