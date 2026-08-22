"""Tasinabilir mesale - Bolum 3'un temel nesnesi.

Duvar yuvalari (`Sconce`) icin ayri bir sinif yok: onlar zaten
`cave_backdrop.draw_torches()`'in cizdigi `(tile_x, tile_y, lit)` uclusu -
Bolum 1/2'de sadece dekorken, Bolum 3'te `lit` calisirken degisen gercek bir
oyun durumu oluyor. Sahne bu listeyi tutuyor (`chapter03.py`), burada tekrar
tanimlamiyoruz.

Meshale ise gercekten yeni bir nesne: elde tasinir, yuvaya konur, ya da
fırlatilir. `Chest` (`world/pickups.py`) ile ayni hafif desen - `__slots__`,
`update()`/`draw()`, sahne carpismayi disaridan yonetir.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import (
    GRAVITY, TILE_SIZE, TORCH_LIGHT_RADIUS, TORCH_THROW_LIFT,
    TORCH_THROW_SPEED,
)

# Durumlar.
HELD = "held"           # Oyuncunun elinde, onu takip eder
THROWN = "thrown"        # Havada, yay ciziyor
LANDED = "landed"        # Dustugu yerde kalici yaniyor
SOCKETED = "socketed"     # Bir yuvaya kondu (yuva Sconce listesine donusuyor)


class Torch:
    """Tek bir tasinabilir mesale."""

    __slots__ = ("x", "y", "state", "vx", "vy", "flicker")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.state = HELD
        self.vx = 0.0
        self.vy = 0.0
        self.flicker = 0.0

    @property
    def radius(self) -> float:
        return TORCH_LIGHT_RADIUS

    @property
    def gives_light(self) -> bool:
        """Sonup sonmedigine degil - hala takip edilecek bir nesne mi?"""
        return self.state != SOCKETED

    def follow(self, x: float, y: float) -> None:
        """Elde tasinirken oyuncunun konumunu takip eder."""
        if self.state == HELD:
            self.x = x
            self.y = y

    def throw(self, direction: int) -> None:
        self.state = THROWN
        self.vx = TORCH_THROW_SPEED * direction
        self.vy = TORCH_THROW_LIFT

    def update(self, tilemap) -> None:
        self.flicker += 1.0
        if self.state != THROWN:
            return
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        tx = int(self.x) // TILE_SIZE
        ty = int(self.y) // TILE_SIZE
        if tilemap.is_solid(tx, ty):
            self.state = LANDED
            self.vx = self.vy = 0.0

    # --- Cizim ----------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset
        x = int(self.x) - ox
        y = int(self.y) - oy

        surface.fill(palette.color("earth_dark"), (x - 1, y - 8, 2, 8))
        flicker = int(self.flicker // 6) % 3
        surface.fill(palette.color("ember"), (x - 1, y - 13, 3, 5 - flicker))
        surface.fill(palette.color("gold"), (x - 1, y - 14, 2, 3 - flicker))
        glow = radial_glow(26, palette.color("ember"),
                           peak=0.46 + 0.05 * math.sin(self.flicker * 0.2))
        surface.blit(glow, (x - 26, y - 34), special_flags=pygame.BLEND_RGB_ADD)
