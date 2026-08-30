"""Bolum 13 - "Cemo". `docs/yapi.md` B13 baglayici.

    B13 - Cemo. Kafeste, canli, sana bakiyor - **ulasamadan tasinir.**
    Kacmayi denemis, muhafizi yaralamis, duvara isaret kazimis.
    *Mekanik:* Zaman kapilari - kovalamaca bolumu.

`docs/gdd.md` 10: *"13 | Cemo | Kovalamaca, **BOSS 2**"*.
`docs/gdd.md` 9 mekanik 8: *"Zaman kapilari | B13"*.
`docs/ekonomi-uretim.md`: zorluk **7/10** - Katman 2'nin zirvesi.

## Bolumun tek cumlesi: DURMA

On iki bolumdur oyuncu "odayi temizle, sonra gec" ogrendi. Burada kol
cevriliyor, surgu inmeye basliyor ve yolda duran her dusman **zaman**
demek. Bu yuzden odalara konan iki dusman Okcu ve Komutan: ikisi de
"once beni hallet" diye bagiriyor, ve ikisinin de dogru cevabi burada
**hayir**.

Katman 2 (B7-B13) tam da burada bitiyor. Dort muhafizin dordu de bu
bolumde ya odada ya boss'un bir fazinda - sinav niteliginde.

## Oda sirasi

    1 kafes      Cemo gorunuyor, tasiniyor.  Dusman yok - an bozulmasin.
    2 kol        OGRETME: tek kol, tek kapi, bol sure, dusman yok.
    3 okcu       Ilk sinav. Durursan kapi kapanir.
    4 komutan    Cagirdiklari birikiyor; kosmak tek cozum.
    5 isaret     ★nefes. Cemo'nun kazidigi isaret + sandik. Dovus yok.
    6 cifte      Zirve: iki kol zincirleme. Mizrakli baski yapiyor.
    7 zindan     BOSS 2 arenasi. Mangallar + karanlik.

Oda 5 bilerek bos: `docs/ekonomi-uretim.md` *"surekli tirmanan gerilim
yorar; dususler zirveleri yukseltir"*. Yedi odalik bir kovalamacanin
ortasinda bir nefes olmazsa boss yorgun bir oyuncuyu karsiliyor.

## Kapilar haritada ACIK duruyor

`T` yalnizca surgunun asili durdugu satiri isaretliyor; zemin orada
bos. Sebep `tools/reachability.py`: BFS dogrulamasi oda **geometrisini**
olcmeli (ziplama zarfi, erisilebilirlik), bulmacanin o anki durumunu
degil. Kapali kapiyi haritaya yazsaydik arac her bolumde yanlis alarm
verirdi. Sahne kurulurken `GateBank.seal_all` hepsini kapatiyor - ayni
desen Bolum 11'in `HALL_DOOR_ROWS`'unda da var.

## Isaretler

    R oyuncu   a Okcu   c Komutan   m Mizrakli   s Suruklenen
    L kol      T surgu (asili satir)   F mangal   Z Zindanci
    C Cemo     $ sandik   X cikis   ! tetikleyici
"""
from __future__ import annotations

from src.world.level import join_rooms, parse

ROOM_HEIGHT = 16
FLOOR_TOP = 14
CEILING = 3
# Surgunun asili durdugu satir. Zemine (14) kadar **5 tile** iniyor;
# oyuncu gecmek icin 2 tile bosluk istiyor, yani surenin son **%20'si**
# gecilemez. Bu kayip `config.py`'deki sayaclara katildi ve
# `tests/test_chapter13.py` her calisisinda yeniden olcuyor.
GATE_TOP = 9


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


def finish(rows: list[list[str]]) -> list[str]:
    return ["".join(row) for row in rows]


# --- Oda 1: Kafes. Dusman YOK. -----------------------------------------------
# Bolumun duygusal cekirdegi burada ve **hicbir sey onunla yarismamali**.
# Bir Suruklenen koysaydik oyuncu Cemo'ya degil ona bakardi.
#
# Kafes **yukarida**, ulasilamayacak yerde. Ilk surum aradaki bosluğu
# bir ucurum yapiyordu; hata buydu: ucurum zemini deldigi icin oyuncu
# haritadan dusuyordu, ve dip solid yapilinca da karsi yakaya
# tirmanip kafese ULASIYORDU - sahnenin tamami cokuyordu.
#
# Dikey engel hem guvenli hem daha okunur: yukari bakmak "oraya
# gidemem"i tek karede anlatiyor. Kafes zemine 6 tile yukarida,
# ziplama zarfi 3 - yani "biraz daha denesem" duygusu bile yok.
# Ulasmak MUMKUN DEGILDI, ve oyuncu bunu bakarak anliyor.
_ROOM1_WIDTH = 22
_r1 = _room(_ROOM1_WIDTH, left_wall=True)
stamp(_r1, 3, 13, "R")
# Kafesin durdugu ust ledge. Kalin (iki satir): altindan gecen
# oyuncunun kafasina "burasi baska bir kat" hissi versin.
block(_r1, 13, 21, 7, 8)
stamp(_r1, 17, 6, "C")           # Cemo - ara sahne onu buradan aliyor
stamp(_r1, 9, 13, "!")           # ara sahne tetikleyicisi
ROOM_1 = finish(_r1)

# --- Oda 2: Kol. OGRETME odasi. ----------------------------------------------
# `docs/gdd.md` 9: once ogret, sonra sina. Tek kol, tek surgu, bol sure,
# **hicbir dusman**. Oyuncu mekanigi baski olmadan cozuyor - ayni
# gerekce Bolum 11'in "ogrenme" odasinda da yazili.
_ROOM2_WIDTH = 20
_r2 = _room(_ROOM2_WIDTH)
stamp(_r2, 3, 12, "L")
stamp(_r2, 14, GATE_TOP, "T")
ROOM_2 = finish(_r2)

# --- Oda 3: Okcu. Ilk sinav. -------------------------------------------------
# Okcu kapinin **otesinde** duruyor, yani oyuncu kosarken vuruluyor ve
# onu susturmak icin durmak kapiyi kapatiyor. Okcu'nun kendi dersi
# ("once onu sustur") burada oyuncuya karsi calisiyor - `docs/gdd.md` 9:
# *"yeni mekanik + eski mekanik = yeni bulmaca"*.
_ROOM3_WIDTH = 26
_r3 = _room(_ROOM3_WIDTH)
stamp(_r3, 3, 12, "L")
stamp(_r3, 12, GATE_TOP, "T")
stamp(_r3, 17, 13, "a")          # Okcu - kapinin otesinde
stamp(_r3, 22, 13, "s")          # Suruklenen: kacisin sonunda bir engel
ROOM_3 = finish(_r3)

# --- Oda 4: Komutan. Kalabalik birikiyor. ------------------------------------
# Komutan cagirdikca oda doluyor. Onu oldurmek 20+ kare suruyor,
# kosmak 3. Sayi burada bir tehdit degil bir **saat**: ne kadar
# oyalanirsan o kadar cok sey arana giriyor.
_ROOM4_WIDTH = 26
_r4 = _room(_ROOM4_WIDTH)
stamp(_r4, 3, 12, "L")
stamp(_r4, 15, GATE_TOP, "T")
stamp(_r4, 9, 13, "c")           # Komutan - kol ile kapi ARASINDA
ROOM_4 = finish(_r4)

# --- Oda 5: Isaret. ★nefes. --------------------------------------------------
# `docs/yapi.md` B13: *"Kacmayi denemis, muhafizi yaralamis, duvara
# isaret kazimis."* Uc cumlenin ucu de bu odada, ve hicbiri diyalogla
# anlatilmiyor - kazinmis isaret, kurumus kan, kirik bir zincir.
#
# Dovus yok. Yedi odalik bir kovalamacanin ortasinda bir nefes
# (`docs/ekonomi-uretim.md`: *"dususler zirveleri yukseltir"*).
_ROOM5_WIDTH = 18
_r5 = _room(_ROOM5_WIDTH)
stamp(_r5, 5, 13, "!")           # ara sahne 2 tetikleyicisi
stamp(_r5, 12, 13, "$")          # gizli sandik
ROOM_5 = finish(_r5)

# --- Oda 6: Cifte kapi. Zirve. -----------------------------------------------
# **Tek kol, iki surgu, tek sayac.** Ilk tasarim iki kol koyuyordu ama
# o bir zincir degil bir siraydi: her kol kendi sayacini baslatiyordu,
# yani ikinci kapi icin acele etmek gerekmiyordu. Tek sayac soruyu
# gercek yapiyor - ikisinden de AYNI sure icinde gecmek zorundasin.
#
# Mizrakli tam iki kapinin arasinda ve menzili uzun (34 piksel;
# oyuncunun kilici ~16). Yani "yanindan gec" bedelsiz degil. Ama yine
# de gecmek dogru cevap: onu oldurmek surenin yarisini yiyor ve
# ikinci kapi yuzune kapaniyor.
#
# Bolumun butun dersi bu odada tek cumleye iniyor: **can vermek
# zaman vermekten ucuz.**
_ROOM6_WIDTH = 30
_r6 = _room(_ROOM6_WIDTH, ceiling=2)
# Mesafe **olculdu**: kol (4) -> kapi B (20) = 16 tile. Ilk yerlesim
# 21 tile'di ve `TIMEGATE_CHAIN_FRAMES` ile birlikte oda **gecilemez**
# cikti (Ardo icin pay 0.71x). Test yakaladi; hem mesafe hem sayac
# duzeltildi.
stamp(_r6, 4, 12, "L")           # tek kol - IKI kapiyi da aciyor
stamp(_r6, 11, GATE_TOP, "T")    # kapi A
stamp(_r6, 15, 13, "m")          # Mizrakli - iki kapinin arasinda
stamp(_r6, 20, GATE_TOP, "T")    # kapi B
ROOM_6 = finish(_r6)

# --- Oda 7: Zindan. BOSS 2 arenasi. ------------------------------------------
# Genis ve yuksek: Zindanci 30x47 piksel, oyunun en buyuk sprite'i, ve
# zincir hamlesi 62 piksel menzilli. Dar bir odada iki hamle de
# okunamazdi.
#
# Uc mangal (`docs/bolum-03.md`: *"isikla arena kontrolu -> B13"*).
# Faz 2'de fener kirilinca tek isik kaynagi onlar.
_ROOM7_WIDTH = 30
_r7 = _room(_ROOM7_WIDTH, ceiling=2, right_wall=True)
stamp(_r7, 2, 13, "!")           # boss ara sahnesi tetikleyicisi
stamp(_r7, 7, 13, "F")
stamp(_r7, 15, 13, "F")
stamp(_r7, 23, 13, "F")
stamp(_r7, 20, 13, "Z")          # Zindanci
stamp(_r7, 27, 13, "X")          # cikis - boss olunce aciliyor
ROOM_7 = finish(_r7)


ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4, ROOM_5, ROOM_6, ROOM_7)
LEVEL = parse("bolum-13-cemo", ROWS)

ROOM_STARTS = (
    ("kafes", 0),
    ("kol", _ROOM1_WIDTH),
    ("okcu", _ROOM1_WIDTH + _ROOM2_WIDTH),
    ("komutan", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH),
    ("isaret", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH + _ROOM4_WIDTH),
    ("cifte", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH + _ROOM4_WIDTH
     + _ROOM5_WIDTH),
    ("zindan", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH + _ROOM4_WIDTH
     + _ROOM5_WIDTH + _ROOM6_WIDTH),
)

# Hangi kol hangi kapiyi aciyor. Kapilar soldan saga numaralaniyor;
# `chapter13.py` bu eslemeyi kuruyor.
#
# Oda 6'da IKI kol ve IKI kapi var, ve esleme **sirali**: soldaki kol
# soldaki kapiyi aciyor. Capraz baglamak (sol kol -> sag kapi) bir
# bulmaca gibi gorunurdu ama degil - oyuncuya hicbir sey ogretmeyen
# bir surpriz olurdu.
GATE_ROWS = range(GATE_TOP, FLOOR_TOP)

CHEST_GOLD = 95
SECRETS_TOTAL = 1
