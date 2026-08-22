"""Zindan tas dokusu - Görev 9.

`world/tilemap.py` şimdiye kadar düz renk dolgu çiziyordu (yorum satırı
zaten "Görev 9'da gerçek tileset gelince değişecek" diyordu). Burada aynı
felsefe: karakter sprite'ları gibi **kod ile üretilir**, elle çizilmiş PNG
yok. `forge.Canvas` aynı indeks tabanlı çizim aracı - palet tek kaynak,
sol-üst ışık otomatik (`shade()`), determinizm `noise()`'un seed'i sayesinde
(kamera geri dönünce aynı taş aynı yerde, `cave_backdrop.py` ile aynı ders).

## Neden autotile değil "kenar farkı"

Tam bir 47-karo blob-autotile bu oyunun ihtiyacı değil: odalar dikdörtgen
bloklar halinde tasarlanıyor (ASCII), köşe/iç köşe karmaşası yok. Asıl
okunurlük sorunu **üst kenar** - oyuncunun bastığı, gördüğü yüzey
(`docs/asset-plani.md` 4: "platform kenar şeridini güçlendir"). O yüzden
her duvar/platform karosu iki halde üretiliyor: üstü açık (basılabilir
yüzey - vurgulu kenar) ve üstü kapalı (iç blok - düz doku).

## Onbellekleme

Her (tür, varyant, üst-açık-mı) kombinasyonu **bir kez** üretilip
saklanır - `CLAUDE.md`'nin "sprite'lar bir kez üretilir" kuralı burada da
geçerli, aksi halde 200+ karo her kare yeniden çizilirdi.
"""
from __future__ import annotations

import pygame

from src.art.forge import Canvas
from src.config import TILE_SIZE

WALL_VARIANTS = 4          # "Tekduzelik kirilsin" (docs/asset-plani.md 4)
PLATFORM_VARIANTS = 2

_ROW_HEIGHT = 4            # Tugla sirasi yuksekligi


def _brick_wall(variant: int, lit_top: bool) -> pygame.Surface:
    """Kosma (running-bond) tugla dokusu - harc cizgileri sira sira kayar."""
    c = Canvas(TILE_SIZE, TILE_SIZE)
    c.fill_rect(0, 0, TILE_SIZE, TILE_SIZE, "stone", 1)

    rows = TILE_SIZE // _ROW_HEIGHT
    for row in range(rows):
        y = row * _ROW_HEIGHT
        c.fill_rect(0, y, TILE_SIZE, 1, "stone", 0)          # yatay harc
        # Her varyant + her ikinci sira farkli bir kaymayla basliyor -
        # ayni blok yan yana durunca goz "kopyala-yapistir" fark etmesin.
        shift = (variant * 5 + (0 if row % 2 == 0 else _ROW_HEIGHT + 3)) \
            % (TILE_SIZE // 2)
        x = shift - TILE_SIZE
        step_x = 6 + ((variant + row) % 3)
        while x < TILE_SIZE:
            c.fill_rect(x, y, 1, _ROW_HEIGHT, "stone", 0)    # dikey harc
            x += step_x

    c.noise(seed=4200 + variant, amount=0.30, chain="stone")

    if lit_top:
        # Basilabilir yuzey: gucclu bir vurgu seridi (asset-plani.md 4 -
        # "platform kenar seridini guclendir").
        c.fill_rect(0, 0, TILE_SIZE, 1, "stone", 3)
        c.fill_rect(0, 1, TILE_SIZE, 1, "stone", 2)

    c.shade()
    c.resolve_alpha = None  # (dokumantasyon amacli; kullanilmiyor)
    return c.resolve()


def _platform(variant: int) -> pygame.Surface:
    """Ahsap kiris - tek yonlu platform, ince (yalnizca ust seride cizilir)."""
    c = Canvas(TILE_SIZE, 6)
    c.fill_rect(0, 0, TILE_SIZE, 6, "earth", 1)
    c.fill_rect(0, 0, TILE_SIZE, 1, "earth", 3)              # ust vurgu
    # Tahta damari: birkac yatay cizik.
    for i, x in enumerate(range(1, TILE_SIZE, 5)):
        step = 0 if (i + variant) % 2 == 0 else 2
        c.fill_rect(x, 2 + (i % 2), 3, 1, "earth", step)
    c.noise(seed=5100 + variant, amount=0.25, chain="earth")
    c.shade()
    return c.resolve()


def _spike() -> pygame.Surface:
    """Diken siresi - ucgen dislere shade() ile hacim."""
    c = Canvas(TILE_SIZE, TILE_SIZE)
    c.fill_rect(0, TILE_SIZE - 4, TILE_SIZE, 4, "stone", 0)
    for i in range(0, TILE_SIZE, 4):
        c.polygon([
            (i, TILE_SIZE - 4), (i + 2, 3), (i + 4, TILE_SIZE - 4),
        ], "danger", 2)
    c.shade()
    return c.resolve()


class TileSet:
    """Uretilen karo yuzeylerinin onbellegi. Bir kez kurulur, hep okunur."""

    def __init__(self) -> None:
        self._cache: dict[tuple, pygame.Surface] = {}

    def wall(self, tx: int, ty: int, lit_top: bool) -> pygame.Surface:
        variant = (tx * 7 + ty * 13) % WALL_VARIANTS
        key = ("wall", variant, lit_top)
        surface = self._cache.get(key)
        if surface is None:
            surface = _brick_wall(variant, lit_top)
            self._cache[key] = surface
        return surface

    def platform(self, tx: int, ty: int) -> pygame.Surface:
        variant = (tx * 11 + ty * 5) % PLATFORM_VARIANTS
        key = ("platform", variant)
        surface = self._cache.get(key)
        if surface is None:
            surface = _platform(variant)
            self._cache[key] = surface
        return surface

    def spike(self) -> pygame.Surface:
        key = ("spike",)
        surface = self._cache.get(key)
        if surface is None:
            surface = _spike()
            self._cache[key] = surface
        return surface


# Tek paylasilan orneği - butun TileMap'ler ayni dokuyu kullaniyor (henuz
# tema farklilasmasi yok; ileride `TileSet(theme=...)` olarak genisler).
_SHARED = TileSet()


def shared() -> TileSet:
    return _SHARED
