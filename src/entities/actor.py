"""Varlik temeli: govde, AABB carpisma, saglik, durum makinesi.

**Eksenler ayri cozulur, piksel piksel ilerlenir.** Yeni konumu tek seferde
test edip carpisma varsa hareketi tamamen iptal etmek yaygin bir hatadir:
duvara surtunce karakter takilir, koseye sikisir, egik hareket engellenir.

X ve Y bagimsiz cozuldugunde duvar boyunca kayma, kose yakalama ve tavana
carpip dusme bedava gelir. Piksel piksel ilerlemek yuksek hizda tunnelleme
sorununu da siler.

Alt piksel birikimi ayri tutulur: konum float, carpisma int. Aksi halde 0.4
piksellik hizlar hicbir zaman hareket etmez ya da yuvarlamalar titreme yaratir.

Hiz birimi **piksel/kare**.
"""
from __future__ import annotations

import pygame

from src.combat.hitbox import DamageResult, Hitbox, Team
from src.config import GRAVITY, MAX_FALL_SPEED
from src.core.juice import HitFlash, Squash


class Body:
    """Dunyada yer kaplayan, tile'lara carpan hacim."""

    __slots__ = ("x", "y", "width", "height", "vx", "vy",
                 "grounded", "was_grounded", "ceiling",
                 "wall_left", "wall_right", "on_platform",
                 "gravity_scale", "drop_through", "ignore_solids",
                 "_remainder_x", "_remainder_y", "_previous_bottom")

    def __init__(self, x: float, y: float, width: int, height: int) -> None:
        self.x = float(x)
        self.y = float(y)
        self.width = int(width)
        self.height = int(height)
        self.vx = 0.0
        self.vy = 0.0

        self.grounded = False
        self.was_grounded = False
        self.ceiling = False
        self.wall_left = False
        self.wall_right = False
        self.on_platform = False

        self.gravity_scale = 1.0
        self.drop_through = False
        self.ignore_solids = False

        self._remainder_x = 0.0
        self._remainder_y = 0.0
        self._previous_bottom = float(y + height)

    # --- Geometri -----------------------------------------------------------
    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    @property
    def center_x(self) -> float:
        return self.x + self.width * 0.5

    @property
    def center_y(self) -> float:
        return self.y + self.height * 0.5

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def top(self) -> float:
        """Govdenin ust kenari - `self.y` ile ayni sey.

        Ayri bir ad olarak duruyor cunku `bottom` vardi ve `top` yoktu;
        bu asimetri `echo_view.draw_answer`'i cokertti (Arda, 29.08.2026:
        `AttributeError: 'Body' object has no attribute 'top'`). Yanki'ya
        soru soruldugunda - yani nadiren - calisan bir cizim yoluydu ve
        oyun aylarca o satira hic ugramadi.

        `bottom`/`top`/`left`/`right` bir arada bulunmali: birinin varligi
        digerlerini de bekletiyor.
        """
        return self.y

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def feet(self) -> tuple[float, float]:
        return (self.center_x, self.y + self.height)

    def set_feet(self, x: float, y: float) -> None:
        self.x = x - self.width * 0.5
        self.y = y - self.height

    # --- Carpisma -----------------------------------------------------------
    def _blocked(self, tilemap, nx: int, ny: int, moving_down: bool) -> bool:
        if self.ignore_solids:
            return False
        probe = pygame.Rect(nx, ny, self.width, self.height)
        if tilemap.solid_overlap(probe):
            return True
        if moving_down and not self.drop_through:
            return tilemap.platform_top_overlap(probe, self._previous_bottom)
        return False

    def move(self, tilemap) -> None:
        """Hizi konuma uygular ve carpismalari cozer. Bir kare."""
        self.was_grounded = self.grounded
        self._previous_bottom = self.bottom
        self.grounded = False
        self.ceiling = False
        self.wall_left = False
        self.wall_right = False
        self.on_platform = False

        self._move_axis(tilemap, horizontal=True)
        self._move_axis(tilemap, horizontal=False)

        if self.grounded and self.vy > 0.0:
            self.vy = 0.0

    def _move_axis(self, tilemap, horizontal: bool) -> None:
        if horizontal:
            self._remainder_x += self.vx
            steps = int(self._remainder_x)
            self._remainder_x -= steps
        else:
            self._remainder_y += self.vy
            steps = int(self._remainder_y)
            self._remainder_y -= steps

        if steps == 0:
            if not horizontal:
                self._probe_ground(tilemap)
            return

        direction = 1 if steps > 0 else -1
        for _ in range(abs(steps)):
            if horizontal:
                nx = int(self.x) + direction
                if self._blocked(tilemap, nx, int(self.y), moving_down=False):
                    if direction > 0:
                        self.wall_right = True
                    else:
                        self.wall_left = True
                    self.vx = 0.0
                    self._remainder_x = 0.0
                    return
                self.x += direction
            else:
                ny = int(self.y) + direction
                if self._blocked(tilemap, int(self.x), ny,
                                 moving_down=direction > 0):
                    if direction > 0:
                        self.grounded = True
                    else:
                        self.ceiling = True
                        self.vy = 0.0
                    self._remainder_y = 0.0
                    return
                self.y += direction

        if not horizontal:
            self._probe_ground(tilemap)

    def _probe_ground(self, tilemap) -> None:
        """Bir piksel asagida kati bir sey var mi? (Zemin temasi.)"""
        if self.vy < 0.0:
            return
        if self._blocked(tilemap, int(self.x), int(self.y) + 1, moving_down=True):
            self.grounded = True

    # --- Kuvvetler ----------------------------------------------------------
    def apply_gravity(self, scale: float | None = None) -> None:
        pull = GRAVITY * (self.gravity_scale if scale is None else scale)
        self.vy = min(self.vy + pull, MAX_FALL_SPEED)

    def approach_vx(self, target: float, amount: float) -> None:
        if self.vx < target:
            self.vx = min(self.vx + amount, target)
        else:
            self.vx = max(self.vx - amount, target)


class Actor:
    """Hasar alabilen, cizilebilen her sey."""

    team: Team = Team.ENEMY
    body_width: int = 10
    body_height: int = 20
    max_health: int = 30
    poise: int = 3                  # Bu kadar vurusta sendeler
    iframes_on_hit: int = 0         # Dusmanlarda 0 - combo kesilmesin

    def __init__(self, scene, x: float, y: float) -> None:
        self.scene = scene
        self.body = Body(x - self.body_width * 0.5, y - self.body_height,
                         self.body_width, self.body_height)
        self.facing = 1
        self.health = self.max_health
        self.dead = False
        self.remove = False

        self.iframes = 0
        self.stagger_frames = 0
        self.poise_left = self.poise

        self.flash = HitFlash()
        self.squash = Squash()

    # --- Sorgular -----------------------------------------------------------
    @property
    def hurtbox(self) -> pygame.Rect:
        """Carpisma dikdortgeni. Sprite'tan kucuk - affedici ve hizli."""
        return self.body.rect

    @property
    def invulnerable(self) -> bool:
        return self.iframes > 0

    @property
    def health_ratio(self) -> float:
        return self.health / self.max_health if self.max_health else 0.0

    def distance_to(self, other: "Actor") -> float:
        return abs(self.body.center_x - other.body.center_x)

    # --- Hasar --------------------------------------------------------------
    def take_damage(self, box: Hitbox, direction: tuple[float, float]) -> DamageResult:
        if self.dead or self.invulnerable:
            return DamageResult(hit=False)

        self.health -= box.damage
        self.iframes = self.iframes_on_hit

        # Geri itme darbe yonunde + hafif yukari bilesen.
        length = max(1e-5, (direction[0] ** 2 + direction[1] ** 2) ** 0.5)
        self.body.vx = direction[0] / length * box.knockback
        self.body.vy = -box.knockback_up

        result = DamageResult(hit=True, amount=box.damage)

        self.poise_left -= box.poise_damage
        if self.poise_left <= 0:
            self.poise_left = self.poise
            self.stagger_frames = self._stagger_length()
            result.staggered = True

        if self.health <= 0:
            self.health = 0
            result.killed = True
            self.die()
        return result

    def _stagger_length(self) -> int:
        from src.config import ENEMY_STAGGER_FRAMES
        return ENEMY_STAGGER_FRAMES

    def die(self) -> None:
        self.dead = True

    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        if self.iframes > 0:
            self.iframes -= 1
        if self.stagger_frames > 0:
            self.stagger_frames -= 1
        self.flash.update()
        self.squash.update()

        self.body.apply_gravity()
        self.body.move(self.scene.tilemap)

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        raise NotImplementedError
