"""Toplanabilir seyler - sandiklar.

Bolum 2'de dogdu ama bolume ait degil: 18 bolumun hepsinde sandik olacak.
`docs/ekonomi-uretim.md` altin akisini sandiklar uzerine kuruyor.

## Dokununca aciliyor, tusa basinca degil

Etkilesim tusu denendi ve reddedildi. Sandik bir bulmaca degil, bir **odul**;
odulle oyuncu arasina tus koymak yalnizca kaciran oyuncu uretir. Ustelik
Bolum 1 etkilesim tusunu hic ogretmiyor - burada ilk kez gerekseydi ogreti
yuku bolumun ortasina duserdi.

## Gizli sandik farkli gorunmuyor

Gizli sandik ana yoldaki sandikla ayni sprite. Farki **nerede durdugu**.
Gizli olani parlatsaydik gizliligi kendisi ele verirdi; oyuncunun onu
bulmasi bir kesif olmali, bir ikon okumasi degil.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow

CHEST_WIDTH = 13
CHEST_HEIGHT = 10
# Kapak bu kadar karede aciliyor. 8 kare = ~7 sanat karesi; animasyon
# hissi 8 FPS (CLAUDE.md 6) ile ayni hizda kaliyor.
OPEN_FRAMES = 8
# Acildiktan sonra parilti bu kadar kare surer, sonra sandik sessizlesir.
AFTERGLOW_FRAMES = 40


class Chest:
    """Zemine oturan bir sandik. Dokununca acilir, altin verir."""

    __slots__ = ("x", "feet_y", "gold", "charm", "secret",
                 "opened", "open_frames", "afterglow")

    def __init__(self, x: float, feet_y: float, gold: int,
                 charm: str = "", secret: bool = False) -> None:
        self.x = x
        self.feet_y = feet_y
        self.gold = gold
        self.charm = charm
        self.secret = secret
        self.opened = False
        self.open_frames = 0
        self.afterglow = 0

    @property
    def rect(self) -> pygame.Rect:
        """Carpisma dikdortgeni - sprite'tan biraz genis.

        Alt-dikdortgen kurali burada **tersine** isliyor: dusman hitbox'i
        oyuncu lehine kucultuluyor, sandiginki de oyuncu lehine
        buyutuluyor. Ikisi de ayni amaca hizmet ediyor - affedicilik.
        """
        return pygame.Rect(int(self.x - CHEST_WIDTH // 2 - 2),
                           int(self.feet_y - CHEST_HEIGHT - 2),
                           CHEST_WIDTH + 4, CHEST_HEIGHT + 4)

    # --- Dongu --------------------------------------------------------------
    def open(self) -> bool:
        """Sandigi ac. Zaten aciksa `False` doner - odul bir kez verilir."""
        if self.opened:
            return False
        self.opened = True
        self.open_frames = OPEN_FRAMES
        self.afterglow = AFTERGLOW_FRAMES
        return True

    def update(self) -> None:
        if self.open_frames > 0:
            self.open_frames -= 1
        if self.afterglow > 0:
            self.afterglow -= 1

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int],
             frame: int = 0) -> None:
        ox, oy = offset
        x = int(self.x - CHEST_WIDTH // 2) - ox
        base = int(self.feet_y) - oy
        top = base - CHEST_HEIGHT

        self._draw_glow(surface, x, base, frame)

        # Govde: koyu ahsap, sol ustten isik (CLAUDE.md 6 - stil sozlesmesi).
        surface.fill(palette.color("earth_dark"),
                     (x, top + 3, CHEST_WIDTH, CHEST_HEIGHT - 3))
        surface.fill(palette.color("earth"),
                     (x, top + 3, CHEST_WIDTH, 1))
        surface.fill(palette.color("earth"), (x, top + 3, 1, CHEST_HEIGHT - 3))
        # Kontur siyah degil, paletin en koyu ikinci rengi.
        pygame.draw.rect(surface, palette.color("ink"),
                         pygame.Rect(x, top + 3, CHEST_WIDTH,
                                     CHEST_HEIGHT - 3), 1)

        self._draw_lid(surface, x, top)
        # Golge: karakterlerdeki gibi altinda tek elips.
        surface.fill(palette.color("abyss_dark"),
                     (x - 1, base - 1, CHEST_WIDTH + 2, 1))

    def _draw_lid(self, surface: pygame.Surface, x: int, top: int) -> None:
        """Kapak acilirken **arkaya** devriliyor: yuksekligi kisaliyor."""
        ratio = 1.0
        if self.opened:
            ratio = self.open_frames / OPEN_FRAMES
        height = max(1, int(round(3 * ratio)))
        lid_y = top + 3 - height
        surface.fill(palette.color("earth"), (x, lid_y, CHEST_WIDTH, height))
        pygame.draw.rect(surface, palette.color("ink"),
                         pygame.Rect(x, lid_y, CHEST_WIDTH, height), 1)
        if not self.opened:
            # Kilit - kapaliyken pirinc bir nokta. Acilinca kayboluyor.
            surface.fill(palette.color("gold"),
                         (x + CHEST_WIDTH // 2, top + 2, 1, 3))

    def _draw_glow(self, surface: pygame.Surface, x: int, base: int,
                   frame: int) -> None:
        """Kapaliyken nefes alir gibi, acilirken bir kez parlar.

        Durgun bir sprite dekor sanilir - Bolum 1'de yerdeki kilic ayni
        sorunu yasadi. Toplanabilir olan **toplanabilir gorunmeli**.
        """
        if self.opened:
            if self.afterglow <= 0:
                return
            peak = 0.55 * (self.afterglow / AFTERGLOW_FRAMES)
            radius = 16
        else:
            peak = 0.18 + 0.06 * math.sin(frame * 0.07)
            radius = 12

        glow = radial_glow(radius, palette.color("gold"), peak=peak)
        surface.blit(glow, (x + CHEST_WIDTH // 2 - radius,
                            base - CHEST_HEIGHT // 2 - radius),
                     special_flags=pygame.BLEND_RGB_ADD)
