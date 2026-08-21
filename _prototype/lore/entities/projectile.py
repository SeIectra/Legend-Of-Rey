"""Mermiler.

Eski koddaki mermi yalnizca saga/sola gidiyordu, yercekimi tanimiyordu ve
duvarlardan geciyordu. Buradaki mermi gercek bir aciya sahip, istege bagli
yercekimi tasiyor, tile'lara carpinca sonuyor ve kendi hitbox'ini savas
sistemine birakiyor - yani parry edilebilir hale gelmesi tek satirlik is.
"""
from __future__ import annotations

import math

import pygame

from lore.constants import MASK_PLAYER, TILE
from lore.gfx.tiles import build_projectile

ANGLE_STEPS = 16


class Projectile:
    def __init__(self, scene, x: float, y: float, angle: float,
                 speed: float = 150.0, kind: str = "arrow", owner=None,
                 target_mask: int = MASK_PLAYER, damage: int = 1,
                 gravity: float = 0.0, lifetime: float = 4.0,
                 knockback: float = 130.0, pierce: bool = False) -> None:
        self.scene = scene
        self.x = float(x)
        self.y = float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.kind = kind
        self.owner = owner
        self.target_mask = target_mask
        self.damage = damage
        self.gravity = gravity
        self.lifetime = lifetime
        self.knockback = knockback
        self.pierce = pierce
        self.remove = False
        self.radius = 3

        self.frames = scene.app.assets.generated(
            f"proj:{kind}", lambda: build_projectile(kind, ANGLE_STEPS))
        self._hitbox = None
        self._spawn_hitbox()

    def _spawn_hitbox(self) -> None:
        """Mermi kendi hitbox'ini savas sistemine devreder.

        Hitbox mermiyi takip eder; boylece hasar cozumu tek yerde kalir ve
        parry/zirh gibi kurallar merminin de icin gecerli olur.
        """
        from lore.systems.combat import Hitbox
        self._hitbox = Hitbox(
            rect=pygame.Rect(int(self.x) - 4, int(self.y) - 4, 8, 8),
            damage=self.damage, owner=self, target_mask=self.target_mask,
            knockback=self.knockback, knockback_up=70.0,
            lifetime=self.lifetime, hitstop=0.04, shake=0.10,
            pierce=self.pierce,
        )
        self.scene.combat.spawn(self._hitbox)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x) - 4, int(self.y) - 4, 8, 8)

    @property
    def angle(self) -> float:
        return math.atan2(self.vy, self.vx)

    def update(self, dt: float) -> None:
        self.lifetime -= dt
        if self.lifetime <= 0.0:
            self.kill(silent=True)
            return

        if self.gravity:
            self.vy += self.gravity * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        if self._hitbox is not None:
            if self._hitbox.expired:
                # Savas sistemi hedefe vurdu ve hitbox'i tuketti.
                self.kill()
                return
            self._hitbox.rect.center = (int(self.x), int(self.y))

        tilemap = self.scene.tilemap
        if tilemap.solid_at_pixel(self.x, self.y):
            self.kill()
            return
        if not (-TILE <= self.x <= tilemap.pixel_width + TILE
                and -TILE * 4 <= self.y <= tilemap.pixel_height + TILE):
            self.kill(silent=True)

    def kill(self, silent: bool = False) -> None:
        if self.remove:
            return
        self.remove = True
        if self._hitbox is not None:
            self._hitbox.expired = True
        if not silent:
            ramp = {"ember": "ember", "hex": "violet"}.get(self.kind, "ash")
            self.scene.spawn_effect("impact", (self.x, self.y), ramp=ramp)
            self.scene.app.audio.play("hit_armor", volume=0.5, pitch=4.0,
                                      pos=(self.x, self.y))

    def draw(self, surface: pygame.Surface, camera) -> None:
        index = int((self.angle % math.tau) / math.tau * ANGLE_STEPS) % ANGLE_STEPS
        image = self.frames[index]
        ox, oy = camera.offset
        surface.blit(image, (int(self.x - image.get_width() * 0.5) - ox,
                             int(self.y - image.get_height() * 0.5) - oy))
