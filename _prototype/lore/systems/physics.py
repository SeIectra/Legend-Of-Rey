"""AABB fizigi ve tile carpismasi.

Yaklasim: **eksenleri ayri coz, piksel piksel ilerle.**

Eski koddaki hata sudur: yeni konum hesaplanip tek seferde test edilir, carpisma
varsa hareket tamamen iptal edilir (hatta geri alinir). Sonuc: duvara surtunce
karakter takilir, koseye sikisir, egik hareket engellenir.

Burada X ve Y bagimsiz cozuluyor. Duvara yatay carpip dikey hareketine devam
edebilirsin - duvar boyunca kayma, kose yakalama, tavana carpip dusme hepsi
bedava geliyor. Piksel piksel ilerlemek yuksek hizda tunnelleme sorununu de
kokten siliyor.

Alt piksel birikimi ayri tutuluyor: konum float, carpisma int. Aksi halde 0.4
piksellik hizlar hicbir zaman hareket etmez ya da yuvarlamalar titreme yaratir.
"""
from __future__ import annotations

import pygame

from lore.constants import GRAVITY, MAX_FALL_SPEED, TILE
from lore.core.mathx import approach, clamp


class Body:
    """Dunyada yer kaplayan, tile'lara carpan bir hacim."""

    __slots__ = (
        "x", "y", "w", "h", "vx", "vy",
        "grounded", "was_grounded", "ceiling", "wall_left", "wall_right",
        "gravity_scale", "max_fall", "drop_through", "on_platform",
        "_rem_x", "_rem_y", "ignore_solids",
    )

    def __init__(self, x: float, y: float, w: int, h: int) -> None:
        self.x = float(x)
        self.y = float(y)
        self.w = int(w)
        self.h = int(h)
        self.vx = 0.0
        self.vy = 0.0

        self.grounded = False
        self.was_grounded = False
        self.ceiling = False
        self.wall_left = False
        self.wall_right = False
        self.on_platform = False

        self.gravity_scale = 1.0
        self.max_fall = MAX_FALL_SPEED
        self.drop_through = False       # Tek yonlu platformdan asagi in
        self.ignore_solids = False      # Hayalet/olum animasyonu icin

        # Alt piksel birikimi
        self._rem_x = 0.0
        self._rem_y = 0.0

    # --- Geometri -----------------------------------------------------------
    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    @property
    def centerx(self) -> float:
        return self.x + self.w * 0.5

    @property
    def centery(self) -> float:
        return self.y + self.h * 0.5

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.w * 0.5, self.y + self.h * 0.5)

    @property
    def feet(self) -> tuple[float, float]:
        return (self.x + self.w * 0.5, self.y + self.h)

    def set_center(self, x: float, y: float) -> None:
        self.x = x - self.w * 0.5
        self.y = y - self.h * 0.5

    def set_feet(self, x: float, y: float) -> None:
        self.x = x - self.w * 0.5
        self.y = y - self.h

    # --- Carpisma testi -----------------------------------------------------
    def _blocked(self, tilemap, nx: int, ny: int, moving_down: bool) -> bool:
        """(nx, ny) konumunda kati bir seye giriyor muyuz?"""
        if self.ignore_solids:
            return False
        probe = pygame.Rect(nx, ny, self.w, self.h)
        x0, y0, x1, y1 = tilemap.tile_range(probe)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if tilemap.is_solid(tx, ty):
                    return True
                if tilemap.is_platform(tx, ty) and moving_down and not self.drop_through:
                    # Tek yonlu platform yalnizca ustunden gelirken katidir.
                    # Ayak seviyesi platformun ustune inmis olmali; yoksa
                    # asagidan ziplayan oyuncu havada takilir.
                    top = ty * TILE
                    if self.y + self.h <= top + 1 <= ny + self.h:
                        return True
        return False

    def _platform_below(self, tilemap, nx: int, ny: int) -> bool:
        probe = pygame.Rect(nx, ny, self.w, self.h)
        x0, _, x1, y1 = tilemap.tile_range(probe)
        for tx in range(x0, x1 + 1):
            if tilemap.is_platform(tx, y1):
                return True
        return False

    # --- Hareket ------------------------------------------------------------
    def move(self, tilemap, dt: float) -> None:
        """Hizi konuma uygular ve carpismalari cozer."""
        self.was_grounded = self.grounded
        self.grounded = False
        self.ceiling = False
        self.wall_left = False
        self.wall_right = False
        self.on_platform = False

        self._move_axis(tilemap, dt, axis="x")
        self._move_axis(tilemap, dt, axis="y")

        # Zeminde duruyorsak dikey hizi sifirla, ama bir tik asagi bastir:
        # egimli inislerde ve platform kenarlarinda "havada suzulme" olmaz.
        if self.grounded and self.vy > 0.0:
            self.vy = 0.0

    def _move_axis(self, tilemap, dt: float, axis: str) -> None:
        if axis == "x":
            self._rem_x += self.vx * dt
            steps = int(self._rem_x)
            self._rem_x -= steps
        else:
            self._rem_y += self.vy * dt
            steps = int(self._rem_y)
            self._rem_y -= steps
        if steps == 0:
            # Hareket etmesek bile zemin temasini bilmeliyiz.
            if axis == "y":
                self._probe_ground(tilemap)
            return

        direction = 1 if steps > 0 else -1
        for _ in range(abs(steps)):
            if axis == "x":
                nx = int(self.x) + direction
                if self._blocked(tilemap, nx, int(self.y), moving_down=False):
                    if direction > 0:
                        self.wall_right = True
                    else:
                        self.wall_left = True
                    self.vx = 0.0
                    self._rem_x = 0.0
                    return
                self.x += direction
            else:
                ny = int(self.y) + direction
                if self._blocked(tilemap, int(self.x), ny, moving_down=direction > 0):
                    if direction > 0:
                        self.grounded = True
                        self.on_platform = self._platform_below(
                            tilemap, int(self.x), ny)
                    else:
                        self.ceiling = True
                        self.vy = 0.0
                    self._rem_y = 0.0
                    return
                self.y += direction

        if axis == "y":
            self._probe_ground(tilemap)

    def _probe_ground(self, tilemap) -> None:
        """Bir piksel asagida kati bir sey var mi? (Zemin temasi.)"""
        if self.vy < 0.0:
            return
        if self._blocked(tilemap, int(self.x), int(self.y) + 1, moving_down=True):
            self.grounded = True
            self.on_platform = self._platform_below(
                tilemap, int(self.x), int(self.y) + 1)

    # --- Kuvvetler ----------------------------------------------------------
    def apply_gravity(self, dt: float, scale: float | None = None) -> None:
        g = GRAVITY * (self.gravity_scale if scale is None else scale)
        self.vy = min(self.vy + g * dt, self.max_fall)

    def friction(self, amount: float, dt: float) -> None:
        self.vx = approach(self.vx, 0.0, amount * dt)

    def clamp_to(self, bounds: pygame.Rect) -> None:
        self.x = clamp(self.x, bounds.left, bounds.right - self.w)
        if self.y > bounds.bottom:
            self.y = bounds.bottom


# --- Yardimci sorgular ------------------------------------------------------
def ledge_ahead(body: Body, tilemap, facing: int, look: int = 2) -> bool:
    """Onunde ucurum var mi? Dusman AI'si kenardan dusmesin diye.

    Ayagin biraz onundeki noktanin altina bakariz; hem kati hem platform
    zemin sayilir.
    """
    probe_x = int(body.x + (body.w + look if facing > 0 else -look)) // TILE
    probe_y = int(body.y + body.h) // TILE
    return not (tilemap.is_solid(probe_x, probe_y)
                or tilemap.is_platform(probe_x, probe_y))


def wall_ahead(body: Body, tilemap, facing: int) -> bool:
    probe_x = int(body.x + (body.w + 1 if facing > 0 else -1)) // TILE
    top = int(body.y + 2) // TILE
    bottom = int(body.y + body.h - 2) // TILE
    return any(tilemap.is_solid(probe_x, ty) for ty in range(top, bottom + 1))


def line_of_sight(tilemap, x0: float, y0: float, x1: float, y1: float,
                  step: float = 4.0) -> bool:
    """Iki nokta arasinda kati tile var mi? Dusmanin oyuncuyu gormesi icin."""
    dx, dy = x1 - x0, y1 - y0
    distance = max(abs(dx), abs(dy))
    if distance < 1.0:
        return True
    count = int(distance / step) + 1
    for i in range(1, count):
        t = i / count
        if tilemap.solid_at_pixel(x0 + dx * t, y0 + dy * t):
            return False
    return True
