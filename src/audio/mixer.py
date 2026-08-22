"""Calma katmani - `sfx.py`'nin urettigi dalga formlarini `pygame.mixer`'a
baglar. Hacim, bogulma ve perde varyasyonu **burada** karar verilir;
`sfx.py` yalnizca ham dalga formu uretir, calmayla ilgilenmez.

## Onbellek tek, paylasilan - `tileset.shared()` ile ayni ders

Her anahtar **sadece ilk cagrildiginda** sentezlenir ve surec boyunca
paylasilan `SoundBank`'ta kalir (`tileset.py`'deki `_SHARED` ile ayni
desen). Boylece testlerin her biri kendi `Game()`'ini kursa da ayni
sesler tekrar tekrar uretilmez - ilk `Game()` neyi calarsa onu sentezler,
geri kalani onbellekten okur.

## Perde varyasyonu - bastan pisirilir, kare icinde degil

`docs/derinlestirme.md` 1.6: her tekrarli efekt +-%8 perde. Kare icinde
numpy yeniden ornekleme yapmak (60 kare/sn butcesini) riske atardi; onun
yerine `PITCH_VARIANTS` kadar sabit varyant onceden uretilip `play()`
rastgele birini secer - maliyet sifira iner.
"""
from __future__ import annotations

import random

import numpy as np
import pygame

from src.audio import sfx, synth
from src.config import ECHO_MUFFLE_VOLUME, SOUND_PITCH_VARIANCE

PITCH_VARIANTS = 5


class SoundBank:
    """Anahtar -> (normal, bogulmus) perde varyant listeleri. Tembel/lazy."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str, bool], list[pygame.mixer.Sound]] = {}

    def variants(self, name: str, muffled: bool = False
                ) -> list[pygame.mixer.Sound]:
        muffled = muffled and name in sfx.MUFFLED_KEYS
        key = (name, muffled)
        cached = self._cache.get(key)
        if cached is None:
            cached = self._build(name, muffled)
            self._cache[key] = cached
        return cached

    def base_sound(self, name: str) -> pygame.mixer.Sound | None:
        """Perde varyasyonsuz tek ornek - donguler (loop) icin."""
        pool = self.variants(name, muffled=False)
        return pool[len(pool) // 2] if pool else None

    def _build(self, name: str, muffled: bool) -> list[pygame.mixer.Sound]:
        wave_fn = sfx.SFX.get(name)
        if wave_fn is None:
            return []
        base = wave_fn()
        if muffled:
            base = synth.normalize(synth.lowpass(base, sfx.MUFFLE_CUTOFF_HZ))
        if name in sfx.LOOP_KEYS:
            return [synth.to_sound(base)]
        spread = np.linspace(-SOUND_PITCH_VARIANCE, SOUND_PITCH_VARIANCE,
                             PITCH_VARIANTS)
        variants = []
        for delta in spread:
            wave = base if delta == 0.0 else synth.resample_pitch(
                base, 1.0 + float(delta))
            variants.append(synth.to_sound(wave))
        return variants


# Tek paylasilan onbellek - butun `AudioMixer` ornekleri bunu kullanir.
_BANK = SoundBank()


class AudioMixer:
    """Sahne/Game seviyesinde ses cagrilarinin giris noktasi.

    Hacim `Settings`'ten **calinirken okunur** (game.py::_on_setting_changed
    yorumu: "ses ayarlarini sahneler kendi okur"), degisiklik anida
    zorlanmiyor - ayar menusunde kaydirici oynatilirken bile dogru deger
    kullanilir.
    """

    def __init__(self, settings) -> None:
        self.settings = settings
        self.bank = _BANK
        self.enabled = pygame.mixer.get_init() is not None
        # Kanal adi -> (calinan anahtar, Channel). Ayni donguyu iki kez
        # baslatmamak icin (crossfade/degistirme burada karar verilir).
        self._loops: dict[str, tuple[str, pygame.mixer.Channel]] = {}

    def _bus_volume(self, bus: str) -> float:
        master = float(self.settings.get("volume_master", 0.9))
        return max(0.0, min(1.0, master * float(self.settings.get(bus, 1.0))))

    # --- Tek seferlik efektler -----------------------------------------------
    def play(self, name: str, muffled: bool = False, bus: str = "volume_sfx",
             volume: float = 1.0) -> None:
        if not self.enabled:
            return
        pool = self.bank.variants(name, muffled=muffled)
        if not pool:
            return
        sound = random.choice(pool)
        final = self._bus_volume(bus) * volume
        if muffled and name in sfx.MUFFLED_KEYS:
            final *= ECHO_MUFFLE_VOLUME
        sound.set_volume(final)
        sound.play()

    # --- Donguler (loop) -------------------------------------------------------
    def play_loop(self, channel_key: str, name: str,
                 bus: str = "volume_music", volume: float = 1.0) -> None:
        """Verilen mantiksal kanalda `name` calar. Zaten caliyorsa hacmini
        gunceller, farkli bir sey caliyorsa once onu durdurur."""
        if not self.enabled:
            return
        current = self._loops.get(channel_key)
        final = self._bus_volume(bus) * volume
        if current is not None and current[0] == name:
            current[1].set_volume(final)
            return
        self.stop_loop(channel_key)
        sound = self.bank.base_sound(name)
        if sound is None:
            return
        channel = sound.play(loops=-1)
        if channel is not None:
            channel.set_volume(final)
            self._loops[channel_key] = (name, channel)

    def set_loop_volume(self, channel_key: str, volume: float,
                        bus: str = "volume_music") -> None:
        """Caliyor olan bir dongunun hacmini degistirir - geciş/crossfade
        icin (`vertical_journey.py`: ruzgar/mahzen karisimi)."""
        current = self._loops.get(channel_key)
        if current is not None:
            current[1].set_volume(self._bus_volume(bus) * volume)

    def stop_loop(self, channel_key: str) -> None:
        current = self._loops.pop(channel_key, None)
        if current is not None:
            current[1].stop()

    def stop_all_loops(self) -> None:
        for key in list(self._loops):
            self.stop_loop(key)
