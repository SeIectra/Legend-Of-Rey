"""Kare sonrasi efektler - vinyet ve bolum renk derecelendirmesi.

Bu katman **oynanisi hic degistirmiyor** ama oyunun "yapim degeri"
algisini en cok degistiren sey. Prototip surumunde vardi, v3'e hic
tasinmamisti; Arda'nin "prototipteki oyun daha iyi duruyor ama nedenini
anlamadim" gozlemi buyuk olcude bunun eksikligiydi (23.08.2026
kiyaslamasi). Sprite'lar iyilesse bile bu katman olmadan kare "cizilmis"
degil "dokulmis" gorunuyor.

Iki is yapiyor, ikisi de tek tam ekran gecisi:

  * **Vinyet** kenarlari karartir. Goz merkeze toplanir; ayrica 480x270'lik
    bir alanda kenarlardaki tile'lar "kesilmis" gibi durmaz, karanliga
    girer. En ucuz derinlik hissi.
  * **Renk derecelendirme** her bolume kendi atmosferini verir - sprite'lari
    yeniden uretmeden koyu maviye, kehribara ya da mora cekmek. Bolum 1
    gece mavisi, Bolum 3 mesale kehribari.

## Neden `BLEND_RGBA_MULT` degil de karistirma yuzeyi

Carpma karartir ama **renk veremez** (mor bir tint carpimla saglanamaz,
yalnizca kanal kisilabilir). Bolum atmosferi renk EKLEMEK istedigi icin
alfali bir duz yuzey `blit` ediliyor. Vinyet ise carpma degil, kenarlara
dogru artan alfali koyu bir halka - ikisi ayni yuzeyde birlesiyor, tek
gecis.

## Onbellek

Vinyet + tint yuzeyi ayarlar degismedikce **bir kez** uretilir. Her karede
yeniden uretmek 480x270 pikselde gereksiz bir maliyet olurdu ve
`CLAUDE.md` 4'un "her karede yeniden uretme" kuralini cignerdi.

## Erisilebilirlik

`postfx` ayari 0'a cekilirse katman tamamen atlanir. Fotosensitivite ve
"ekran cok karanlik" sikayeti icin tek dugme.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH

# Bolum atmosferleri: (renk adi, tint gucu 0..1, vinyet gucu 0..1).
# Renkler **palet icinden** - CLAUDE.md 6, palet disi renk yasak.
GRADES: dict[str, tuple[str, float, float]] = {
    # Bolum 1 - koy, gece. Hafif mavi, acik gokyuzu oldugu icin vinyet az.
    "village": ("abyss_dark", 0.10, 0.26),
    # Bolum 2 - ilk inis. Tas koridorlar, daha kapali.
    "descent": ("abyss_dark", 0.14, 0.36),
    # Bolum 3 - mesale mahzeni. Kehribar; zaten karartma maskesi var,
    # vinyet onun ustune binmesin diye dusuk.
    "crypt": ("ember_dark", 0.12, 0.22),
    # Bolum 4 - kayit odasi. ★nefes: dovus yok, gerilim dusuyor. Ton
    # topraga kayiyor (sicak ama olu bir oda), vinyet "descent"ten hafif -
    # cerceve daralirsa oda sikistirir, oysa bu bolum tam tersini
    # yapmali. Gerilimi tasarim degil **derecelendirme** de anlatiyor.
    "record": ("earth_dark", 0.11, 0.24),
    # Menu/sinematik - notr ama cerceveli.
    "void": ("void", 0.0, 0.34),
}
DEFAULT_GRADE = "descent"

_cache: dict[tuple, pygame.Surface] = {}


def _build(grade: str, strength: float) -> pygame.Surface:
    """Vinyet + tint'i TEK yuzeyde birlestirir. Onbelleklenir."""
    tone_name, tint_amount, vignette_amount = GRADES.get(
        grade, GRADES[DEFAULT_GRADE])
    tint = tint_amount * strength
    vignette = vignette_amount * strength

    layer = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
    tone = palette.color(tone_name)
    dark = palette.color("void")

    cx, cy = INTERNAL_WIDTH * 0.5, INTERNAL_HEIGHT * 0.5
    # En uzak kose - vinyet oranini buna gore normalize ediyoruz.
    max_d = math.hypot(cx, cy)

    for y in range(INTERNAL_HEIGHT):
        dy = (y - cy) / cy
        for x in range(INTERNAL_WIDTH):
            dx = (x - cx) / cx
            # Elips mesafe: ekran 16:9 oldugu icin dairesel vinyet
            # yanlardan cok fazla yiyordu.
            d = math.hypot(dx, dy) / math.hypot(1.0, 1.0)
            # Merkezde tamamen temiz kalsin: ilk %35 hic karartilmiyor.
            fall = max(0.0, (d - 0.35) / 0.65)
            v = fall * fall * vignette
            a = tint + v
            if a <= 0.004:
                continue
            # Tint rengi ile vinyet koyulugunu agirliklariyla karistir.
            total = tint + v
            r = int((tone[0] * tint + dark[0] * v) / total)
            g = int((tone[1] * tint + dark[1] * v) / total)
            b = int((tone[2] * tint + dark[2] * v) / total)
            layer.set_at((x, y), (r, g, b, min(255, int(a * 255))))
    return layer


def surface(grade: str, strength: float = 1.0) -> pygame.Surface | None:
    """Bir derecelendirmenin hazir katmani. `strength` 0 ise `None`."""
    if strength <= 0.0:
        return None
    # Guc kademelendiriliyor: her ondalik degisimde yeniden uretmek yerine
    # 20 kademeye yuvarlaniyor. Onbellek boylece kucuk kaliyor.
    key = (grade, round(strength * 20) / 20)
    cached = _cache.get(key)
    if cached is None:
        cached = _build(key[0], key[1])
        _cache[key] = cached
    return cached


def apply(target: pygame.Surface, grade: str, strength: float = 1.0) -> None:
    """Katmani kareye uygular. Cizimin **en sonunda** cagrilir."""
    layer = surface(grade, strength)
    if layer is not None:
        target.blit(layer, (0, 0))


def clear_cache() -> None:
    """Palet degisince (renk korlugu modu) yeniden uretilmeli."""
    _cache.clear()
