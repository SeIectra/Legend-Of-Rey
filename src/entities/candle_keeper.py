"""Mum Bekcisi - konusmayan, savasmayan, ticaret yapan varlik.

`docs/bolum-03.md` Oda 3-A: *"Hollow Knight dersi - dusmanca bir dunyada
dusman olmayan varliklar, yalnizligi azaltmaz, derinlestirir."*

Bilinclu olarak `Actor`'dan turemiyor: can, hasar, durum makinesi hicbirine
ihtiyaci yok. Bir "sey" degil "biri" hissi vermesi gereken, saldirilamayan
bir sahne parcasi - vurus onun icinden gecer, hicbir sey olmaz (sahne
tarafinda hitbox hedefi olarak hic eklenmiyor).

Gozleri sprite degil: iki parcacik emitoru, kod ile uretilip titretiliyor
(docs'un actikca istedigi sey). `cave_backdrop`'un deterministik
hash+sinus deseniyle ayni ruh - `random` yok, ayni kare hep ayni titremeyi
verir.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow

BODY_WIDTH = 12
BODY_HEIGHT = 20


class CandleKeeper:
    """Pasif NPC. Ticaret sahne tarafindan (`chapter03.py`) yonetilir."""

    __slots__ = ("x", "feet_y", "frame")

    def __init__(self, x: float, feet_y: float) -> None:
        self.x = x
        self.feet_y = feet_y
        self.frame = 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - BODY_WIDTH // 2 - 4),
                           int(self.feet_y - BODY_HEIGHT - 4),
                           BODY_WIDTH + 8, BODY_HEIGHT + 8)

    def update(self) -> None:
        self.frame += 1

    # --- Cizim ----------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset
        x = int(self.x) - ox
        base = int(self.feet_y) - oy
        top = base - BODY_HEIGHT

        # Oturan siluet: kukuletali, yuzu bos. Sol-ust isik kurali (CLAUDE.md 6).
        surface.fill(palette.color("ink_soft"),
                     (x - BODY_WIDTH // 2, top + 3, BODY_WIDTH, BODY_HEIGHT - 3))
        surface.fill(palette.color("stone"),
                     (x - BODY_WIDTH // 2, top + 3, BODY_WIDTH, 1))
        # Kukulete - basin ustunu ve yuzun ust yarisini kapatir, "yuz yok"
        # hissi boylece siluetten geliyor, ayrica bir "bos yuz" cizmiyoruz.
        surface.fill(palette.color("ink"), (x - 4, top, 8, 6))

        self._draw_eyes(surface, x, top + 8)

    def _draw_eyes(self, surface: pygame.Surface, x: int, eye_y: int) -> None:
        """Iki titreyen mum alevi - sprite degil, kod uretimi."""
        for side in (-1, 1):
            jitter = math.sin(self.frame * 0.22 + side * 1.7) * 0.6
            ex = x + side * 3
            ey = int(eye_y + jitter)
            surface.fill(palette.color("gold"), (ex, ey, 1, 1))
            glow = radial_glow(7, palette.color("ember"),
                               peak=0.5 + 0.1 * math.sin(self.frame * 0.3 + side))
            surface.blit(glow, (ex - 7, ey - 7), special_flags=pygame.BLEND_RGB_ADD)
