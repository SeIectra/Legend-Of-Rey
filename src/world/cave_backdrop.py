"""Yeraltinin arka plani - kaya kutlesi, katmanlar, mesaleler.

Bolum 2'de dogdu ama bolume ait degil: Bolum 3, 5, 7... hepsi yeralti.
Bolume ozel yazilsaydi her yeralti bolumu kendi arka planini yeniden icat
ederdi ve hicbiri digerine benzemezdi.

## Magarada gokyuzu yoktur

Ilk hali duz zemin uzerine ayri ayri dikdortgenler koyuyordu ve ekranda
**sehir silueti** gibi okunuyordu: duz tepeli bloklar, aralarinda bos
karanlik. Sorun bloklarda degil, aralarindaki **bosluktaydi** - bos
karanlik gokyuzu gibi okunuyor.

Simdi ekranin tamami kaya. Katmanlar birbirinin ustune biniyor, aralarinda
bosluk degil **dikis** var. Uc kademe:

    abyss_dark   en derin kaya  (parlaklik 25)
    ink          orta kademe    (16)
    void         en yakin kaya  (6) - siluet gibi koyu

Uc kademe **tek yonde** koyulasiyor. Ilk denemede orta kademe en aciktu
(abyss, 46) ve ekranin ortasina mavi bir tepe serisi cizilmis gibi
duruyordu: goz onu arka plan degil **nesne** sanıyordu. Sirali koyulasma
ayni derinligi verirken hicbir katman one ciknmiyor.

Ucunun de tile'lardan (stone_dark 64) belirgin koyu olmasi sart: oyun
alaninin arka plani, oynanan seyin arkasinda kalmali.

## Ofset **tam sayiya** yuvarlanir

Ondalik ofset piksel art dokusunu titretir (CLAUDE.md 9). Parallax
carpanlari ondalik uretmeye en yatkin yer, o yuzden burada acikca
yuvarlaniyor.

## Desen deterministik ve **adim adim** ciziliyor

`random` yok: profil bir hash + iki sinusten uretiliyor, yani kamera geri
donduğunde ayni kaya ayni yerde. Sutun sutun cizmek kare basina 480 fill
demek olurdu; `STEP` piksellik dilimler halinde ciziliyor - 16x16 tile
olceginde fark gorunmuyor, maliyet dortte bire iniyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH, TILE_SIZE

FAR_PARALLAX = 0.22
MID_PARALLAX = 0.38
NEAR_PARALLAX = 0.60
STEP = 3                         # Profil dilimi genisligi (piksel)

# Kaya dikislerinin taban yuksekligi ve dalga genligi.
# Harita 16 tile (256 piksel) yuksekliginde ve ekran 270; oyun alani
# satir 4-13 arasi, yani ekranda kabaca y=70..230. Dikisler bu bandin
# **icinde** kalmali, yoksa tavan tile'larinin arkasinda kaybolurlar.
FAR_BASE, FAR_AMP = 186, 26
MID_BASE, MID_AMP = 132, 22
NEAR_BASE, NEAR_AMP = 74, 18

STRATA_SPACING = 19              # Yatay kaya katmanlari arasi
CRACK_SPACING = 61               # Duvardaki dusey yarik araligi


def _profile(x: int, seed: int, base: int, amp: int) -> int:
    """Bir sutundaki kaya yuksekligi. Deterministik, surekli.

    Iki farkli frekansta sinus + hash: tek sinus dalgali bir tepe gibi
    okunuyordu (cok duzenli), saf hash ise gurultu gibi (cok duzensiz).
    Ikisinin toplami kaya gibi okunuyor.
    """
    value = base
    value += amp * math.sin((x + seed) * 0.0170)
    value += amp * 0.45 * math.sin((x + seed) * 0.0413 + 1.7)
    value += ((x * 2654435761 + seed) >> 9) & 5
    return int(value)


def _draw_layer(surface: pygame.Surface, shift: int, colour, seed: int,
                base: int, amp: int) -> None:
    """Bir kaya kademesi: dalgali bir dikisin **altindaki** her sey dolu."""
    height = surface.get_height()
    for screen_x in range(0, INTERNAL_WIDTH, STEP):
        world_x = screen_x + shift
        top = height - _profile(world_x, seed, base, amp)
        surface.fill(colour, (screen_x, top, STEP, height - top))


def draw(surface: pygame.Surface, offset: tuple[int, int],
         frame: int = 0) -> None:
    """Magara arka plani. Zeminden **once** cizilir."""
    ox, _oy = offset
    # Taban dolgu: ekranda bos karanlik kalmiyor - magarada gokyuzu yok.
    surface.fill(palette.color("abyss_dark"))

    _draw_strata(surface, int(round(ox * FAR_PARALLAX)))
    _draw_layer(surface, int(round(ox * MID_PARALLAX)),
                palette.color("ink"), 311, MID_BASE, MID_AMP)
    _draw_cracks(surface, int(round(ox * MID_PARALLAX)))
    _draw_layer(surface, int(round(ox * NEAR_PARALLAX)),
                palette.color("void"), 977, NEAR_BASE, NEAR_AMP)
    _draw_stalactites(surface, int(round(ox * NEAR_PARALLAX)))
    _draw_haze(surface, frame)


def _draw_strata(surface: pygame.Surface, shift: int) -> None:
    """Yatay kaya katmanlari - derin kayanin uzerinde sonuk cizgiler.

    Tek basina dolgu duz bir duvar gibi okunuyor. Katmanlar hem doku
    veriyor hem de yeralti oldugunu anlatiyor: bu cizgiler tortul kaya.
    """
    colour = palette.color("abyss")
    top = INTERNAL_HEIGHT - _profile(shift, 7, FAR_BASE, FAR_AMP)
    for index in range(12):
        y = top + index * STRATA_SPACING
        if y >= INTERNAL_HEIGHT:
            break
        # Katmanlar **kesik**. Ilk hali ekrani bastan basa kesen duz
        # cizgiler ciziyordu ve cizgili kagit gibi okunuyordu: kaya
        # katmani sureklidir ama duz degildir, ustelik cogu yeri baska
        # kayanin altinda kalir.
        for screen_x in range(0, INTERNAL_WIDTH, STEP * 3):
            seed = (screen_x + shift + index * 137) * 2654435761
            if (seed >> 12) & 3:         # Dortte biri ciziliyor
                continue
            wobble = ((seed >> 9) & 1)
            surface.fill(colour, (screen_x, y + wobble, STEP * 3, 1))


def _draw_cracks(surface: pygame.Surface, shift: int) -> None:
    """Duvarda dusey yariklar. Dikey vurgu yoksa magara yatay bir seride
    donusuyor."""
    colour = palette.color("void")
    start = -(shift % CRACK_SPACING)
    for x in range(start, INTERNAL_WIDTH + CRACK_SPACING, CRACK_SPACING):
        seed = ((x + shift) * 2246822519) & 0xFFFF
        top = 90 + seed % 60
        length = 40 + (seed >> 5) % 70
        for i in range(length):
            drift = ((seed >> (i % 11)) & 1)
            surface.fill(colour, (x + drift, top + i, 1, 1))


def _draw_stalactites(surface: pygame.Surface, shift: int) -> None:
    """Tavandan sarkan disler. En yakin katman - siluet gibi koyu."""
    colour = palette.color("void")
    spacing = 23
    start = -(shift % spacing)
    for x in range(start, INTERNAL_WIDTH + spacing, spacing):
        seed = ((x + shift) * 40503 + 12345) & 0xFFFF
        length = 12 + seed % 26
        for row in range(length):
            span = max(1, int((1.0 - row / length) * 5))
            surface.fill(colour, (x - span, row, span * 2, 1))


def _draw_haze(surface: pygame.Surface, frame: int) -> None:
    """Alt kenarda yavasca kabaran sis. Derinligi tabandan da anlatir."""
    colour = palette.color("abyss")
    for i in range(4):
        wave = math.sin(frame * 0.011 + i * 1.7)
        y = INTERNAL_HEIGHT - 6 - i * 3 + int(round(wave * 1.5))
        surface.fill(colour, (0, y, INTERNAL_WIDTH, 1))


def draw_torches(surface: pygame.Surface, offset: tuple[int, int],
                 torches, frame: int = 0) -> None:
    """Mesaleler. `torches` (tile_x, tile_y, yaniyor_mu) uclusu.

    **Tavana asili** ciziliyor: sap yukari uzanip tavan tile'ina giriyor.
    Ilk hali sapi asagi uzatiyordu ve mesale havada asili duruyordu -
    hicbir seye baglanmayan bir isik kaynagi sahneyi bozuyor.

    Sonmus mesale de ciziliyor: gizli odadaki sonmus mesale bir **anlati**
    parcasi - buraya birisi gelmis ve donmemis.
    """
    ox, oy = offset
    for tile_x, tile_y, lit in torches:
        x = tile_x * TILE_SIZE + TILE_SIZE // 2 - ox
        y = tile_y * TILE_SIZE - oy
        if x < -40 or x > INTERNAL_WIDTH + 40:
            continue                     # Gorunmeyeni cizme

        # Sap: tavandan asagi sarkiyor. Tepesi tile sinirinin bir piksel
        # ustunde - tavana **girmis** gorunsun.
        surface.fill(palette.color("earth_dark"), (x, y - 1, 2, 8))
        surface.fill(palette.color("ink"), (x + 2, y - 1, 1, 8))

        if not lit:
            surface.fill(palette.color("ink"), (x - 1, y + 7, 4, 3))
            continue

        # Alev sapin **ucunda**, uc kareli bir dongude oynuyor.
        flicker = (frame // 6 + tile_x) % 3
        surface.fill(palette.color("ember"), (x - 1, y + 7, 4, 5 - flicker))
        surface.fill(palette.color("gold"), (x, y + 8, 2, 3 - flicker))
        glow = radial_glow(30, palette.color("ember"),
                           peak=0.46 + 0.05 * math.sin(frame * 0.09 + tile_x))
        surface.blit(glow, (x - 29, y - 21),
                     special_flags=pygame.BLEND_RGB_ADD)
