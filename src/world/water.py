"""Su seviyesi - Bolum 5'in mekanigi.

`docs/yapi.md` mekanik havuzu 3: *"Su seviyesi | B5 | Vana cevir, alan
yuksel/alcal, yuzerek gecis"*. Bulmaca: *"Suyu yukselt -> yuzerek ust
kata gec -> suyu indir -> alttaki kapiyi ac."*

## Tek duzlem, oda basina

Su bir **yatay duzlem**: `level` dunya koordinatinda bir y degeri, altinda
kalan her sey suyun icinde. Tile basina su tutmak (hucre otomati, akis)
bu bulmaca icin gereksiz karmasiklik olurdu - vana bir sayiyi
degistiriyor, o kadar. Basit oldugu icin de OKUNUR: oyuncu suyun nereye
kadar cikacagini tahmin edebiliyor.

## Seviye ANINDA degismiyor

Vana cevrilince `target` degisiyor, `level` ona **kare basina sabit hizla**
yaklasiyor. Ani siçrama hem okunmaz (oyuncu neyin degistigini goremez)
hem tehlikeli olurdu (oyuncu bir anda suyun icinde kalirdi). Yavas
yukselen su ayrica gerilim uretiyor - oyuncu yukselirken kosmak zorunda.

## Kaldirma kuvveti `gravity_scale` uzerinden

`Body` zaten `gravity_scale` tasiyor; su onu **eziyor** degil, sahne her
karede ayarliyor. Yeni bir fizik yolu acmadik - suyun disina cikan govde
kendiliginde eski davranisina donuyor.

Batma orani (`submersion`) 0..1: govdenin ne kadari suyun altinda.
Yarim batmis bir govde yarim kaldirma aliyor - esik olsaydi su yuzeyinde
titreme olurdu.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import (
    INTERNAL_HEIGHT, INTERNAL_WIDTH, TILE_SIZE, WATER_BUOYANCY,
    WATER_DRAG_X, WATER_LEVEL_SPEED, WATER_MAX_SINK_SPEED, WATER_SWIM_SPEED,
    WATER_SURFACE_WAVE,
)


class WaterState:
    """Bir odanin su seviyesi. Sahne basina bir tane."""

    __slots__ = ("level", "target", "min_level", "max_level", "frame")

    def __init__(self, level: float, min_level: float,
                 max_level: float) -> None:
        # Dunya koordinatinda y. **Kucuk y = yuksek su** (ekran yukari
        # dogru azaliyor) - bu ters sezgi kodun her yerinde tuzak, o
        # yuzden sinirlar `min_level`/`max_level` degil "en yuksek/en
        # alcak" diye dusunulmemeli: min_level SAYICA kucuk, yani suyun
        # EN YUKSEK hali.
        self.level = float(level)
        self.target = float(level)
        self.min_level = float(min_level)
        self.max_level = float(max_level)
        self.frame = 0

    # --- Sorgular -----------------------------------------------------------
    @property
    def moving(self) -> bool:
        return abs(self.target - self.level) > 0.5

    @property
    def rising(self) -> bool:
        return self.target < self.level - 0.5

    def contains(self, x: float, y: float) -> bool:
        """Bu nokta suyun altinda mi?"""
        return y >= self.level

    def submersion(self, body) -> float:
        """Govdenin ne kadari suyun altinda (0..1).

        Esik yerine oran: yarim batmis govde yarim kaldirma aliyor.
        Esik olsaydi su yuzeyinde govde her karede iceri/disari girip
        titrerdi.
        """
        if body.height <= 0:
            return 0.0
        depth = (body.y + body.height) - self.level
        return max(0.0, min(1.0, depth / body.height))

    # --- Denetim ------------------------------------------------------------
    def set_target(self, level: float) -> None:
        self.target = max(self.min_level, min(self.max_level, float(level)))

    def raise_by(self, tiles: float) -> None:
        """Suyu `tiles` tile YUKSELTIR (y azalir)."""
        self.set_target(self.target - tiles * TILE_SIZE)

    def lower_by(self, tiles: float) -> None:
        self.set_target(self.target + tiles * TILE_SIZE)

    def toggle(self) -> None:
        """Vana: su en ustteyse en alta, degilse en uste."""
        midpoint = (self.min_level + self.max_level) * 0.5
        self.set_target(self.max_level if self.target < midpoint
                        else self.min_level)

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        self.frame += 1
        if not self.moving:
            self.level = self.target
            return
        step = math.copysign(WATER_LEVEL_SPEED, self.target - self.level)
        if abs(self.target - self.level) <= WATER_LEVEL_SPEED:
            self.level = self.target
        else:
            self.level += step

    def apply(self, body, swimming_up: bool = False) -> float:
        """Govdeye suyun etkisini uygular. Batma oranini doner.

        Sahne her karede cagiriyor. Sudan cikan govde bir sonraki karede
        oran 0 aldigi icin **kendiliginden** eski davranisina donuyor -
        ayri bir "sudan cikti" yolu yok.
        """
        ratio = self.submersion(body)
        if ratio <= 0.0:
            body.gravity_scale = 1.0
            return 0.0

        # Kaldirma: yercekimi orana gore azaliyor. Tam batmis govde
        # neredeyse asili kaliyor ama SIFIR degil - sifir olsaydi oyuncu
        # suda donup kalirdi, hafif batma "yuzmek icin tusa bas" diyor.
        body.gravity_scale = 1.0 - WATER_BUOYANCY * ratio

        # Batma hizi tavani: suda dusus yavas. Yoksa derin suya giren
        # oyuncu dibe cakiliyordu.
        if body.vy > WATER_MAX_SINK_SPEED:
            body.vy = WATER_MAX_SINK_SPEED

        # Yatay surtunme: suda hareket agir.
        body.vx *= (1.0 - WATER_DRAG_X * ratio)

        if swimming_up:
            body.vy = -WATER_SWIM_SPEED
        return ratio


# --- Cizim ------------------------------------------------------------------
def draw(surface: pygame.Surface, offset: tuple[int, int],
         water: WaterState) -> None:
    """Su kutlesi + dalgali yuzey.

    Yuzeyin **uzerine** degil, altina ciziliyor ve yari saydam: icindeki
    aktorler gorunmeye devam etmeli, yoksa oyuncu suya girince kayboluyor.
    """
    ox, oy = offset
    top = int(round(water.level)) - oy
    if top >= INTERNAL_HEIGHT:
        return
    top = max(-4, top)
    depth = INTERNAL_HEIGHT - top
    if depth <= 0:
        return

    body = pygame.Surface((INTERNAL_WIDTH, depth), pygame.SRCALPHA)
    body.fill((*palette.color("abyss"), 120))
    surface.blit(body, (0, top))

    # Yuzey cizgisi dalgali - duz bir cizgi "su" degil "zemin" gibi
    # okunuyordu. Dalga tam sayiya yuvarlaniyor (CLAUDE.md 9).
    bright = palette.color("abyss_light")
    pale = palette.color("echo")
    for x in range(INTERNAL_WIDTH):
        wave = math.sin((x + water.frame * 0.6) * 0.09) * WATER_SURFACE_WAVE
        y = top + int(round(wave))
        surface.fill(bright, (x, y, 1, 1))
        if (x + water.frame // 3) % 7 == 0:
            surface.fill(pale, (x, y + 1, 1, 1))
