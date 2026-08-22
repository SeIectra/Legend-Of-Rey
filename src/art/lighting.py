"""Bolum 3'un karanlik/isik katmani.

`docs/bolum-03.md` "Uygulama Notlari" bunu tarif ediyor ama kod tabaninda
hic karsiligi yoktu: **tek bir karartma yuzeyinde toplanan isik maskesi**,
her kaynak `BLEND_RGBA_SUB` ile ayni yuzeye islenir - kaynak basina ayri
gecis yok. `PlayScene.draw_foreground()` kancasindan cagrilir (aktorlerden
sonra, HUD'dan once): dunya karariyor ama arayuz her zaman tam parlaklikta
okunur.

Karanlik ≠ siyah: paletin en koyu rengi kullanilir (zaten sogukca), ve tam
opak degil - `DARKNESS_SILHOUETTE_ALPHA` kadar siluetler karanlikta bile
hafifce sizar (oyuncu tamamen kor olmasin).

`radial_glow` (art/glow.py) ile karistirilmasin: o RGB'yi **ekliyordu**
(BLEND_RGB_ADD, isik halesi ustuste bindirme). Burasi tam tersi - alfayi
**siliyor** (BLEND_RGBA_SUB, karanligi deliyor).
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pygame

from src.art import palette
from src.config import DARKNESS_SILHOUETTE_ALPHA
from src.systems.light import LightState

_DARK_NAME = palette.darkest_names(1)[0]


@lru_cache(maxsize=32)
def _hole(radius: int) -> pygame.Surface:
    """Merkezde tam delik (alfa 0), kenarda tam karanlik (alfa 255).

    Yaricap kucuk bir tam sayi kumesinden geldigi icin (mesale/Mor Alev/
    mangal - hepsi sabit birkac deger) `lru_cache` her kareyi yeniden
    hesaplamayi onluyor.
    """
    radius = max(1, radius)
    size = radius * 2
    yy, xx = np.ogrid[:size, :size]
    distance = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    falloff = np.clip(1.0 - distance, 0.0, 1.0) ** 2

    hole = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.surfarray.pixels_alpha(hole)[:, :] = (falloff * 255).astype(np.uint8)
    return hole


def render(surface: pygame.Surface, offset: tuple[int, int],
           light: LightState) -> None:
    """Karanlik maskesini olusturup `surface` uzerine isler.

    **Sadece Chapter03Scene bunu cagirir** - Bolum 1/2 hic cagirmadigi
    icin o sahnelerde maliyeti yok. Kaynak listesi bossa bile maske
    tam kuvvetle cizilir: mesalesi/Mor Alevi olmayan bir oyuncu icin
    "hicbir isik yok" **tam karanlik** demektir, "aydinlik say" degil -
    ilk halde kaynak yoksa hic cizmiyordu ve mesalesini dusuren oyuncu
    yanlislikla normal aydinlikta kaliyordu.
    """
    ox, oy = offset
    width, height = surface.get_size()
    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    dark_alpha = int(255 * (1.0 - DARKNESS_SILHOUETTE_ALPHA))
    mask.fill((*palette.color(_DARK_NAME), dark_alpha))

    for source in light.all_sources():
        radius = int(source.radius)
        if radius <= 0:
            continue
        hole = _hole(radius)
        mask.blit(hole, (int(source.x - ox - radius), int(source.y - oy - radius)),
                  special_flags=pygame.BLEND_RGBA_SUB)

    surface.blit(mask, (0, 0))
