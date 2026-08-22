"""Ozel fare imleci - Command & Conquer tarzi altin ok.

Arda'nin istegi: C&C'deki gibi bir custom cursor. Isletim sisteminin
varsayilan oku bu oyunun piksel-art diline uymuyor - kendi imlecimizi
kod ile uretip (CLAUDE.md 6: sprite'lar koddan gelir, elle cizilmis PNG
yok) ic cozunurlukte (480x270) ciziyoruz ki geri kalan her sey gibi tam
sayida buyusun, bulanmasin.

Neden altin: palette'in "brass" zinciri (ember_dark -> gold) zaten oyun
boyunca "onemli/degerli" seyler icin kullaniliyor (altin, parlak vurgular)
- C&C'nin ikonik altin/sari imleciyle ayni ruh, ayni palet.

Gorunurluk kurali oyunun geri kalaniyla ayni: fare hareket edince gorunur,
klavye/gamepad kullanilinca kaybolur (`InputManager.last_device`) - bu
zaten merkezi bir durum, ayrica bir "mouse_visible" bayragi gerekmiyor.
"""
from __future__ import annotations

import pygame

from src.art.forge import Canvas

# Klasik ok ucu: sol-ust kose sivri, govde asagi-saga uzanir. Hotspot
# (tiklama noktasi) tam (0, 0) - okun sivri ucu.
_POINTS: tuple[tuple[int, int], ...] = (
    (0, 0), (0, 12), (3, 9), (5, 14), (7, 13), (5, 8), (9, 8),
)
_WIDTH = 10
_HEIGHT = 15

_cached: pygame.Surface | None = None


def _build() -> pygame.Surface:
    canvas = Canvas(_WIDTH, _HEIGHT)
    canvas.polygon(list(_POINTS), "brass", 2)
    canvas.shade()
    canvas.outline("shadow", 1)
    return canvas.resolve()


def sprite() -> pygame.Surface:
    """Imlec yuzeyi - bir kez uretilir, sonra onbellekten okunur."""
    global _cached
    if _cached is None:
        _cached = _build()
    return _cached


def draw(surface: pygame.Surface, position: tuple[float, float]) -> None:
    """Imleci verilen ic-cozunurluk konumuna ciz - hotspot sol-ust kose."""
    x, y = position
    surface.blit(sprite(), (int(x), int(y)))
