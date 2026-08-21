"""Parcacik sistemi.

Parcaciklar nesne degil, numpy sutunlaridir. 2000 parcacigi tek tek Python
nesnesi olarak guncellemek kare butcesini yer; dizi uzerinde toplu islem
neredeyse bedavadir.

Iki tur var:
  * **Nokta parcaciklari** (kivilcim, kan, toz zerresi) - tek piksel, hizli.
  * **Sprite efektleri** (kilic izi, carpma yildizi, halka) - onceden uretilmis
    kare dizileri.

Ayrica `Afterimage`: dash sirasinda birakılan solan siluetler.
"""
from __future__ import annotations

import math

import numpy as np
import pygame

from lore.gfx.forge import silhouette
from lore.gfx.palette import RAMPS

MAX_PARTICLES = 2400


class ParticleField:
    """Nokta parcaciklari icin sutun tabanli havuz."""

    def __init__(self, capacity: int = MAX_PARTICLES) -> None:
        self.cap = capacity
        self.x = np.zeros(capacity, dtype=np.float32)
        self.y = np.zeros(capacity, dtype=np.float32)
        self.vx = np.zeros(capacity, dtype=np.float32)
        self.vy = np.zeros(capacity, dtype=np.float32)
        self.life = np.zeros(capacity, dtype=np.float32)
        self.max_life = np.ones(capacity, dtype=np.float32)
        self.gravity = np.zeros(capacity, dtype=np.float32)
        self.drag = np.zeros(capacity, dtype=np.float32)
        self.size = np.ones(capacity, dtype=np.float32)
        self.ramp = np.zeros(capacity, dtype=np.int16)
        self.glow = np.zeros(capacity, dtype=np.uint8)
        self.count = 0                  # Havuzun kullanilan on kismi

        self._ramp_names = list(RAMPS.keys())
        self._ramp_index = {n: i for i, n in enumerate(self._ramp_names)}

    def emit(self, x: float, y: float, count: int = 1, *,
             speed: tuple[float, float] = (20.0, 60.0),
             angle: tuple[float, float] = (0.0, math.tau),
             life: tuple[float, float] = (0.25, 0.6),
             gravity: float = 220.0, drag: float = 1.6,
             size: tuple[float, float] = (1.0, 2.0),
             ramp: str = "ash", glow: int = 0) -> None:
        rng = np.random
        for _ in range(count):
            if self.count >= self.cap:
                # Havuz dolu: en eski parcacigin uzerine yaz. Sikismaktansa
                # birkac parcacigi kaybetmek yeglenir.
                index = int(np.argmin(self.life[:self.cap]))
            else:
                index = self.count
                self.count += 1
            a = rng.uniform(*angle)
            s = rng.uniform(*speed)
            self.x[index] = x
            self.y[index] = y
            self.vx[index] = math.cos(a) * s
            self.vy[index] = math.sin(a) * s
            lifetime = rng.uniform(*life)
            self.life[index] = lifetime
            self.max_life[index] = lifetime
            self.gravity[index] = gravity
            self.drag[index] = drag
            self.size[index] = rng.uniform(*size)
            self.ramp[index] = self._ramp_index.get(ramp, 0)
            self.glow[index] = glow

    def update(self, dt: float) -> None:
        if self.count == 0:
            return
        n = self.count
        alive = self.life[:n] > 0.0
        if not alive.any():
            self.count = 0
            return
        self.life[:n] = np.where(alive, self.life[:n] - dt, 0.0)
        damping = np.maximum(0.0, 1.0 - self.drag[:n] * dt)
        self.vx[:n] *= damping
        self.vy[:n] = self.vy[:n] * damping + self.gravity[:n] * dt
        self.x[:n] += self.vx[:n] * dt
        self.y[:n] += self.vy[:n] * dt

    def draw(self, surface: pygame.Surface, camera) -> None:
        if self.count == 0:
            return
        n = self.count
        alive = self.life[:n] > 0.0
        if not alive.any():
            return
        ox, oy = camera.offset
        view = camera.view_rect
        # Yasam orani -> rampa basamagi: parcacik sonerken koyulasir.
        ratio = np.clip(self.life[:n] / np.maximum(self.max_life[:n], 1e-5), 0, 1)
        steps = np.clip((ratio * 4.2).astype(np.int16), 0, 4)

        xs = self.x[:n]
        ys = self.y[:n]
        visible = (alive
                   & (xs >= view.left - 8) & (xs <= view.right + 8)
                   & (ys >= view.top - 8) & (ys <= view.bottom + 8))
        indices = np.nonzero(visible)[0]
        for i in indices:
            color = RAMPS[self._ramp_names[self.ramp[i]]][steps[i]]
            size = max(1, int(self.size[i] * (0.4 + ratio[i] * 0.8)))
            px = int(xs[i]) - ox
            py = int(ys[i]) - oy
            if size <= 1:
                if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
                    surface.set_at((px, py), color)
            else:
                surface.fill(color, (px, py, size, size))

    def clear(self) -> None:
        self.count = 0
        self.life[:] = 0.0


class SpriteEffect:
    """Tek seferlik, kare dizisiyle oynayan efekt."""

    __slots__ = ("frames", "x", "y", "timer", "fps", "flip", "remove", "additive")

    def __init__(self, frames: list[pygame.Surface], x: float, y: float,
                 fps: float = 26.0, flip: bool = False,
                 additive: bool = False) -> None:
        self.frames = frames
        self.x = x
        self.y = y
        self.timer = 0.0
        self.fps = fps
        self.flip = flip
        self.additive = additive
        self.remove = False

    def update(self, dt: float) -> None:
        self.timer += dt * self.fps
        if self.timer >= len(self.frames):
            self.remove = True

    def draw(self, surface: pygame.Surface, camera) -> None:
        index = min(int(self.timer), len(self.frames) - 1)
        image = self.frames[index]
        if self.flip:
            image = pygame.transform.flip(image, True, False)
        ox, oy = camera.offset
        pos = (int(self.x - image.get_width() * 0.5) - ox,
               int(self.y - image.get_height() * 0.5) - oy)
        if self.additive:
            surface.blit(image, pos, special_flags=pygame.BLEND_RGB_ADD)
        else:
            surface.blit(image, pos)


class Afterimage:
    """Dash izi: solan siluet. Hiz hissinin en ucuz kaynagi."""

    __slots__ = ("image", "x", "y", "life", "max_life", "remove", "color")

    def __init__(self, image: pygame.Surface, x: float, y: float,
                 life: float = 0.22, color=(150, 200, 255)) -> None:
        self.image = silhouette(image, color)
        self.x = x
        self.y = y
        self.life = life
        self.max_life = life
        self.remove = False

    def update(self, dt: float) -> None:
        self.life -= dt
        if self.life <= 0.0:
            self.remove = True

    def draw(self, surface: pygame.Surface, camera) -> None:
        ratio = max(0.0, self.life / self.max_life)
        image = self.image.copy()
        image.set_alpha(int(150 * ratio))
        ox, oy = camera.offset
        surface.blit(image, (int(self.x) - ox, int(self.y) - oy))


class DamageNumber:
    """Yukselen hasar sayisi. Vurusun degdiginin sayisal onayi."""

    __slots__ = ("x", "y", "value", "life", "max_life", "remove", "color", "crit")

    def __init__(self, x: float, y: float, value: int, color=(255, 240, 200),
                 crit: bool = False) -> None:
        self.x = x
        self.y = y
        self.value = value
        self.life = 0.7
        self.max_life = 0.7
        self.color = color
        self.crit = crit
        self.remove = False

    def update(self, dt: float) -> None:
        self.life -= dt
        self.y -= 26.0 * dt
        if self.life <= 0.0:
            self.remove = True

    def draw(self, surface: pygame.Surface, camera) -> None:
        from lore.gfx.text import draw_text
        ox, oy = camera.offset
        ratio = max(0.0, self.life / self.max_life)
        text = f"{self.value}" + ("!" if self.crit else "")
        draw_text(surface, text, int(self.x) - ox, int(self.y) - oy,
                  color=self.color, align="center", outline=True,
                  alpha=int(255 * min(1.0, ratio * 2.2)))
