"""Bolum 12 - "Mektup". `docs/yapi.md` B12 baglayici.

    ★B12 - Mektup. Ardo'nun gectigi yoldan gidiyorsun. Kamp
    kalintilari, onun cizdigi isaretler, senin icin birakilmis erzak,
    **duvara kazinmis kucuk bir figur: sen.**
    *Romantik an:* Yoklugunda anlatilan yakinlik. Tek bir dovus yok,
    sadece iz surme.

`docs/gdd.md` 138: *"12 | Mektup ★nefes | Ardo'nun izleri - yoklukta
yakinlik"*. `docs/ekonomi-uretim.md`: zorluk **—** (nefes, dovus yok).
`docs/asset-plani.md` 57: B12 anlatim paneli alan bes bolumden biri.

## Bolum bir KUYU

Bolum 9 dikey kaliba oncu oldu (tek uzun harita, `_floor_at(y)`).
Burasi ayni fikir ama ters yonde: kule tirmaniliyordu, kuyuya
**iniliyor**.

Sekli mekanik belirledi. Ardo'nun kurdugu kafes asagi iniyor ve tek
kontrol fren; isaretler duvarlarda, yalnizca yavasken okunuyor.
Yatay bir bolumde "yavasla" demek yururken durmak olurdu - yani
hicbir sey. Dikeyde yercekimi sizi surekli ilerletiyor, durmak bir
**karar** oluyor.

## Kuyu dar - bilerek

Genislik 15 tile, kafes 5. Iki yanda birer tile'lik bosluk kaliyor,
yani isaretler her zaman **kolun uzanabilecegi** kadar yakin. Genis
bir kuyuda isaretler uzakta kalirdi ve okumak bir mesafe sorunu
olurdu; oysa soru mesafe degil **dikkat**.

## Erisilebilirlik

Kuyunun icinde zemin YOK - orada yururek inilmiyor, kafesle
iniliyor. `tools/reachability.py` bunu bilmiyor, o yuzden dogrulama
sirasinda kafesin gectigi sutuna gecici basamaklar konuyor (Bolum
7'nin cukuru ve Bolum 9'un kulesi ile ayni yaklasim: senaryolu
gecisi varsay, geri kalan her seyi gercekten sina).

## Isaretler

    R oyuncu   N Mum Bekcisi   X cikis   ! tetikleyici

Kafes, Ardo'nun isaretleri ve kamp kalintilari isaret DEGIL -
asagidaki sabitler. Bir kere gecen harf ortak sozlugu sisirir.
"""
from __future__ import annotations

from src.world.level import parse

# Genislik ekranin tamamini kapliyor: 30 tile = 480 piksel = ic
# cozunurlugun tam eni. Ilk surum 15 genisti ve kamera haritanin
# disini gosteriyordu - ekranin yarisi **duz siyah**ti. Ekran
# goruntusu bunu gosterdi.
#
# Kuyu yine dar (7 tile); genisleyen sey etrafindaki KAYA. Yani
# duzeltme gorsel bir yamadan ibaret degil: kuyu artik bosluga
# asili degil, bir kutlenin **icine oyulmus**. Dar bir yarigin iki
# yaninda tonlarca tas olmasi zaten anlatilmak istenen sey.
WIDTH = 30
HEIGHT = 68

# Ust oda (kuyu basi) ve dip oda zeminleri.
TOP_FLOOR = 8
BOTTOM_FLOOR = HEIGHT - 4

# Dip odanin tavani. Kuyu buraya kadar dar; asagisi tekrar aciliyor.
# Kafes dip odanin **icine** iniyor, tavanindan degil - inen kisi
# odaya varmali, tavana carpmamali.
BOTTOM_ROOM_TOP = BOTTOM_FLOOR - 6

# Kuyu agzi: kafesin indigi dikey aralik.
SHAFT_TOP = TOP_FLOOR
SHAFT_BOTTOM = BOTTOM_FLOOR - 1

# Kafesin yatay merkezi (tile) ve kuyunun ic genisligi. Kafes 5
# tile; kuyu 7. Iki yanda birer tile bosluk kaliyor, yani isaretler
# her zaman kolun uzanabilecegi kadar yakin.
RIG_CENTER_TILE = WIDTH // 2
SHAFT_HALF = 3
SHAFT_LEFT = RIG_CENTER_TILE - SHAFT_HALF
SHAFT_RIGHT = RIG_CENTER_TILE + SHAFT_HALF


def _blank() -> list[list[str]]:
    """Kuyu: ustte ve altta genis oda, arada kayaya oyulmus dar yarik.

    Odalar tam genislikte (yuruyecek yer gerek), kuyu bolumu dar ve
    **iki yani dolu kaya**. Kesit soyle:

        ##############  oda
        ##..........##
        ####........##  <- kuyu agzi
        #####....#####
        #####    #####  <- yarik: yalnizca kafesin gectigi yer
        #####    #####
        #####....#####
        ##..........##  oda
        ##############
    """
    rows: list[list[str]] = []
    for y in range(HEIGHT):
        if y < 2 or y >= HEIGHT - 2:
            rows.append(["#"] * WIDTH)
            continue
        row = ["."] * WIDTH
        row[0] = row[1] = "#"
        row[-1] = row[-2] = "#"
        rows.append(row)
    return rows


def _carve_shaft() -> None:
    """Ust odanin altindan dip odaya kadar her seyi kayaya cevirip
    yalnizca yarigi aciyor."""
    for y in range(TOP_FLOOR + 1, BOTTOM_ROOM_TOP):
        for x in range(WIDTH):
            _rows[y][x] = "." if SHAFT_LEFT <= x <= SHAFT_RIGHT else "#"


_rows = _blank()


def _floor(row: int) -> None:
    for x in range(2, WIDTH - 2):
        _rows[row][x] = "#"


# --- Ust oda: KUYU BASI ------------------------------------------------------
# Ardo'nun kampi. Sogumus ates, birakilmis denk, ve kuyuya kurdugu
# duzenek. Dusman YOK - `docs/ekonomi-uretim.md`: nefes bolumu.
_floor(TOP_FLOOR)
_rows[TOP_FLOOR - 1][3] = "R"        # oyuncu
_rows[TOP_FLOOR - 1][4] = "!"        # ara sahne 1 - kuyu agzinin SOLUNDA

# Kuyu agzi: ust odanin zemininde kafesin gececegi delik.
for _x in range(SHAFT_LEFT, SHAFT_RIGHT + 1):
    _rows[TOP_FLOOR][_x] = "."

# Ve kuyunun kendisi - iki yani dolu kaya.
_carve_shaft()

# --- Dip oda -----------------------------------------------------------------
# Zemin ve **altindaki her sey** dolu. Ilk surumde `_blank()` govdeyi
# HEIGHT-3'e kadar oyuyordu ve dip zeminin altinda bir satirlik
# erisilemez cep kaliyordu - `tools/reachability.py` bunu yakalar,
# ama haritayi bastan dogru yazmak daha ucuz.
for _row in range(BOTTOM_FLOOR, HEIGHT):
    _rows[_row] = ["#"] * WIDTH

# Kafes dibe indiginde oyuncu buraya iniyor. Uc sey yan yana ve
# **araliklari genis**: ara sahne, Bekci, cikis. Ilk yerlesimde Bekci
# tetikleyicinin uzerine denk gelmisti (ikisi de sutun 10) ve
# tetikleyici sessizce kayboluyordu - ara sahne hic oynamiyordu.
_rows[BOTTOM_FLOOR - 1][RIG_CENTER_TILE + 2] = "!"   # ara sahne 2
_rows[BOTTOM_FLOOR - 1][WIDTH - 4] = "N"             # Mum Bekcisi (3. kez)
_rows[BOTTOM_FLOOR - 1][WIDTH - 3] = "X"             # cikis


ROWS = ["".join(row) for row in _rows]
LEVEL = parse("bolum-12-mektup", ROWS)


# --- Ardo'nun biraktiklari ---------------------------------------------------
# (tile_y, taraf, dil_anahtari, tur). Taraf -1 sol duvar, +1 sag.
#
# Siralamanin kendisi bir anlatim: once **islevsel** seyler (ok,
# erzak), sonra **kisisel** olanlar (kamp, kirik kalem), en sonda
# figur. Ardo yolun basinda ise yariyor, sonunda ozluyor.
#
# `docs/yapi.md` B12'nin dort ogesi de burada ve **hicbiri dovus
# degil**: isaret, erzak, kamp kalintisi, kazinmis figur.
# Anahtarlar **iki ayri duz dize** olarak duruyor - `key + "_ardo"`
# diye hesaplanmiyor. `tests/test_lang.py` hesaplanan anahtari
# GOREMIYOR ve bu bolumde tam olarak bu tuzaga dusuldu: on iki Ardo
# repligi "olu anahtar" diye raporlandi, oysa hepsi kullaniliyordu.
# Projedeki ucuncu tekrar; CLAUDE.md 9 bunu acikca yaziyor.
MARKS = (
    (14, -1, "line.ch12_mark_arrow", "line.ch12_mark_arrow_ardo", "mark"),
    (21, +1, "line.ch12_mark_cache", "line.ch12_mark_cache_ardo", "cache"),
    (29, -1, "line.ch12_mark_camp", "line.ch12_mark_camp_ardo", "camp"),
    (37, +1, "line.ch12_mark_count", "line.ch12_mark_count_ardo", "mark"),
    (45, -1, "line.ch12_mark_pencil", "line.ch12_mark_pencil_ardo", "camp"),
    # ★ Bolumun tepesi. `docs/yapi.md`: *"duvara kazinmis kucuk bir
    # figur: sen."* En sonda ve tek basina - once beslemis, sonra
    # yol gostermis, en sonunda ozlemis.
    (54, +1, "line.ch12_mark_figure", "line.ch12_mark_figure_ardo", "figure"),
)

MARKS_TOTAL = len(MARKS)

# Erzak sandiginin altini (`docs/ekonomi-uretim.md`: B12 nefes, altin
# akisi yok - bu bir ODUL degil bir JEST, o yuzden kucuk).
CACHE_GOLD = 30
