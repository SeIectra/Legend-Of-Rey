"""Rey ve Ardo'nun sayisal farklari.

`docs/dovus-sistemi.md` 8 baglayicidir. Tasarim niyeti: **Rey bilgiyle ve
akisla kazanir, Ardo zamanlamayla ve dayaniklilikla.** Ardo'nun Yanki
eksikligi, karsi vurus gucuyle telafi edilir - yardim almiyorsa okumayi iyi
bilmeli.

Veri burada, davranis `player.py`'de. Ikinci karakter oynanabilir olunca bu
ayrim buyuyecek.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.config import (
    ARDO_CHAIN_WINDOW, ARDO_DODGE_CHARGES, ARDO_MAX_HEALTH,
    ARDO_MOVE_MULTIPLIER, COUNTER_DAMAGE_BONUS, COUNTER_DAMAGE_BONUS_ARDO,
    REY_CHAIN_WINDOW, REY_DODGE_CHARGES, REY_MAX_HEALTH, REY_MOVE_MULTIPLIER,
)


@dataclass(frozen=True)
class CharacterStats:
    name: str
    move_multiplier: float
    max_health: int
    chain_window: int
    dodge_charges: int
    counter_bonus: float
    has_echo: bool
    sprite_name: str        # src.art.animation.CHARACTERS icindeki anahtar
    body_color: str         # Kutu kipinde kullanilir (F4)
    accent_color: str


REY = CharacterStats(
    name="Rey",
    move_multiplier=REY_MOVE_MULTIPLIER,
    max_health=REY_MAX_HEALTH,
    chain_window=REY_CHAIN_WINDOW,
    dodge_charges=REY_DODGE_CHARGES,
    counter_bonus=COUNTER_DAMAGE_BONUS,
    has_echo=True,
    sprite_name="rey",
    body_color="abyss_light",
    accent_color="echo_bright",
)

ARDO = CharacterStats(
    name="Ardo",
    move_multiplier=ARDO_MOVE_MULTIPLIER,
    max_health=ARDO_MAX_HEALTH,
    chain_window=ARDO_CHAIN_WINDOW,
    dodge_charges=ARDO_DODGE_CHARGES,
    counter_bonus=COUNTER_DAMAGE_BONUS_ARDO,
    has_echo=False,
    sprite_name="ardo",
    body_color="stone",
    accent_color="ember_light",
)
