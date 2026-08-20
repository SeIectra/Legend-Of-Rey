"""Varlik temeli ve animasyon oynatici.

`Animator` kare zamanlamasini tek yerde toplar: her varlik kendi sayacini
tutmaz. `Entity` ise her canlinin ortak yuzeyini tanimlar - govde, saglik,
dokunulmazlik, hasar flasi, cizim.

Hasar flasi kucuk ama kritik bir detay: vurulan varlik birkac kare beyaz
siluete doner. Oyuncu vurusun degdigini sprite'i incelemeden anlar.
"""
from __future__ import annotations

import pygame

from lore.constants import MASK_ENEMY
from lore.gfx.forge import silhouette
from lore.systems.combat import DamageResult, DamageType
from lore.systems.physics import Body


class Animator:
    """Kare listesi oynatir; durum degisiminde bastan baslar."""

    def __init__(self, sprite_set: dict[str, list[pygame.Surface]],
                 fps: dict[str, float] | None = None,
                 looping: dict[str, bool] | None = None) -> None:
        self.sets = sprite_set
        self.fps = fps or {}
        self.looping = looping or {}
        self.state = next(iter(sprite_set), "idle")
        self.frame = 0
        self.timer = 0.0
        self.finished = False
        self.default_fps = 10.0

    def play(self, state: str, restart: bool = False) -> None:
        if state not in self.sets:
            return
        if state == self.state and not restart:
            return
        self.state = state
        self.frame = 0
        self.timer = 0.0
        self.finished = False

    def update(self, dt: float, speed: float = 1.0) -> None:
        frames = self.sets.get(self.state)
        if not frames:
            return
        if self.finished and not self.looping.get(self.state, True):
            return
        rate = self.fps.get(self.state, self.default_fps) * max(0.05, speed)
        self.timer += dt * rate
        while self.timer >= 1.0:
            self.timer -= 1.0
            self.frame += 1
            if self.frame >= len(frames):
                if self.looping.get(self.state, True):
                    self.frame = 0
                else:
                    self.frame = len(frames) - 1
                    self.finished = True
                    break

    @property
    def image(self) -> pygame.Surface | None:
        frames = self.sets.get(self.state)
        if not frames:
            return None
        return frames[min(self.frame, len(frames) - 1)]

    @property
    def progress(self) -> float:
        """Animasyonun 0..1 arasi ilerlemesi. Hitbox zamanlamasi icin."""
        frames = self.sets.get(self.state)
        if not frames:
            return 1.0
        return (self.frame + self.timer) / len(frames)


class Entity:
    """Dunyada yasayan, hasar alabilen her sey."""

    # Alt siniflar bunlari ezer
    sprite_key = "goblin"
    max_health = 3
    team_mask = MASK_ENEMY
    body_w = 10
    body_h = 18
    iframe_time = 0.4
    flash_time = 0.12
    gravity_enabled = True

    def __init__(self, scene, x: float, y: float) -> None:
        self.scene = scene
        self.body = Body(x - self.body_w * 0.5, y - self.body_h, self.body_w,
                         self.body_h)
        self.facing = 1
        self.health = self.max_health
        self.dead = False
        self.remove = False

        self.iframes = 0.0
        self.flash = 0.0
        self.stagger = 0.0
        self.anim: Animator | None = None
        # Sprite hucresi icinde karakterin taban cizgisi (CharSpec.foot_y).
        # Hucre karakterden buyuktur - silahin savrulmasina yer birakir - ve
        # ayaklarin altinda bos piksel kalir. Bu degeri bilmezsek hucrenin
        # altini zemine hizalamak zorunda kaliriz ve karakter havada durur.
        self.sprite_foot_y: int | None = None
        self.sprite_offset = (0, 0)     # Ince ayar icin ek kaydirma
        self._flash_cache: dict[int, pygame.Surface] = {}

    # --- Geometri -----------------------------------------------------------
    @property
    def hurtbox(self) -> pygame.Rect:
        return self.body.rect

    @property
    def x(self) -> float:
        return self.body.centerx

    @property
    def y(self) -> float:
        return self.body.centery

    def distance_to(self, other) -> float:
        return abs(self.body.centerx - other.body.centerx)

    # --- Hasar --------------------------------------------------------------
    def take_damage(self, amount: int, source=None, direction: int = 1,
                    knockback: float = 120.0, knockback_up: float = 60.0,
                    damage_type: DamageType = DamageType.PHYSICAL,
                    stagger: float = 0.2) -> DamageResult:
        if self.dead or self.iframes > 0.0:
            return DamageResult(hit=False)

        self.health -= amount
        self.iframes = self.iframe_time
        self.flash = self.flash_time
        self.stagger = max(self.stagger, stagger)
        self.body.vx = direction * knockback
        self.body.vy = -knockback_up

        result = DamageResult(hit=True, amount=amount)
        if self.health <= 0:
            self.health = 0
            result.killed = True
            self.die(source)
        else:
            self.on_hurt(source)
        return result

    def on_hurt(self, source) -> None: ...

    def die(self, source=None) -> None:
        self.dead = True
        if self.anim:
            self.anim.play("death", restart=True)

    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    # --- Dongu --------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.iframes = max(0.0, self.iframes - dt)
        self.flash = max(0.0, self.flash - dt)
        self.stagger = max(0.0, self.stagger - dt)

        if self.gravity_enabled:
            self.body.apply_gravity(dt)
        self.body.move(self.scene.tilemap, dt)
        if self.anim:
            self.anim.update(dt)

    def draw(self, surface: pygame.Surface, camera) -> None:
        image = self.anim.image if self.anim else None
        if image is None:
            return
        if self.facing < 0:
            image = pygame.transform.flip(image, True, False)
        if self.flash > 0.0:
            image = self._flashed(image)
        elif self.iframes > 0.0 and int(self.iframes * 30) % 2 == 0:
            # Dokunulmazlik boyunca yanip sonme: durumu gizlemeden bildirir.
            image = image.copy()
            image.set_alpha(140)

        ox, oy = camera.offset
        # Yatayda hucre merkezini govde merkezine, dikeyde sprite'in taban
        # cizgisini govdenin altina hizala. `sprite_foot_y` bilinmiyorsa
        # hucrenin altini kullan (eski davranis).
        foot = self.sprite_foot_y
        if foot is None:
            foot = image.get_height()
        x = int(self.body.centerx - image.get_width() * 0.5) - ox
        y = int(self.body.y + self.body.h - foot + self.sprite_offset[1]) - oy
        surface.blit(image, (x, y))

    def _flashed(self, image: pygame.Surface) -> pygame.Surface:
        key = id(image)
        cached = self._flash_cache.get(key)
        if cached is None:
            cached = silhouette(image, (255, 250, 250))
            if len(self._flash_cache) > 64:
                self._flash_cache.clear()
            self._flash_cache[key] = cached
        return cached

    def draw_debug(self, surface: pygame.Surface, camera) -> None:
        ox, oy = camera.offset
        r = self.hurtbox
        pygame.draw.rect(surface, (240, 120, 160),
                         (r.x - ox, r.y - oy, r.w, r.h), 1)
