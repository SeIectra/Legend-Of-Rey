"""Silah profilleri - yumruk/hancer/balta/kilic ayni zincir motorunu kullanir.

Arda'nin karari (22.08.2026): Rey artik tamamen silahsiz baslamiyor,
**yumrukla** basliyor - kilici Bolum 1'de buluyor. `ChainState`
(`combat/combo.py`) hangi tabloyu okuyacagini bilmiyordu, hep modul
seviyesi `CHAIN` sabitine bakiyordu; artik `Player.equip()` hangi silahi
kusandiysa onun tablosunu veriyor.

## Hancer/Balta/Yay - mimari hazir, icerik degil

Bolum 2 mini-boss sonrasi silah secimi (DEVIR.md acik madde 9) ve ileride
menzilli bir silah (yay/arbalet) bu tabloya birer `Weapon` eklemekten
ibaret olacak. Ama o secim ekrani/odul akisi ayri bir gorev - burada
yalnizca **altyapi**: Hancer ve Balta tanimli ama hicbir sahne henuz
vermiyor (CLAUDE.md: sirasi gelmemis icerik yazilmaz).

## Sprite eksigi bilerek boyle

`src/art/animation.py`'de yalnizca `rey`/`rey_armed`/`ardo` var - Hancer ve
Balta'nin kendi sprite'i yok, o yuzden `sprite_suffix="_armed"` ile
kilicla ayni gorunumu kullaniyorlar (numaralar farkli, silüet ayni).
Gercek sanat Gorev 9'un devami olarak gelecek - **acikca** boyle, sessiz
bir varsayim degil.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.config import AXE_CHAIN, CHAIN, ChainHit, DAGGER_CHAIN, FIST_CHAIN

FISTS = "fists"
SWORD = "sword"
DAGGER = "dagger"
AXE = "axe"


@dataclass(frozen=True)
class Weapon:
    key: str
    label_key: str          # Dil anahtari - hazir metin degil
    chain: tuple[ChainHit, ...]
    # "" ise cizim taban (silahsiz) sprite'ini kullanir - yumrugun kendi
    # sprite'i zaten "silahsiz Rey" oldugu icin ek varyant gerekmiyor.
    sprite_suffix: str = "_armed"


WEAPONS: dict[str, Weapon] = {
    FISTS: Weapon(FISTS, "weapon.fists", FIST_CHAIN, sprite_suffix=""),
    SWORD: Weapon(SWORD, "weapon.sword", CHAIN, sprite_suffix="_armed"),
    DAGGER: Weapon(DAGGER, "weapon.dagger", DAGGER_CHAIN, sprite_suffix="_armed"),
    AXE: Weapon(AXE, "weapon.axe", AXE_CHAIN, sprite_suffix="_armed"),
}


def get(key: str) -> Weapon:
    return WEAPONS.get(key, WEAPONS[FISTS])


def starting_weapon(character: str) -> str:
    """Rey yumrukla baslar; Ardo egitimli bir yabanci, kilicla gelir."""
    return SWORD if character == "ardo" else FISTS
