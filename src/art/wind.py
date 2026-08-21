"""Ruzgar - dikey dilim kaydirma (vertical slice shear).

Pelerin, sac, bayrak, orumcek agi, su yuzeyi: hepsi ayni teknikle kimildar.
Sprite yatay seritlere bolunur, her serit sinus dalgasiyla yatay kaydirilir.

    offset = amplitude * sin(time * frequency + y * wave_length)

Alt seritler az, ust seritler cok kayar - kumas fizigi (docs/menu-ui.md 1).

**Neden ayri kare cizmiyoruz:** 4 karelik bir pelerin animasyonu hem daha
kotu gorunur (dongusel, tekrar eden) hem de her varyant icin yeniden
cizilmek zorundadir. Kaydirma surekli, tekrarsiz ve **sifir ek sprite**
gerektiriyor. Ayni fonksiyon Rey'in sacini da Ardo'nun pelerinini de
B9'daki bayragi da oynatir.

**Tam sayi kaydirma sart.** Ondalik ofset piksel art dokusunu titretir -
projenin en cok tekrarlanan hatasi bu (CLAUDE.md 9).
"""
from __future__ import annotations

import math

import pygame


def shear(surface: pygame.Surface, phase: float,
          amplitude: float = 1.6,
          wave_length: float = 0.45,
          anchor: str = "bottom",
          slice_height: int = 1) -> pygame.Surface:
    """Yuzeyi ruzgarda dalgalandirir.

    `phase`    zaman - her karede biraz artir (orn. frame * 0.08)
    `amplitude` azami yatay kayma, piksel
    `anchor`   hangi uc sabit kalir: "bottom" (ayakta duran kumas),
               "top" (asili zincir, orumcek agi)
    """
    width, height = surface.get_size()
    if height <= 0 or amplitude <= 0.0:
        return surface

    # Kaydirma sprite'i genisletebilir; tasmasin diye pay birak.
    pad = int(math.ceil(amplitude)) + 1
    out = pygame.Surface((width + pad * 2, height), pygame.SRCALPHA)

    for top in range(0, height, slice_height):
        band = min(slice_height, height - top)
        # Sabit uca yaklastikca kayma azalir.
        if anchor == "bottom":
            weight = 1.0 - (top + band * 0.5) / height
        else:
            weight = (top + band * 0.5) / height
        weight = weight * weight          # ucta daha belirgin, dipte sakin

        offset = amplitude * weight * math.sin(phase + top * wave_length)
        strip = surface.subsurface(pygame.Rect(0, top, width, band))
        # Tam sayiya yuvarla: ondalik ofset dokuyu titretir.
        out.blit(strip, (pad + int(round(offset)), top))

    return out


def shear_offsets(height: int, phase: float, amplitude: float = 1.6,
                  wave_length: float = 0.45,
                  anchor: str = "bottom") -> list[int]:
    """Kaydirma ofsetleri - kendi cizimini yapanlar icin (zincir gibi).

    Yuzey uretmeden sadece sayilari ister.
    """
    offsets: list[int] = []
    for y in range(height):
        if anchor == "bottom":
            weight = 1.0 - y / max(1, height)
        else:
            weight = y / max(1, height)
        weight = weight * weight
        offsets.append(int(round(amplitude * weight
                                 * math.sin(phase + y * wave_length))))
    return offsets
