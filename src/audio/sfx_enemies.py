"""Ses efekti icerigi: DUSMANLAR (SES-LISTESI 5).

Bkz. `sfx.py` docstring'i - genel aciklama orada.
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


@_register("shambler_idle")
def _shambler_idle() -> np.ndarray:
    growl = synth.lowpass(synth.noise(0.22, seed=91), 500.0)
    n = len(growl)
    return synth.normalize(growl * synth.env_ad(n, attack=0.3, decay=0.6))


@_register("shambler_tell")
def _shambler_tell() -> np.ndarray:
    """Nefes cekme - vurustan ONCE."""
    breath = synth.lowpass(synth.noise(0.3, seed=92), 700.0)
    n = len(breath)
    return synth.normalize(breath * synth.env_ad(n, attack=0.85, decay=0.15))


@_register("shambler_attack")
def _shambler_attack() -> np.ndarray:
    return synth.normalize(synth.whoosh(0.14, 300.0, 1800.0, seed=93))


@_register("shambler_death")
def _shambler_death() -> np.ndarray:
    return synth.normalize(synth.thump(0.35, 90.0, 30.0, decay=5.0,
                                       noise_amt=0.4, seed=94))


@_register("climber_cling")
def _climber_cling() -> np.ndarray:
    scratch = synth.lowpass(synth.noise(0.12, seed=101), 3000.0)
    n = len(scratch)
    return synth.normalize(
        scratch * synth.env_ad(n, attack=0.2, decay=0.7) * 0.5)


@_register("climber_tell")
def _climber_tell() -> np.ndarray:
    """Sallanma + toz dokulmesi."""
    rattle = synth.mix(synth.noise(0.3, seed=102) * 0.6,
                       synth.sine(60.0, 0.3) * 0.3)
    n = len(rattle)
    return synth.normalize(rattle * synth.env_ad(n, attack=0.7, decay=0.3))


@_register("climber_drop")
def _climber_drop() -> np.ndarray:
    return synth.normalize(synth.tone_sweep(0.18, 500.0, 120.0, attack=0.02,
                                            decay=0.9))


@_register("climber_death")
def _climber_death() -> np.ndarray:
    """Bocegsi catirti - birkac kisa tik ust uste."""
    gap = np.zeros(int(synth.SAMPLE_RATE * 0.015), dtype=np.float32)
    clicks = [np.concatenate([
        synth.click(0.02, freq=1800.0 + i * 340.0, seed=103 + i), gap,
    ]) for i in range(4)]
    return synth.normalize(np.concatenate(clicks))


@_register("bloated_idle")
def _bloated_idle() -> np.ndarray:
    breath = synth.lowpass(synth.noise(0.3, seed=111), 350.0)
    n = len(breath)
    return synth.normalize(breath * synth.env_ad(n, attack=0.4, decay=0.5))


@_register("bloated_fuse")
def _bloated_fuse() -> np.ndarray:
    """Siseme - surekli yukselen. Sabit sure, ogrenilebilir."""
    return synth.normalize(synth.tone_sweep(0.5, 90.0, 340.0, attack=0.9,
                                            decay=0.1))


@_register("bloated_explode")
def _bloated_explode() -> np.ndarray:
    return synth.normalize(synth.thump(0.32, 80.0, 25.0, decay=4.0,
                                       noise_amt=0.55, seed=112))


@_register("enemy_stagger")
def _enemy_stagger() -> np.ndarray:
    tone = synth.sine(180.0, 0.09)
    n = len(tone)
    return synth.normalize(tone * synth.env_exp_decay(n, rate=18.0))


@_register("enemy_blocked")
def _enemy_blocked() -> np.ndarray:
    ring = synth.mix(synth.sine(760.0, 0.12), synth.sine(1140.0, 0.12) * 0.4)
    n = len(ring)
    return synth.normalize(ring * synth.env_exp_decay(n, rate=10.0))


@_register("enemy_tell")
def _enemy_tell() -> np.ndarray:
    """Genel/yedek tell sesi - tip bazli ozel sesi olmayan dusman icin
    (`Enemy.tell_sound` varsayilani). Kod-kaynakli yeni anahtar; hicbir
    SES-LISTESI satirinda yoktu, buraya eklendi (dosyanin kendi kurali:
    "kodun gercekten cagirdigi olaylardan turetildi")."""
    return _shambler_tell()
