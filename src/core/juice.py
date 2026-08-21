"""Game feel: hitstop, yonlu sarsinti, flas, squash & stretch.

**Uclu senkron kurali (docs/derinlestirme.md 1.4):** Hitstop, sarsinti ve
parcacik **tek bir `on_hit()` cagrisindan** tetiklenir. Ayri ayri cagrilirsa
kare kaymasi olur ve his bozulur. Bu modulun var olma sebebi budur.

Uc incelik, cogu oyunun atladigi:

1. **Sarsinti yonludur, rastgele degil.** Darbe vektoru boyunca iter. Rastgele
   titreme "hata" gibi okunur; yonlu itme "kuvvet" gibi okunur.
2. **Orta ve buyuk sarsintiya rotasyon eklenir** (0.3-0.8 derece). Saf oteleme
   bozukluk hissi verir; birkac ondalik derece rotasyon guc hissi verir.
   Kucuk sarsintida rotasyon YOK - uc buyukluk kurali.
3. **Bozunum ustel** (`amp *= 0.85`), dogrusal degil. Dogrusal sarsinti ucuz durur.

Tum sureler kare cinsindendir.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum, auto

from src.config import (
    HIT_FLASH_FRAMES, HITSTOP_BOSS, HITSTOP_FINISHER, HITSTOP_KILL,
    HITSTOP_NORMAL, SHAKE_BOSS_FRAMES, SHAKE_BOSS_PIXELS, SHAKE_BOSS_ROTATION,
    SHAKE_DECAY, SHAKE_FINISHER_FRAMES, SHAKE_FINISHER_PIXELS,
    SHAKE_FINISHER_ROTATION, SHAKE_NORMAL_FRAMES, SHAKE_NORMAL_PIXELS,
    SHAKE_NORMAL_ROTATION, SOUND_PITCH_VARIANCE, SQUASH_HIT, SQUASH_HIT_FRAMES,
    SQUASH_JUMP, SQUASH_JUMP_FRAMES, SQUASH_LAND, SQUASH_LAND_FRAMES,
)


class ImpactWeight(Enum):
    """Darbenin buyuklugu. Uc kademe - rutin aksiyon kucuk, gercek olay buyuk."""

    NORMAL = auto()
    FINISHER = auto()
    BOSS = auto()
    KILL = auto()


_HITSTOP = {
    ImpactWeight.NORMAL: HITSTOP_NORMAL,
    ImpactWeight.FINISHER: HITSTOP_FINISHER,
    ImpactWeight.BOSS: HITSTOP_BOSS,
    ImpactWeight.KILL: HITSTOP_KILL,
}

# (piksel, kare, derece)
_SHAKE = {
    ImpactWeight.NORMAL: (SHAKE_NORMAL_PIXELS, SHAKE_NORMAL_FRAMES,
                          SHAKE_NORMAL_ROTATION),
    ImpactWeight.FINISHER: (SHAKE_FINISHER_PIXELS, SHAKE_FINISHER_FRAMES,
                            SHAKE_FINISHER_ROTATION),
    ImpactWeight.BOSS: (SHAKE_BOSS_PIXELS, SHAKE_BOSS_FRAMES,
                        SHAKE_BOSS_ROTATION),
    ImpactWeight.KILL: (SHAKE_BOSS_PIXELS, SHAKE_BOSS_FRAMES,
                        SHAKE_BOSS_ROTATION),
}


@dataclass
class Squash:
    """Squash & stretch durumu - yeni kare cizmeden deformasyon."""

    scale_x: float = 1.0
    scale_y: float = 1.0
    frames_left: int = 0
    total_frames: int = 0

    def trigger(self, scale: tuple[float, float], frames: int) -> None:
        self.scale_x, self.scale_y = scale
        self.frames_left = frames
        self.total_frames = max(1, frames)

    def update(self) -> None:
        if self.frames_left <= 0:
            self.scale_x = self.scale_y = 1.0
            return
        self.frames_left -= 1

    @property
    def current(self) -> tuple[float, float]:
        """Deformasyon kalan sureye gore 1.0'a geri doner."""
        if self.frames_left <= 0:
            return (1.0, 1.0)
        ratio = self.frames_left / self.total_frames
        return (1.0 + (self.scale_x - 1.0) * ratio,
                1.0 + (self.scale_y - 1.0) * ratio)

    @property
    def active(self) -> bool:
        return self.frames_left > 0

    def jump(self) -> None:
        self.trigger(SQUASH_JUMP, SQUASH_JUMP_FRAMES)

    def land(self) -> None:
        self.trigger(SQUASH_LAND, SQUASH_LAND_FRAMES)

    def hit(self) -> None:
        self.trigger(SQUASH_HIT, SQUASH_HIT_FRAMES)


@dataclass
class ScreenShake:
    """Yonlu, ustel bozunumlu, rotasyonlu ekran sarsintisi."""

    enabled: bool = True
    intensity_scale: float = 1.0     # Ayarlardan 0.0 (kapali) .. 1.0

    amplitude: float = 0.0
    frames_left: int = 0
    direction_x: float = 0.0
    direction_y: float = 0.0
    rotation_amplitude: float = 0.0

    offset_x: float = 0.0
    offset_y: float = 0.0
    rotation: float = 0.0

    def add(self, weight: ImpactWeight, direction: tuple[float, float]) -> None:
        """Darbe yonunde sarsinti ekler. `direction` normalize edilir."""
        if not self.enabled or self.intensity_scale <= 0.0:
            return
        pixels, frames, degrees = _SHAKE[weight]
        pixels *= self.intensity_scale
        degrees *= self.intensity_scale

        length = math.hypot(direction[0], direction[1])
        if length < 1e-5:
            # Yon yoksa radyal davran - patlamalarda olur.
            angle = random.uniform(0.0, math.tau)
            dx, dy = math.cos(angle), math.sin(angle)
        else:
            dx, dy = direction[0] / length, direction[1] / length

        # En guclu sarsinti kazanir; ust uste binerek kamera cildirmaz.
        if pixels >= self.amplitude:
            self.amplitude = pixels
            self.frames_left = frames
            self.direction_x, self.direction_y = dx, dy
            self.rotation_amplitude = degrees

    def update(self) -> None:
        if self.frames_left <= 0:
            self.amplitude = 0.0
            self.offset_x = self.offset_y = self.rotation = 0.0
            return

        self.frames_left -= 1
        # Yonlu itme + kucuk rastgele bilesen. Salinim isareti her kare doner
        # ki sarsinti "itip birakma" degil "titresim" gibi okunsun.
        swing = 1.0 if self.frames_left % 2 == 0 else -1.0
        jitter = random.uniform(-0.35, 0.35)
        self.offset_x = (self.direction_x * swing + jitter) * self.amplitude
        self.offset_y = (self.direction_y * swing + jitter) * self.amplitude
        self.rotation = self.rotation_amplitude * swing

        self.amplitude *= SHAKE_DECAY      # Ustel bozunum

    @property
    def active(self) -> bool:
        return self.frames_left > 0

    @property
    def offset(self) -> tuple[int, int]:
        """Tam sayi kaydirma - ondalik ofset piksel art dokusunu titretir."""
        return (round(self.offset_x), round(self.offset_y))


@dataclass
class HitFlash:
    """Vurulan hedefin birkac kare tamamen beyaz olmasi."""

    frames_left: int = 0

    def trigger(self, frames: int = HIT_FLASH_FRAMES) -> None:
        self.frames_left = max(self.frames_left, frames)

    def update(self) -> None:
        if self.frames_left > 0:
            self.frames_left -= 1

    @property
    def active(self) -> bool:
        return self.frames_left > 0


@dataclass
class ImpactEvent:
    """Bir vurusun tum duyusal sonuclarini tasiyan paket."""

    x: float
    y: float
    direction: tuple[float, float]
    weight: ImpactWeight = ImpactWeight.NORMAL
    particle_path: str = "blood"
    particle_count: int = 8
    sound: str = "hit"


class Juice:
    """Game feel merkezi. Vurus geri bildirimi buradan gecer, baska yerden degil.

    `on_hit()` tek giris noktasidir; hitstop, sarsinti ve parcacigi ayni karede
    tetikler. Sahne yalnizca `particles` geri cagrisini saglar.
    """

    def __init__(self, game, spawn_particles=None) -> None:
        self.game = game
        self.shake = ScreenShake()
        self._spawn_particles = spawn_particles

    def configure(self, *, shake_enabled: bool = True,
                  shake_scale: float = 1.0) -> None:
        self.shake.enabled = shake_enabled
        self.shake.intensity_scale = shake_scale

    def update(self) -> None:
        self.shake.update()

    # --- Tek giris noktasi --------------------------------------------------
    def on_hit(self, event: ImpactEvent, target_flash: HitFlash | None = None,
               target_squash: Squash | None = None) -> None:
        """Ucu birden ayni karede: hitstop + sarsinti + parcacik."""
        self.game.hitstop(_HITSTOP[event.weight])
        self.shake.add(event.weight, event.direction)

        if target_flash is not None:
            target_flash.trigger()
        if target_squash is not None:
            target_squash.hit()

        if self._spawn_particles is not None:
            self._spawn_particles(event)

    def explosion(self, x: float, y: float,
                  weight: ImpactWeight = ImpactWeight.BOSS) -> None:
        """Radyal sarsinti - patlamalarda yon yoktur."""
        self.shake.add(weight, (0.0, 0.0))
        self.game.hitstop(_HITSTOP[weight])


def pitch_variation() -> float:
    """Her tekrarli ses efekti icin +-%8 rastgele perde carpani.

    Tek satir, tekrar hissini yok eder (docs/derinlestirme.md 1.6).
    """
    return 1.0 + random.uniform(-SOUND_PITCH_VARIANCE, SOUND_PITCH_VARIANCE)
