"""Gurultu - Bolum 15'in mekanigi.

`docs/yapi.md` mekanik 9: *"Yanki kapali oynama; **ses cikarirsan suru
uyanir**."* Ve ayni belgenin uygulama notu yontemi de veriyor:

    "Sessizlik bolumu: dusmanlara `alert_level` float'i ekle, gurultu
     olaylariyla artir/azalt. **Var olan AI'ya eklenti, yeni sistem
     degil.**"

Bu dosya o notun ikinci yarisi: olaylari toplayan ince bir katman.
Uyaniklik `Enemy`de yasiyor (`hear`, `_update_alert`), burada yalnizca
**kim ne kadar ses cikardi** var.

## Gurultu GORUNUR olmali

Gizlilik mekaniginin en sik hatasi sessiz bir sayac: oyuncu ne kadar
gurultulu oldugunu bilmeden yakalanir ve haksizliga ugramis hisseder.

O yuzden her gurultu ekranda **genisleyen bir halka**. Ayni gorsel dil
Rezonans'ta zaten var (`resonance.py`: *"halka, patlama degil"*) - ve
bu bir tesaduf degil: ikisi de ses. Oyuncu daha ilk odada "bu halka
duyulan sey" baglantisini kuruyor cunku halkayi tanıyor.

## Sayilar bir cumle kuruyor

    yurumek     0.06   duyulmuyor denecek kadar az
    kosmak      0.30   birkac adimda uyandirir
    kacinma     0.34
    inis        0.85   neredeyse aninda
    vurus       1.20   **tek vurus yeter** - dovus cozum degil

Sonuncusu `docs/yapi.md`nin *"tamamen dovussuz gecilebilir - ve daha
iyi odul verir"* cumlesinin mekanik karsiligi: kilic cekmek bolumu
kaybetmenin en hizli yolu.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from src.art import palette
from src.config import NOISE_RANGE

# Halkanin ekranda kaldigi sure (kare).
RING_FRAMES = 26


@dataclass
class Ring:
    """Duyulmus bir gurultunun gorsel karsiligi."""

    x: float
    y: float
    strength: float
    frames: int = 0

    @property
    def progress(self) -> float:
        return min(1.0, self.frames / RING_FRAMES)

    @property
    def done(self) -> bool:
        return self.frames >= RING_FRAMES

    @property
    def radius(self) -> float:
        # Halka **duyulma menzili kadar** buyuyor, sesin siddetiyle
        # olcekli. Yani gordugun cember gercekten "kimler duydu"
        # demek - dekoratif degil, bilgi.
        return NOISE_RANGE * min(1.0, self.strength) * self.progress


class NoiseField:
    """Bir sahnedeki gurultu olaylari.

    Sahne `emit()` cagiriyor, alan hem dusmanlara duyuruyor hem
    ekranda halka birakiyor. Ikisini ayirmak cazipti ama yanlis
    olurdu: **duyulan sey ile gorulen sey ayni olmali**, yoksa halka
    bir sus olur ve oyuncu ona guvenemez.
    """

    def __init__(self) -> None:
        self.rings: list[Ring] = []
        # Bu bolumde toplam kac kez uyandirildi - odul olcutu.
        self.wakes = 0

    def emit(self, enemies, x: float, y: float, strength: float) -> int:
        """Gurultu cikar. Kac dusmanin uyandigini dondurur."""
        if strength <= 0.0:
            return 0
        self.rings.append(Ring(x, y, strength))
        woke = 0
        for enemy in enemies:
            if enemy.hear(x, y, strength):
                woke += 1
        self.wakes += woke
        return woke

    def update(self) -> None:
        for ring in self.rings:
            ring.frames += 1
        self.rings = [r for r in self.rings if not r.done]

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        """Genisleyen halkalar - **oyuncunun tek geri bildirimi.**

        Kalinlik siddetle degil **solmayla** degisiyor: yeni halka
        kalin, dagilan ince. Siddeti yaricap zaten anlatiyor; iki
        kanali ayni seye harcamak birini bosa harcamak olurdu.
        """
        ox, oy = offset
        for ring in self.rings:
            radius = int(ring.radius)
            if radius < 2:
                continue
            fade = 1.0 - ring.progress
            colour = tuple(int(c * (0.25 + 0.75 * fade))
                           for c in palette.color("bone"))
            width = max(1, int(1 + 2 * fade))
            pygame.draw.circle(surface, colour,
                               (int(ring.x) - ox, int(ring.y) - oy),
                               radius, width)


@dataclass
class Chime:
    """Dikkat dagitici - can ya da gevsek tas.

    `docs/yapi.md` B15: *"Gurultu kaynaklarini (dusen tas, can, su
    damlasi) kullanarak dikkat dagitma."*

    Rezonansla calindiyor (B8'de ogrenilen mekanik). Yani bu bolum
    yeni bir arac vermiyor - **var olan araci ters yone ceviriyor**:
    on iki bolumdur kapi acan ses, burada dikkat dagitiyor.
    `docs/gdd.md` 9: *yeni mekanik + eski mekanik = yeni bulmaca.*

    Bir kez calinip susmuyor: `cooldown` bitince yeniden calinabiliyor.
    Tek kullanimlik olsaydi yanlis zamanda calan oyuncu odayi
    kilitlerdi (yumusak kilit yasak, bkz. `DEVIR.md`).
    """

    tile_x: int
    tile_y: int
    cooldown: int = 0
    rings: int = 0

    @property
    def x(self) -> float:
        from src.config import TILE_SIZE
        return self.tile_x * TILE_SIZE + TILE_SIZE * 0.5

    @property
    def y(self) -> float:
        from src.config import TILE_SIZE
        return self.tile_y * TILE_SIZE + TILE_SIZE * 0.5

    @property
    def rect(self):
        """`ResonanceState.reaches()` bunu ariyor.

        Rezonans halkasi **nesnenin dikdortgeni** uzerinden geciyor
        mu diye bakiyor (`resonance.py`). Kristal ve can zaten oyle
        calisiyordu; can da ayni sozlesmeyi tasimali, yoksa
        `reaches()` `AttributeError` verir - ve bu ancak oyuncu
        rezonansi ilk kullandiginda ortaya cikardi.
        """
        import pygame
        from src.config import TILE_SIZE
        return pygame.Rect(self.tile_x * TILE_SIZE,
                           self.tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    @property
    def ready(self) -> bool:
        return self.cooldown <= 0

    def update(self) -> None:
        if self.cooldown > 0:
            self.cooldown -= 1

    def ring(self) -> bool:
        if not self.ready:
            return False
        self.cooldown = 90
        self.rings += 1
        return True

    def draw(self, surface: pygame.Surface, offset: tuple[int, int],
             frame: int) -> None:
        ox, oy = offset
        x = int(self.x) - ox
        y = int(self.y) - oy
        # Aski ve govde.
        surface.fill(palette.color("earth_dark"), (x - 1, y - 12, 2, 5))
        tone = "gold" if self.ready else "stone_dark"
        surface.fill(palette.color(tone), (x - 5, y - 7, 11, 9))
        surface.fill(palette.color("stone_darkest"), (x - 5, y + 2, 11, 1))
        if not self.ready:
            # Calarken sallaniyor - durumu **sekil** de anlatiyor,
            # yalnizca renk degil (`CLAUDE.md` 10).
            swing = int(math.sin(frame * 0.5) * 2)
            surface.fill(palette.color("gold"), (x - 1 + swing, y + 2, 2, 3))
