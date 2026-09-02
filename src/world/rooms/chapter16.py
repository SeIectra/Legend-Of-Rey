"""Bolum 16 - "Sirt Sirta". `docs/yapi.md` B16 baglayici.

    **B16 - Sirt Sirta.** Ardo geri doner, havali giris. Ama bu sefer
    **Rey de onu kurtarir.** Karsilikli.
    *Mekanik:* En uzun team-up. Asist kombolar zirvede. Bolum sonu:
    kalp balonu.

`docs/gdd.md` 11 romantik yay: *"B16 | Esitlik | Sen onu
kurtariyorsun."* `docs/ekonomi-uretim.md`: zorluk **6/10** - "team-up,
kalabalik", oyunun en yogun dovusu.

## Bolumun sekli bir CUMLE: yalniz -> birlikte -> esit

Uc perde ve ucu de oda dizilisinde:

    1-2   YALNIZ    kalabalik seni yiyor, yoldas yok
    3-5   BIRLIKTE  o geldi; asist kombo, sonra o dusuyor ve SEN
                    kaldiriyorsun
    6-7   ESIT      sirt sirta - iki taraftan geliyorlar

Ilk oda bilerek zor ve bilerek **kazanilmasi gerekmiyor**: oyuncunun
"bu kadari fazla" demesi lazim ki ikinci perdedeki giris bir kurtulus
gibi okunsun. B15 tam tersini yapmisti (yalnizlik bir beceriydi);
burada yalnizlik bir eksiklik.

## Oda sirasi

    1 yalniz     Kalabalik. Yoldas yok. "Bu kadari fazla."
    2 kapi       Dar bir geciste sikisiyorsun -> DONUS ara sahnesi
    3 birlikte   Ilk beraber dovus. **Asist kombo** ogretiliyor.
    4 dusus      O diz cokuyor -> KALDIR ara sahnesi. Ilk kaldirma.
    5 koridor    Sinav: dalgalar, ne zaman kaldiracagina SEN karar
                 veriyorsun.
    6 sirt       Zirve. Iki taraftan geliyorlar, sirt sirtasiniz.
    7 cikis      Sayim ve cikis -> KALP ara sahnesi.

Oda 4 ve 5'in farki B15'teki oda 4/5 farkinin ayni kalibi: once olay
**sana oluyor** (senaryolu dusus), sonra **sen karar veriyorsun**.
Ogret, sonra sina.

## Yoldas burada KENDI KENDINE KALKMIYOR

`Companion.self_recovers` bu bolumde False (`chapter16.py` ornekte
veriyor). Bolumun butun tezi bu - ayrinti `src/systems/rescue.py`.
Oda 4'un ara sahnesi mekanigi acikca ogretiyor; ogretilmeden
birakilsaydi oyuncu yoldassiz oynar ve bolumun yarisini gormezdi.

## Isaretler

    R oyuncu      $ sandik    X cikis    ! tetikleyici
    s Suruklenen  m Mizrakli  k Kalkanli  a Okcu  c Komutan
    n Sessiz      y Yankilayan  p Bolunen

Katman 2 ve Katman 3 birlikte: bu bolum yeni bir dusman TANITMIYOR,
on bes bolumun kadrosunu bir araya getiriyor. "Kalabalik" bir tip
degil bir **yogunluk**, ve saldiri hakki sistemi (`CLAUDE.md` 7: ayni
anda en fazla 2 dusman saldirabilir) kalabaligi adil tutuyor.
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


# --- Oda 1: Yalniz. Kalabalik seni yiyor. ------------------------------------
# Bes dusman ve yoldas yok. Kazanmak mumkun ama pahali - amac oyuncuyu
# yormak, oldurmek degil (`docs/ekonomi-uretim.md` zorluk 6, duvar
# degil).
#
# Okcu ve Komutan **birlikte**: Komutan otekileri iteliyor, Okcu
# uzaktan bastiriyor. Bu ikili B13'te tanitildi; burada yoldassiz
# karsilasmak onun ne kadar isini kolaylastirdigini gosteriyor.
_ROOM1_WIDTH = 22
_r1 = _room(_ROOM1_WIDTH, left_wall=True)
stamp(_r1, 3, 13, "R")
stamp(_r1, 10, 13, "s")
stamp(_r1, 13, 13, "m")
stamp(_r1, 16, 13, "a")
stamp(_r1, 19, 13, "c")
ROOM_1 = finish(_r1)

# --- Oda 2: Kapi. Sikisma ve DONUS. ------------------------------------------
# Dar bir gecit ve arkasindan gelen ikinci dalga. Oyuncu sikisiyor -
# tam o anda ara sahne. "Havali giris" bir odul degil bir **kurtulus**
# olmali, o yuzden tetikleyici gecidin ORTASINDA.
_ROOM2_WIDTH = 20
_r2 = _room(_ROOM2_WIDTH)
stamp(_r2, 5, 13, "k")       # Kalkanli - gecidi tikiyor
stamp(_r2, 8, 13, "s")
stamp(_r2, 11, 13, "!")      # -> DonusCinematic
ROOM_2 = finish(_r2)

# --- Oda 3: Birlikte. ASIST KOMBO ogretiliyor. -------------------------------
# Yoldas artik yaninda. Dusmanlar bilerek **dayanikli** (Kalkanli,
# Bolunen): tek basina uzun surecek isler, asistle kisaliyor. Ders
# soylenmeden ogretiliyor - oyuncu farki hissediyor.
#
# Bolunen (B14) burada ikinci kez: vurunca ikiye ayriliyor, yani
# kalabaligi oyuncunun KENDISI buyutuyor. Yoldasin degeri tam olarak
# orada okunuyor.
_ROOM3_WIDTH = 28
_r3 = _room(_ROOM3_WIDTH)
stamp(_r3, 8, 13, "k")
stamp(_r3, 14, 13, "p")
stamp(_r3, 20, 13, "s")
stamp(_r3, 24, 13, "m")
stamp(_r3, 4, 13, "$")       # gizli sandik - geri donen oyuncuya
ROOM_3 = finish(_r3)

# --- Oda 4: Dusus. O diz cokuyor, SEN kaldiriyorsun. -------------------------
# Bolumun donum noktasi. Tetikleyici odanin BASINDA: ara sahne
# dovusten once oynuyor, cunku mekanigi ogretmeden birakmak oyuncuyu
# yoldassiz birakirdi.
#
# Ara sahneden sonraki dovus bilerek orta zorlukta: ilk kaldirmayi
# **guvenle** denemesi lazim. Sinav bir sonraki odada.
_ROOM4_WIDTH = 26
_r4 = _room(_ROOM4_WIDTH)
stamp(_r4, 3, 13, "!")       # -> KaldirCinematic
stamp(_r4, 12, 13, "s")
stamp(_r4, 17, 13, "y")      # Yankilayan - sahte ipucu
stamp(_r4, 22, 13, "m")
ROOM_4 = finish(_r4)

# --- Oda 5: Koridor. Karar SENIN. --------------------------------------------
# Uzun ve kalabalik. Yoldas burada gercekten dusuyor ve **ne zaman**
# kaldiracagina oyuncu karar veriyor: simdi mi (risk), yoksa once
# ortaligi temizleyip mi (yoldassiz, daha uzun)?
#
# Ogretilen mekanigin ilk gercek maliyeti burada.
_ROOM5_WIDTH = 24
_r5 = _room(_ROOM5_WIDTH)
stamp(_r5, 6, 13, "s")
stamp(_r5, 10, 13, "a")
stamp(_r5, 14, 13, "n")      # Sessiz - Yanki gostermiyor
stamp(_r5, 19, 13, "m")
ROOM_5 = finish(_r5)

# --- Oda 6: Sirt. Zirve. -----------------------------------------------------
# Bolumun adi. Dusmanlar **iki uctan** basliyor: oyuncu ortada
# kaliyor ve yoldas dogal olarak oteki tarafa donuyor
# (`Companion._pick_target` en yakini seciyor - ayri bir "sirt sirta"
# yapay zekasi yazmak gerekmedi, dizilis yeter).
#
# Iki Komutan bilerek: her biri kendi tarafini itiyor. Ortada
# kalmanin anlami var.
_ROOM6_WIDTH = 28
_r6 = _room(_ROOM6_WIDTH)
stamp(_r6, 2, 13, "c")
stamp(_r6, 5, 13, "k")
stamp(_r6, 8, 13, "s")
stamp(_r6, 19, 13, "s")
stamp(_r6, 22, 13, "p")
stamp(_r6, 25, 13, "c")
ROOM_6 = finish(_r6)

# --- Oda 7: Cikis. -----------------------------------------------------------
_ROOM7_WIDTH = 16
_r7 = _room(_ROOM7_WIDTH, right_wall=True)
stamp(_r7, 5, 13, "!")       # -> KalpCinematic
stamp(_r7, 12, 13, "X")
ROOM_7 = finish(_r7)


ROWS = join_rooms(ROOM_1, ROOM_2, ROOM_3, ROOM_4, ROOM_5, ROOM_6, ROOM_7)
LEVEL = parse("bolum-16-sirt-sirta", ROWS)

_STARTS = (_ROOM1_WIDTH, _ROOM2_WIDTH, _ROOM3_WIDTH, _ROOM4_WIDTH,
           _ROOM5_WIDTH, _ROOM6_WIDTH)
_NAMES = ("yalniz", "kapi", "birlikte", "dusus", "koridor", "sirt", "cikis")


def _room_starts() -> tuple[tuple[str, int], ...]:
    """(oda adi, baslangic sutunu). Genislikler toplanarak turuyor.

    B15'te bu tablo elle yazilmisti ve her oda eklendiginde uc yerde
    ayni toplam tekrarlaniyordu; burada tek yerden cikiyor.
    """
    starts: list[tuple[str, int]] = []
    column = 0
    for index, name in enumerate(_NAMES):
        starts.append((name, column))
        if index < len(_STARTS):
            column += _STARTS[index]
    return tuple(starts)


ROOM_STARTS = _room_starts()

# Gizli sandik - bu bolumde tek tane.
CHEST_GOLD = 110
SECRETS_TOTAL = 1

# Hic dusmeden bitirmenin degil, **kaldirmanin** odulu.
#
# `docs/yapi.md` B16'nin olcusu yoldasi birakmamak. Yoldas bu bolumde
# kendi kendine kalkmadigi icin "hic kaldirmadan" gecmek de mumkun -
# ama o zaman bolumun yarisi yoldassiz oynanmis olur. Odul o farki
# gorunur kiliyor (`ChapterResult.ghost` ile ayni desen, B15).
LIFT_BONUS = 90
