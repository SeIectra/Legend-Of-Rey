"""Bolum 4 - "Kayit Odasi". `docs/yapi.md` B4 baglayici.

    ★B4 - Kayit Odasi. Dovus yok. Onceki maceracinin kampi: iskelet,
    gunluk (resimli, kelimesiz), yarim harita.
    Ilerleme: Ilk yetenek agaci ekrani. Rey burada kolyeyi ilk kez
    cevirir - sessiz karakter ani.

`docs/gdd.md` bunu **★nefes** bolumu diye isaretliyor ve `docs/yapi.md`
uygulama notu da ayni seyi soyluyor: *"Nefes bolumleri (B4, B8, B12) sifir
dovus kodu ister. Sadece dekor + yuruyus + panel."* Bu dosyada bu yuzden
**hicbir dusman isareti yok** - `s`, `t`, `b`, `g`, `M` hicbiri gecmiyor.
Bolum 2 ve 3'te olan arena/kapi/anahtar makinesi de yok: kapatilacak bir
sey yok.

## Isaretler

    R oyuncu   $ sandik   X cikis

Kamp, gunluk, yarim harita ve kolye ani **isaret degil**, asagidaki tile
sabitleri. Sebep Bolum 3'teki Mor Alev kaidesi ile ayni: bunlarin hicbiri
carpisan ya da doguran bir varlik degil, cizilen ve yaklasilan bir nokta.
`level.MARKERS`'a dort yeni harf eklemek butun bolumlerin ortak sozlugunu
yalnizca bu bolum icin sisirirdi.

## Odalar kod ile insa ediliyor

`chapter03.py` ile ayni: `_room()` duz bir tuval acar, `stamp()` tek
karakter koyar, `raise_floor()` zemini bir kademe yukseltir. Elle ASCII
sayarken olan sutun kaymasi (chapter02.py'de bir kez yasandi) boylece
yapisal olarak imkansiz.

## Kirik merdiven - Oda 3

Yarim harita kirik merdivenin **tepesinde** duruyor. Kademeler birer tile:
14 -> 13 -> 12 -> 11 ve simetrik olarak geri iniyor. Ziplama zarfi 3 tile
(`MAX_JUMP_HEIGHT_TILES`) ama nefes bolumunde sinira dayanmak yanlis olur -
oyuncu burada zorlanmamali, bakmali. Kademe **ayrica** ana yolun kendisi:
oyuncu haritanin ustunden yurumeden gecemez, yani buluntu kacirilamaz.
Bu bilincli - bu bolumun gizli alani yok (`SECRETS_TOTAL = 0`), yarim
harita bir odul degil bir **anlati** parcasi.
"""
from __future__ import annotations

from src.world.level import join_rooms, parse

ROOM_HEIGHT = 16          # Butun odalar 16 satir (chapter02/03 ile ayni)
FLOOR_TOP = 14            # Zemin satir 14 - basilabilir satir 13


def _room(width: int, ceiling: int = 4, floor: int = FLOOR_TOP,
          left_wall: bool = False, right_wall: bool = False) -> list[list[str]]:
    """Duz bir oda tuvali: `ceiling` satir tavan, `floor`den asagisi zemin.

    Zemin butun genislik boyunca kesintisiz - odalar arasi gecis hep bu
    satirdan. `left_wall`/`right_wall` yalnizca ilk/son odada disariya
    tasmayi onlemek icin; ara odalarda kullanilmaz.
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


def raise_floor(rows: list[list[str]], x0: int, x1: int, top: int) -> None:
    """`x0`..`x1` (dahil) sutunlarinda zemini `top` satirina yukseltir.

    Oyuncu govdesi 2 tile: zemine basan oyuncu **satir 12 ve 13'u** kapliyor.
    Bu yuzden ana koridorun uzerinden gecen hicbir kutle 12'ye inemez
    (chapter03.py'nin gizli cebinde ayni kural pahaliya ogrenildi). Burada
    sorun yok cunku yukseltilen sey koridorun **kendisi** - altindan
    gecilecek bir yol yok, uzerinden yurunuyor.
    """
    for x in range(x0, x1 + 1):
        for y in range(top, FLOOR_TOP):
            rows[y][x] = "#"


def finish(rows: list[list[str]]) -> list[str]:
    return ["".join(row) for row in rows]


# --- Oda 1: Inis. Bolum 3'un karanligindan cikis. Bos. --------------------
# Ilk oda bilerek **bos**: oyuncu Bolum 3'ten mesale ekonomisi ve bir
# mini-boss'la cikiyor. Nefes bolumunun ilk isi omuzlari indirmek.
_r1 = _room(22, left_wall=True)
stamp(_r1, 2, 13, "R")
ROOM_1 = finish(_r1)

# --- Oda 2: Kamp. Iskelet, sonmus ates, dagilmis esya, gunluk. -----------
# Odanin genisligi (34) bilincli: kamp ogeleri arasinda **yuruyecek yer**
# olmali. Hepsi bir araya toplanirsa vitrin gibi okunuyor; dagilinca
# birinin gercekten burada yasadigi hissi cikiyor.
_r2 = _room(34)
stamp(_r2, 29, 13, "$")
ROOM_2 = finish(_r2)

# --- Oda 3: Kirik Merdiven. Yarim harita tepede. -------------------------
_r3 = _room(30, ceiling=3)
raise_floor(_r3, 8, 10, 13)
raise_floor(_r3, 11, 13, 12)
raise_floor(_r3, 14, 19, 11)      # Sahanlik - yarim harita burada
raise_floor(_r3, 20, 22, 12)
raise_floor(_r3, 23, 25, 13)
ROOM_3 = finish(_r3)

# --- Oda 4: Esik. Kolye ani ve cikis. -------------------------------------
# Oda uzun ve bos: kolye ani icin bosluk gerekiyor. Ekranda baska hicbir
# sey olmadigi icin oyuncunun gozu kolyeye gidiyor - "sessiz karakter ani"
# ancak sessiz bir odada olur.
_r4 = _room(26, right_wall=True)
stamp(_r4, 22, 13, "X")
ROOM_4 = finish(_r4)

ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4)

LEVEL = parse("bolum-04-kayit-odasi", ROWS)

# Oda sinirlari - tetikleyiciler ve anlatim icin. (ad, baslangic tile)
_WIDTHS = (22, 34, 30, 26)
_starts: list[tuple[str, int]] = []
_acc = 0
for _name, _width in zip(("inis", "kamp", "kirik_merdiven", "esik"), _WIDTHS):
    _starts.append((_name, _acc))
    _acc += _width
ROOM_STARTS = tuple(_starts)

_room1_start = ROOM_STARTS[0][1]
_room2_start = ROOM_STARTS[1][1]
_room3_start = ROOM_STARTS[2][1]
_room4_start = ROOM_STARTS[3][1]

# --- Kamp (Oda 2) ---------------------------------------------------------
# Hepsi (tile_x, tile_y) - `tile_y` uzerinde **durulan** satir, yani nesne
# bu tile'in altina oturur. Zemin satiri 13 oldugu icin hepsi 13.
SKELETON_TILE = (_room2_start + 9, 13)      # Duvara yaslanmis, oturur
FIRE_TILE = (_room2_start + 14, 13)         # Sonmus ates - kampin merkezi
JOURNAL_TILE = (_room2_start + 19, 13)      # Kelimesiz gunluk
# Dagilmis esya: (tile_x, tile_y, tur). Tur `chapter04_render` icinde cizilir.
GEAR_TILES: tuple[tuple[int, int, str], ...] = (
    (_room2_start + 6, 13, "bedroll"),
    (_room2_start + 12, 13, "flask"),
    (_room2_start + 17, 13, "pack"),
    (_room2_start + 23, 13, "sword"),
    (_room2_start + 26, 13, "flask"),
)

# --- Yarim harita (Oda 3) -------------------------------------------------
# Sahanligin ortasi. Butun konum sabitleri gibi bu da oyuncunun **icinde
# durdugu** bos tile'i gosteriyor (kati zemini degil): sahanligin ust kati
# satir 11, dolayisiyla uzerinde durulan bos satir 10. Nesne
# `(tile_y + 1) * TILE_SIZE` yuksekligine, yani zemine oturur - kamp
# ogeleriyle ayni sozlesme.
HALF_MAP_TILE = (_room3_start + 16, 10)

# --- Kolye ani (Oda 4) ----------------------------------------------------
# Odanin ortasina yakin ama cikistan uzak: an bittikten sonra oyuncunun
# yurumeye devam edecek yeri kalsin, ekran hemen kapanmasin.
NECKLACE_TILE = (_room4_start + 9, 13)

# --- Mesaleler - (tile_x, tile_y, yaniyor_mu) -----------------------------
# `tile_y` mesalenin asili oldugu tavanin altindaki ilk bos satir
# (`cave_backdrop.draw_torches` sozlesmesi). Oda 3'un tavani bir satir
# yukarida (ceiling=3), o yuzden oradakiler 3.
#
# Kampin iki yanindaki ikisi **sonuk**: bu bolumde yanan her mesale
# oyuncunun degil, birinin **birakip gittigi** isik. Kampin kendi atesi
# sonmus; yanindaki yuvalarin da yanmasi celiski olurdu.
TORCHES: tuple[tuple[int, int, bool], ...] = (
    (_room1_start + 5, 4, True),
    (_room1_start + 16, 4, True),
    (_room2_start + 4, 4, True),
    (_room2_start + 13, 4, False),          # Kampin ustu - sonuk
    (_room2_start + 16, 4, False),
    (_room2_start + 27, 4, True),
    (_room3_start + 5, 3, True),
    (_room3_start + 16, 3, True),           # Sahanligin ustu - harita gorunsun
    (_room3_start + 26, 3, True),
    (_room4_start + 4, 4, True),
    (_room4_start + 20, 4, True),
)

# --- Sayilar --------------------------------------------------------------
# Sandik: maceracinin kendi kesesi. Bolum 2'nin ana sandigindan (30) az,
# cunku burada dovus yok - `docs/ekonomi-uretim.md`'nin zorluk/odul
# dengesi bunu ister.
CHAPTER4_CHEST_GOLD = 25

# Bu bolumde gizli alan yok. Nefes bolumu kesif degil **duraklama**;
# "0/1 gizli alan" satiri burada oyuncuya bir sey kacirdigini soylerdi ve
# duraklamayi goreve cevirirdi.
SECRETS_TOTAL = 0
