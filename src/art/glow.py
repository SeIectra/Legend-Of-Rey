"""Isik yardimcilari - hale ve kenar isigi.

Menuden ayri tutuldu: ikisi de genel amacli. Mesale odalari, Yanki
vinyeti ve mor alev sahnesi ayni fonksiyonlari kullanacak.

**Eklemeli harmanlamada siddet renkle ayarlanir, alfayla degil.**
`BLEND_RGB_ADD` alfayi agirlik olarak kullanmaz; RGB'yi oldugu gibi ekler.
Dusuk alfa hicbir sey yapmaz ve hale opak bir diske doner. Bu projede
ayni hata iki kez yapildi, ucuncusu olmasin.
"""
from __future__ import annotations

import numpy as np
import pygame

from src.art import palette


def radial_glow(radius: int, colour: palette.RGB,
                peak: float = 0.55) -> pygame.Surface:
    """Merkezde parlak, kenarda sifir - eklemeli isik halesi.

    **Alfa ile siddet ayarlanmaz.** `BLEND_RGB_ADD` alfayi agirlik olarak
    kullanmaz, RGB'yi oldugu gibi ekler; dusuk alfa hicbir sey yapmaz ve
    hale opak bir diske doner. Siddeti **renklerin kendisini olcekleyerek**
    veriyoruz (CLAUDE.md 9, DEVIR.md 10 - ayni ders bir kez daha).

    `peak` merkezdeki carpan: 1.0 rengin tamami, 0.5 yarisi.
    """
    size = radius * 2
    yy, xx = np.ogrid[:size, :size]
    distance = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / max(1, radius)
    # Kenarda sifirlanan yumusak dususu: (1 - d)^2
    falloff = np.clip(1.0 - distance, 0.0, 1.0) ** 2 * peak

    rgb = np.zeros((size, size, 3), dtype=np.float32)
    for channel in range(3):
        rgb[:, :, channel] = colour[channel] * falloff

    glow = pygame.Surface((size, size))
    pygame.surfarray.blit_array(glow, rgb.transpose(1, 0, 2).astype(np.uint8))
    return glow.convert()


def rim_light(image: pygame.Surface, colour: palette.RGB,
              direction: int, strength: float = 0.75) -> pygame.Surface | None:
    """Siluetin isik tarafindaki tek piksellik kenarini dondurur.

    Alev sahnenin tek isik kaynagi; karakterlerin bir yani mor/turuncu,
    obur yani karanlik olmali (docs/menu-ui.md 1). Sprite'i bastan bu isikla
    cizmek her poz icin ayri kare demek olurdu - kenar cizgisi ayni etkiyi
    sifir ek sprite ile veriyor.

    Maske farkiyla bulunuyor: siluetten, kendisinin ters yone kaydirilmis
    kopyasi silinince geriye yalnizca isik tarafindaki serit kaliyor.
    """
    mask = pygame.mask.from_surface(image)
    edge = mask.copy()
    edge.erase(mask, (-direction, 0))
    if edge.count() == 0:
        return None
    tint = tuple(int(c * strength) for c in colour)
    return edge.to_surface(setcolor=(*tint, 255), unsetcolor=(0, 0, 0, 0))
