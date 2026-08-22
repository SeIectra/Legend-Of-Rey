"""Ses efekti icerigi: DOVUS + HAREKET (`assets/audio/SES-LISTESI.md` 1-2).

Kayit defterinin geri kalani `sfx.py`'de birlestirilir - bkz. o dosyanin
docstring'i icin genel aciklama (onbellekleme, bogulmus set, perde
varyasyonu).
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from src.audio import synth

SFX: dict[str, Callable[[], np.ndarray]] = {}


def _register(name: str) -> Callable:
    def wrap(fn: Callable[[], np.ndarray]) -> Callable[[], np.ndarray]:
        SFX[name] = fn
        return fn
    return wrap


# --- 1. DOVUS -----------------------------------------------------------------
@_register("hit_light")
def _hit_light() -> np.ndarray:
    return synth.normalize(synth.thump(0.09, 200.0, 90.0, decay=16.0, seed=11))


@_register("hit_heavy")
def _hit_heavy() -> np.ndarray:
    return synth.normalize(synth.thump(0.18, 110.0, 45.0, decay=7.0,
                                       noise_amt=0.22, seed=12))


@_register("hit_counter")
def _hit_counter() -> np.ndarray:
    """Diger vuruslardan **belirgin farkli** - metalik cinlama, odul sesi."""
    ring = synth.mix(synth.sine(880.0, 0.16), synth.sine(1320.0, 0.16) * 0.5,
                     synth.sine(1760.0, 0.16) * 0.25)
    n = len(ring)
    return synth.normalize(ring * synth.env_exp_decay(n, rate=5.0))


@_register("hit_kill")
def _hit_kill() -> np.ndarray:
    """Islak, kisa, kesin - kill cancel'in duyulur isareti."""
    return synth.normalize(synth.thump(0.11, 140.0, 40.0, decay=18.0,
                                       noise_amt=0.35, seed=13))


@_register("swing_light")
def _swing_light() -> np.ndarray:
    return synth.normalize(synth.whoosh(0.12, 800.0, 3200.0, seed=21))


@_register("swing_heavy")
def _swing_heavy() -> np.ndarray:
    return synth.normalize(synth.whoosh(0.22, 500.0, 2200.0, seed=22))


@_register("player_hurt")
def _player_hurt() -> np.ndarray:
    """Nefes kesilmesi + kumas - aci cigligi DEGIL."""
    breath = synth.lowpass(synth.noise(0.22, seed=31), 1400.0)
    n = len(breath)
    return synth.normalize(breath * synth.env_ad(n, attack=0.1, decay=0.9))


@_register("player_death")
def _player_death() -> np.ndarray:
    return synth.normalize(synth.tone_sweep(0.8, 260.0, 40.0, attack=0.02,
                                            decay=0.95))


@_register("dodge")
def _dodge() -> np.ndarray:
    scrape = synth.lowpass(synth.noise(0.07, seed=41), 2600.0)
    n = len(scrape)
    return synth.normalize(scrape * synth.env_exp_decay(n, rate=10.0))


# --- 2. HAREKET ----------------------------------------------------------------
@_register("step_stone")
def _step_stone() -> np.ndarray:
    hit = synth.noise(0.06, seed=51)
    n = len(hit)
    return synth.normalize(hit * synth.env_exp_decay(n, rate=22.0))


@_register("step_earth")
def _step_earth() -> np.ndarray:
    hit = synth.lowpass(synth.noise(0.08, seed=52), 1200.0)
    n = len(hit)
    return synth.normalize(hit * synth.env_exp_decay(n, rate=14.0))


@_register("step_water")
def _step_water() -> np.ndarray:
    splash = synth.lowpass(synth.noise(0.10, seed=53), 2000.0)
    n = len(splash)
    return synth.normalize(splash * synth.env_ad(n, attack=0.05, decay=0.9))


@_register("step_gravel")
def _step_gravel() -> np.ndarray:
    crunch = synth.noise(0.09, seed=54)
    n = len(crunch)
    return synth.normalize(crunch * synth.env_exp_decay(n, rate=9.0))


@_register("jump")
def _jump() -> np.ndarray:
    return synth.normalize(synth.whoosh(0.10, 400.0, 2400.0, seed=61))


@_register("land_soft")
def _land_soft() -> np.ndarray:
    return synth.normalize(synth.thump(0.09, 160.0, 70.0, decay=15.0,
                                       noise_amt=0.25, seed=62))


@_register("land_hard")
def _land_hard() -> np.ndarray:
    return synth.normalize(synth.thump(0.16, 130.0, 45.0, decay=8.0,
                                       noise_amt=0.35, seed=63))


@_register("ledge_grab")
def _ledge_grab() -> np.ndarray:
    scratch = synth.lowpass(synth.noise(0.08, seed=64), 2200.0)
    n = len(scratch)
    return synth.normalize(scratch * synth.env_exp_decay(n, rate=16.0) * 0.6)
