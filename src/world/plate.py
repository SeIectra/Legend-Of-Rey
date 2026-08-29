"""Agirlik plakalari - beraberligin mekanige girdigi yer.

`docs/gdd.md` 9 mekanik 4: *"Agirlik plakalari | B6"*.
`docs/yapi.md` B6: *"ilk team-up dovusu + agirlik plakalari (**ikisi ayri
plakada durmali** - beraberlik mekanige giriyor)"*.

## Bulmacanin tamami tek cumlede

Kapi ancak **butun plakalar ayni anda basiliyken** aciliyor. Tek kisi iki
plakaya birden basamaz; yani kapi bir bilmece degil bir **anlasma**.

Bu, B6'nin anlatisiyla birebir ayni sey: iki yabanci karsilasiyor,
konusmuyorlar (soru isareti balonu - `docs/gdd.md` 11), ve ilk kez
birlikte bir sey yapiyorlar. Anlati bunu SOYLEMIYOR, kapi yapiyor.

## Tolerans: "es zamanli" degil "birlikte"

`PLATE_GRACE_FRAMES` kadar bir kuyruk var: plakadan cikan biri yarim
saniye daha basili sayiliyor. Sifir olsaydi ikisinin **ayni karede**
basmasi gerekirdi - bir yapay zeka yoldasla bu imkansiza yakin ve
adaletsiz olurdu. Tolerans bulmacayi zamanlama sinavi olmaktan cikarip
konumlanma sinavi yapiyor.

## Plaka **tilemap'e dokunmuyor**

Kapi `keydoor.LockedDoor` gibi gercek `SOLID` tile yaziyor; plakalar
yalnizca "basili mi" diye soruyor. Ikisi ayri kaliyor: plaka bir GIRDI,
kapi bir SONUC. Bir arada olsalardi "hangi plaka hangi kapiyi aciyor"
sorusu koda gomulur ve ikinci bir bulmacada kopyalanirdi.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import (
    PLATE_GRACE_FRAMES, PLATE_HEIGHT, PLATE_WIDTH, TILE_SIZE,
)


class WeightPlate:
    """Ustunde biri durunca basilan zemin plakasi."""

    __slots__ = ("x", "y", "grace", "pressed", "_was_pressed", "frame")

    def __init__(self, tile_x: int, tile_y: int) -> None:
        # Plaka tile'in **ustune** oturuyor: zemin satiri `tile_y`, plaka
        # onun ust yuzeyinde duruyor.
        self.x = float(tile_x * TILE_SIZE)
        self.y = float(tile_y * TILE_SIZE - PLATE_HEIGHT)
        self.grace = 0
        self.pressed = False
        self._was_pressed = False
        self.frame = 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), PLATE_WIDTH, PLATE_HEIGHT)

    @property
    def centre_x(self) -> float:
        return self.x + PLATE_WIDTH * 0.5

    @property
    def held(self) -> bool:
        """Tolerans dahil basili sayiliyor mu - kapi bunu soruyor."""
        return self.pressed or self.grace > 0

    def update(self, actors) -> bool:
        """Ustunde duran var mi diye bakar. Yeni basildiysa True doner.

        Ayak hizasi kontrolu **govdenin alti** ile: govde merkezine
        bakilsaydi plakanin yanindan gecen biri de basmis sayilirdi.
        """
        self.frame += 1
        zone = pygame.Rect(int(self.x), int(self.y) - 6, PLATE_WIDTH,
                           PLATE_HEIGHT + 8)
        self.pressed = any(
            not getattr(actor, "dead", False)
            and zone.collidepoint(int(actor.body.center_x),
                                  int(actor.body.bottom))
            for actor in actors)

        if self.pressed:
            self.grace = PLATE_GRACE_FRAMES
        elif self.grace > 0:
            self.grace -= 1

        newly = self.pressed and not self._was_pressed
        self._was_pressed = self.pressed
        return newly

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        """Basili plaka **coker ve parlar** - iki kanal.

        Yalnizca renk degisseydi renk gormeyen oyuncu durumu okuyamazdi
        (`CLAUDE.md` 10). Cokme siluet farki, parlama renk farki.
        """
        ox, oy = offset
        rect = self.rect.move(-ox, -oy)
        if self.held:
            rect.y += 2
            rect.height -= 1

        base = "gold" if self.held else "stone_dark"
        surface.fill(palette.color("stone_darkest"),
                     rect.inflate(2, 2))
        surface.fill(palette.color(base), rect)
        # Yan kizaklar - plakanin "hareketli parca" oldugunu soyluyor.
        for side in (rect.left - 1, rect.right):
            surface.fill(palette.color("stone_darkest"),
                         (side, rect.y - 2, 1, rect.height + 3))


class PlateGate:
    """Butun plakalar basiliyken acilan kapi.

    `keydoor.LockedDoor` ile ayni yol: gorsel bir kapak degil gercek
    `SOLID` tile'lar. Carpisma zaten tilemap'ten geliyor, ikinci bir
    carpisma yolu acmaya gerek yok.
    """

    __slots__ = ("column", "rows", "plates", "open", "_applied")

    def __init__(self, column: int, rows, plates) -> None:
        self.column = column
        self.rows = tuple(rows)
        self.plates = tuple(plates)
        self.open = False
        self._applied = False

    @property
    def satisfied(self) -> bool:
        """Butun plakalar ayni anda basili mi.

        `all()` - **hepsi**. Bir tanesi yeterli olsaydi bulmaca tek
        kisilik olurdu ve B6'nin butun anlami (beraberlik) kaybolurdu.
        """
        return bool(self.plates) and all(p.held for p in self.plates)

    def close(self, tilemap) -> None:
        from src.world.tilemap import SOLID
        for row in self.rows:
            tilemap.set_tile(self.column, row, SOLID)
        self.open = False
        self._applied = True

    def update(self, tilemap) -> bool:
        """Durumu plakalardan turetir. Durum DEGISTIYSE True doner.

        Kapi bir kez acilinca **acik kaliyor**: bulmaca cozuldukten sonra
        plakadan inince kapinin tekrar kapanmasi oyuncuyu arenaya
        hapsedebilirdi ve "cozdum" hissini geri alirdi.
        """
        if self.open:
            return False
        if not self.satisfied:
            return False
        from src.world.tilemap import EMPTY
        for row in self.rows:
            tilemap.set_tile(self.column, row, EMPTY)
        self.open = True
        return True
