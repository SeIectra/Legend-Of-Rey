"""Silah izi - savurmanin yayini havada birakan seritler.

Dovus hissi katmani (CLAUDE.md 7). Vurusun **nereye gittigini** gosteren
tek gorsel ipucu simdiye kadar hitbox'in kendisiydi ve o yalnizca kutu
kipinde ciziliyordu. Iz, sprite kipinde ayni bilgiyi veriyor: kilic
nereden gecti, savurma ne kadar genisti.

## Neden ek sprite degil

4-5 karelik bir "iz" animasyonu her silah ve her savurma icin ayri
cizilmek zorunda kalirdi. Iz burada **kilicin ucunun gectigi noktalardan**
uretiliyor (`spritegen.weapon_tip`), yani her silah ve her poz icin
bedava dogru cikiyor.

## Kaybolma **kare** ile, saniye degil

Her nokta `TRAIL_LIFE_FRAMES` kare yasiyor. Zaman birimi kare (CLAUDE.md 4);
saniye tabanli bir sonme kare hizindan etkilenirdi.

## Renk yolu

Iz omru boyunca paletin uzerinde bir yol izliyor: parlak uc -> silah
rengi -> kaybolus. `particle_paths` deseninin ayni (CLAUDE.md 7'nin
"parcacik renk yolu" kurali) ama tek fark: iz **cizgi**, parcacik degil.

## Tam sayi cizim

Noktalar `int(round(...))` ile ciziliyor. Ondalik konum piksel art
dokusunu titretir - projenin en cok tekrarlanan hatasi (CLAUDE.md 9).
"""
from __future__ import annotations

import pygame

from src.art import palette

# Bir iz noktasinin omru. 10 kare = ~0.17 sn: savurmayi okutacak kadar
# uzun, "bulasik" gorunecek kadar degil.
TRAIL_LIFE_FRAMES = 10
# En fazla kac nokta tutulur. Savurma 5 sanat karesi surer, her oyun
# karesinde bir nokta eklenir - 24 fazlasiyla yeter.
TRAIL_MAX_POINTS = 24
# Iki nokta arasi en kucuk mesafe. Daha yakinlari atlaniyor: karakter
# dururken saldirirsa ayni piksele onlarca nokta yigiliyordu.
TRAIL_MIN_STEP = 1.5
# Seridin en genis yeri (piksel). Uca dogru inceliyor.
TRAIL_WIDTH = 3.0


class WeaponTrail:
    """Bir aktorun silah izi. Aktor basina bir tane."""

    __slots__ = ("points", "chain")

    def __init__(self, chain: str = "bone_pale") -> None:
        # (x, y, kalan_kare) - dunya koordinati.
        self.points: list[list[float]] = []
        self.chain = chain

    # --- Denetim ------------------------------------------------------------
    def add(self, x: float, y: float) -> None:
        """Silahin ucunun bu karedeki dunya konumunu ekler."""
        if self.points:
            px, py, _ = self.points[-1]
            if abs(x - px) + abs(y - py) < TRAIL_MIN_STEP:
                return
        self.points.append([x, y, float(TRAIL_LIFE_FRAMES)])
        if len(self.points) > TRAIL_MAX_POINTS:
            del self.points[0]

    def clear(self) -> None:
        self.points.clear()

    @property
    def active(self) -> bool:
        return bool(self.points)

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        for point in self.points:
            point[2] -= 1.0
        # Omru bitenler bastan dusuyor - liste zaten eskiden yeniye sirali.
        while self.points and self.points[0][2] <= 0.0:
            del self.points[0]

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        if len(self.points) < 2:
            return
        ox, oy = offset
        count = len(self.points)
        for index in range(count - 1):
            x1, y1, life = self.points[index]
            x2, y2, _ = self.points[index + 1]
            ratio = max(0.0, min(1.0, life / TRAIL_LIFE_FRAMES))
            # Yeni ucuna dogru hem kalinlasiyor hem parliyor: seridin
            # yonu boylece okunuyor, simetrik bir serit "hangi yone
            # savurdu?" sorusunu cevaplamiyordu.
            head = (index + 1) / count
            width = max(1, int(round(TRAIL_WIDTH * ratio * (0.35 + head))))
            step = 3 if head > 0.75 else (2 if head > 0.4 else 1)
            colour = palette.chain_color(self.chain, step)
            pygame.draw.line(surface, colour,
                             (int(round(x1)) - ox, int(round(y1)) - oy),
                             (int(round(x2)) - ox, int(round(y2)) - oy),
                             width)
