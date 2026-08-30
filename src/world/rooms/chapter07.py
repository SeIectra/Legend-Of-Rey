"""Bolum 7 - "Dar Gecit". `docs/yapi.md` B7 baglayici.

    ★B7 - Dar Gecit. Tek kisilik bir aralik. Ardo gecemez, Rey gecer.
    Rey obur taraftan kapiyi acar.
    Romantik an: Ardo elini uzatir, Rey tutar, aralıktan ceker. Ilk
    fiziksel temas. Balon yok - sadece bir saniye fazla tutulan el.

`docs/gdd.md` 11: *"B7 | Ilk temas | Elden cekme, bir saniye fazla"*.

## Cografya: kapi ve catlak AYNI duvarda

Iki oda arasindaki duvarda iki gecis var:

    * **Buyuk kapi** - kapali, bu taraftan acilmiyor
    * **Catlak** - yaninda, dar. Yalnizca ince olan geciyor.

Ikisi ayni duvarda olmasa "kapiyi obur taraftan ac" cumlesi anlamsiz
olurdu: cark bir yerde, kapi bambaska bir yerde durur ve oyuncu ikisini
baglayamazdi. Yan yana olunca oyuncu carki cevirince **arkasindaki**
kapinin acildigini duyuyor ve yoldas oradan giriyor.

## Kim geciyor - `girth`

`CharacterStats.girth`: Rey 10, Ardo 15. Catlagin acikligi 12. Sayi
carpisma kutusundan ayri tutuldu (bkz. `character_stats.py`): carpisma
kutusunu karakter basina degistirmek alti bolumun koridor davranisini
etkilerdi.

**Ardo oynanirken roller degisiyor ve bu bilerek.** O zaman gecemeyen
sensin; catlaktan yoldas (Rey) geciyor, carki o ceviriyor, kapiyi sana o
aciyor. Ve eli uzatan taraf sen oluyorsun. Ayni sahne, ters taraf.

## Bes oda

    1  KAPI ONU   Katman 2 ile tanisma (Kalkanli) + kapi ve catlak
    2  CARKHANE   obur taraf. YALNIZSIN. Cark kapiyi aciyor.
    3  EL         ★ bulusma - kirik zemin, uzanan el
    4  GECIT      birlikte dovus: bulusmanin bir karsiligi olmali
    5  CIKIS      dorduncu isaret

## Isaretler

    R oyuncu   k Kalkanli   s Suruklenen   t Tirmanan   $ sandik   X cikis

Cark, kapi sutunu ve catlak isaret DEGIL - asagidaki sabitler. Ayni
gerekce Bolum 4'un gunlugu, Bolum 5'in vanalari ve Bolum 6'nin plakalari
icin de yazilmisti: yalniz bir bolumde gecen harf ortak sozlugu sisirir.
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


# --- Oda 1: Kapi Onu. Katman 2 ile tanisma. ------------------------------
# Tek Kalkanli, bilerek yalniz: `docs/gdd.md` 9 "once ogret". B5'te bir
# ornekle taniticilmisti, burada Katman 2'nin **ilk gercek odasi** oldugu
# icin oyuncu onu tek basina, sakin bir yerde cozmeli. Kalabalik B7'nin
# 4. odasinda.
#
# Odanin sag ucunda duvar var; icinde iki gecis:
#   * kapi   (satir 10-13) - kapali, SOLID. Cark acacak.
#   * catlak (satir 12-13) - acik ama dar. `NarrowGap` bekciligi yapiyor.
_ROOM1_WIDTH = 28
_r1 = _room(_ROOM1_WIDTH, left_wall=True)
stamp(_r1, 3, 13, "R")
stamp(_r1, 16, 13, "k")          # Kalkanli
stamp(_r1, 9, 13, "s")           # taniidik bir Suruklenen - Katman 1 el sallıyor

# Sag ucu duvar: kapi ve catlak disinda gecilmiyor.
block(_r1, _ROOM1_WIDTH - 3, _ROOM1_WIDTH - 1, CEILING, FLOOR_TOP - 1)
# Catlak: zemin hizasinda iki satirlik bir yarik. Tilemap acik birakiyor;
# **kimin gectigine `NarrowGap` karar veriyor** (girth).
carve(_r1, _ROOM1_WIDTH - 3, _ROOM1_WIDTH - 1, FLOOR_TOP - 2, FLOOR_TOP - 1)
ROOM_1 = finish(_r1)

# Duvar UC tile kalinliginda (25-27), yani kapi da uc sutun. Tek sutun
# acilsaydi duvarin icinde bir cukur olurdu ve yoldas hala gecemezdi -
# ilk surumde tam olarak oyle oldu.
DOOR_COLUMNS = range(_ROOM1_WIDTH - 3, _ROOM1_WIDTH)
DOOR_ROWS = range(CEILING, FLOOR_TOP - 2)
# Catlak kapinin ALTINDA, ayni duvarda: "obur taraftan kapiyi ac"
# cumlesinin anlamli olmasi icin ikisi yan yana olmali.
GAP_COLUMN = _ROOM1_WIDTH - 2            # tunelin ortasi - bekci noktasi
GAP_ROWS = range(FLOOR_TOP - 2, FLOOR_TOP)

# --- Oda 2: Carkhane. YALNIZSIN. -----------------------------------------
# Dusman az ve secili (2): yoldas yokken kalabalik bir oda ceza gibi
# okunurdu. Amac zorluk degil **yalnizlik hissi** - bolum boyunca yaninda
# duran birinin yoklugu ancak tehlike varken hissediliyor.
#
# Cark odanin en sagında: oyuncu yalnizligi yurumek zorunda.
_ROOM2_WIDTH = 26
_r2 = _room(_ROOM2_WIDTH)
stamp(_r2, 8, 13, "s")
stamp(_r2, 15, 4, "t")           # tavandan - yalnizken daha korkutucu
stamp(_r2, 4, 13, "$")           # gizli sandik: yalnizligin odulu
ROOM_2 = finish(_r2)

WINCH_COLUMN = _ROOM2_WIDTH - 4

# --- Oda 3: El. ★ Bolumun kalbi. -----------------------------------------
# **Dusman yok.** `docs/gdd.md` 11: romantik anlar mekanikle anlatilir ve
# bir dovusun ortasinda anlatilamaz. Bolum 4'un (Kayit Odasi) sessizligi
# ayni gerekceyle kuruldu.
#
# Odanin zemini yuksek (satir 11); ortasinda bir cukur var. Cukura
# **basamaklarla iniliyor** ve ayni basamaklardan geri cikiliyor - yani
# duserek kilitlenmek imkansiz. Cukurun SAG duvari ise 4 tile
# (`MAX_JUMP_HEIGHT_TILES` = 3): tirmanilmiyor. Yatay olarak da
# gecilmiyor - son basamak ile karsi kenar arasi 6 tile
# (`MAX_JUMP_GAP_TILES` = 4).
#
# Iki sinir da **hesaplandi, denenmedi**: "herhalde atlayamaz" demek
# oyuncunun bir kez atlayabildigi anlamina gelir ve o zaman sahnenin
# tamami atlanir.
_ROOM3_WIDTH = 20
_r3 = _room(_ROOM3_WIDTH, floor=11)

# Oda 2'nin zemininden (14) bu odanin zeminine (11) rampa. Sert bir
# duvar olsaydi oyuncu odaya giremezdi.
carve(_r3, 0, 2, 11, 13)         # yuzey 14 - oda 2 ile ayni hiza
carve(_r3, 3, 4, 11, 12)         # yuzey 13
carve(_r3, 5, 6, 11, 11)         # yuzey 12
# 7-8: yuzey 11 (kenar)

# Cukura inen basamaklar - **geri cikilabilir**.
carve(_r3, 9, 9, 11, 11)         # yuzey 12
carve(_r3, 10, 10, 11, 12)       # yuzey 13
carve(_r3, 11, 11, 11, 13)       # yuzey 14
carve(_r3, 12, 16, 11, 14)       # cukur tabani: yuzey 15
# 17-19: yuzey 11 - cukurdan 4 tile yukarida. Tek cikis: uzanan el.
ROOM_3 = finish(_r3)

CHASM_COLUMNS = range(12, 17)    # cukur tabani
CHASM_ROWS = range(11, 15)       # dogrulamada gecici olarak dolduruluyor
LEDGE_COLUMN = 14                # oyuncunun cukurda durdugu yer
LEDGE_ROW = 14                   # tabanin (15) uzerindeki hava satiri
HAND_COLUMN = 18                 # karsi kenar - sahne sonrasi birakildigi yer
HAND_ROW = 11

# --- Oda 4: Gecit. Birlikte. ---------------------------------------------
# Bulusmanin bir karsiligi olmali: yoldas geri dondu ve oda **onsuz
# zor**. Iki Kalkanli + Suruklenenler - Katman 2'nin dersi (combo'yu
# kirmak) burada ilk kez ciddi soruluyor.
_ROOM4_WIDTH = 30
_r4 = _room(_ROOM4_WIDTH)
for column in (7, 12, 21):
    stamp(_r4, column, 13, "s")
stamp(_r4, 16, 13, "k")
stamp(_r4, 24, 13, "k")
ROOM_4 = finish(_r4)

# --- Oda 5: Cikis. Dorduncu isaret. --------------------------------------
_ROOM5_WIDTH = 16
_r5 = _room(_ROOM5_WIDTH, right_wall=True)
stamp(_r5, 12, 13, "X")
ROOM_5 = finish(_r5)


ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4, ROOM_5)
LEVEL = parse("bolum-07-dar-gecit", ROWS)

ROOM_STARTS = (
    ("kapi_onu", 0),
    ("carkhane", _ROOM1_WIDTH),
    ("el", _ROOM1_WIDTH + _ROOM2_WIDTH),
    ("gecit", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH),
    ("cikis", _ROOM1_WIDTH + _ROOM2_WIDTH + _ROOM3_WIDTH + _ROOM4_WIDTH),
)

# Sutunlar birlestirilmis haritada kayiyor.
_R1 = ROOM_STARTS[0][1]
_R2 = ROOM_STARTS[1][1]
_R3 = ROOM_STARTS[2][1]

DOOR_TILES = range(_R1 + DOOR_COLUMNS.start, _R1 + DOOR_COLUMNS.stop)
GAP_TILE = _R1 + GAP_COLUMN
WINCH_TILE = (_R2 + WINCH_COLUMN, FLOOR_TOP - 1)
LEDGE_TILE = (_R3 + LEDGE_COLUMN, LEDGE_ROW)
HAND_TILE = (_R3 + HAND_COLUMN, HAND_ROW)
CHASM_TILES = range(_R3 + CHASM_COLUMNS.start, _R3 + CHASM_COLUMNS.stop)

# Catlagin acikligi (piksel). Rey'in girth'i 10 (gecer), Ardo'nunki 15
# (gecmez). Aradaki sayi: ikisini de ayiran ve ikisine de yakin olmayan
# tek deger araligi 11-14; ortasi secildi ki ileride bir karakterin
# girth'i bir iki puan oynarsa sonuc degismesin.
GAP_CLEARANCE = 12

CHEST_GOLD = 55
SECRETS_TOTAL = 1
