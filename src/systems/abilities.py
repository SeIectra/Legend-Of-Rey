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

# **Yalnizca Rey'e ait** yetenekler. Ardo'nun Yanki'si yok
# (`docs/gdd.md` 3, kanon); onun karsiligi Iz Surme.
#
# Kayit tek dosya ve ayni kayitla iki karakter de oynanabiliyor, yani
# Rey'in kazandigi `echo_sight` orada duruyor. Geri yuklerken
# suzulmezse Ardo oynanisinda Yanki aciliyordu - sessiz bir kanon
# ihlali (`tests/test_chapter01.py` yakaladi).
ECHO_SET: Final[frozenset[str]] = frozenset({ECHO_SIGHT, ECHO_ASK})

# Bir yetenegin **anlati icinde ilk kez verildigi** bolum.
#
# Kayittan geri yukleme bu tabloyu okuyor: bir yetenek tanitildigi
# bolumden ONCE (ve o bolumun kendisinde) geri yuklenmiyor. Sebep
# somut: ilerlemis bir kayitla Bolum 1'i tekrar oynayan oyuncuya kilici
# basta vermek "kilici buluyor" anini cope atar; Bolum 2'nin Yanki
# odasina Yanki Gorusu ile girmek de o odayi anlamsizlastirir.
#
# Ikisi de gercekten oldu ve `tests/test_weapon_choice.py` ile
# `tests/test_chapter02.py` yakaladi.
#
# Bolum o yetenegi zaten kendi akisinda veriyor - tablo yalnizca
# "erken verme" diyor, "hic verme" demiyor.
INTRODUCED_IN: Final[dict[str, int]] = {
    SWORD: 1,           # B1: koyde bulunuyor
    DODGE: 2,           # B2: ilk inis
    ECHO_SIGHT: 2,      # B2: Yanki odasi
    ECHO_ASK: 3,        # B3: karanlikta soru sormak
}


def restorable(ability: str, chapter: int) -> bool:
    """Bu yetenek bu bolumde kayittan geri yuklenebilir mi?"""
    return chapter > INTRODUCED_IN.get(ability, 0)


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
