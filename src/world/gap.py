"""Dar gecit - kimin gectigine **govde genisligi** karar verir.

`docs/yapi.md` B7: *"Tek kisilik bir aralik. Ardo gecemez, Rey gecer."*

## Neden tilemap degil

Catlagi tilemap'e kapali bir tile olarak koymak ise yaramaz: tile ya
herkesi geciriyor ya kimseyi. Kapiyi karaktere gore acmak da olmaz -
`TileMap` kimin geldigini bilmiyor ve bilmemeli.

O yuzden catlak tilemap'te **acik**, onunde duran bir bekci var. Bekci
tek soru soruyor: `girth <= clearance` mi.

## Neden `girth`, neden carpisma kutusu degil

`CharacterStats.girth` bu is icin ayri bir sayi (Rey 10, Ardo 15) ve
gerekcesi `character_stats.py`'de yazili: carpisma kutusunu karakter
basina degistirmek alti bolumun butun koridor/kenar/ziplama davranisini
etkilerdi ve Ardo baska yerlerde de takilirdi - bunu ancak elle oynayarak
fark ederdik.

## Itme, dondurma degil

Sigmayan karakter **geri itiliyor**, yerinde dondurulmuyor. Fark hisde:
donan bir karakter "oyun bozuldu" gibi okunur, geri itilen "olmuyor"
gibi. Itme yumusak (`PUSH_BACK`) ve hiz sifirlaniyor - duvara toslamanin
ayni dili.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import TILE_SIZE

# Sigmayan govde bu kadar piksel geri itiliyor. Bir kareye yayiliyor,
# yani ziplayarak zorlamak da ise yaramiyor.
PUSH_BACK = 2.0

# Catlagin kenarindaki kaya disleri: gorsel olarak "burasi dar" demek.
# Renk tek basina yeterli degil (CLAUDE.md 10) - siluet de degisiyor.
TOOTH_COUNT = 5


class NarrowGap:
    """Belirli bir sutundaki dar yarik.

    `clearance` piksel; `girth`i buyuk olan gecemez.
    """

    def __init__(self, tile_x: int, rows: range, clearance: int) -> None:
        self.tile_x = tile_x
        self.rows = rows
        self.clearance = clearance
        self.rect = pygame.Rect(tile_x * TILE_SIZE, rows.start * TILE_SIZE,
                                TILE_SIZE, len(rows) * TILE_SIZE)
        # Bir kez bile gecildi mi - sinematik tetiklemesi bunu soruyor.
        self.passed = False
        # Sigmayan biri **kac kere denedi**. Sahne bunu okuyup "sigmiyor"
        # sahnesini tetikliyor: oyuncuya soylemek yerine denemesini
        # bekliyoruz.
        self.refusals = 0

    def fits(self, girth: int) -> bool:
        return girth <= self.clearance

    def blocks(self, body, girth: int) -> bool:
        """Bu govde su an catlaga girmeye calisiyor ve sigmiyor mu?"""
        if self.fits(girth):
            return False
        return body.rect.colliderect(self.rect)

    def enforce(self, body, girth: int) -> bool:
        """Sigmayani geri iter. Itildiyse True doner."""
        if not self.blocks(body, girth):
            return False
        self.refusals += 1
        # Hangi taraftan geldiyse o tarafa geri: catlagin iki yaninda da
        # calisiyor (Ardo obur taraftan donmeye kalkarsa da).
        if body.center_x < self.rect.centerx:
            body.x = float(self.rect.left - body.width)
        else:
            body.x = float(self.rect.right)
        body.vx = 0.0
        return True

    def note_passage(self, body, girth: int) -> None:
        """Sigan biri gectiyse isaretle."""
        if not self.fits(girth):
            return
        if body.center_x > self.rect.right:
            self.passed = True

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        """Kaya disleri - yarigin dar oldugu **goruluyor**.

        Yarik tilemap'te sadece bos bir sutun; hicbir sey cizilmezse
        oyuncu neden gecemedigini anlamaz ve hatali sanir.
        """
        ox, oy = offset
        left = self.rect.left - ox
        top = self.rect.top - oy
        height = self.rect.height
        dark = palette.color("stone_darkest")
        edge = palette.color("stone_dark")

        for index in range(TOOTH_COUNT):
            ratio = index / max(1, TOOTH_COUNT - 1)
            y = top + int(ratio * (height - 3))
            # Ust ve alttakiler uzun, ortadakiler kisa: acikligin ortada
            # oldugu okunuyor.
            depth = 5 - int(abs(ratio - 0.5) * 4)
            surface.fill(dark, (left, y, depth, 3))
            surface.fill(dark, (left + TILE_SIZE - depth, y, depth, 3))
            surface.fill(edge, (left + depth - 1, y, 1, 3))
            surface.fill(edge, (left + TILE_SIZE - depth, y, 1, 3))
