"""Yetenek kapilari - neyi ne zaman yapabilirsin.

Prototipte iyi calisan bir seydi ve Arda geri istedi: kilici sonradan
almak, atilmayi sonradan ogrenmek.

## Neden sadece "bir sey acilmasi"ndan fazlasi

Bir yetenegi bastan vermek onu **gorunmez** yapar. Oyuncu kacinmayla
baslarsa kacinma "tuslardan biri" olur. Otuz dakika kacinmadan oynayip
sonra ogrenirse, o an bir sey **kazanmis** olur - ve o andan sonra her
kacinma bir hatirlatma.

Bolum 1'de bu hikayeyle de ortusuyor: Rey bir koy kizi. Cemo kacirildiginda
elinde **yalnizca kolye** var. Kilic zindanda bulunuyor, cunku oraya kadar
kilicla gitmesinin bir sebebi yok.

## Kapi tek yerde

`Player.has()` disinda hicbir yerde "bu yetenek var mi" sorusu sorulmuyor.
Dagitilsaydi biri mutlaka bir yerde unutulur ve oyuncu henuz almadigi bir
seyi yapabilirdi - ki bunu fark etmek neredeyse imkansiz olur.

Kayitta **liste** olarak duruyor: yeni yetenek eklemek kayit surumu
degistirmiyor, eski kayitlar sadece o yetenege sahip olmuyor.
"""
from __future__ import annotations

from typing import Final

# --- Yetenek anahtarlari ----------------------------------------------------
# Kayit dosyasinda bu dizeler duruyor; **degistirilmeleri eski kayitlari
# bozar.** Yeni yetenek eklemek serbest, var olani yeniden adlandirmak degil.
SWORD: Final[str] = "sword"           # Saldiri - B1 sonunda bulunur
DODGE: Final[str] = "dodge"           # Kacinma - B2'de ogrenilir
ECHO_SIGHT: Final[str] = "echo_sight"  # Yanki Gorusu - B1 tutorial
ECHO_ASK: Final[str] = "echo_ask"     # Yanki'ya soru sorma - B4
DOUBLE_JUMP: Final[str] = "double_jump"
WALL_JUMP: Final[str] = "wall_jump"

ALL: Final[tuple[str, ...]] = (
    SWORD, DODGE, ECHO_SIGHT, ECHO_ASK, DOUBLE_JUMP, WALL_JUMP,
)

# Ardo hikayeye sonradan katiliyor; **egitimli** bir yabanci, sifirdan
# baslamiyor. Rey'in ogrenme yayini tekrar oynatmak anlamsiz olurdu.
ARDO_STARTING: Final[frozenset[str]] = frozenset({SWORD, DODGE})

# Rey hicbir seyle baslamiyor - koy kizi.
REY_STARTING: Final[frozenset[str]] = frozenset()


def starting_set(character: str) -> set[str]:
    return set(ARDO_STARTING if character == "ardo" else REY_STARTING)


def label_key(ability: str) -> str:
    """Yetenek kazanildiginda gosterilecek metnin dil anahtari.

    Anahtarlar **acikca** yazili: f-string ile kurulan anahtari
    tests/test_lang.py kaynak taramasinda goremiyor.
    """
    return {
        SWORD: "ability.sword",
        DODGE: "ability.dodge",
        ECHO_SIGHT: "ability.echo_sight",
        ECHO_ASK: "ability.echo_ask",
        DOUBLE_JUMP: "ability.double_jump",
        WALL_JUMP: "ability.wall_jump",
    }.get(ability, "ability.unknown")
