"""Ses efekti icerigi: MENU + ACILIS/GECISLER + ORTAM (SES-LISTESI 6-8).

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


# --- 6. MENU VE ARAYUZ -----------------------------------------------------------
# Kare dalga (square wave) burada **bilerek kullanilmiyor** - ilk surumde
# ui_tick/ui_deny/ui_slider kare dalgaydi ve "rahatsiz edici, oyunun
# havasina uymuyor" geri bildirimi aldi (Arda, 22.08.2026, canli oynanis).
# Kare dalga sert/vizir bir 8-bit bip'i - LORE'un karanlik/atmosferik
# tonuyla celisiyor. Yerine yumusak sinus + kisa sonme kullaniliyor.
@_register("ui_tick")
def _ui_tick() -> np.ndarray:
    tone = synth.sine(720.0, 0.035)
    n = len(tone)
    return synth.normalize(tone * synth.env_exp_decay(n, rate=30.0)) * 0.5


@_register("ui_confirm")
def _ui_confirm() -> np.ndarray:
    tone = synth.mix(synth.sine(500.0, 0.1), synth.sine(760.0, 0.1) * 0.6)
    n = len(tone)
    return synth.normalize(tone * synth.env_ad(n, attack=0.1, decay=0.8))


@_register("ui_back")
def _ui_back() -> np.ndarray:
    return synth.normalize(synth.tone_sweep(0.12, 520.0, 320.0, attack=0.05,
                                            decay=0.8))


@_register("ui_deny")
def _ui_deny() -> np.ndarray:
    tone = synth.sine(160.0, 0.1)
    n = len(tone)
    return synth.normalize(tone * synth.env_exp_decay(n, rate=11.0)) * 0.6


@_register("ui_slider")
def _ui_slider() -> np.ndarray:
    tone = synth.sine(560.0, 0.03)
    n = len(tone)
    return synth.normalize(tone * synth.env_exp_decay(n, rate=32.0)) * 0.4


@_register("ui_tab")
def _ui_tab() -> np.ndarray:
    return synth.normalize(synth.tone_sweep(0.1, 420.0, 640.0, attack=0.2,
                                            decay=0.6))


@_register("save_written")
def _save_written() -> np.ndarray:
    tone = synth.sine(300.0, 0.18)
    n = len(tone)
    return synth.normalize(tone * synth.env_ad(n, attack=0.2, decay=0.7))


@_register("gold_pickup")
def _gold_pickup() -> np.ndarray:
    tone = synth.mix(synth.sine(900.0, 0.12), synth.sine(1350.0, 0.12) * 0.5)
    n = len(tone)
    return synth.normalize(tone * synth.env_exp_decay(n, rate=9.0))


@_register("item_pickup")
def _item_pickup() -> np.ndarray:
    return synth.normalize(synth.tone_sweep(0.16, 400.0, 760.0, attack=0.2,
                                            decay=0.6))


@_register("chest_open")
def _chest_open() -> np.ndarray:
    """Kod-kaynakli anahtar - `chapter02.py`/`chapter03.py` sandik acma."""
    creak = synth.lowpass(synth.noise(0.2, seed=121), 900.0)
    n = len(creak)
    return synth.normalize(creak * synth.env_ad(n, attack=0.3, decay=0.7))


@_register("torch_light")
def _torch_light() -> np.ndarray:
    """Kod-kaynakli anahtar - Bolum 3 mesale yakma/sondurme (torch.py)."""
    crackle = synth.mix(synth.noise(0.16, seed=122) * 0.6,
                        synth.sine(220.0, 0.16) * 0.3)
    n = len(crackle)
    return synth.normalize(crackle * synth.env_exp_decay(n, rate=8.0))


# --- 7. ACILIS VE GECISLER -------------------------------------------------------
@_register("intro_spark")
def _intro_spark() -> np.ndarray:
    return synth.normalize(synth.click(0.05, freq=3200.0, seed=131))


@_register("intro_hum")
def _intro_hum() -> np.ndarray:
    seconds = 4.0
    body = synth.mix(synth.sine(70.0, seconds), synth.sine(105.0, seconds) * 0.4)
    return synth.normalize(synth.loop_smooth(body, blend=1200))


@_register("journey_wind")
def _journey_wind() -> np.ndarray:
    seconds = 3.0
    body = synth.lowpass(synth.noise(seconds, seed=141), 1800.0)
    return synth.normalize(synth.loop_smooth(body, blend=1500))


@_register("journey_cellar")
def _journey_cellar() -> np.ndarray:
    seconds = 3.0
    body = synth.lowpass(synth.noise(seconds, seed=142), 260.0)
    return synth.normalize(synth.loop_smooth(body, blend=1500))


@_register("journey_night")
def _journey_night() -> np.ndarray:
    """Gece bocekleri - seyrek yuksek tik'ler, sessizlik uzerine."""
    seconds = 3.0
    n = synth.samples(seconds)
    out = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(151)
    chirp = synth.click(0.03, freq=4200.0, seed=151)
    for _ in range(10):
        pos = int(rng.uniform(0, n - len(chirp)))
        out[pos:pos + len(chirp)] += chirp * 0.5
    return synth.normalize(synth.loop_smooth(out, blend=200))


@_register("rift_open")
def _rift_open() -> np.ndarray:
    tear = synth.noise(0.3, seed=161)
    boom = synth.sweep(140.0, 35.0, 0.6)
    return synth.normalize(synth.mix(
        tear * synth.env_exp_decay(len(tear), rate=6.0) * 0.6,
        boom * synth.env_ad(len(boom), attack=0.05, decay=0.9) * 0.8))


@_register("rift_close")
def _rift_close() -> np.ndarray:
    return synth.normalize(
        synth.tone_sweep(0.4, 60.0, 160.0, attack=0.1, decay=0.85) * 0.7)


@_register("chapter_end")
def _chapter_end() -> np.ndarray:
    tone = synth.mix(synth.sine(340.0, 0.5), synth.sine(510.0, 0.5) * 0.4)
    n = len(tone)
    return synth.normalize(tone * synth.env_ad(n, attack=0.15, decay=0.8))


# --- 8. ORTAM (dongu) ------------------------------------------------------------
@_register("amb_village_night")
def _amb_village_night() -> np.ndarray:
    seconds = 3.0
    n = synth.samples(seconds)
    out = synth.lowpass(synth.noise(seconds, seed=171), 1200.0) * 0.25
    rng = np.random.default_rng(172)
    chirp = synth.click(0.03, freq=3800.0, seed=172)
    for _ in range(8):
        pos = int(rng.uniform(0, n - len(chirp)))
        out[pos:pos + len(chirp)] += chirp * 0.35
    return synth.normalize(synth.loop_smooth(out, blend=600))


@_register("amb_cellar")
def _amb_cellar() -> np.ndarray:
    seconds = 3.0
    n = synth.samples(seconds)
    out = synth.lowpass(synth.noise(seconds, seed=181), 220.0) * 0.5
    rng = np.random.default_rng(182)
    drip = synth.thump(0.05, 900.0, 500.0, decay=24.0, noise_amt=0.1, seed=182)
    for _ in range(4):
        pos = int(rng.uniform(0, n - len(drip)))
        out[pos:pos + len(drip)] += drip * 0.4
    return synth.normalize(synth.loop_smooth(out, blend=600))


@_register("amb_torch")
def _amb_torch() -> np.ndarray:
    seconds = 2.5
    body = synth.lowpass(synth.noise(seconds, seed=191), 2600.0) * 0.4
    return synth.normalize(synth.loop_smooth(body, blend=500))


@_register("amb_water")
def _amb_water() -> np.ndarray:
    seconds = 2.5
    body = synth.lowpass(synth.noise(seconds, seed=192), 900.0)
    return synth.normalize(synth.loop_smooth(body, blend=500))


@_register("amb_deep")
def _amb_deep() -> np.ndarray:
    seconds = 3.0
    body = synth.lowpass(synth.noise(seconds, seed=193), 180.0)
    breath = synth.sine(45.0, seconds) * 0.3
    return synth.normalize(synth.loop_smooth(synth.mix(body, breath), blend=700))
