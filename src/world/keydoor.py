"""Kilitli kapi + anahtar - boss odasindan cikis.

Arda'nin bildirdigi hata (24.08.2026): *"birinci boss fight ile hic
kapismadan bolumu gecebiliyorsun, sadece ilerlemek yeterli."* Arena
kapisi yalnizca **girisi** muhurluyordu; oyuncu iceri girip boss'a hic
dokunmadan sag tarafa yuruyup cikis odasina geciyordu - arka tarafta
hicbir sey yoktu.

Arda'nin cozumu: *"bosslardan sonra bir kapi olsun kilitli olsun. boss'u
oldurunce anahtar dusursun, onu alip gecebilelim."*

## Neden ayri modul

Ayni yapi **her boss odasinda** tekrar edecek (18 bolum, 4 buyuk boss +
bolum basi mini-boss). Bolum 2'ye gomulseydi Bolum 3 onu kopyalar,
ikisi ayrisir ve bir gun biri duzeltilip oteki unutulurdu - projenin
`_seal_arena` ile tam olarak basina gelen sey buydu (Bolum 3'e hic
tasinmamisti, Arda "duvara sikisiyorum" diye bildirdi).

## Anahtar bir NESNE, bayrak degil

`boss_defeated = True` yapip kapiyi acmak daha kisa olurdu ama oyuncu
odulu **gormezdi**. Anahtarin dusmesi, yerde parlamasi ve toplanmasi
zaferi bir ana ceviriyor. Ayrica dovusten kacan oyuncuya "bir sey
eksik" bilgisini mekan uzerinden veriyor: kapi orada, kilitli, sebebi
belli.

## Kapi tilemap'e yaziliyor

Gorsel bir kapi degil, gercek `SOLID` tile'lar - carpisma zaten
tilemap'ten geliyor, ayri bir carpisma yolu acmak gereksiz. Acilinca
`EMPTY`'ye donuyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import TILE_SIZE

# Anahtarin yerden yukselip suzulme genligi (piksel).
KEY_BOB = 2.2
# Oyuncu bu mesafeye girince anahtari alir. Sandiktan genis: anahtar
# kucuk bir nesne, oyuncunun ustune basmaya calismasi gerekmesin.
KEY_PICKUP_RANGE = 14.0
# Dususten sonra kac kare boyunca "yeni dustu" parlamasi surer.
KEY_FLASH_FRAMES = 45


class BossKey:
    """Boss oldugunde dusen anahtar. Dokununca alinir."""

    __slots__ = ("x", "feet_y", "frame", "taken", "flash")

    def __init__(self, x: float, feet_y: float) -> None:
        self.x = x
        self.feet_y = feet_y
        self.frame = 0
        self.taken = False
        self.flash = KEY_FLASH_FRAMES

    @property
    def rect(self) -> pygame.Rect:
        reach = int(KEY_PICKUP_RANGE)
        return pygame.Rect(int(self.x - reach), int(self.feet_y - reach * 2),
                           reach * 2, reach * 2)

    def update(self) -> None:
        self.frame += 1
        if self.flash > 0:
            self.flash -= 1

    def try_take(self, player) -> bool:
        """Oyuncu yeterince yakinsa alir. Alindiysa `True`."""
        if self.taken:
            return False
        if not self.rect.colliderect(player.body.rect):
            return False
        self.taken = True
        return True

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        if self.taken:
            return
        ox, oy = offset
        bob = math.sin(self.frame * 0.07) * KEY_BOB
        x = int(round(self.x)) - ox
        y = int(round(self.feet_y - 9 + bob)) - oy

        # Yeni dusen anahtar daha parlak - gozu oraya cekiyor.
        peak = 0.34 + (0.30 * self.flash / KEY_FLASH_FRAMES)
        glow = radial_glow(12, palette.color("gold"), peak=peak)
        surface.blit(glow, (x - 12, y - 12), special_flags=pygame.BLEND_RGB_ADD)

        # Anahtar: halka + sap + iki dis. Bu olcekte ayrinti degil SILUET
        # onemli - "anahtar" bir bakista okunmali.
        gold = palette.color("gold")
        dark = palette.color("earth_dark")
        pygame.draw.circle(surface, gold, (x, y - 2), 3, 1)
        surface.fill(dark, (x - 1, y + 1, 2, 6))
        surface.fill(gold, (x - 1, y + 1, 1, 6))
        surface.fill(gold, (x + 1, y + 4, 2, 1))
        surface.fill(gold, (x + 1, y + 6, 3, 1))


class LockedDoor:
    """Tilemap'e yazilan kilitli kapi. Anahtarla acilir.

    `column` tile sutunu, `rows` kapatilan satirlar. Kapi kurulusta
    **kapali** - bossa giden yol acik, cikis kapali.
    """

    __slots__ = ("column", "rows", "locked", "open_frames")

    def __init__(self, column: int, rows) -> None:
        self.column = column
        self.rows = tuple(rows)
        self.locked = True
        self.open_frames = 0

    # --- Denetim ------------------------------------------------------------
    def close(self, tilemap) -> None:
        from src.world.tilemap import SOLID
        self.locked = True
        for row in self.rows:
            tilemap.set_tile(self.column, row, SOLID)

    def unlock(self, tilemap) -> None:
        from src.world.tilemap import EMPTY
        if not self.locked:
            return
        self.locked = False
        self.open_frames = 1
        for row in self.rows:
            tilemap.set_tile(self.column, row, EMPTY)

    def update(self) -> None:
        if self.open_frames > 0:
            self.open_frames += 1

    def bumped_by(self, player, reach: float = 20.0) -> bool:
        """Oyuncu kilitli kapiya dayandi mi?

        Kapinin KENDISI zaten kati tile - oyuncu gecemiyor. Bu yalnizca
        "neden gecemiyorum" sorusunu cevaplamak icin: kapiya dayanan
        oyuncuya bir kez "kilitli, anahtar gerek" denir. Soylenmezse
        oyuncu onu siradan bir duvar sanip geri doner ve boss'u aradigini
        hic anlamaz.
        """
        if not self.locked:
            return False
        door_x = self.column * TILE_SIZE + TILE_SIZE * 0.5
        return abs(player.body.center_x - door_x) <= reach

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int],
             frame: int) -> None:
        """Kilitliyken kapinin ustunde altin bir kilit isareti.

        Kapinin KENDISI tilemap'ten cizilyor (normal duvar gibi); buradaki
        yalnizca "bu duvar acilabilir" bilgisi. Isaret olmasaydi oyuncu
        onu siradan bir duvar sanip geri donerdi - kapali yol ile kilitli
        kapi arasindaki fark tam olarak bu.
        """
        if not self.locked or not self.rows:
            return
        ox, oy = offset
        mid_row = self.rows[len(self.rows) // 2]
        x = self.column * TILE_SIZE + TILE_SIZE // 2 - ox
        y = mid_row * TILE_SIZE + TILE_SIZE // 2 - oy

        pulse = 0.20 + 0.10 * math.sin(frame * 0.06)
        glow = radial_glow(10, palette.color("gold"), peak=pulse)
        surface.blit(glow, (x - 10, y - 10), special_flags=pygame.BLEND_RGB_ADD)

        gold = palette.color("gold")
        # Asma kilit: govde + kulp.
        surface.fill(gold, (x - 3, y - 1, 7, 6))
        surface.fill(palette.color("earth_dark"), (x - 1, y + 1, 3, 2))
        pygame.draw.arc(surface, gold,
                        pygame.Rect(x - 2, y - 6, 5, 8), 0.0, math.pi, 1)
