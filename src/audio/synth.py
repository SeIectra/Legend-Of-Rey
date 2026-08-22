"""Ses sentezi - dalga formu uretimi, sprite'lar gibi koddan.

CLAUDE.md 6: "Sprite'lari PNG olarak elle cizme, kod ile uret." Gorev 10'da
gercek kaydedilmis ses yok (kayit stüdyosu/ses tasarimcisi bu ortamda
mevcut degil); ayni felsefeyi sese uyguluyoruz - kisa efektler numpy ile
dalga formu olarak uretiliyor, `pygame.mixer.Sound`'a donusturuluyor.

**Bu acikca bir ilk gecis** (CLAUDE.md 12: "placeholder acikca placeholder
olsun"). Gercek kayit/profesyonel sentez gelirse `assets/audio/*.ogg`
dosyalari eklenip `sfx.py` oradan okuyacak sekilde degistirilir - bu
modulun disina hicbir sey sizmiyor.

## Format

44.1 kHz, mono, 16-bit - `assets/audio/SES-LISTESI.md` 0 ile ayni. Tum
dalga formlari once `float32` `[-1, 1]` araliginda uretilir, en sonda
`to_sound()` ile int16'ya donusturulur.
"""
from __future__ import annotations

import numpy as np
import pygame

SAMPLE_RATE = 44100


def init_mixer() -> None:
    """`pygame.init()`'ten ONCE cagrilmali - mixer format ayarini kilitler.

    Cagrilmazsa pygame varsayilan bir format secer (platforma gore
    degisebilir); `to_sound()` o zaman `pygame.mixer.get_init()`'e
    uyum saglar, o yuzden bu fonksiyon zorunlu degil ama tercih edilir.
    """
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)


def samples(seconds: float) -> int:
    """Verilen sureye karsilik gelen ornek sayisi - `sfx_*.py` de kullanir."""
    return max(1, int(SAMPLE_RATE * seconds))


def _time(seconds: float) -> np.ndarray:
    return np.linspace(0.0, seconds, samples(seconds), endpoint=False)


# --- Osilatorler --------------------------------------------------------------
def sine(freq: float, seconds: float, phase: float = 0.0) -> np.ndarray:
    t = _time(seconds)
    return np.sin(2.0 * np.pi * freq * t + phase).astype(np.float32)


def square(freq: float, seconds: float, duty: float = 0.5) -> np.ndarray:
    t = _time(seconds)
    phase = np.mod(freq * t, 1.0)
    return np.where(phase < duty, 1.0, -1.0).astype(np.float32)


def triangle(freq: float, seconds: float) -> np.ndarray:
    t = _time(seconds)
    phase = np.mod(freq * t, 1.0)
    return (2.0 * np.abs(2.0 * phase - 1.0) - 1.0).astype(np.float32)


def sweep(freq_start: float, freq_end: float, seconds: float) -> np.ndarray:
    """Yukselen/alcalan ton - frekans dogrusal degisir (chirp).

    Faz, aninlik frekansin integrali: dogrudan `sin(2*pi*f(t)*t)` yazmak
    frekans degisince faz siciramasi (tik sesi) uretir.
    """
    t = _time(seconds)
    freq_t = freq_start + (freq_end - freq_start) * (t / max(seconds, 1e-9))
    phase = 2.0 * np.pi * np.cumsum(freq_t) / SAMPLE_RATE
    return np.sin(phase).astype(np.float32)


def noise(seconds: float, seed: int = 0) -> np.ndarray:
    """Beyaz gurultu - deterministik (ayni `seed` ayni sonucu verir).

    Sprite'taki `Canvas.noise()` ile ayni ders: rastgelelik her calistigin
    da farkli olursa "ayni sesi" onbelleklemenin anlami kalmaz.
    """
    rng = np.random.default_rng(seed)
    return rng.uniform(-1.0, 1.0, samples(seconds)).astype(np.float32)


# --- Zarf (envelope) -----------------------------------------------------------
def env_ad(n: int, attack: float, decay: float,
           sustain: float = 0.0) -> np.ndarray:
    """0'dan 1'e cikar (attack), sonra `sustain`'e kadar sonup (decay) kalir.

    Kisa vurmali efektler icin yeterli - tam ADSR'a gerek yok, "tok" bir
    darbe hissi attack+decay ile kuruluyor.
    """
    a = max(1, int(n * attack))
    d = max(1, n - a)
    rise = np.linspace(0.0, 1.0, a, endpoint=False)
    fall = np.linspace(1.0, sustain, d)
    return np.concatenate([rise, fall]).astype(np.float32)[:n]


def env_exp_decay(n: int, rate: float = 6.0) -> np.ndarray:
    """Aninda tepe, sonra ustel sonme. Perkusif vurus/tik icin dogal his."""
    t = np.linspace(0.0, 1.0, n)
    return np.exp(-rate * t).astype(np.float32)


def env_linear_fade(n: int, fade_in: float = 0.05,
                    fade_out: float = 0.05) -> np.ndarray:
    """Basit giris/cikis rampasi - donguluk (loop) parcalarda tik'i keser."""
    i = max(1, int(n * fade_in))
    o = max(1, int(n * fade_out))
    env = np.ones(n, dtype=np.float32)
    env[:i] = np.linspace(0.0, 1.0, i)
    env[-o:] = np.linspace(1.0, 0.0, o)
    return env


# --- Filtre ---------------------------------------------------------------
def lowpass(signal: np.ndarray, cutoff_hz: float) -> np.ndarray:
    """Tek kutuplu alcak-geciren filtre - Yanki'nin "bogulmus" seti icin.

    `docs/dovus-sistemi.md` 5: gercek zamanli filtre yok, onceden
    filtrelenmis ikinci bir kopya var. Bu fonksiyon o kopyayi uretiyor.

    Duzum (IIR) her ornegin bir oncekine bagli oldugu icin numpy ile
    vektorize edilemiyor - ama yalnizca `sfx.py` onbellegi **kurulurken**
    bir kez calisiyor, kare basina degil (CLAUDE.md 4 performans kurali
    calisma zamani icin - burada gecerli degil).
    """
    alpha = 1.0 - np.exp(-2.0 * np.pi * cutoff_hz / SAMPLE_RATE)
    out = np.empty_like(signal)
    acc = 0.0
    for i, sample in enumerate(signal):
        acc += alpha * (sample - acc)
        out[i] = acc
    return out.astype(np.float32)


# --- Karistirma ve donusum ------------------------------------------------------
def mix(*signals: np.ndarray) -> np.ndarray:
    """Farkli uzunluktaki sinyalleri **en uzununa** hizalayip toplar."""
    length = max((len(s) for s in signals), default=0)
    out = np.zeros(length, dtype=np.float32)
    for s in signals:
        out[:len(s)] += s
    return out


def pad_or_trim(signal: np.ndarray, n: int) -> np.ndarray:
    if len(signal) >= n:
        return signal[:n].astype(np.float32)
    return np.pad(signal, (0, n - len(signal))).astype(np.float32)


def resample_pitch(signal: np.ndarray, pitch: float) -> np.ndarray:
    """Perde varyasyonu - hiz degisimiyle (bant kasedi gibi).

    `pitch > 1` daha tiz ve daha kisa, `pitch < 1` daha pes ve daha uzun.
    `docs/derinlestirme.md` 1.6: her tekrarli efekt +-%8 - tek dosya
    yeterli, kod uretiyor.
    """
    if pitch == 1.0 or len(signal) < 2:
        return signal
    n_new = max(1, int(len(signal) / pitch))
    src_index = np.arange(n_new) * pitch
    return np.interp(src_index, np.arange(len(signal)), signal).astype(np.float32)


def normalize(signal: np.ndarray, peak: float = 0.55) -> np.ndarray:
    """Kirpilmayi (clipping) onler - en yuksek genlik `peak`'e olceklenir.

    Varsayilan **0.92'den 0.55'e** dusuruldu (Arda'nin canli oynanis geri
    bildirimi, 22.08.2026: "sesler cok rahatsiz edici"). Sentezlenmis
    dalga formlari kayitli seslerden daha "cıplak" - ayni tepe genligi
    kulakta cok daha agresif hissettiriyor.
    """
    m = float(np.max(np.abs(signal))) if len(signal) else 0.0
    if m < 1e-6:
        return signal
    return (signal * (peak / m)).astype(np.float32)


# --- Ortak sekiller (sfx_*.py hepsinde kullanir) --------------------------------
def loop_smooth(signal: np.ndarray, blend: int) -> np.ndarray:
    """Basi ile sonunu karistirir - dongude tik/cirt sesini keser."""
    blend = min(blend, len(signal) // 2)
    if blend <= 0:
        return signal
    out = signal.copy()
    fade = np.linspace(0.0, 1.0, blend, dtype=np.float32)
    head = out[:blend]
    tail = out[-blend:]
    out[:blend] = head * fade + tail * (1.0 - fade)
    out[-blend:] = tail * fade + head * (1.0 - fade)
    return out


def thump(seconds: float, freq_start: float, freq_end: float,
         decay: float = 7.0, noise_amt: float = 0.15,
         seed: int = 1) -> np.ndarray:
    """Ortak "vurus" iskeleti: alcalan ton + hafif gurultu, ustel sonme."""
    tone = sweep(freq_start, freq_end, seconds)
    body = mix(tone, noise(seconds, seed) * noise_amt)
    n = len(body)
    return body * env_exp_decay(n, rate=decay)


def click(seconds: float = 0.03, freq: float = 2400.0,
         seed: int = 2) -> np.ndarray:
    tone = sine(freq, seconds)
    burst = noise(seconds, seed)
    n = len(tone)
    return (tone * 0.6 + burst * 0.4) * env_exp_decay(n, rate=14.0)


def whoosh(seconds: float, low: float, high: float,
          seed: int = 3) -> np.ndarray:
    body = lowpass(noise(seconds, seed), high)
    body = body - lowpass(body, low)
    n = len(body)
    return body * env_ad(n, attack=0.25, decay=0.75)


def chorus(freqs: tuple[float, ...], seconds: float,
          spread: float = 0.015) -> np.ndarray:
    """Birden fazla hafif detune edilmis sinus - "fisilti katmani"."""
    layers = [sine(f * (1.0 + i * spread), seconds)
             for i, f in enumerate(freqs)]
    return mix(*layers) / max(1, len(freqs))


def tone_sweep(seconds: float, freq_start: float, freq_end: float,
              attack: float = 0.1, decay: float = 0.5) -> np.ndarray:
    tone = sweep(freq_start, freq_end, seconds)
    n = len(tone)
    return tone * env_ad(n, attack=attack, decay=decay)


def to_sound(signal: np.ndarray, volume: float = 1.0) -> pygame.mixer.Sound:
    """Float dalga formunu `pygame.mixer.Sound`'a cevirir.

    Mixer birden fazla kanalli baslatilmissa (bazi platformlarda varsayilan
    stereo) diziyi kopyalayarak uyum saglar - `SAMPLE_RATE`/mono
    varsayimi `init_mixer()` ile kilitlenir ama garanti degildir.
    """
    clipped = np.clip(signal, -1.0, 1.0)
    ints = (clipped * 32767.0).astype(np.int16)
    init = pygame.mixer.get_init()
    channels = init[2] if init else 1
    if channels and channels > 1:
        ints = np.repeat(ints.reshape(-1, 1), channels, axis=1)
    sound = pygame.sndarray.make_sound(np.ascontiguousarray(ints))
    sound.set_volume(max(0.0, min(1.0, volume)))
    return sound
