"""Tile haritasi: veri, carpisma sorgulari, cizim.

16x16 tile. Harita ASCII satirlardan kurulur - bir bolumu duz metin olarak
gormek tasarim hatalarini daha yazarken yakalatir.

Carpisma dogrudan diziden okunur: tile'lar nesne degil, sayidir. Bir
dikdortgenin dokundugu tile araligi hesaplanip yalnizca o araliga bakilir.

Tek yonlu platformlar (`=`) yalnizca **asagi dogru hareket ederken** ve ayak
platformun ustundeyken katidir. Kural fizik katmaninda uygulanir.

Gorev 4'te 9-slice ve oda gecisleriyle genisleyecek; su an dovus testinin
ihtiyaci kadar.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import TILE_DRAW_MARGIN, TILE_SIZE

EMPTY = 0
SOLID = 1
PLATFORM = 2
SPIKE = 3
# Kirilabilir duvar: kati gibi davranir ama vurulunca yok olur. Yanki
# olmadan **normal duvardan ayirt edilemez** - gizli gecidin tamami bu
# ayirt edilemezlik uzerine kurulu (docs/gdd.md 4).
BREAKABLE = 4

SOLID_TILES = frozenset({SOLID, BREAKABLE})
HAZARD_TILES = frozenset({SPIKE})

LEGEND: dict[str, int] = {
    ".": EMPTY, " ": EMPTY,
    "#": SOLID,
    "=": PLATFORM,
    "^": SPIKE,
    "B": BREAKABLE,
}

# Placeholder cizim renkleri. Gorev 9'da gercek tileset gelince degisecek.
TILE_COLORS: dict[int, str] = {
    # Kirilabilir duvar normal duvarla **ayni renkte** cizilir. Farkli
    # cizilseydi Yanki'nin isi kalmazdi: oyuncu gizli gecidi zaten gorurdu.
    BREAKABLE: "stone_dark",
    SOLID: "stone_dark",
    PLATFORM: "earth",
    SPIKE: "danger",
}
TILE_TOP_COLORS: dict[int, str] = {
    BREAKABLE: "stone",
    SOLID: "stone",
    PLATFORM: "earth",
}


class TileMap:
    def __init__(self, rows: list[str]) -> None:
        self.height = len(rows)
        self.width = max((len(r) for r in rows), default=0)
        self.tiles: list[list[int]] = [
            [LEGEND.get(char, EMPTY) for char in row.ljust(self.width, ".")]
            for row in rows
        ]

    # --- Sorgular -----------------------------------------------------------
    @property
    def pixel_width(self) -> int:
        return self.width * TILE_SIZE

    @property
    def pixel_height(self) -> int:
        return self.height * TILE_SIZE

    @property
    def bounds(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.pixel_width, self.pixel_height)

    def at(self, tx: int, ty: int) -> int:
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.tiles[ty][tx]
        # Harita disi: yanlar kati (oyuncu bolumden cikamaz), tepe ve taban
        # bos (bosluga dusen gercekten duser, gorunmez zeminde durmaz).
        if ty < 0 or ty >= self.height:
            return EMPTY
        return SOLID

    def is_solid(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) in SOLID_TILES

    def is_breakable(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) == BREAKABLE

    def break_at(self, tx: int, ty: int) -> bool:
        """Kirilabilir duvari yikar. Yikildiysa True."""
        if not self.is_breakable(tx, ty):
            return False
        row = self.tiles[ty]
        row[tx] = EMPTY
        return True

    def breakable_rects(self) -> list[pygame.Rect]:
        """Kalan kirilabilir duvarlarin dikdortgenleri.

        Yanki bunlari parlatiyor. Liste kucuk - bir odada en fazla birkac
        tane - o yuzden her karede yeniden uretmek sorun degil.
        """
        found: list[pygame.Rect] = []
        for ty, row in enumerate(self.tiles):
            for tx, value in enumerate(row):
                if value == BREAKABLE:
                    found.append(pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE,
                                             TILE_SIZE, TILE_SIZE))
        return found

    def is_platform(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) == PLATFORM

    def is_hazard(self, tx: int, ty: int) -> bool:
        return self.at(tx, ty) in HAZARD_TILES

    def tile_range(self, rect: pygame.Rect) -> tuple[int, int, int, int]:
        return (rect.left // TILE_SIZE, rect.top // TILE_SIZE,
                (rect.right - 1) // TILE_SIZE, (rect.bottom - 1) // TILE_SIZE)

    def solid_overlap(self, rect: pygame.Rect) -> bool:
        x0, y0, x1, y1 = self.tile_range(rect)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.is_solid(tx, ty):
                    return True
        return False

    def platform_top_overlap(self, rect: pygame.Rect,
                             previous_bottom: float) -> bool:
        """Tek yonlu platforma **ustunden** iniliyor mu?

        Ayak onceki karede platformun ustundeyse kati sayilir; asagidan
        ziplayan oyuncu icin gecirgen kalir.
        """
        x0, _, x1, y1 = self.tile_range(rect)
        for tx in range(x0, x1 + 1):
            if not self.is_platform(tx, y1):
                continue
            top = y1 * TILE_SIZE
            if previous_bottom <= top + 1 <= rect.bottom:
                return True
        return False

    def hazard_rects(self, rect: pygame.Rect) -> list[pygame.Rect]:
        found: list[pygame.Rect] = []
        x0, y0, x1, y1 = self.tile_range(rect)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.is_hazard(tx, ty):
                    # Diken hitbox'i tile'dan kucuk - tepesine degmeden olmek
                    # oyuncuyu haksiz yere cezalandirir.
                    found.append(pygame.Rect(tx * TILE_SIZE + 2,
                                             ty * TILE_SIZE + 6,
                                             TILE_SIZE - 4, TILE_SIZE - 6))
        return found

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        """Yalnizca gorunur tile'lari cizer (kamera alani + marj)."""
        ox, oy = offset
        view = pygame.Rect(ox, oy, surface.get_width(), surface.get_height())
        margin = TILE_DRAW_MARGIN
        x0 = max(0, view.left // TILE_SIZE - margin)
        y0 = max(0, view.top // TILE_SIZE - margin)
        x1 = min(self.width - 1, view.right // TILE_SIZE + margin)
        y1 = min(self.height - 1, view.bottom // TILE_SIZE + margin)

        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                value = self.tiles[ty][tx]
                if value == EMPTY:
                    continue
                x = tx * TILE_SIZE - ox
                y = ty * TILE_SIZE - oy
                self._draw_tile(surface, value, tx, ty, x, y)

    def _draw_tile(self, surface: pygame.Surface, value: int, tx: int, ty: int,
                   x: int, y: int) -> None:
        if value == SPIKE:
            surface.fill(palette.color("stone_dark"),
                         (x, y + TILE_SIZE - 4, TILE_SIZE, 4))
            for i in range(0, TILE_SIZE, 4):
                pygame.draw.polygon(surface, palette.color(TILE_COLORS[SPIKE]), [
                    (x + i, y + TILE_SIZE - 4),
                    (x + i + 2, y + 4),
                    (x + i + 4, y + TILE_SIZE - 4)])
            return

        height = TILE_SIZE if value == SOLID else 5
        surface.fill(palette.color(TILE_COLORS[value]), (x, y, TILE_SIZE, height))
        # Ust kenar seridi: platform okunurlugu icin kritik (asset-plani.md 4).
        if not self.is_solid(tx, ty - 1):
            surface.fill(palette.color(TILE_TOP_COLORS[value]),
                         (x, y, TILE_SIZE, 2))
            surface.fill(palette.color("stone_light"), (x, y, TILE_SIZE, 1))

    def draw_debug(self, surface: pygame.Surface,
                   offset: tuple[int, int]) -> None:
        ox, oy = offset
        colors = {SOLID: "echo_bright", PLATFORM: "gold", SPIKE: "danger_bright"}
        for ty in range(self.height):
            for tx in range(self.width):
                value = self.tiles[ty][tx]
                if value == EMPTY:
                    continue
                pygame.draw.rect(
                    surface, palette.color(colors.get(value, "bone")),
                    (tx * TILE_SIZE - ox, ty * TILE_SIZE - oy,
                     TILE_SIZE, TILE_SIZE), 1)
