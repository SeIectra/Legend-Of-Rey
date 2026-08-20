"""Toplanabilirler ve etkilesimli prop'lar.

Dusen Essence oyuncuya dogru *cekilir*. Bu kucuk detay oynanisi belirgin
sekilde iyilestirir: oyuncu her zerreyi kovalamak zorunda kalmaz, savasa
odaklanir. Cekim gecikmeli baslar ki dusme animasyonu gorunur kalsin.
"""
from __future__ import annotations

import math

import pygame

from lore.constants import TILE
from lore.core.mathx import approach, dist, rand_range
from lore.gfx.tiles import (
    build_chest, build_door, build_essence_orb, build_heart, build_shrine,
    build_torch,
)
from lore.systems.physics import Body


class Pickup:
    """Toplanabilir temeli: dusen, seken, cekilen kucuk nesne."""

    magnet_delay = 0.35
    magnet_range = 46.0
    magnet_speed = 320.0
    lifetime = 18.0
    bounce = 0.42

    def __init__(self, scene, x: float, y: float, w: int = 8, h: int = 8) -> None:
        self.scene = scene
        self.body = Body(x - w * 0.5, y - h * 0.5, w, h)
        self.body.vx = rand_range(-52.0, 52.0)
        self.body.vy = rand_range(-130.0, -70.0)
        self.age = 0.0
        self.remove = False
        self.frame_timer = rand_range(0.0, 4.0)

    def update(self, dt: float) -> None:
        self.age += dt
        self.frame_timer += dt
        if self.age > self.lifetime:
            self.remove = True
            return

        player = self.scene.player
        if player and not player.dead and self.age > self.magnet_delay:
            d = dist(self.body.centerx, self.body.centery,
                     player.body.centerx, player.body.centery)
            if d < self.magnet_range:
                # Yaklastikca hizlan: son anda kacan zerre olmaz.
                pull = self.magnet_speed * (1.0 - d / self.magnet_range) + 60.0
                dx = player.body.centerx - self.body.centerx
                dy = player.body.centery - self.body.centery
                norm = max(1.0, math.hypot(dx, dy))
                self.body.vx = approach(self.body.vx, dx / norm * pull, 1400.0 * dt)
                self.body.vy = approach(self.body.vy, dy / norm * pull, 1400.0 * dt)
                if d < 9.0:
                    self.collect(player)
                    return

        self.body.apply_gravity(dt)
        was_grounded = self.body.grounded
        self.body.move(self.scene.tilemap, dt)
        if self.body.grounded and not was_grounded:
            self.body.vy = -abs(self.body.vy) * self.bounce
            self.body.vx *= 0.7

    def collect(self, player) -> None:
        self.remove = True

    def draw(self, surface: pygame.Surface, camera) -> None: ...

    def _blink(self) -> bool:
        """Omrunun sonuna yaklasan toplanabilir yanip soner."""
        remaining = self.lifetime - self.age
        return remaining < 3.0 and int(remaining * 8) % 2 == 0


class EssenceOrb(Pickup):
    def __init__(self, scene, x: float, y: float, value: int = 1) -> None:
        super().__init__(scene, x, y, 6, 6)
        self.value = value
        self.frames = scene.app.assets.generated(
            "orb:essence", lambda: [build_essence_orb(i, 8) for i in range(8)])

    def collect(self, player) -> None:
        super().collect(player)
        player.add_essence(self.value)
        self.scene.spawn_particles(self.body.center, 4, ramp="azure", glow=140)

    def draw(self, surface, camera) -> None:
        if self._blink():
            return
        image = self.frames[int(self.frame_timer * 12) % len(self.frames)]
        ox, oy = camera.offset
        surface.blit(image, (int(self.body.centerx - image.get_width() * 0.5) - ox,
                             int(self.body.centery - image.get_height() * 0.5) - oy))


class HeartPickup(Pickup):
    lifetime = 26.0

    def __init__(self, scene, x: float, y: float, amount: int = 2) -> None:
        super().__init__(scene, x, y, 10, 9)
        self.amount = amount
        self.image = scene.app.assets.generated("pickup:heart",
                                                lambda: build_heart(True))

    def collect(self, player) -> None:
        if player.health >= player.max_health:
            return              # Dolu canla toplama: israf olmasin
        super().collect(player)
        player.heal(self.amount)
        self.scene.app.audio.play("heal")
        self.scene.spawn_particles(self.body.center, 8, ramp="blood", glow=90)

    def draw(self, surface, camera) -> None:
        if self._blink():
            return
        ox, oy = camera.offset
        bob = math.sin(self.frame_timer * 3.0) * 1.5
        surface.blit(self.image,
                     (int(self.body.centerx - self.image.get_width() * 0.5) - ox,
                      int(self.body.centery + bob - self.image.get_height() * 0.5) - oy))


# --- Sabit prop'lar ---------------------------------------------------------
class Prop:
    """Haritaya yerlestirilen, carpismasiz ama etkilesimli olabilen nesne."""

    interactive = False
    prompt = ""

    def __init__(self, scene, x: float, y: float, **options) -> None:
        self.scene = scene
        self.x = float(x)
        self.y = float(y)
        self.options = options
        self.remove = False
        self.timer = rand_range(0.0, 6.0)
        self.image: pygame.Surface | None = None

    @property
    def rect(self) -> pygame.Rect:
        if self.image is None:
            return pygame.Rect(int(self.x) - 8, int(self.y) - 16, 16, 16)
        w, h = self.image.get_size()
        return pygame.Rect(int(self.x - w * 0.5), int(self.y - h), w, h)

    def update(self, dt: float) -> None:
        self.timer += dt

    def interact(self, player) -> None: ...

    def draw(self, surface: pygame.Surface, camera) -> None:
        if self.image is None:
            return
        ox, oy = camera.offset
        r = self.rect
        surface.blit(self.image, (r.x - ox, r.y - oy))

    def light(self) -> tuple[float, float, float, tuple] | None:
        """Isik kaynagiysa (x, y, yaricap, renk) doner."""
        return None


class Torch(Prop):
    def __init__(self, scene, x: float, y: float, **options) -> None:
        super().__init__(scene, x, y, **options)
        self.frames = scene.app.assets.generated(
            "prop:torch", lambda: [build_torch(i, 6) for i in range(6)])
        self.image = self.frames[0]
        self.flicker = rand_range(0.0, math.tau)

    def update(self, dt: float) -> None:
        super().update(dt)
        self.image = self.frames[int(self.timer * 11) % len(self.frames)]

    def light(self):
        # Titreme: sabit yaricapli isik "olu" gorunur.
        pulse = 1.0 + math.sin(self.timer * 7.0 + self.flicker) * 0.09 \
            + math.sin(self.timer * 17.0) * 0.04
        return (self.x, self.y - 10, 62.0 * pulse, (255, 186, 110))


class Shrine(Prop):
    """Echo Shrine: kayit noktasi ve can yenileme."""
    interactive = True
    prompt = "Yankiya dokun"

    def __init__(self, scene, x: float, y: float, **options) -> None:
        super().__init__(scene, x, y, **options)
        self.active = bool(options.get("active", False))
        self.frames_on = scene.app.assets.generated(
            "prop:shrine_on", lambda: [build_shrine(True, i) for i in range(8)])
        self.frames_off = scene.app.assets.generated(
            "prop:shrine_off", lambda: [build_shrine(False, 0)])
        self.image = self.frames_off[0]
        self.id = options.get("id", f"shrine_{int(x)}_{int(y)}")

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.active:
            self.image = self.frames_on[int(self.timer * 9) % len(self.frames_on)]
        else:
            self.image = self.frames_off[0]

    def interact(self, player) -> None:
        first_time = not self.active
        self.active = True
        player.heal(player.max_health)
        self.scene.app.audio.play("checkpoint")
        self.scene.spawn_effect("ring", (self.x, self.y - 12), ramp="azure",
                                radius=30)
        self.scene.on_checkpoint(self, first_time)

    def light(self):
        if not self.active:
            return None
        pulse = 1.0 + math.sin(self.timer * 2.4) * 0.14
        return (self.x, self.y - 12, 74.0 * pulse, (120, 200, 240))


class Door(Prop):
    """Sonraki bolume gecis. Kilitliyse anahtar ister."""
    interactive = True
    prompt = "Gec"

    def __init__(self, scene, x: float, y: float, **options) -> None:
        super().__init__(scene, x, y, **options)
        self.target = options.get("target", "")
        self.locked = bool(options.get("locked", False))
        self.boss = bool(options.get("boss", False))
        self.open_amount = 0.0
        boss = self.boss
        self.image = scene.app.assets.generated(
            f"prop:door_{int(boss)}", lambda: build_door(0.0, boss))

    def interact(self, player) -> None:
        if self.locked:
            self.scene.show_toast("Kilitli. Bir anahtar gerekiyor.")
            self.scene.app.audio.play("ui_back")
            return
        self.scene.app.audio.play("door")
        self.scene.transition_to_level(self.target)

    def light(self):
        if not self.boss:
            return None
        return (self.x, self.y - 20, 52.0, (170, 120, 220))


class Chest(Prop):
    interactive = True
    prompt = "Ac"

    def __init__(self, scene, x: float, y: float, **options) -> None:
        super().__init__(scene, x, y, **options)
        self.opened = False
        self.contents = options.get("contents", "essence")
        self.amount = int(options.get("amount", 12))
        self.id = options.get("id", f"chest_{int(x)}_{int(y)}")
        self.image = scene.app.assets.generated("prop:chest_closed",
                                                lambda: build_chest(False))

    def interact(self, player) -> None:
        if self.opened:
            return
        self.opened = True
        self.image = self.scene.app.assets.generated("prop:chest_open",
                                                     lambda: build_chest(True))
        self.scene.app.audio.play("pickup")
        self.scene.on_chest_opened(self)


class Breakable(Prop):
    """Kirilabilir kup: vurunca dagilir, icinden Essence cikar."""

    def __init__(self, scene, x: float, y: float, **options) -> None:
        super().__init__(scene, x, y, **options)
        from lore.gfx.tiles import build_breakable
        self.image = scene.app.assets.generated("prop:breakable",
                                                lambda: build_breakable(TILE))
        self.health = 1


PROP_TYPES: dict[str, type[Prop]] = {
    "torch": Torch,
    "shrine": Shrine,
    "door": Door,
    "chest": Chest,
    "breakable": Breakable,
}


def spawn_prop(scene, kind: str, x: float, y: float, **options) -> Prop | None:
    cls = PROP_TYPES.get(kind)
    if cls is None:
        print(f"[pickups] bilinmeyen prop turu: {kind}")
        return None
    return cls(scene, x, y, **options)
