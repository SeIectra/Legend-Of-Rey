"""Ses efekti icerigi: YANKI + KOLYE PUSULASI (SES-LISTESI 3-4).

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


# --- 3. YANKI -------------------------------------------------------------------
_ECHO_FREQS = (220.0, 277.0, 330.0)


@_register("echo_open")
def _echo_open() -> np.ndarray:
    n = synth.samples(0.24)
    body = synth.chorus(_ECHO_FREQS, 0.24)
    return synth.normalize(body * synth.env_ad(n, attack=0.9, decay=0.1))


@_register("echo_loop")
def _echo_loop() -> np.ndarray:
    """Surekli, kelimesiz fisilti - `AudioMixer.play_loop()` ile dongude
    calinir. Frekanslar tam sayi devir yapacak sekilde secildi -
    kesintisiz baglaniyor (ek olarak `loop_smooth` tik'i temizler)."""
    seconds = 2.0
    body = synth.chorus(_ECHO_FREQS, seconds, spread=0.02)
    breath = synth.lowpass(synth.noise(seconds, seed=71), 900.0) * 0.12
    mixed = synth.mix(body * 0.5, breath)
    return synth.normalize(synth.loop_smooth(mixed, blend=800))


@_register("echo_close")
def _echo_close() -> np.ndarray:
    n = synth.samples(0.32)
    body = synth.chorus(_ECHO_FREQS, 0.32)
    return synth.normalize(body * synth.env_ad(n, attack=0.05, decay=0.95))


@_register("echo_ask")
def _echo_ask() -> np.ndarray:
    return synth.normalize(synth.tone_sweep(0.18, 320.0, 620.0, attack=0.15,
                                            decay=0.6))


@_register("echo_answer_truth")
def _echo_answer_truth() -> np.ndarray:
    """Net, tek, guven veren."""
    tone = synth.sine(440.0, 0.22)
    n = len(tone)
    return synth.normalize(tone * synth.env_ad(n, attack=0.06, decay=0.85))


# `echo_answer_lie` dogruyla **AYNI** olmali (SES-LISTESI 3: "Dogruyla ayni
# olmali. Oyuncu kulaktan anlamamali." - mekanigin kalbi bu satirda).
SFX["echo_answer_lie"] = _echo_answer_truth


@_register("echo_answer_partial")
def _echo_answer_partial() -> np.ndarray:
    """Ayni ton ama **kirik**, yarim kalan."""
    full = _echo_answer_truth()
    cut = full[: int(len(full) * 0.55)]
    n = len(cut)
    return synth.normalize(cut * synth.env_ad(n, attack=0.06, decay=0.8))


@_register("echo_tier_down")
def _echo_tier_down() -> np.ndarray:
    return synth.normalize(synth.tone_sweep(0.32, 500.0, 220.0, attack=0.05,
                                            decay=0.8))


@_register("echo_tier_up")
def _echo_tier_up() -> np.ndarray:
    return synth.normalize(synth.tone_sweep(0.32, 300.0, 640.0, attack=0.05,
                                            decay=0.7))


@_register("echo_silent")
def _echo_silent() -> np.ndarray:
    """Ani kesilme + cinlama - kulak cinlamasi gibi."""
    ring = synth.sine(5200.0, 0.9)
    n = len(ring)
    return synth.normalize(ring * synth.env_exp_decay(n, rate=3.0))


@_register("echo_reveal")
def _echo_reveal() -> np.ndarray:
    tone = synth.sine(180.0, 0.1)
    n = len(tone)
    return synth.normalize(tone * synth.env_exp_decay(n, rate=12.0))


@_register("echo_wall")
def _echo_wall() -> np.ndarray:
    tone = synth.mix(synth.sine(260.0, 0.14), synth.sine(390.0, 0.14) * 0.4)
    n = len(tone)
    return synth.normalize(tone * synth.env_exp_decay(n, rate=9.0))


@_register("echo_sonar")
def _echo_sonar() -> np.ndarray:
    """Tek can tinisi ve yayilan dalga (docs/bolum-03.md)."""
    bell = synth.mix(synth.sine(660.0, 0.5), synth.sine(1320.0, 0.5) * 0.3)
    n = len(bell)
    return synth.normalize(bell * synth.env_exp_decay(n, rate=4.0))


# --- 4. KOLYE PUSULASI -----------------------------------------------------------
@_register("necklace_beat")
def _necklace_beat() -> np.ndarray:
    """Tak-tak cift vurus, alcak, gogusten."""
    pulse = synth.thump(0.05, 130.0, 70.0, decay=20.0, noise_amt=0.05, seed=81)
    gap = np.zeros(int(synth.SAMPLE_RATE * 0.05), dtype=np.float32)
    second = synth.thump(0.05, 130.0, 70.0, decay=20.0, noise_amt=0.05,
                         seed=81) * 0.7
    return synth.normalize(np.concatenate([pulse, gap, second]))


@_register("necklace_warm")
def _necklace_warm() -> np.ndarray:
    tone = synth.sine(500.0, 0.07)
    n = len(tone)
    return synth.normalize(tone * synth.env_exp_decay(n, rate=16.0))


@_register("necklace_conflict")
def _necklace_conflict() -> np.ndarray:
    """Iki ses ust uste, hafif akortsuz - temanin sesi."""
    tone = synth.mix(synth.sine(400.0, 0.3), synth.sine(413.0, 0.3) * 0.8)
    n = len(tone)
    return synth.normalize(tone * synth.env_ad(n, attack=0.1, decay=0.85))
