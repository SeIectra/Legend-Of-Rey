"""Ses efekti kayit defteri - `assets/audio/SES-LISTESI.md`'nin oncelik 1
seti (dikey dilim icin sart) + kod-kaynakli birkac ek anahtar.

Her `sfx_*.py` dosyasi kendi bolumunu tutar (dosya basina 400 satir
kurali - CLAUDE.md 11); bu dosya yalnizca **birlestirir**. Icerige
uretim mantigi icin `sfx_combat.py`'nin ust docstring'ine bak.

## Neden sentez, kayit degil

`docs/derinlestirme.md` ve `CLAUDE.md` 6 sprite'lar icin "kod ile uret,
elle cizme" diyor. Bu ortamda ne bir ses kaydi stüdyosu ne bir ses
tasarimcisi var; ayni ilkeyi sese uyguluyoruz - `src/audio/synth.py`
numpy ile dalga formu uretiyor. **Bu acikca bir ilk gecis**
(CLAUDE.md 12): gercek kayit/profesyonel ses gelirse `assets/audio/*.ogg`
eklenip yalnizca bu dosyanin okuma sekli degisir, geri kalan (mixer,
muffled set, pitch varyasyonu) aynen kalir.

## ★ Bogulmus (muffled) set

`docs/dovus-sistemi.md` 5: Yanki acikken gercek zamanli filtre yok, her
★'li sesin **onceden alcak-geciren filtreden gecmis ikinci kopyasi**
calinir. `MUFFLED_KEYS` SES-LISTESI'ndeki 12 ★ satirla birebir ayni.

## Donguler

`LOOP_KEYS` - `AudioMixer.play_loop()`/`stop_loop()` ile calinan
anahtarlar (echo_loop, journey_*, amb_*, intro_hum). Bunlarin dalga
formu `synth.loop_smooth()` ile bas/son karistirilarak uretilir; kesin
sifir-tikirtili loop degil ama isitilir bir tik birakmiyor.

## Onbellekleme ve perde varyasyonu

`SoundBank` (bkz. `mixer.py`) her anahtari **bir kez** uretir ve
`PITCH_VARIANTS` kadar perde varyanti onceden hazirlar
(`docs/derinlestirme.md` 1.6: +-%8) - kare icinde numpy yeniden
ornekleme yapmamak icin.
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from src.audio import sfx_combat, sfx_enemies, sfx_ui, sfx_world

SFX: dict[str, Callable[[], np.ndarray]] = {
    **sfx_combat.SFX, **sfx_world.SFX, **sfx_enemies.SFX, **sfx_ui.SFX,
}

# SES-LISTESI'ndeki 12 ★ satirla birebir ayni (dogrulamasi tests/test_audio.py).
MUFFLED_KEYS: frozenset[str] = frozenset({
    "hit_light", "hit_heavy", "hit_counter", "hit_kill", "player_hurt",
    "step_stone", "step_earth", "step_water", "step_gravel",
    "shambler_tell", "climber_tell", "bloated_fuse",
})

# `AudioMixer.play_loop()` ile calinacak surekli sesler.
LOOP_KEYS: frozenset[str] = frozenset({
    "echo_loop", "intro_hum", "journey_wind", "journey_cellar",
    "journey_night", "amb_village_night", "amb_cellar", "amb_torch",
    "amb_water", "amb_deep",
})

MUFFLE_CUTOFF_HZ = 900.0        # Bogulmus kopyanin alcak-geciren esigi


def keys() -> frozenset[str]:
    return frozenset(SFX.keys())
