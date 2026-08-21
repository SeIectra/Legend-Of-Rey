"""Tilemap: veri, carpisma sorgulari ve parcali (chunk) on-cizim.

Iki tasarim karari performansi belirliyor:

1. **Chunk on-cizimi.** Harita 16x16'lik parcalara bolunur ve her parca bir kez
   Surface'e cizilir. Kare basina birkac yuz tile blit etmek yerine birkac
   parca blit ediyoruz. 200x60'lik bir seviye bile bedava geliyor.

2. **Carpisma dogrudan diziden okunur.** Tile'lar nesne degil, numpy
   dizisindeki sayilardir. Bir dikdortgenin cakistigi tile araligini
   hesaplayip sadece o araliga bakariz - tum haritayi taramayiz.

Tek yonlu platformlar ozel: sadece asagi dogru hareket ederken ve oyuncunun
ayagi platformun ustundeyken katidir. Bu kural fizik katmaninda uygulanir,
burada yalnizca isaretlenir.
"""
from __future__ import annotations

import numpy as np
import pygame

from lore.constants import CHUNK, TILE
from lore.gfx.tiles import (
    build_breakable, build_ladder, build_spikes, build_tileset,
)

# --- Tile turleri -----------------------------------------------------------
EMPTY = 0
SOLID = 1
PLATFORM = 2
BACKDROP = 3
SPIKE = 4
LADDER = 5
WATER = 6
BREAKABLE = 7

SOLID_TYPES = frozenset({SOLID, BREAKABLE})
HAZARD_TYPES = frozenset({SPIKE})

# ASCII seviye formatinin sozlugu. Seviyeleri elle yazilabilir tutmak,
# icerik uretim hizini her seyden fazla etkiliyor.
LEGEND: dict[str, int] = {
    ".": EMPTY, " ": EMPTY,
    "#": SOLID, "X": SOLID,
    "=": PLATFORM, "-": PLATFORM,
    "b": BACKDROP, ",": BACKDROP,
    "^": SPIKE,
    "H": LADDER,
    "~": WATER,
    "o": BREAKABLE,
}


class TileMap:
    def __init__(self, width: int, height: int, theme: str = "hollow") -> None:
        self.w = width
        self.h = height
        self.theme = theme
        self.tiles = np.zeros((height, width), dtype=np.uint8)
        self.tileset = build_tileset(theme)
        # Tekil dekor tile'lari bir kez uretilir; her parca yeniden cizerken
        # bunlari tekrar uretmek chunk maliyetini gereksiz yere katliyordu.
        self._decor = {
            "spike": build_spikes(),
            "ladder": build_ladder(),
            "breakable": build_breakable(),
            "water": self._make_water(),
        }

        self._chunks: dict[tuple[int, int], pygame.Surface] = {}
        self._chunks_w = (width + CHUNK - 1) // CHUNK
        self._chunks_h = (height + CHUNK - 1) // CHUNK

    @staticmethod
    def _make_water() -> pygame.Surface:
        """Yari saydam su yuzeyi; ustunde bir tik acik bir cizgi."""
        water = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        water.fill((34, 92, 142, 110))
        water.fill((62, 140, 190, 150), (0, 0, TILE, 2))
        return water

    # --- Kurulum ------------------------------------------------------------
    @classmethod
    def from_ascii(cls, rows: list[str], theme: str = "hollow") -> "TileMap":
        height = len(rows)
        width = max((len(r) for r in rows), default=0)
        tm = cls(width, height, theme)
        for y, row in enumerate(rows):
            for x, char in enumerate(row):
                tm.tiles[y, x] = LEGEND.get(char, EMPTY)
        return tm

    def to_ascii(self) -> list[str]:
        reverse = {}
        for char, value in LEGEND.items():
            reverse.setdefault(value, char)
        return ["".join(reverse.get(int(v), ".") for v in row) for row in self.tiles]

    # --- Sorgular -----------------------------------------------------------
    @property
    def pixel_width(self) -> int:
        return self.w * TILE

    @property
    def pixel_height(self) -> int:
        return self.h * TILE

    @property
    def bounds(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.pixel_width, self.pixel_height)

    def at(self, tx: int, ty: int) -> int:
        if 0 <= tx < self.w and 0 <= ty < self.h:
            return int(self.tiles[ty, tx])
        # Harita disi kurallari:
        #   yanlar  -> kati  (oyuncu bolumun disina yuruyemez)
        #   tepe    -> bos   (yuksek ziplama tavana carpmasin)
        #   taban   -> bos   (bosluga dusen gercekten duser; gorunmez bir
        #                     zeminde durup kalmak hem cirkin hem kafa karistirici)
        if ty < 0 or ty >= self.h:
            return EMPTY
        return SOLID

    def set(self, tx: int, ty: int, value: int) -> None:
        if 0 <= tx < self.w and 0 <= ty < self.h:
            self.tiles[ty, tx] = value
            self._invalidate_chunk(tx // CHUNK, ty // CHUNK)

    def is_solid(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) in SOLID_TYPES

    def is_platform(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) == PLATFORM

    def is_hazard(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) in HAZARD_TYPES

    def is_ladder(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) == LADDER

    def solid_at_pixel(self, x: float, y: float) -> bool:
        return self.is_solid(int(x // TILE), int(y // TILE))

    def tile_range(self, rect: pygame.Rect) -> tuple[int, int, int, int]:
        """Bir dikdortgenin dokundugu tile araligi (x0, y0, x1, y1) - kapsayici."""
        return (
            rect.left // TILE,
            rect.top // TILE,
            (rect.right - 1) // TILE,
            (rect.bottom - 1) // TILE,
        )

    def overlaps_solid(self, rect: pygame.Rect) -> bool:
        x0, y0, x1, y1 = self.tile_range(rect)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.is_solid(tx, ty):
                    return True
        return False

    def solid_rects(self, rect: pygame.Rect) -> list[pygame.Rect]:
        """Dikdortgenle kesisen kati tile'larin dikdortgenleri."""
        out: list[pygame.Rect] = []
        x0, y0, x1, y1 = self.tile_range(rect)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.is_solid(tx, ty):
                    out.append(pygame.Rect(tx * TILE, ty * TILE, TILE, TILE))
        return out

    def hazard_rects(self, rect: pygame.Rect) -> list[pygame.Rect]:
        out: list[pygame.Rect] = []
        x0, y0, x1, y1 = self.tile_range(rect)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.is_hazard(tx, ty):
                    # Diken hitbox'i tile'dan kucuk: tepesine degmeden olmek
                    # oyuncuyu hakli olarak sinirlendirir.
                    out.append(pygame.Rect(tx * TILE + 2, ty * TILE + 6,
                                           TILE - 4, TILE - 6))
        return out

    def ground_below(self, tx: int, ty: int, limit: int = 40) -> int | None:
        """Verilen tile'in altindaki ilk zemin. Dusman kenar algilamasi icin."""
        for step in range(1, limit):
            probe = ty + step
            if probe >= self.h:
                return None
            if self.is_solid(tx, probe) or self.is_platform(tx, probe):
                return probe
        return None

    # --- Autotile -----------------------------------------------------------
    def _mask_at(self, tx: int, ty: int) -> int:
        """Komsu maskesi: dolu komsular bit olarak isaretlenir."""
        mask = 0
        if self.is_solid(tx, ty - 1):
            mask |= 1        # N
        if self.is_solid(tx + 1, ty):
            mask |= 2        # E
        if self.is_solid(tx, ty + 1):
            mask |= 4        # S
        if self.is_solid(tx - 1, ty):
            mask |= 8        # W
        return mask

    @staticmethod
    def _variant(tx: int, ty: int) -> int:
        """Konuma bagli sahte-rastgele varyant.

        Rastgele sayi uretici kullanmiyoruz: ayni tile her cizimde ayni
        varyanti almali, yoksa chunk yeniden cizildiginde doku degisir.
        """
        return (tx * 73856093 ^ ty * 19349663) % 4

    # --- Cizim --------------------------------------------------------------
    def _invalidate_chunk(self, cx: int, cy: int) -> None:
        self._chunks.pop((cx, cy), None)

    def invalidate_all(self) -> None:
        self._chunks.clear()

    def _build_chunk(self, cx: int, cy: int) -> pygame.Surface:
        surface = pygame.Surface((CHUNK * TILE, CHUNK * TILE), pygame.SRCALPHA)
        solid_set = self.tileset["solid"]
        platforms = self.tileset["platform"]
        backdrops = self.tileset["backdrop"]

        spike_img = self._decor["spike"]
        ladder_img = self._decor["ladder"]
        breakable_img = self._decor["breakable"]

        for ly in range(CHUNK):
            ty = cy * CHUNK + ly
            if ty >= self.h:
                break
            for lx in range(CHUNK):
                tx = cx * CHUNK + lx
                if tx >= self.w:
                    break
                value = int(self.tiles[ty, tx])
                if value == EMPTY:
                    continue
                px, py = lx * TILE, ly * TILE
                variant = self._variant(tx, ty)
                if value == SOLID:
                    surface.blit(solid_set[self._mask_at(tx, ty)][variant], (px, py))
                elif value == PLATFORM:
                    surface.blit(platforms[variant], (px, py))
                elif value == BACKDROP:
                    surface.blit(backdrops[variant], (px, py))
                elif value == SPIKE:
                    surface.blit(spike_img, (px, py))
                elif value == LADDER:
                    surface.blit(ladder_img, (px, py))
                elif value == BREAKABLE:
                    surface.blit(breakable_img, (px, py))
                elif value == WATER:
                    surface.blit(self._decor["water"], (px, py))
        return surface

    def draw(self, surface: pygame.Surface, camera) -> None:
        """Yalnizca gorunur parcalari cizer."""
        ox, oy = camera.offset
        view = camera.view_rect
        cx0 = max(0, view.left // (CHUNK * TILE))
        cy0 = max(0, view.top // (CHUNK * TILE))
        cx1 = min(self._chunks_w - 1, view.right // (CHUNK * TILE))
        cy1 = min(self._chunks_h - 1, view.bottom // (CHUNK * TILE))

        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                chunk = self._chunks.get((cx, cy))
                if chunk is None:
                    chunk = self._build_chunk(cx, cy)
                    self._chunks[(cx, cy)] = chunk
                surface.blit(chunk, (cx * CHUNK * TILE - ox, cy * CHUNK * TILE - oy))

    def draw_debug(self, surface: pygame.Surface, camera) -> None:
        """Carpisma kutularini cizer (F3)."""
        ox, oy = camera.offset
        view = camera.view_rect
        x0, y0, x1, y1 = self.tile_range(view)
        for ty in range(max(0, y0), min(self.h, y1 + 1)):
            for tx in range(max(0, x0), min(self.w, x1 + 1)):
                value = int(self.tiles[ty, tx])
                if value == EMPTY or value == BACKDROP:
                    continue
                color = {
                    SOLID: (90, 200, 120), PLATFORM: (240, 200, 90),
                    SPIKE: (240, 90, 90), LADDER: (140, 160, 240),
                    WATER: (90, 180, 240), BREAKABLE: (200, 140, 90),
                }.get(value, (255, 255, 255))
                pygame.draw.rect(
                    surface, color,
                    (tx * TILE - ox, ty * TILE - oy, TILE, TILE), 1)
