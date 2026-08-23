"""Koy arka plani - Bolum 1'in dekoru.

`cave_backdrop.py`'nin magara icin yaptiginin koy karsiligi: sahne
mantigini degil, yalnizca **cizimi** tutuyor. Ayrildi cunku
`chapter01.py` 732 satira cikmisti - CLAUDE.md 11'in 400 satir siniri.

Dort parallax katmani: gokyuzu -> ay -> uzak tepeler -> koy. Ilk halinde
yalnizca yildizlar ve evler vardi; aradaki bosluk "gokyuzu" degil
"hiclik" gibi okunuyordu (ayni tuzak magara arka planinda da yasanmisti,
DEVIR.md 4 madde 19). Ay ve tepe siluetleri o boslugu MESAFEYE ceviriyor.

Butun fonksiyonlar saf: durum tutmuyorlar, `frame` disaridan geliyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH, TILE_SIZE
from src.world.rooms.chapter01 import SCENERY


def _draw_stars(surface: pygame.Surface, ox: float, frame: int) -> None:
    """Yildizlar - bir kismi nabiz atiyor, hepsi ayni parlaklikta degil."""
    for i in range(70):
        x = int(i * 97 - ox * 0.10) % INTERNAL_WIDTH
        y = (i * 53) % 118
        if i % 7 == 0:
            # Titreyen yildiz: sabit bir yildiz alani "doku" gibi
            # okunuyordu, birkac tanesinin nabzi onu gokyuzu yapiyor.
            twinkle = math.sin(frame * 0.04 + i) > 0.2
            tone = "white_flash" if twinkle else "stone_dark"
        else:
            tone = "bone" if i % 5 == 0 else "stone_dark"
        surface.fill(palette.color(tone), (x, y, 1, 1))

def _draw_moon(surface: pygame.Surface, ox: float) -> None:
    """Ay - neredeyse sabit (cok uzak) ve hafif haleli."""
    mx = int(INTERNAL_WIDTH * 0.78 - ox * 0.04)
    my = 34
    if mx < -24 or mx > INTERNAL_WIDTH + 24:
        return
    halo = radial_glow(20, palette.color("abyss_light"), peak=0.22)
    surface.blit(halo, (mx - 20, my - 20),
                 special_flags=pygame.BLEND_RGB_ADD)
    pygame.draw.circle(surface, palette.color("bone"), (mx, my), 7)
    # Hilal: ust uste ikinci daire gokyuzu renginde - dolunay yerine
    # hilal, siluete kimlik veriyor.
    pygame.draw.circle(surface, palette.color("abyss_dark"),
                       (mx + 4, my - 2), 6)

def _draw_hills(surface: pygame.Surface, ox: float) -> None:
    """Uzak tepe siluetleri - iki kademe, ikisi de tek renk.

    Tek renk bilincli: ayrinti verirsek yakinda sanilir. Uzaklik
    ayrintinin YOKLUGU ile anlatilir.
    """
    horizon = 128
    for layer, (speed, tone, amp, step) in enumerate((
            (0.22, "abyss", 16.0, 0.020),
            (0.35, "ink_soft", 11.0, 0.034))):
        base_y = horizon + layer * 9
        shift = ox * speed
        for x in range(INTERNAL_WIDTH):
            world = x + shift
            h = (math.sin(world * step) * amp
                 + math.sin(world * step * 2.3 + layer) * amp * 0.35)
            top = int(base_y - h)
            if top < INTERNAL_HEIGHT:
                surface.fill(palette.color(tone),
                             (x, top, 1, INTERNAL_HEIGHT - top))

def draw(surface: pygame.Surface, offset, frame: int) -> None:
    """Evler, kuyu, cit. Carpisma yok - yalnizca dekor.

    Koyun koye benzemesi icin sart: duz zemin uzerinde iki platform
    "koy" degil "test odasi" gibi okunuyordu.
    """
    ox, oy = offset
    for tx, ty, tw, th, kind in SCENERY:
        x = tx * TILE_SIZE - ox
        base = (ty + 1) * TILE_SIZE - oy
        width = tw * TILE_SIZE
        height = th * TILE_SIZE
        if x + width < -20 or x > INTERNAL_WIDTH + 20:
            continue                     # Gorunmeyeni cizme

        if kind == "house":
            _draw_house(surface, frame, x, base, width, height)
        elif kind == "well":
            _draw_well(surface, frame, x, base, width, height)
        else:
            _draw_fence(surface, frame, x, base, width, height)

def _draw_house(surface: pygame.Surface, frame: int, x: int, base: int,
                width: int, height: int) -> None:
    """Ev: govde + saclik yapan cati + kapi + isikli pencere + baca.

    **Kapi sart oldu** (23.08.2026): koyluler `door_x`'e kosuyor ve
    oraya girip kayboluyor. Gorunur bir kapi olmadan bu hareket
    "duvara girdi" gibi okunuyordu.
    """
    top = base - height
    surface.fill(palette.color("ink_soft"), (x, top, width, height))
    # Yatay tahta cizgileri - duz dolgu "kutu" gibi okunuyordu.
    for row in range(top + 3, base, 4):
        surface.fill(palette.color("void"), (x + 1, row, width - 2, 1))

    # Cati: govdeden iki piksel TASAR (saclik). Tam govde genisliginde
    # biten cati, evi ustten kesilmis bir kutu yapiyordu.
    roof_h = max(4, height // 3)
    for i in range(roof_h):
        t = i / max(1, roof_h - 1)
        inset = int((width * 0.5 + 2) * t)
        tone = "earth" if i < 2 else "earth_dark"
        surface.fill(palette.color(tone),
                     (x - 2 + inset, top - i, width + 4 - inset * 2, 1))

    # Kapi - koylunun kactigi yer. Govdenin ortasinda, zemine oturur.
    door_w = max(5, width // 5)
    door_h = max(8, height // 2)
    dx = x + width // 2 - door_w // 2
    surface.fill(palette.color("earth_dark"),
                 (dx, base - door_h, door_w, door_h))
    surface.fill(palette.color("void"), (dx, base - door_h, door_w, 1))
    surface.fill(palette.color("gold"),
                 (dx + door_w - 2, base - door_h // 2, 1, 1))   # kol

    # Isikli pencere - koyde hayat var. Titriyor: mum isigi.
    flicker = 1 if (frame // 17 + x) % 5 else 0
    win_y = top + max(3, height // 3)
    surface.fill(palette.color("ember" if flicker else "ember_dark"),
                 (x + 3, win_y, 3, 3))
    if width > 40:
        surface.fill(palette.color("ember" if not flicker else "ember_dark"),
                     (x + width - 6, win_y, 3, 3))

    # Baca + duman - hareket eden tek dekor ogesi, koyu "canli" yapar.
    chimney_x = x + width - max(6, width // 4)
    surface.fill(palette.color("stone_darkest"),
                 (chimney_x, top - roof_h - 4, 4, 6))
    _draw_smoke(surface, frame, chimney_x + 2, top - roof_h - 5)

def _draw_smoke(surface: pygame.Surface, frame: int, x: int, y: int) -> None:
    """Bacadan yukselen duman - yukari cikarken saga savrulur ve soner."""
    for i in range(6):
        phase = frame * 0.035 + i * 0.9 + x * 0.11
        drift = math.sin(phase) * (1.0 + i * 0.5)
        puff_x = int(round(x + drift))
        puff_y = y - 3 - i * 4
        if puff_y < -4:
            continue
        size = 1 if i < 2 else 2
        tone = "stone_dark" if i < 3 else "stone_darkest"
        surface.fill(palette.color(tone), (puff_x, puff_y, size, size))

def _draw_well(surface: pygame.Surface, frame: int, x: int, base: int,
               width: int, height: int) -> None:
    top = base - height
    surface.fill(palette.color("stone_darkest"), (x, top, width, height))
    surface.fill(palette.color("stone_dark"), (x - 2, top, width + 4, 2))
    # Direk + makara: siluete dikey bir cizgi katiyor.
    surface.fill(palette.color("earth_dark"), (x + 1, top - 9, 1, 9))
    surface.fill(palette.color("earth_dark"),
                 (x + width - 2, top - 9, 1, 9))
    surface.fill(palette.color("earth"), (x, top - 10, width, 1))
    surface.fill(palette.color("stone"), (x + width // 2, top - 8, 1, 4))

def _draw_fence(surface: pygame.Surface, frame: int, x: int, base: int,
                width: int, height: int) -> None:
    top = base - height
    for i in range(0, width, 5):
        surface.fill(palette.color("earth_dark"), (x + i, top, 1, height))
    surface.fill(palette.color("earth_dark"), (x, top + 2, width, 1))


def draw_sky(surface: pygame.Surface, ox: float, frame: int) -> None:
    """Gokyuzu katmanlari: yildizlar + ay. Koyden ONCE cizilir.

    Katman hizlari bilerek farkli: yildiz 0.10, ay 0.04 (neredeyse
    sabit - cok uzak), tepeler 0.22/0.35, koy 1.0.
    """
    surface.fill(palette.color("abyss_dark"))
    _draw_stars(surface, ox, frame)
    _draw_moon(surface, ox)
    _draw_hills(surface, ox)
