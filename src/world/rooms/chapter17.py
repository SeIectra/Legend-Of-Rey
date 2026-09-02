"""Bolum 17 - "Ikili Kule". `docs/yapi.md` B17 baglayici.

    ★B17 - Ikili Kule. Ayri yollardan tirmanis, karakter arasi gecis.
    *Bulmaca:* Biri kolu tutar, digeri gecer. Sonra tersi.
    Camdan/parmakliktan birbirini gorursunuz ama dokunamazsiniz.
    *Romantik an:* Mekanik olarak "birbirine bagimli olmak." Anlatim
    degil, oynanis.

`docs/gdd.md` 11: *"B17 | Bagimlilik | Biri olmadan gecilmiyor."*
`docs/ekonomi-uretim.md`: zorluk **5/10** - "bulmaca agirlikli".

## Tek kule, ORTADAN bolunmus

Harita 26 x 48 - B9'un kulesiyle ayni olculer, ama ortasinda iki
tile'lik bir bolme var:

    sutun  0  1 | 2 ....... 11 | 12 13 | 14 ....... 23 | 24 25
           duvar  SOL SAFT        BOLME    SAG SAFT      duvar

Bolme gercek `SOLID` tile - iki karakter birbirine **dokunamiyor**.
Ama cizimde parmaklik olarak gorunuyor ve isik gecirdigi icin
oteki saftaki figur secilebiliyor: belgenin "camdan/parmakliktan
birbirinizi gorursunuz" cumlesi.

## Kimse tek basina tirmanamiyor - ama sebep B9'unkinden BASKA

B9'da katlar arasi 8 tile idi ve firlatma zorunluydu: **mesafe**
engeldi. Burada katlar arasi 3 tile, yani ziplama yetiyor -
engel **kapi**. Ayni cumle ("birlikte"), iki farkli dille soylenmis;
tek fikri iki bolum ayni sekilde tekrarlasaydi ikincisi gereksiz
olurdu.

## Bulmacanin sekli: SIRAYLA

Bes kat, bes kapi, ve plaka **degisimli**:

    kat 1  plaka SOLDA  -> kapi SAGDA     (ogretme: en kolay yerlesim)
    kat 2  plaka SAGDA  -> kapi SOLDA     "sonra tersi"
    kat 3  plaka SOLDA  -> kapi SAGDA
    kat 4  plaka SAGDA  -> kapi SOLDA
    kat 5  plaka SOLDA  -> kapi SAGDA
    zirve  plaka SAGDA  -> **cikis kapisi** SOLDA

Her katta bir saft serbest, oteki kapali. Serbest olan tirmaniyor,
kapali olan otekinin plakaya basmasini bekliyor - ve siradaki katta
roller degisiyor. "Biri kolu tutar, digeri gecer. **Sonra tersi.**"

Zirve ozel ve gerekcesi asagida (`SUMMIT_STAGE`): cikis yalnizca sol
safta ve onundeki kapiyi sagdaki karakter tutuyor. Yani bolum
"biri kapiyi tutarken oteki cikiyor" goruntusuyle bitiyor.

## Kapilar basili tutuldugu surece acik

Arda 02.09.2026: B6'nin `PlateGate`i bir kez acilinca acik kalir
(gerekce: oyuncuyu arenaya hapsetmemek). Burada `latching=False`:
plakadan inince kapi kapaniyor. Latch'lenseydi mekanik bir dizi tek
seferlik dugmeye donerdi ve bolumun adi "bagimlilik" olmazdi.

Hapsolma riski iki sekilde kapali: kapi sutununda biri dururken
kapanmiyor (`PlateGate.blocked_by`), ve kule yukari tek yon - gecen
karakterin geri donmesi gerekmiyor.

## Isaretler

    R  soldaki oyuncunun dogumu   $ sandik   X cikis   ! tetikleyici

Sagdaki dogum, plakalar ve kapilar isaret DEGIL - asagidaki sabitler.
Ayni gerekce B6 ve B9'da da yazildi: yalniz bir bolumde gecen harf
ortak sozlugu sisirir.
"""
from __future__ import annotations

from src.world.level import parse

WIDTH = 26
HEIGHT = 48

# Saftlarin sinirlari (sutun). Bolme iki tile: dokunulmaz ama gorunur.
LEFT_MIN, LEFT_MAX = 2, 11
DIVIDER = (12, 13)
RIGHT_MIN, RIGHT_MAX = 14, 23

# Katlarin zemin satirlari - **asagidan yukari**. Aralarinda 6 tile
# var ama ortada birer cikinti duruyor (3 + 3), yani ziplama
# (3,8 tile) tek basina yetiyor. B9'un tersi: orada mesafe engeldi,
# burada kapi.
FLOOR_ROWS = (45, 39, 33, 27, 21)
LEDGE_ROWS = (42, 36, 30, 24, 18)
# Ikisinin bulustugu tepe.
SUMMIT_ROW = 15

CEILING = 3


def _blank() -> list[list[str]]:
    """Bos kule govdesi: yanlarda duvar, ortada bolme, icerisi hava."""
    rows: list[list[str]] = []
    for y in range(HEIGHT):
        if y < CEILING or y >= HEIGHT - 2:
            rows.append(["#"] * WIDTH)
            continue
        row = ["." for _ in range(WIDTH)]
        row[0] = row[1] = "#"
        row[-1] = row[-2] = "#"
        for column in DIVIDER:
            row[column] = "#"
        rows.append(row)
    return rows


def _floor(rows: list[list[str]], y: int, gaps: tuple = ()) -> None:
    """Iki safta da kat zemini - `gaps` sutunlari **acik** birakilir.

    Bosluk sart: ilk surumde katlar tamamen doluydu ve alttaki
    cikintida duran karakter yukari ziplayinca tavana carpiyordu -
    kule hic tirmanilamiyordu. Her katin, altindaki cikintinin tam
    ustunde bir gecidi olmali.
    """
    open_columns = set()
    for x0, x1 in gaps:
        open_columns.update(range(x0, x1 + 1))
    for x in range(LEFT_MIN, LEFT_MAX + 1):
        rows[y][x] = "." if x in open_columns else "#"
    for x in range(RIGHT_MIN, RIGHT_MAX + 1):
        rows[y][x] = "." if x in open_columns else "#"


def _ledge(rows: list[list[str]], y: int, x0: int, x1: int) -> None:
    """Ara cikinti - ziplayarak ulasilan kucuk platform."""
    for x in range(x0, x1 + 1):
        rows[y][x] = "="


# Cikintilarin sutun araliklari. Cift katlarda saftin SAG yarisinda,
# tek katlarda SOL yarisinda - karakterin her katta yon degistirmesi
# tirmanisa ritim veriyor ve kapiyi yolun ustune koyuyor.
LEDGE_SPANS = {
    0: ((8, 11), (20, 23)),     # cift: sag yari
    1: ((2, 5), (14, 17)),      # tek: sol yari
}

# Gecidin sutunlari - cikintidan **dar**, ve bilerek.
#
# Ilk surumde gecit cikintiyla ayni genislikteydi ve karakter yukari
# ziplayinca inecek yer bulamiyordu: delikten geciyor, ustunde bos
# hava buluyor, geri dusuyordu. Gecit iki tile, yanindaki iki tile
# zemin kaliyor - karakter delikten cikip **yanina** iniyor.
#
# Ve inis noktasi kapinin BERISINDE: kata cikan karakter kapiyi
# gecmis olmuyor, bulmaca bozulmuyor.
HOLE_SPANS = {
    0: ((8, 9), (20, 21)),
    1: ((4, 5), (16, 17)),
}


def _spans(index: int) -> tuple:
    return LEDGE_SPANS[index % 2]


def _holes(index: int) -> tuple:
    return HOLE_SPANS[index % 2]


_rows = _blank()

# --- Katlar ------------------------------------------------------------------
# Her katin zemini tam, ustunde iki ara cikinti. Cikintilar saftin
# **kapinin otesindeki** yarisinda: yani kapi kapaliyken tirmanilamaz.
#
# Kapi sutunu saftin ortasinda; plaka kapinin BERISINDE (oyuncunun
# geldigi tarafta) degil, OTEKI safta - bulmaca zaten bu.
for _index, _floor_row in enumerate(FLOOR_ROWS):
    # Kat zemini: taban dolu, ustundekilerde ALTTAKI cikintinin
    # hizasinda bir gecit var.
    _floor(_rows, _floor_row,
           gaps=() if _index == 0 else _holes(_index - 1))
    for _x0, _x1 in _spans(_index):
        _ledge(_rows, LEDGE_ROWS[_index], _x0, _x1)

# Tepe: son cikintinin ustunde gecit var, bolmede yok - bulusma ara
# sahnede oluyor (belge: "dokunamazsiniz").
_floor(_rows, SUMMIT_ROW, gaps=_holes(len(FLOOR_ROWS) - 1))

# --- Kapilar ve plakalar -----------------------------------------------------
# (kat, plakanin_safti, kapinin_safti). Degisimli - `docs/yapi.md`
# "Biri kolu tutar, digeri gecer. **Sonra tersi.**"
#
# Kapi sutunu her katta saftin ortasinda: cikintiya ulasmak icin oradan
# gecmek sart.
GATE_COLUMN_LEFT = 7
GATE_COLUMN_RIGHT = 19

# Plaka kapinin ACILDIGI saftin degil, OTEKININ icinde.
PLATE_COLUMN_LEFT = 4
PLATE_COLUMN_RIGHT = 21


def _stage(index: int) -> dict:
    """Bir katin plaka/kapi tanimi. Cift indekste plaka SOLDA."""
    floor_row = FLOOR_ROWS[index]
    plate_left = index % 2 == 0
    if plate_left:
        plates = [(PLATE_COLUMN_LEFT, floor_row)]
        gate_column = GATE_COLUMN_RIGHT
    else:
        plates = [(PLATE_COLUMN_RIGHT, floor_row)]
        gate_column = GATE_COLUMN_LEFT
    return {
        "floor_row": floor_row,
        "plates": plates,
        "gate_column": gate_column,
        # Kapi zeminden cikintinin **iki tile ustune** kadar.
        #
        # Bir tile yeterli degildi: ziplama 3,8 tile ve kat yuksekligi
        # 3, yani apeks kapinin tepesiyle ayni hizaya geliyordu -
        # oyuncu kapinin uzerinden atlayip bulmacayi atlayabilirdi.
        # Iki tile apeksi kesin olarak altta birakiyor.
        "gate_rows": tuple(range(LEDGE_ROWS[index] - 2, floor_row)),
    }


STAGES = [_stage(i) for i in range(len(FLOOR_ROWS))]

# --- Zirve: biri kapiyi TUTUYOR, oteki cikiyor -------------------------------
#
# Ilk tasarim son kata iki plaka koyuyordu ("ikisi birden gerekiyor").
# Yazarken cikti: iki karakter var ve ikisi de plakadaysa **gececek
# kimse kalmiyor.** Bulmaca cozulemezdi.
#
# Yerine gecen sey daha iyi ve zaten belgede yaziyordu
# (`docs/gdd.md` 11, B17'nin romantik ani): *"Mekanik olarak
# birbirine bagimli olmak."* Zirvede cikis SOL safta, onunde bir kapi,
# ve o kapiyi acan plaka SAG safta. Yani:
#
#     biri kapiyi tutuyor, oteki cikiyor - ve tutan geride kaliyor.
#
# Bolumun son hareketi bir bulmaca degil bir **karar goruntusu**.
# Kapanis ara sahnesi bunun uzerine kuruluyor.
SUMMIT_GATE_COLUMN = 7
SUMMIT_GATE_ROWS = tuple(range(SUMMIT_ROW - 5, SUMMIT_ROW))
# Plaka sag saftin **zemini olan** kisminda: 20-21 gecit, oraya plaka
# konamaz.
SUMMIT_PLATE = (17, SUMMIT_ROW)

SUMMIT_STAGE = {
    "floor_row": SUMMIT_ROW,
    "plates": [SUMMIT_PLATE],
    "gate_column": SUMMIT_GATE_COLUMN,
    "gate_rows": SUMMIT_GATE_ROWS,
}

ALL_STAGES = STAGES + [SUMMIT_STAGE]

# Kapilari haritaya **kapali** olarak isle - oyun basinda hepsi kapali.
for _stage_data in ALL_STAGES:
    for _row in _stage_data["gate_rows"]:
        _rows[_row][_stage_data["gate_column"]] = "#"

# --- Yerlesim ----------------------------------------------------------------
# Soldaki dogum isaretli ("R") - `LEVEL.first("player")` ve
# `tools/reachability.py` onu okuyor. Sagdaki bir sabit: yalniz bu
# bolumde gecen bir harf ortak sozlugu sisirirdi.
_rows[FLOOR_ROWS[0] - 1][3] = "R"
SPAWN_RIGHT = (15, FLOOR_ROWS[0] - 1)

# Gizli sandik: ilk katin sag saftinda, kapinin OTESINDE. Yani ancak
# bulmacayi cozen goruyor - ve gormek icin geri donmesi gerekmiyor,
# yol zaten oradan geciyor.
_rows[FLOOR_ROWS[1] - 1][22] = "$"

# Tepe: tetikleyici ve cikis, ikisi de zirve kapisinin **otesinde**
# (sutun 7'nin solunda). Yani cikisa ancak kapi tutulurken varilyor.
#
# Gecit sutun 8-9'da; cikisi oraya koymak onu delige koymak olurdu.
_rows[SUMMIT_ROW - 1][5] = "!"
_rows[SUMMIT_ROW - 1][3] = "X"

ROWS = ["".join(row) for row in _rows]
LEVEL = parse("bolum-17-ikili-kule", ROWS)

# Kat adlari - `chapter17.py` `_floor_at(y)` ile okuyor. B9'un deseni.
FLOOR_NAMES = ("taban", "ikinci", "ucuncu", "dorduncu", "zirve")

CHEST_GOLD = 120
SECRETS_TOTAL = 1

# Hic dusmeden degil, **az gecisle** bitirmenin odulu.
#
# B15 "hic uyandirmadan", B16 "kaldirarak" olcuyordu. Burada olcu
# **verimlilik**: bulmacayi anlayan oyuncu az gecisle cikiyor,
# deneme-yanilma yapan cok gecisle. Ceza yok - yalnizca odul.
TIDY_SWITCHES = 14
TIDY_BONUS = 100


# --- Dogrulama yardimcilari --------------------------------------------------
def open_terrain() -> list[str]:
    """Butun kapilari **acik** haldeki zemin.

    `tools/reachability.py` bunu okuyor. Kapali haritayla dogrulama
    yapmak yanlis olurdu: kapilar bulmacanin kendisi, ve arac
    "bulmaca cozulmus mu" diye degil **geometri saglam mi** diye
    bakiyor - ziplama yuksekligi, gecit genisligi, ulasilamayan
    kose var mi.
    """
    rows = [list(row) for row in LEVEL.terrain_rows]
    for stage in ALL_STAGES:
        for row in stage["gate_rows"]:
            rows[row][stage["gate_column"]] = "."
    return ["".join(row) for row in rows]


def shaft_tiles(left: bool) -> set[tuple[int, int]]:
    """Bir saftin tile'lari - otekini "bilerek erisilemez" saymak icin.

    Iki karakter iki ayri safta ve aralarinda gercek duvar var; tek
    dogumdan yapilan bir tarama otekini elbette bulamaz. Dogru soru
    "hepsi bir yerden erisiliyor mu" degil, **"her saft kendi
    dogumundan tirmanilabiliyor mu"**.
    """
    x0, x1 = (LEFT_MIN, LEFT_MAX) if left else (RIGHT_MIN, RIGHT_MAX)
    return {(x, y) for x in range(x0, x1 + 1) for y in range(HEIGHT)}
