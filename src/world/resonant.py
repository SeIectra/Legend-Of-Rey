"""Rezonansa tepki veren dunya nesneleri.

`docs/yapi.md` mekanik havuzu 5: *"Sesle kristal kir, can cal, uzaktaki
kapiyi ac."* Ucu de burada tek bir tabandan turuyor - `ResonantObject`
yalnizca "vuruldum" diyor, ne oldugu alt sinifin isi.

Uc nesne, uc farkli is:

    Crystal  kiriliyor ve **yok oluyor** - yolu aciyor
    Latch    ulasilamaz bir yerde, kapiyi aciyor
    Bell     caliyor ve **yerinde kaliyor** - sirasi hatirlaniyor

`Bell` Bolum 8'de bilerek yazilmamisti: `CLAUDE.md` 3 sirasi gelmemis
bolum icerigini yasakliyor ve B9'un sira bulmacasi tasarlanmadan bir
can sinifi yazmak tahmin uzerine kurmak olurdu. Sirasi geldi
(30.08.2026) ve taban sinif oldugu gibi ise yaradi - dogru sinir
oradaymis.

## Neden `pickups.py`'ye eklenmedi

`Chest` gibi seyler **dokunmayla** calisiyor: oyuncunun govdesi
carpiyor. Bunlar **uzaktan** calisiyor ve tetikleyicileri bir govde
degil bir halka. Ayni dosyaya koymak iki farkli etkilesim modelini
karistirirdi.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE

# Kristalin kirilma animasyonu (kare).
SHATTER_FRAMES = 24
# Mandalin acilma animasyonu.
LATCH_FRAMES = 30
# Canin calma suresi - sallanma ve ses bu kadar surer.
RING_FRAMES = 46


class ResonantObject:
    """Rezonans halkasinin vurabilecegi her sey."""

    def __init__(self, tile_x: int, tile_y: int,
                 width: int = 1, height: int = 1) -> None:
        self.rect = pygame.Rect(tile_x * TILE_SIZE, tile_y * TILE_SIZE,
                                width * TILE_SIZE, height * TILE_SIZE)
        self.triggered = False
        self.frames = 0

    @property
    def done(self) -> bool:
        return self.triggered and self.frames <= 0

    def strike(self) -> bool:
        """Halka vurdu. Ilk kez vuruluyorsa True."""
        if self.triggered:
            return False
        self.triggered = True
        self.frames = self.duration
        return True

    duration = SHATTER_FRAMES

    def update(self) -> None:
        if self.frames > 0:
            self.frames -= 1

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        raise NotImplementedError


class Crystal(ResonantObject):
    """Ses kristali - kirilinca yolu aciyor.

    Tilemap'te kati bir sutun olarak duruyor; kirilinca sahne o
    sutunu bosaltiyor (`chapter08.py`). Kristalin kendisi tilemap'i
    bilmiyor - dunya nesnesi kendi kendini kaldirmiyor, sahne
    kaldiriyor. Ayni ayrim `plate.PlateGate`'te de var.
    """

    duration = SHATTER_FRAMES

    def __init__(self, tile_x: int, tile_y: int, height: int = 2) -> None:
        super().__init__(tile_x, tile_y, 1, height)
        self.shards: list[tuple[float, float, float, float]] = []

    def strike(self) -> bool:
        if not super().strike():
            return False
        # Parcalar disari savruluyor - `ParticleField` degil, cunku
        # bunlar sahnenin parcacik butcesini yemeden yalnizca 24 kare
        # yasayan bir avuc kare.
        for index in range(10):
            angle = index * math.tau / 10
            self.shards.append((float(self.rect.centerx),
                                float(self.rect.centery),
                                math.cos(angle) * 1.6,
                                math.sin(angle) * 1.6 - 0.6))
        return True

    def update(self) -> None:
        super().update()
        moved = []
        for x, y, vx, vy in self.shards:
            moved.append((x + vx, y + vy, vx * 0.94, vy * 0.94 + 0.16))
        self.shards = moved

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset
        if self.done:
            return
        if not self.triggered:
            self._draw_body(surface, ox, oy)
            return
        fade = self.frames / max(1, self.duration)
        colour = tuple(int(c * fade) for c in palette.color("echo_bright"))
        for x, y, _vx, _vy in self.shards:
            surface.fill(colour, (int(x) - ox, int(y) - oy, 2, 2))

    def _draw_body(self, surface: pygame.Surface, ox: int, oy: int) -> None:
        """Kristal govdesi - **sivri**, kutu degil.

        Siluet testi (`CLAUDE.md` 6): tek renge indiginde ne oldugu
        anlasilmali. Bir dikdortgen "kutu" okunur; asagi dogru daralan
        bir bicim "kristal" okunur.
        """
        left = self.rect.x - ox
        top = self.rect.y - oy
        height = self.rect.height
        for row in range(height):
            inset = int(abs(row - height * 0.35) * 0.28)
            width = max(2, TILE_SIZE - inset * 2)
            tone = "echo" if row % 3 else "echo_bright"
            surface.fill(palette.color(tone),
                         (left + inset, top + row, width, 1))
        # Kontur - paletin en koyu 2. rengi (CLAUDE.md 6).
        surface.fill(palette.color("ink"), (left, top, TILE_SIZE, 1))
        surface.fill(palette.color("ink"), (left, top + height - 1,
                                            TILE_SIZE, 1))


class Latch(ResonantObject):
    """Uzaktaki kapinin mandali - ses varinca aciliyor.

    Kristalden farki: mandal **ulasilamaz** bir yerde duruyor. Oyuncu
    oraya yuruyemez, yalnizca sesi gonderebilir. Mekanigin butun
    noktasi bu - elle yapilabilen bir sey icin sese gerek olmazdi.
    """

    duration = LATCH_FRAMES

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset
        left = self.rect.x - ox
        top = self.rect.y - oy
        # Halka + dil. Acilinca dil dusuyor.
        drop = 0 if not self.triggered else int(
            (1.0 - self.frames / max(1, self.duration)) * 5)
        surface.fill(palette.color("earth_dark"),
                     (left + 3, top + 2, TILE_SIZE - 6, 4))
        surface.fill(palette.color("ember" if self.triggered else "stone"),
                     (left + 6, top + 6 + drop, 4, 6))
        if not self.triggered:
            # Titresim isareti: mandalin **ses** bekledigi okunsun.
            surface.fill(palette.color("echo"), (left + 2, top, 2, 2))
            surface.fill(palette.color("echo"),
                         (left + TILE_SIZE - 4, top, 2, 2))


class Bell(ResonantObject):
    """Can - **calindigi SIRA hatirlaniyor.**

    `docs/yapi.md` B9: *"Rezonans ile uc cani dogru sirada calmak. Sira
    ipucu duvardaki freskte."*

    Kristalden farki bir sey **yikmamasi**: kristal kirilip yok oluyor,
    can caliyor ve yerinde duruyor. Yanlis sira geldiginde hepsi
    sifirlaniyor ve yeniden calinabiliyor - bir bulmaca geri
    alinabilir olmali, yoksa oyuncu bolumu bastan oynamak zorunda
    kalir.

    Taban sinif Bolum 8'de (`Crystal`, `Latch`) yazilmisti; can o zaman
    **bilerek** yazilmadi: `CLAUDE.md` 3 sirasi gelmemis bolum
    icerigini yasakliyor ve bir sira bulmacasi tasarlanmadan `Bell`
    yazmak tahmin uzerine kurmak olurdu. Sirasi geldi.
    """

    duration = RING_FRAMES

    def __init__(self, tile_x: int, tile_y: int, index: int,
                 height: int = 2) -> None:
        super().__init__(tile_x, tile_y, 1, height)
        # Freskteki numarasi - dogru sirayi bu belirliyor.
        self.index = index

    def reset(self) -> None:
        """Yanlis sira - can yeniden calinabilir hale geliyor."""
        self.triggered = False
        self.frames = 0

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset
        x = self.rect.x - ox
        y = self.rect.y - oy
        # Askı
        surface.fill(palette.color("earth_dark"), (x + 6, y, 4, 3))
        # Govde: asagi dogru genisleyen bir cerceve - siluet testi
        # (`CLAUDE.md` 6) tek renkte "can" demeli, "kutu" degil.
        swing = 0
        if self.triggered and self.frames > 0:
            # Calarken sallaniyor. Genlik sonuyor - bir can vurulup
            # birakilir, surekli sallanmaz.
            fade = self.frames / max(1, self.duration)
            swing = int(math.sin(self.frames * 0.55) * 2 * fade)
        # "gold"/"ember" birer RENK. `brass` bir golge ZINCIRI ve
        # `palette.color()` onu tanimaz - projede bu tuzaga uc kez
        # dusuldu (`steel`, `brass`).
        tone = "gold" if self.triggered else "ember"
        for row in range(3, self.rect.height - 2):
            spread = min(5, row // 2)
            surface.fill(palette.color(tone),
                         (x + 5 - spread + swing, y + row,
                          6 + spread * 2, 1))
        surface.fill(palette.color("ink"),
                    (x + 3 + swing, y + self.rect.height - 2, 10, 1))
        # Tokmak
        surface.fill(palette.color("earth_dark"),
                     (x + 7 + swing, y + self.rect.height - 2, 2, 2))
