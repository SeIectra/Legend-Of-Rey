"""Prosedurel piksel sanat atolyesi.

Temel fikir: **renkle degil, golge zinciri indeksiyle cizeriz.**

Her piksel iki sayi tutar - hangi zincir (`hair_dark`, `steel`, `skin_tan`...)
ve o zincirin kacinci basamagi (0 en koyu, 3 en acik). Cizim bittikten sonra:

  * `shade()`   sol-usttan isik alan kenarin basamagini +1, sag-alt golgenin
                -1 yapar. Elle golge boyamak yok; tek gecis hacim uretir.
  * `outline()` siluetin cevresine kontur cizer - paletin en koyu 2. rengi.
  * `resolve()` indeks ciftlerini gercek renklere cevirip Surface uretir.

Bunun bedava getirdikleri:
  * Ayni sprite farkli zincirle cozulunce bambaska bir karakter olur
  * Palet degisince tum oyun degisir, tek dosyadan
  * Golgeleme her varlikta tutarli - stil sozlesmesi otomatik uygulanir
  * Palet disina cikmak **imkansiz** (CLAUDE.md 6)

Uretilen her yuzey `convert_alpha()` gorur; unutulursa oyun 3-5 kat yavaslar.
"""
from __future__ import annotations

import math

import numpy as np
import pygame

from src.art import palette

EMPTY = 255                  # "burada piksel yok" isareti
MAX_STEP = 3                 # Zincirler 4 basamak: 0..3

# Zincir adlarini sabit sirayla indeksliyoruz; uint8 tamponda saklamak icin.
CHAIN_NAMES: tuple[str, ...] = tuple(palette.SHADE_CHAINS.keys())
CHAIN_INDEX: dict[str, int] = {name: i for i, name in enumerate(CHAIN_NAMES)}

# Cozunmus renk tablosu: [zincir][basamak] -> RGB. Bir kez kurulur.
_LUT = np.zeros((len(CHAIN_NAMES), MAX_STEP + 1, 3), dtype=np.uint8)
for _i, _name in enumerate(CHAIN_NAMES):
    for _s in range(MAX_STEP + 1):
        _LUT[_i, _s] = palette.chain_color(_name, _s)

# Isik yonu: sol-ust. Tum oyun boyunca degismez (CLAUDE.md 6).
LIGHT_DX, LIGHT_DY = -1, -1


class Canvas:
    """Indeks tabanli cizim yuzeyi."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.chain = np.full((height, width), EMPTY, dtype=np.uint8)
        self.step = np.zeros((height, width), dtype=np.uint8)
        self.glow = np.zeros((height, width), dtype=np.uint8)

    # --- Yardimcilar --------------------------------------------------------
    @staticmethod
    def _chain_id(name: str) -> int:
        try:
            return CHAIN_INDEX[name]
        except KeyError as exc:
            raise palette.PaletteError(
                f"tanimsiz golge zinciri: {name!r}") from exc

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def clear(self) -> None:
        self.chain[:] = EMPTY
        self.step[:] = 0
        self.glow[:] = 0

    # --- Ilkel sekiller -----------------------------------------------------
    def px(self, x: int, y: int, chain: str, step: int, glow: int = 0) -> None:
        if not self.in_bounds(x, y):
            return
        self.chain[y, x] = self._chain_id(chain)
        self.step[y, x] = max(0, min(MAX_STEP, step))
        if glow:
            self.glow[y, x] = glow

    def fill_rect(self, x: int, y: int, w: int, h: int, chain: str, step: int,
                  glow: int = 0) -> None:
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.width, x + w), min(self.height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        self.chain[y0:y1, x0:x1] = self._chain_id(chain)
        self.step[y0:y1, x0:x1] = max(0, min(MAX_STEP, step))
        if glow:
            self.glow[y0:y1, x0:x1] = glow

    def rect(self, x: int, y: int, w: int, h: int, chain: str,
             step: int) -> None:
        self.fill_rect(x, y, w, 1, chain, step)
        self.fill_rect(x, y + h - 1, w, 1, chain, step)
        self.fill_rect(x, y, 1, h, chain, step)
        self.fill_rect(x + w - 1, y, 1, h, chain, step)

    def disc(self, cx: float, cy: float, radius: float, chain: str, step: int,
             glow: int = 0) -> None:
        r2 = radius * radius
        for y in range(max(0, int(cy - radius) - 1),
                       min(self.height, int(cy + radius) + 2)):
            dy = y + 0.5 - cy
            for x in range(max(0, int(cx - radius) - 1),
                           min(self.width, int(cx + radius) + 2)):
                dx = x + 0.5 - cx
                if dx * dx + dy * dy <= r2:
                    self.px(x, y, chain, step, glow)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, chain: str,
                step: int, glow: int = 0) -> None:
        if rx <= 0 or ry <= 0:
            return
        for y in range(max(0, int(cy - ry) - 1),
                       min(self.height, int(cy + ry) + 2)):
            dy = (y + 0.5 - cy) / ry
            for x in range(max(0, int(cx - rx) - 1),
                           min(self.width, int(cx + rx) + 2)):
                dx = (x + 0.5 - cx) / rx
                if dx * dx + dy * dy <= 1.0:
                    self.px(x, y, chain, step, glow)

    def line(self, x0: float, y0: float, x1: float, y1: float,
             thickness: float, chain: str, step: int, glow: int = 0) -> None:
        """Kalin cizgi, uclari yuvarlak. Uzuvlar bununla ciziliyor."""
        steps = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1)
        radius = thickness * 0.5
        for i in range(steps + 1):
            t = i / steps
            cx = x0 + (x1 - x0) * t
            cy = y0 + (y1 - y0) * t
            if thickness <= 1.2:
                self.px(int(round(cx)), int(round(cy)), chain, step, glow)
            else:
                self.disc(cx, cy, radius, chain, step, glow)

    def limb(self, x0: float, y0: float, angle: float, length: float,
             thickness: float, chain: str, step: int) -> tuple[float, float]:
        """Aciyla uzuv cizer, uc noktayi doner (zincirleme icin)."""
        x1 = x0 + math.cos(angle) * length
        y1 = y0 + math.sin(angle) * length
        self.line(x0, y0, x1, y1, thickness, chain, step)
        return x1, y1

    def taper(self, x0: float, y0: float, x1: float, y1: float,
              w0: float, w1: float, chain: str, step: int,
              glow: int = 0) -> None:
        """Bir uctan digerine incelen sekil (bicak agzi, boynuz, kuyruk)."""
        steps = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1)
        for i in range(steps + 1):
            t = i / steps
            cx = x0 + (x1 - x0) * t
            cy = y0 + (y1 - y0) * t
            radius = (w0 + (w1 - w0) * t) * 0.5
            if radius < 0.6:
                self.px(int(round(cx)), int(round(cy)), chain, step, glow)
            else:
                self.disc(cx, cy, radius, chain, step, glow)

    def polygon(self, points: list[tuple[float, float]], chain: str, step: int,
                glow: int = 0) -> None:
        """Tarama cizgisiyle dolu cokgen."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for y in range(max(0, int(min(ys))), min(self.height, int(max(ys)) + 1)):
            crossings: list[float] = []
            for i in range(len(points)):
                ax, ay = points[i]
                bx, by = points[(i + 1) % len(points)]
                if (ay <= y < by) or (by <= y < ay):
                    crossings.append(ax + (y - ay) / (by - ay) * (bx - ax))
            crossings.sort()
            for i in range(0, len(crossings) - 1, 2):
                left = int(crossings[i])
                width = max(1, int(crossings[i + 1]) - left + 1)
                self.fill_rect(left, y, width, 1, chain, step, glow)

    # --- Doku ---------------------------------------------------------------
    def noise(self, seed: int, amount: float = 0.35,
              chain: str | None = None) -> None:
        """Dolu piksellerin basamagini rastgele oynatir: yuzey dokusu.

        Deterministik seed sart - ayni sprite her calistirmada ayni gorunmeli,
        yoksa animasyon kareleri arasinda doku titrer.
        """
        rng = np.random.default_rng(seed)
        mask = self.chain != EMPTY
        if chain is not None:
            mask &= self.chain == self._chain_id(chain)
        roll = rng.random(self.chain.shape)
        up = mask & (roll < amount * 0.5)
        down = mask & (roll > 1.0 - amount * 0.5)
        self.step[up] = np.minimum(self.step[up] + 1, MAX_STEP)
        self.step[down] = np.maximum(
            self.step[down].astype(np.int16) - 1, 0).astype(np.uint8)

    # --- Golgeleme ----------------------------------------------------------
    def shade(self, strength: int = 1) -> None:
        """Sol-ust isik kuralini uygular - stil sozlesmesi otomatiklesir.

        Sol-ustu bos olan piksel isik alir (+1), sag-altta bosluk goren piksel
        golgede kalir (-1). Tek gecis, duz siluetlere hacim verir.
        """
        solid = self.chain != EMPTY

        lit = np.zeros_like(solid)
        lit[1:, 1:] = solid[1:, 1:] & ~solid[:-1, :-1]
        lit[0, :] |= solid[0, :]
        lit[:, 0] |= solid[:, 0]

        dark = np.zeros_like(solid)
        dark[:-1, :-1] = solid[:-1, :-1] & ~solid[1:, 1:]
        dark[-1, :] |= solid[-1, :]
        dark[:, -1] |= solid[:, -1]

        step = self.step.astype(np.int16)
        step[lit & ~dark] += strength
        step[dark & ~lit] -= strength
        self.step = np.clip(step, 0, MAX_STEP).astype(np.uint8)

    def outline(self, chain: str = "shadow", step: int = 1,
                diagonal: bool = False) -> None:
        """Siluetin disina 1 piksel kontur. Pixel art okunurlugunun temeli.

        Varsayilan `shadow` zincirinin 1. basamagi = `ink`, yani paletin en
        koyu 2. rengi. Siyah degil (CLAUDE.md 6).
        """
        solid = self.chain != EMPTY
        grown = np.zeros_like(solid)
        grown[1:, :] |= solid[:-1, :]
        grown[:-1, :] |= solid[1:, :]
        grown[:, 1:] |= solid[:, :-1]
        grown[:, :-1] |= solid[:, 1:]
        if diagonal:
            grown[1:, 1:] |= solid[:-1, :-1]
            grown[:-1, :-1] |= solid[1:, 1:]
            grown[1:, :-1] |= solid[:-1, 1:]
            grown[:-1, 1:] |= solid[1:, :-1]
        edge = grown & ~solid
        self.chain[edge] = self._chain_id(chain)
        self.step[edge] = max(0, min(MAX_STEP, step))

    def recolor(self, source: str, target: str) -> None:
        """Bir zinciri digeriyle degistir - ayni sprite, farkli karakter."""
        self.chain[self.chain == self._chain_id(source)] = self._chain_id(target)

    def blit(self, other: "Canvas", x: int, y: int) -> None:
        """Baska bir canvas'i uzerine yapistir (bos pikseller atlanir)."""
        x0, y0 = max(0, x), max(0, y)
        x1 = min(self.width, x + other.width)
        y1 = min(self.height, y + other.height)
        if x1 <= x0 or y1 <= y0:
            return
        sx, sy = x0 - x, y0 - y
        w, h = x1 - x0, y1 - y0
        sub = other.chain[sy:sy + h, sx:sx + w]
        mask = sub != EMPTY
        self.chain[y0:y1, x0:x1][mask] = sub[mask]
        self.step[y0:y1, x0:x1][mask] = other.step[sy:sy + h, sx:sx + w][mask]
        self.glow[y0:y1, x0:x1][mask] = other.glow[sy:sy + h, sx:sx + w][mask]

    # --- Cikti --------------------------------------------------------------
    def resolve(self, alpha: int = 255) -> pygame.Surface:
        """Indeks tamponunu gercek renklere cevirip Surface uretir."""
        rgb = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        solid = self.chain != EMPTY
        if solid.any():
            rgb[solid] = _LUT[self.chain[solid].astype(np.int32),
                              self.step[solid].astype(np.int32)]

        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        surface = surface.convert_alpha()
        # numpy (satir, sutun), pygame (genislik, yukseklik) - eksen cevrimi.
        pygame.surfarray.pixels3d(surface)[:] = np.transpose(rgb, (1, 0, 2))
        pygame.surfarray.pixels_alpha(surface)[:] = np.transpose(
            np.where(solid, alpha, 0).astype(np.uint8), (1, 0))
        return surface

    def glow_mask(self) -> pygame.Surface | None:
        """Isik yayan piksellerin maskesi; isiklandirma katmani kullanir."""
        if not self.glow.any():
            return None
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        surface = surface.convert_alpha()
        rgb = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        solid = self.chain != EMPTY
        if solid.any():
            rgb[solid] = _LUT[self.chain[solid].astype(np.int32),
                              self.step[solid].astype(np.int32)]
        pygame.surfarray.pixels3d(surface)[:] = np.transpose(rgb, (1, 0, 2))
        pygame.surfarray.pixels_alpha(surface)[:] = np.transpose(self.glow, (1, 0))
        return surface


# --- Yuzey duzeyinde yardimcilar --------------------------------------------
def flip_h(surface: pygame.Surface) -> pygame.Surface:
    return pygame.transform.flip(surface, True, False)


def silhouette(surface: pygame.Surface,
               colour: palette.RGB | None = None) -> pygame.Surface:
    """Tek renkli siluet. Hem hasar flasi hem F4 siluet modu icin."""
    out = surface.copy()
    colour = colour or palette.role("hit_flash")
    rgb = pygame.surfarray.pixels3d(out)
    rgb[:, :, 0] = colour[0]
    rgb[:, :, 1] = colour[1]
    rgb[:, :, 2] = colour[2]
    del rgb
    return out


def tint(surface: pygame.Surface, colour: palette.RGB,
         strength: float) -> pygame.Surface:
    """Sprite'i bir renge dogru karistirir. Alfaya dokunmaz, siluet bozulmaz."""
    out = surface.copy()
    strength = max(0.0, min(1.0, strength))
    if strength <= 0.0:
        return out
    rgb = pygame.surfarray.pixels3d(out).astype(np.float32)
    target = np.array(colour, dtype=np.float32)
    rgb += (target - rgb) * strength
    pygame.surfarray.pixels3d(out)[:] = rgb.astype(np.uint8)
    return out


def squash_surface(surface: pygame.Surface,
                   scale: tuple[float, float]) -> pygame.Surface:
    """Squash & stretch: yeni kare cizmeden deformasyon.

    `smoothscale` degil `scale` - piksel art bulaniklasmamali.
    """
    scale_x, scale_y = scale
    if abs(scale_x - 1.0) < 0.01 and abs(scale_y - 1.0) < 0.01:
        return surface
    width = max(1, int(round(surface.get_width() * scale_x)))
    height = max(1, int(round(surface.get_height() * scale_y)))
    return pygame.transform.scale(surface, (width, height))
