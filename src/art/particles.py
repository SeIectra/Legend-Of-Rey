"""Parcacik sistemi - sutun tabanli, ust sinirli.

Parcaciklar nesne degil numpy sutunlaridir; yuzlerce parcacigi tek tek Python
nesnesi olarak guncellemek kare butcesini yer.

Iki kural belgeden gelir:
  * **Ust sinir 200** (docs/derinlestirme.md 8.4) - asilinca en eskisi geri
    donusturulur, yeni parcacik kaybolmaz
  * **Renk yolu** (docs/derinlestirme.md 1.3) - her parcacik omru boyunca
    palet uzerinde bir yol izler: parlak -> koyu -> is. Baslangicta keskin
    parlak, sonunda yumusak duman; ekrani kalabaliklastirmadan yuksek etki

Parcaciklar darbe **vektoru boyunca** disa fiskirir - bu, darbenin yonunu
gorsel olarak pekistirir.
"""
from __future__ import annotations

import math
import random

import numpy as np
import pygame

from src.art import palette
from src.config import MAX_PARTICLES


class ParticleField:
    __slots__ = ("capacity", "x", "y", "vx", "vy", "life", "max_life",
                 "gravity", "drag", "size", "path_index", "count",
                 "_path_names", "_next_slot")

    def __init__(self, capacity: int = MAX_PARTICLES) -> None:
        self.capacity = capacity
        self.x = np.zeros(capacity, dtype=np.float32)
        self.y = np.zeros(capacity, dtype=np.float32)
        self.vx = np.zeros(capacity, dtype=np.float32)
        self.vy = np.zeros(capacity, dtype=np.float32)
        self.life = np.zeros(capacity, dtype=np.float32)
        self.max_life = np.ones(capacity, dtype=np.float32)
        self.gravity = np.zeros(capacity, dtype=np.float32)
        self.drag = np.zeros(capacity, dtype=np.float32)
        self.size = np.ones(capacity, dtype=np.float32)
        self.path_index = np.zeros(capacity, dtype=np.int16)
        self.count = 0
        self._next_slot = 0
        self._path_names = list(palette.PARTICLE_PATHS.keys())

    def _acquire(self) -> int:
        """Bos yuva bul; havuz doluysa en eskisini geri donustur."""
        if self.count < self.capacity:
            slot = self.count
            self.count += 1
            return slot
        # Halka tampon: sinirsiz buyumek yerine en eskisinin uzerine yaz.
        slot = self._next_slot
        self._next_slot = (self._next_slot + 1) % self.capacity
        return slot

    def burst(self, x: float, y: float, count: int,
              direction: tuple[float, float] = (0.0, 0.0),
              path: str = "blood", spread: float = 1.1,
              speed: tuple[float, float] = (0.6, 2.2),
              life: tuple[int, int] = (14, 32),
              gravity: float = 0.10, drag: float = 0.06,
              size: tuple[float, float] = (1.0, 2.0)) -> None:
        """Darbe yonunde disa fiskiran parcacik demeti.

        `life` kare cinsindendir. `direction` sifirsa radyal dagilir.
        """
        try:
            path_id = self._path_names.index(path)
        except ValueError:
            path_id = 0

        base_angle = math.atan2(direction[1], direction[0])
        radial = abs(direction[0]) < 1e-5 and abs(direction[1]) < 1e-5

        for _ in range(count):
            slot = self._acquire()
            angle = (random.uniform(0.0, math.tau) if radial
                     else base_angle + random.uniform(-spread, spread))
            velocity = random.uniform(*speed)
            frames = random.randint(*life)

            self.x[slot] = x
            self.y[slot] = y
            self.vx[slot] = math.cos(angle) * velocity
            self.vy[slot] = math.sin(angle) * velocity
            self.life[slot] = frames
            self.max_life[slot] = frames
            self.gravity[slot] = gravity
            self.drag[slot] = drag
            self.size[slot] = random.uniform(*size)
            self.path_index[slot] = path_id

    def update(self) -> None:
        """Bir kare ilerlet. Sureler kare cinsinden."""
        if self.count == 0:
            return
        n = self.count
        alive = self.life[:n] > 0.0
        if not alive.any():
            return
        self.life[:n] = np.where(alive, self.life[:n] - 1.0, 0.0)
        damping = np.maximum(0.0, 1.0 - self.drag[:n])
        self.vx[:n] *= damping
        self.vy[:n] = self.vy[:n] * damping + self.gravity[:n]
        self.x[:n] += self.vx[:n]
        self.y[:n] += self.vy[:n]

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        if self.count == 0:
            return
        n = self.count
        ox, oy = offset
        width, height = surface.get_size()

        alive = self.life[:n] > 0.0
        ratio = np.clip(self.life[:n] / np.maximum(self.max_life[:n], 1e-5),
                        0.0, 1.0)
        screen_x = np.round(self.x[:n]).astype(np.int32) - ox
        screen_y = np.round(self.y[:n]).astype(np.int32) - oy
        visible = alive & (screen_x >= -4) & (screen_x < width + 4) \
            & (screen_y >= -4) & (screen_y < height + 4)

        for index in np.nonzero(visible)[0]:
            path_name = self._path_names[self.path_index[index]]
            colour = palette.path_color(path_name, float(ratio[index]))
            size = max(1, int(self.size[index] * (0.4 + ratio[index] * 0.8)))
            surface.fill(colour, (int(screen_x[index]), int(screen_y[index]),
                                  size, size))

    def clear(self) -> None:
        self.count = 0
        self._next_slot = 0
        self.life[:] = 0.0

    @property
    def alive_count(self) -> int:
        return int(np.count_nonzero(self.life[:self.count] > 0.0))
