"""Tile, prop ve efekt uretimi.

**Autotile.** Her tile komsularina gore secilir. 4 bitlik bir maske tutuyoruz
(kuzey/dogu/guney/bati komsusu dolu mu) ve acik kalan her kenari isikla veya
golgeyle isaretliyoruz. Boylece 16 varyantlik bir set, elle cizilmis bir tileset
gibi davranir: zeminin ustu isik alir, alti kararir, yan yuzler ara tonda kalir.

**Varyant gurultusu.** Ayni maskeden birkac varyant uretip konuma gore
seciyoruz; tekrar eden doku deseni (pixel art'in en cok ele veren hatasi)
boylece kayboluyor.
"""
from __future__ import annotations

import math

import numpy as np
import pygame

from lore.constants import TILE
from lore.gfx.forge import Canvas

# Komsu maskesi bitleri
N, E, S, W = 1, 2, 4, 8
VARIANTS = 4


# --- Tema tanimlari ---------------------------------------------------------
class TileTheme:
    """Bir bolgenin zemin karakteri."""

    def __init__(self, name: str, base: str, top: str, deep: str,
                 accent: str | None = None, mossy: bool = False,
                 cracked: bool = False, crystal: bool = False) -> None:
        self.name = name
        self.base = base            # Govde rampasi
        self.top = top              # Ust yuzey rampasi (cim, kar, kul)
        self.deep = deep            # Derin/golgeli ic rampa
        self.accent = accent        # Damar/kristal vurgusu
        self.mossy = mossy
        self.cracked = cracked
        self.crystal = crystal


THEMES: dict[str, TileTheme] = {
    "hollow":  TileTheme("hollow", "stone", "moss", "ink", accent="moss",
                         mossy=True, cracked=True),
    "forest":  TileTheme("forest", "earth", "moss", "ink", accent="moss",
                         mossy=True),
    "vault":   TileTheme("vault", "stone", "azure", "ink", accent="azure",
                         cracked=True, crystal=True),
    "spire":   TileTheme("spire", "ash", "ember", "ink", accent="ember",
                         cracked=True),
    "sundered": TileTheme("sundered", "violet", "violet", "ink", accent="violet",
                          crystal=True),
}


# --- Tile uretimi -----------------------------------------------------------
def _build_solid_tile(theme: TileTheme, mask: int, variant: int,
                      size: int = TILE) -> pygame.Surface:
    c = Canvas(size, size)
    seed = mask * 977 + variant * 131 + hash(theme.name) % 1000

    # Govde
    c.fill_rect(0, 0, size, size, theme.base, 2)
    c.noise(seed, 0.5, theme.base)

    # Ic derinlik: merkeze dogru bir tik koyu, hacim hissi
    c.dither(3, 3, size - 6, size - 6, theme.deep, 1, density=3)

    open_n = not (mask & N)
    open_s = not (mask & S)
    open_e = not (mask & E)
    open_w = not (mask & W)

    # Ust yuzey: acik kenar isik alir; tema "ustu" farkli bir madde ise
    # (cim, kul, kristal) o rampayla ciziyoruz.
    if open_n:
        c.fill_rect(0, 0, size, 2, theme.top, 3)
        c.fill_rect(0, 0, size, 1, theme.top, 4)
        if theme.mossy:
            rng = np.random.default_rng(seed)
            for x in range(size):
                if rng.random() < 0.45:
                    c.px(x, 2, theme.top, 3)
                if rng.random() < 0.2:
                    c.px(x, 3, theme.top, 2)
    if open_s:
        c.fill_rect(0, size - 2, size, 2, theme.deep, 1)
        c.fill_rect(0, size - 1, size, 1, "ink", 0)
    if open_w:
        c.fill_rect(0, 0, 1, size, theme.base, 3)
        c.fill_rect(1, 0, 1, size, theme.base, 2)
    if open_e:
        c.fill_rect(size - 1, 0, 1, size, theme.deep, 1)
        c.fill_rect(size - 2, 0, 1, size, theme.base, 1)

    # Catlaklar
    if theme.cracked and variant % 2 == 0:
        rng = np.random.default_rng(seed + 7)
        cx, cy = int(rng.integers(3, size - 3)), int(rng.integers(3, size - 3))
        for _ in range(int(rng.integers(3, 6))):
            nx = cx + int(rng.integers(-2, 3))
            ny = cy + int(rng.integers(-1, 3))
            c.px(nx, ny, theme.deep, 0)
            cx, cy = nx, ny

    # Kristal damar
    if theme.crystal and variant % 3 == 0 and theme.accent:
        rng = np.random.default_rng(seed + 19)
        vx, vy = int(rng.integers(4, size - 4)), int(rng.integers(4, size - 4))
        c.px(vx, vy, theme.accent, 4, glow=140)
        c.px(vx + 1, vy, theme.accent, 3, glow=90)
        c.px(vx, vy + 1, theme.accent, 3, glow=90)

    return c.resolve()


def _build_platform_tile(theme: TileTheme, variant: int,
                         size: int = TILE) -> pygame.Surface:
    """Tek yonlu platform: sadece ustten basilir, alttan gecilir."""
    c = Canvas(size, size)
    seed = variant * 313 + hash(theme.name) % 500
    c.fill_rect(0, 0, size, 5, theme.base, 2)
    c.noise(seed, 0.4, theme.base)
    c.fill_rect(0, 0, size, 1, theme.top, 4)
    c.fill_rect(0, 1, size, 1, theme.top, 3)
    c.fill_rect(0, 4, size, 1, "ink", 0)
    # Destek civileri: platformun tek yonlu oldugunu gorsel olarak ele verir
    for x in (2, size - 3):
        c.px(x, 2, theme.accent or theme.base, 4)
    return c.resolve()


def _build_backdrop_tile(theme: TileTheme, variant: int,
                         size: int = TILE) -> pygame.Surface:
    """Arka duvar: carpisma yok, sadece derinlik."""
    c = Canvas(size, size)
    seed = variant * 641 + hash(theme.name) % 700
    c.fill_rect(0, 0, size, size, theme.deep, 1)
    c.noise(seed, 0.35, theme.deep)
    # Tugla derzi
    row = (variant % 2) * (size // 2)
    c.fill_rect(0, row, size, 1, theme.deep, 0)
    c.fill_rect((variant * 5) % size, row, 1, size // 2, theme.deep, 0)
    return c.resolve()


def build_tileset(theme_name: str, size: int = TILE) -> dict:
    """Bir temanin tum tile varyantlarini uretir.

    Donen sozluk:
        "solid"    -> {maske: [varyant, ...]}
        "platform" -> [varyant, ...]
        "backdrop" -> [varyant, ...]
    """
    theme = THEMES.get(theme_name, THEMES["hollow"])
    solid: dict[int, list[pygame.Surface]] = {}
    for mask in range(16):
        solid[mask] = [_build_solid_tile(theme, mask, v, size)
                       for v in range(VARIANTS)]
    return {
        "theme": theme,
        "solid": solid,
        "platform": [_build_platform_tile(theme, v, size) for v in range(VARIANTS)],
        "backdrop": [_build_backdrop_tile(theme, v, size) for v in range(VARIANTS)],
    }


# --- Prop'lar ---------------------------------------------------------------
def build_torch(frame: int, frames: int = 6) -> pygame.Surface:
    """Mesale. Alev sekli kare basina degisir; isik yaymasi icin glow tasir."""
    c = Canvas(12, 20)
    c.fill_rect(5, 10, 2, 9, "earth", 2)           # sap
    c.fill_rect(4, 9, 4, 2, "earth", 3)            # yuvasi
    t = frame / frames
    flick = math.sin(t * math.tau)
    height = 6 + flick * 1.5
    for i in range(int(height)):
        k = i / max(1.0, height)
        width = max(1.0, (1.0 - k) * 3.0 + 0.5)
        y = 9 - i
        step = 4 if k < 0.35 else (3 if k < 0.7 else 2)
        ramp = "gold" if k < 0.45 else "ember"
        c.disc(6 + flick * k * 1.6, y, width * 0.5, ramp, step,
               glow=int(230 - k * 90))
    c.shade()
    c.outline("ink", 0)
    return c.resolve()


def build_door(open_amount: float = 0.0, boss: bool = False) -> pygame.Surface:
    c = Canvas(20, 30)
    frame_ramp = "stone" if not boss else "violet"
    c.fill_rect(0, 0, 20, 30, frame_ramp, 1)
    c.rect(0, 0, 20, 30, frame_ramp, 3)
    inner_h = int(26 * (1.0 - open_amount))
    if inner_h > 0:
        c.fill_rect(3, 30 - inner_h - 1, 14, inner_h, "earth", 2)
        c.noise(42, 0.4, "earth")
        for x in (6, 10, 14):
            c.fill_rect(x, 30 - inner_h - 1, 1, inner_h, "earth", 1)
        c.disc(13, 30 - inner_h // 2, 1.5, "gold", 4)
    if boss:
        c.disc(10, 8, 3.0, "violet", 4, glow=200)
        c.disc(10, 8, 1.5, "ink", 1)
    c.shade()
    c.outline("ink", 0)
    return c.resolve()


def build_chest(open_state: bool = False) -> pygame.Surface:
    c = Canvas(16, 14)
    c.fill_rect(1, 6, 14, 7, "earth", 2)
    c.noise(11, 0.35, "earth")
    if open_state:
        c.fill_rect(1, 2, 14, 4, "earth", 1)
        c.fill_rect(3, 7, 10, 3, "gold", 4, glow=120)
    else:
        c.fill_rect(1, 4, 14, 3, "earth", 3)
        c.fill_rect(0, 5, 16, 1, "gold", 3)
    c.fill_rect(7, 7, 2, 3, "gold", 4)
    c.shade()
    c.outline("ink", 0)
    return c.resolve()


def build_shrine(active: bool = False, frame: int = 0) -> pygame.Surface:
    """Echo Shrine - kayit noktasi."""
    c = Canvas(20, 28)
    c.fill_rect(4, 20, 12, 7, "stone", 2)
    c.fill_rect(6, 8, 8, 13, "stone", 3)
    c.noise(23, 0.35, "stone")
    ramp = "azure" if active else "ink"
    step = 4 if active else 2
    glow = 200 if active else 0
    bob = math.sin(frame / 8 * math.tau) * 1.2 if active else 0.0
    c.disc(10, 6 + bob, 3.2, ramp, step, glow=glow)
    if active:
        c.disc(10, 6 + bob, 1.6, "bone", 4, glow=255)
        for i in range(6):
            a = i * math.tau / 6 + frame * 0.2
            c.px(int(10 + math.cos(a) * 6), int(10 + math.sin(a) * 4),
                 "azure", 4, glow=180)
    c.shade()
    c.outline("ink", 0)
    return c.resolve()


def build_spikes(size: int = TILE) -> pygame.Surface:
    c = Canvas(size, size)
    c.fill_rect(0, size - 4, size, 4, "stone", 2)
    spike_count = size // 4
    for i in range(spike_count):
        bx = i * 4 + 2
        c.taper(bx, size - 4, bx, size - 13, 3.4, 0.6, "bone", 4)
    c.shade()
    c.outline("ink", 0)
    return c.resolve()


def build_breakable(size: int = TILE) -> pygame.Surface:
    c = Canvas(size, size)
    c.ellipse(size / 2, size / 2 + 1, size * 0.4, size * 0.42, "earth", 3)
    c.noise(77, 0.45, "earth")
    c.fill_rect(int(size * 0.3), 2, int(size * 0.4), 2, "earth", 1)
    c.shade()
    c.outline("ink", 0)
    return c.resolve()


def build_ladder(size: int = TILE) -> pygame.Surface:
    c = Canvas(size, size)
    c.fill_rect(3, 0, 2, size, "earth", 3)
    c.fill_rect(size - 5, 0, 2, size, "earth", 2)
    for y in (2, 9):
        c.fill_rect(3, y, size - 6, 2, "earth", 4)
    c.shade()
    c.outline("ink", 0)
    return c.resolve()


# --- Toplanabilirler --------------------------------------------------------
def build_essence_orb(frame: int, frames: int = 8) -> pygame.Surface:
    c = Canvas(10, 10)
    t = frame / frames
    r = 2.6 + math.sin(t * math.tau) * 0.5
    c.disc(5, 5, r + 1.2, "azure", 2, glow=110)
    c.disc(5, 5, r, "azure", 4, glow=220)
    c.px(4, 4, "bone", 4, glow=255)
    return c.resolve()


def build_heart(full: bool = True) -> pygame.Surface:
    c = Canvas(12, 11)
    ramp = "blood" if full else "ink"
    step = 3 if full else 2
    c.disc(4, 4, 3.0, ramp, step)
    c.disc(8, 4, 3.0, ramp, step)
    c.polygon([(1, 5), (11, 5), (6, 10)], ramp, step)
    if full:
        c.px(3, 3, ramp, 4)
        c.px(4, 2, ramp, 4)
    c.outline("ink", 0)
    return c.resolve()


def build_potion(kind: str = "health") -> pygame.Surface:
    c = Canvas(10, 14)
    fluid = {"health": "blood", "essence": "azure", "power": "ember"}.get(kind, "blood")
    c.fill_rect(4, 1, 2, 3, "stone", 3)
    c.ellipse(5, 8, 3.6, 4.4, "bone", 2)
    c.ellipse(5, 9, 2.8, 3.2, fluid, 3, glow=90)
    c.px(3, 7, "bone", 4)
    c.shade()
    c.outline("ink", 0)
    return c.resolve()


# --- Efektler ---------------------------------------------------------------
def build_slash(frame: int, frames: int = 4, radius: float = 20.0,
                arc: float = 2.2, ramp: str = "bone") -> pygame.Surface:
    """Kilic izi. Kare ilerledikce yay incelir ve disari acilir.

    Vurus geri bildiriminin en onemli parcasi: oyuncu kilici degil, izi gorur.
    """
    size = int(radius * 2 + 8)
    c = Canvas(size, size)
    cx = cy = size / 2
    t = (frame + 1) / frames
    r = radius * (0.55 + t * 0.5)
    thickness = max(1.0, 3.4 * (1.0 - t * 0.7))
    span = arc * (0.5 + t * 0.5)
    steps = 26
    for i in range(steps + 1):
        k = i / steps
        a = -span / 2 + span * k
        # Yayin ortasi kalin, uclari ince: hiz hissi
        w = thickness * math.sin(k * math.pi) ** 0.6
        if w < 0.4:
            continue
        px = cx + math.cos(a) * r
        py = cy + math.sin(a) * r
        step = 4 if k > 0.25 and k < 0.75 else 3
        c.disc(px, py, w * 0.5, ramp, step, glow=int(150 * (1.0 - t)))
    return c.resolve(alpha=int(255 * (1.0 - t * 0.55)))


def build_impact(frame: int, frames: int = 4, ramp: str = "gold") -> pygame.Surface:
    """Carpma yildizi: merkezden disa firlayan isinlar."""
    size = 24
    c = Canvas(size, size)
    cx = cy = size / 2
    t = (frame + 1) / frames
    for i in range(6):
        a = i * math.tau / 6 + t * 0.4
        inner = 2.0 + t * 4.0
        outer = inner + 5.0 * (1.0 - t * 0.5)
        c.line(cx + math.cos(a) * inner, cy + math.sin(a) * inner,
               cx + math.cos(a) * outer, cy + math.sin(a) * outer,
               max(1.0, 2.6 * (1.0 - t)), ramp, 4, glow=int(200 * (1.0 - t)))
    if t < 0.5:
        c.disc(cx, cy, 3.0 * (1.0 - t * 2), "bone", 4, glow=255)
    return c.resolve(alpha=int(255 * (1.0 - t * 0.6)))


def build_dust(frame: int, frames: int = 5) -> pygame.Surface:
    """Toz bulutu: kosarken, inerken, dash atarken."""
    size = 16
    c = Canvas(size, size)
    t = (frame + 1) / frames
    rng = np.random.default_rng(frame * 17 + 3)
    for _ in range(5):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 5) + t * 5
        r = max(0.5, (2.2 - t * 1.6) * rng.uniform(0.6, 1.2))
        c.disc(size / 2 + math.cos(a) * d, size / 2 + math.sin(a) * d * 0.5,
               r, "ash", 3)
    return c.resolve(alpha=int(200 * (1.0 - t)))


def build_ring(frame: int, frames: int = 6, ramp: str = "violet",
               max_radius: float = 22.0) -> pygame.Surface:
    """Genisleyen halka: buyu, boss faz gecisi, patlama."""
    size = int(max_radius * 2 + 6)
    c = Canvas(size, size)
    cx = cy = size / 2
    t = (frame + 1) / frames
    r = max_radius * t
    thickness = max(1.0, 3.0 * (1.0 - t))
    steps = max(12, int(r * 4))
    for i in range(steps):
        a = i * math.tau / steps
        c.disc(cx + math.cos(a) * r, cy + math.sin(a) * r, thickness * 0.5,
               ramp, 4, glow=int(220 * (1.0 - t)))
    return c.resolve(alpha=int(255 * (1.0 - t)))


def build_projectile(kind: str = "arrow", angle_steps: int = 8) -> list[pygame.Surface]:
    """Mermi sprite'lari, aci basamaklarina gore onceden dondurulmus."""
    frames: list[pygame.Surface] = []
    for i in range(angle_steps):
        angle = i * math.tau / angle_steps
        c = Canvas(16, 16)
        cx = cy = 8
        if kind == "arrow":
            tx, ty = cx + math.cos(angle) * 6, cy + math.sin(angle) * 6
            bx, by = cx - math.cos(angle) * 6, cy - math.sin(angle) * 6
            c.line(bx, by, tx, ty, 1.6, "earth", 2)
            c.taper(cx + math.cos(angle) * 3, cy + math.sin(angle) * 3, tx, ty,
                    2.4, 0.6, "bone", 4)
        elif kind == "bone":
            c.line(cx - 4, cy, cx + 4, cy, 2.0, "bone", 3)
            c.disc(cx - 4, cy, 1.8, "bone", 4)
            c.disc(cx + 4, cy, 1.8, "bone", 4)
        elif kind == "ember":
            c.disc(cx, cy, 3.0, "ember", 2, glow=140)
            c.disc(cx, cy, 2.0, "ember", 4, glow=220)
            c.disc(cx - math.cos(angle) * 3, cy - math.sin(angle) * 3, 1.2,
                   "gold", 4, glow=160)
        elif kind == "hex":
            c.disc(cx, cy, 3.4, "violet", 2, glow=160)
            c.disc(cx, cy, 2.0, "violet", 4, glow=230)
        else:
            c.disc(cx, cy, 2.4, "bone", 4)
        if kind in ("arrow", "bone"):
            c.shade()
            c.outline("ink", 0)
        frames.append(c.resolve())
    return frames
