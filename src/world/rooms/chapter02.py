"""Bolum 2 - "Ilk Inis". Dikey dilim.

`docs/bolum-02.md` oda oda tasarlandi. *"Oyunun normal dokusunu tam
kalitede kanitlamak. Bu bolum iyiyse oyun iyidir."*

## Odalar yan yana, kesme yok

Sekiz oda tek surekli haritada. Kapili gecisler yerine akici kaydirma:
bolum bir **yer** gibi hissetsin, birbirine baglanmis sahneler gibi degil.
Her oda kendi ASCII blogu olarak yaziliyor ve `join_rooms` birlestiriyor -
tek blok 380 sutun olurdu ve okunamazdi.

## Isaretler

    R oyuncu   s Suruklenen   t Tirmanan   b Sismek   M mini-boss
    W kilic    B kirilabilir duvar   $ sandik   ! tetikleyici   X cikis

## Ziplama zarfi

Her basilabilir kat bir oncekinden en fazla **3 tile** yukarida
(`MAX_JUMP_HEIGHT_TILES`), ucurumlar en fazla **4 tile**.
`tests/test_level.py` her kosuda dogruluyor - Bolum 1'de bu kontrol iki
gercek hata yakaladi.

## Ogretim sirasi

Odalarin sirasi rastgele degil, her biri bir soru soruyor:

    2  ilk kan          uc vurusluk zincir, kill cancel
    3  yukari bak       dikey farkindalik
    4  Yanki odasi      ana mekanigin dogdugu an  ★
    4A gizli oda        kesfin karsiligi - **hemen** verilir
    5  patlayanlar      konumlandirma
    6  kacinma dersi    dar alan, karsi vurus kendi kesfedilir
    7  mini-boss        ogrenilenin sinavi
"""
from __future__ import annotations

from src.world.level import join_rooms, parse

# Butun odalar 16 satir. Zemin satir 14, tavan satir 0.
# Satir 11 = zeminden 3 tile yukari, satir 8 = 6, satir 5 = 9.

# --- Oda 1: Inis. Dusman yok, nefes. Cakil zemin, tirmik izi. -------------
ROOM_1 = [
    "################",
    "################",
    "################",
    "################",
    "#...............",
    "#...............",
    "#...............",
    "#...............",
    "#...............",
    "#...............",
    "#...............",
    "#...............",
    "#...............",
    "#.R.............",
    "################",
    "################",
]

# --- Oda 2: Ilk Kan. Ilk dusman **tek basina**. --------------------------
# Tasarim notu: ilk Suruklenen kesinlikle yalniz. Oyuncunun ilk combo'sunu
# kesintisiz tamamlamasi butun dovus sistemine dair ilk izlenimi belirler.
ROOM_2 = [
    "########################",
    "########################",
    "########################",
    "########################",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "........................",
    "..........####..........",
    "........................",
    "....s.........s...s...$.",
    "########################",
    "########################",
]

# --- Oda 3: Yukari Bak. Uc kademeli, tavanda Tirmananlar. ----------------
ROOM_3 = [
    "############################",
    "############################",
    "############################",
    "....########....########....",
    "....t...............t.......",
    "............................",
    "............................",
    "............................",
    "......####..........####....",
    "............................",
    "............................",
    "..####..........####........",
    "............................",
    "..............s.............",
    "############################",
    "############################",
]

# --- Oda 4: YANKI ODASI. Cikmaz gibi gorunur; sag duvar kirilabilir. -----
# Ogretim zirvesi: Yanki kendiliginden yukselir, catlak parlar, kirilir.
ROOM_4 = [
    "####################",
    "####################",
    "####################",
    "####################",
    "...................B",
    "...................B",
    "...................B",
    "...................B",
    "...................B",
    "...................B",
    "...................B",
    "..........####.....B",
    "...................B",
    "....!..............B",
    "####################",
    "####################",
]

# --- Oda 4-A: GIZLI ODA. Muzik kesilir. Comert. --------------------------
# Ilk gizli alan comert olmali; oyuncu bir daha hep arar.
#
# Oda 4'un catlagi **ogretiyor** - kirmadan ilerlenemez, Yanki catlagi
# gosteriyor. Buradaki ikinci catlak ise **sinav**: hicbir ipucu yok,
# ana yol alt koridordan duz gecip gidiyor. Ogrendigini uygulayan
# oyuncu yukari tirmanip ikinci catlagi kiriyor ve sandigi buluyor;
# uygulamayan farkina bile varmadan geciyor.
#
# Bolum sonu ekraninin "0/1 gizli alan" satiri ancak boyle anlamli:
# gizli oda ana yolun uzerinde olsaydi herkes 1/1 gorurdu.
ROOM_4A = [
    "################",
    "################",
    "################",
    "################",
    "################",
    ".......#########",
    "........B......#",
    "........B...$..#",
    ".......#########",
    "................",
    "................",
    "...####.........",
    "................",
    "................",
    "################",
    "################",
]

# --- Oda 5: Patlayanlar. Ilk Sismek **tek basina, genis alanda**. --------
ROOM_5 = [
    "############################",
    "############################",
    "############################",
    "############################",
    "..........t.................",
    "............................",
    "............................",
    "............................",
    "............................",
    "............................",
    "............................",
    ".......####.....####........",
    "............................",
    ".....b............s..b..s...",
    "############################",
    "############################",
]

# --- Oda 6: Kacinma Dersi. Dar, iki yonden dort Suruklenen. --------------
ROOM_6 = [
    "########################",
    "########################",
    "########################",
    "########################",
    "########################",
    "########################",
    "########################",
    "########################",
    "########################",
    "........................",
    "........................",
    "........................",
    "........................",
    "..s...s........s....s...",
    "########################",
    "########################",
]

# --- Oda 7: MINI-BOSS arenasi. Iki yan platform - guvenli alan yok. ------
ROOM_7 = [
    "############################",
    "############################",
    "############################",
    "############################",
    "............................",
    "............................",
    "............................",
    "............................",
    "............................",
    "............................",
    "............................",
    "..####................####..",
    "............................",
    ".............M..............",
    "############################",
    "############################",
]

# --- Oda 8: Cikis. Dovussuz. Ikinci tirmik izi. --------------------------
ROOM_8 = [
    "################",
    "################",
    "################",
    "################",
    "################",
    "################",
    "################",
    "...............#",
    "...............#",
    "...............#",
    "...............#",
    "...............#",
    "...............#",
    ".............X.#",
    "################",
    "################",
]

ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4, ROOM_4A,
                  ROOM_5, ROOM_6, ROOM_7, ROOM_8)

LEVEL = parse("bolum-02-ilk-inis", ROWS)

# Oda sinirlari - tetikleyiciler ve anlatim icin. (ad, baslangic tile)
ROOM_STARTS = (
    ("inis", 0),
    ("ilk_kan", 16),
    ("yukari_bak", 40),
    ("yanki_odasi", 68),
    ("gizli_oda", 88),
    ("patlayanlar", 104),
    ("kacinma", 132),
    ("miniboss", 156),
    ("cikis", 184),
)

# Duvarda tirmik izleri - Cemo'nun boyunda. (tile_x, tile_y)
# Ikincisi belgeye gore "daha derin, daha caresiz".
CLAW_MARKS = ((9, 12), (188, 12))

# Mesaleler. (tile_x, tile_y, yaniyor_mu)
# `tile_y` mesalenin **asili oldugu tavanin altindaki** ilk bos satir.
# Odalarin tavan yuksekligi ayni degil (Oda 6 satir 8'e, Oda 8 satir 6'ya
# kadar dolu), o yuzden her mesale kendi odasinin tavanina gore yaziliyor.
# `tests/test_chapter02.py` her mesalenin ustunde gercekten tavan olup
# olmadigini dogruluyor - havada asili bir isik kaynagi sahneyi bozuyor.
# Gizli odadaki **sonmus**: buraya birisi gelmis ve donmemis.
TORCHES = (
    (6, 4, True),                 # Oda 1 - inis
    (28, 4, True),                # Oda 2 - "mesale isigi ortada"
    (46, 4, True),                # Oda 3
    (76, 4, True),                # Oda 4 - Yanki odasi
    (101, 6, False),              # Gizli odacik - **sonmus**
    (112, 4, True),               # Oda 5
    (126, 4, True),
    (144, 9, True),               # Oda 6 - alcak tavan
    (166, 4, True),               # Oda 7 - arena
    (178, 4, True),
    (190, 7, True),               # Oda 8 - cikis
)

# Iki kirilabilir duvarin **anlamlari farkli**, o yuzden ikisi de adiyla
# aniliyor. Sutun numarasi tek ayirt edici: Yanki duvari 87, gizli oda
# duvari 96. Sahne kirilan tile'in sutununa bakip hangisi oldugunu anliyor.
# Gizli odacigin **zemin satiri**. Ana koridor onun altindan (satir 13)
# duz gecip gidiyor; sutun araligi ikisinde de ayni. Sessizlik yalnizca
# odacigin icinde olmali, altindan gecerken degil - yoksa gizli odayi hic
# bulmamis oyuncu da sessizligi yasar ve efekt anlamini kaybeder.
SECRET_CHAMBER_FLOOR_ROW = 8

ECHO_WALL_COLUMN = 87            # Ogretici - kirmadan ilerlenemez
SECRET_WALL_COLUMN = 96          # Sinav - hicbir ipucu yok
# Bu sutundan buyuk her kirilabilir duvar gizli odaya ait.
SECRET_WALL_MIN_COLUMN = 88

# Mini-boss arenasinin kapisi bu sutunda iniyor (Oda 7'nin girisi).
ARENA_DOOR_COLUMN = 157
ARENA_DOOR_ROWS = range(4, 14)

# Arenanin CIKIS kapisi - bastan KILITLI (src/world/keydoor.py).
# Arda'nin bildirdigi hata: giris kapisi muhurlense de arkada hicbir sey
# yoktu, oyuncu boss'a hic dokunmadan saga yuruyup cikis odasina
# geciyordu. Bu kapi o kacagi kapatiyor; anahtari boss dusuruyor.
# Sutun 180: arenanin sag ucu, cikis odasi (184) baslamadan once.
ARENA_EXIT_COLUMN = 180
ARENA_EXIT_ROWS = range(4, 14)

# Yanki odasinda ses bu kadar kare sonra **kendiliginden** yukselir.
# Belge "oyuncu takilir, birkac saniye sonra" diyor: 150 kare = 2.5 saniye.
# Daha kisasi oyuncuya takilma firsati vermiyor, daha uzunu sikiyor.
ECHO_RISE_DELAY = 150
ECHO_RISE_FRAMES = 180           # Ses bu kadar kare acik kalir

# Tirmik izinin yaninda kamera bu kadar kare oyalanir (belge: ~0.5 sn).
CLAW_LINGER_FRAMES = 34

# Bolumdeki gizli alan sayisi. Bolum sonu ekraninin "0/1" satiri bundan.
SECRETS_TOTAL = 1

# Sandik degerleri (docs/bolum-02.md "ALTIN AKISI")
CHEST_GOLD_MAIN = 30
CHEST_GOLD_SECRET = 80
BOSS_GOLD = 55
