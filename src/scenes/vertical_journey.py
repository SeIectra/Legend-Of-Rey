"""Dikey yolculuk - menuden oyuna kesintisiz gecis.

`docs/menu-ui.md` 0.3 ve 0.4. God of War 2'deki koltuktan oynanisa gecen
kamera mantigi.

**Sorun:** Menu sahnesi mahzende (derinde), Bolum 1 koyde (yuzeyde). Duz
kayma bu iki mekani baglamaz.

**Cozum:** Kamera mor alevden **yukari** cikar.

    KOY / GECE          <- Bolum 1 baslar
    toprak, kokler
    ust kaya katmani
    tas tonoz
    MOR ALEV            <- menu sahnesi

**Anlami:** Menu **gideceginiz** yer, oyun **geldiginiz** yer. Mor alev sen
daha baslamadan orada seni bekliyor. Oyuncu bunu ilk oynayista anlamaz -
B3'te alevi bulunca fark eder.

DEVAM ET ayni gecisin tersi: kamera alevden **asagi** iner, kaldigin bolume
kadar. Ne kadar ilerlediysen o kadar uzun dusersin - ilerlemeyi bedavaya
hissettiren bir gecis.

## Teknik

Tek bir uzun dikey doku yuzeyi, dort parallax katmani. Her karede yalnizca
y-ofset degisir.

**Ofset tam sayiya yuvarlanir.** Ondalik ofset piksel art dokusunu titretir -
projenin en yaygin ve en fark edilir hatasi (CLAUDE.md 9).

Hizli gecerken hafif dikey hareket bulanikligi: ayni yuzey uc kez, birer
piksel kaydirilarak, dusuk alfa ile ust uste. Ucuz ve etkili.
"""
from __future__ import annotations

import random

import pygame

from src.art import palette
from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.cinematic import CinematicScene

TOTAL_UP = int(4.5 * FPS)       # Menuden koye
BAND_HEIGHT = 300               # Bir katmanin dikey yuksekligi
MOTION_BLUR_AT = 1.6            # Bu hizin ustunde bulaniklik

# Katmanlar asagidan yukari: mahzenden yuzeye.
# (ad, taban rengi, doku rengi, yogunluk)
BANDS = (
    ("alev",   "abyss_dark",    "violet_dark",  0.05),
    ("tonoz",  "ink_soft",      "stone_darkest", 0.30),
    ("kaya",   "stone_darkest", "stone_dark",   0.45),
    ("toprak", "earth_dark",    "earth",        0.55),
    ("koy",    "abyss",         "abyss_light",  0.12),
)


class VerticalJourneyScene(CinematicScene):
    """Menu ile bolum arasindaki dikey kamera yolculugu."""

    duration_frames = TOTAL_UP

    def on_enter(self, direction: str = "up", chapter: int = 1,
                 character: str = "rey", **kwargs: object) -> None:
        super().on_enter(**kwargs)
        self.direction = direction
        self.chapter = chapter
        self.character = character

        # Ne kadar ilerlediysen o kadar uzun dusersin (docs/menu-ui.md 0.4).
        if direction == "down":
            extra = min(3.0, 0.12 * max(0, chapter - 1))
            self.duration_frames = int(TOTAL_UP * (1.0 + extra))

        self._strip = self._build_strip()
        self._last_offset = 0

    # --- Doku --------------------------------------------------------------
    def _build_strip(self) -> pygame.Surface:
        """Tek uzun dikey yuzey. Bir kez uretilir, sonra yalnizca kaydirilir."""
        height = BAND_HEIGHT * len(BANDS)
        strip = pygame.Surface((INTERNAL_WIDTH, height))
        rng = random.Random(23)

        for index, (_name, base, detail, density) in enumerate(BANDS):
            top = height - (index + 1) * BAND_HEIGHT     # 0 = en ust (koy)
            strip.fill(palette.color(base),
                       (0, top, INTERNAL_WIDTH, BAND_HEIGHT))

            # Katmanlar birbirine **gecerek** karisir - keskin sinir olmasin.
            blend = 40
            for i in range(blend):
                if top + i >= height:
                    break
                alpha_row = pygame.Surface((INTERNAL_WIDTH, 1), pygame.SRCALPHA)
                alpha_row.fill((*palette.color(base),
                                int(255 * (1.0 - i / blend))))
                strip.blit(alpha_row, (0, top + i))

            count = int(INTERNAL_WIDTH * BAND_HEIGHT * density / 220)
            for _ in range(count):
                x = rng.randrange(INTERNAL_WIDTH)
                y = top + rng.randrange(BAND_HEIGHT)
                if index == 3:        # toprak: kokler - dikey cizgiler
                    for k in range(rng.randrange(3, 9)):
                        strip.set_at((x, min(height - 1, y + k)),
                                     palette.color(detail))
                elif index == 4:      # koy: gece gokyuzu
                    strip.set_at((x, y), palette.color(
                        "bone" if rng.random() < 0.3 else "stone_light"))
                else:                 # tas: catlak ve derz
                    length = rng.randrange(2, 7)
                    for k in range(length):
                        strip.set_at((min(INTERNAL_WIDTH - 1, x + k // 3),
                                      min(height - 1, y + k)),
                                     palette.color(detail))
        self._decorate_village(strip, height)
        return strip.convert()

    def _decorate_village(self, strip: pygame.Surface, height: int) -> None:
        """Varis noktasi okunur olmali.

        Yolculuk boyunca gecilen katmanlar dokudan ibaret; **varilan yer**
        bir yer gibi gorunmeli, yoksa yolculuk "karanlikta kaydik" olur.
        Ay ve ufuk cizgisi bunu tek basina yapiyor.
        """
        band_top = height - len(BANDS) * BAND_HEIGHT
        band_top = 0                       # koy en ustteki band
        horizon = BAND_HEIGHT - 46

        # Ay - sag ust, yumusak hale.
        from src.art.glow import radial_glow
        moon_x, moon_y = INTERNAL_WIDTH - 96, band_top + 62
        halo = radial_glow(34, palette.color("stone_light"), peak=0.30)
        strip.blit(halo, (moon_x - 34, moon_y - 34),
                   special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.circle(strip, palette.color("bone"), (moon_x, moon_y), 11)
        pygame.draw.circle(strip, palette.color("stone_light"),
                           (moon_x - 3, moon_y - 2), 3)

        # Ufuk: tepeler ve koy silueti.
        rng = random.Random(31)
        x = 0
        while x < INTERNAL_WIDTH:
            width = rng.randrange(26, 62)
            top = horizon - rng.randrange(6, 26)
            pygame.draw.polygon(strip, palette.color("ink_soft"), [
                (x, horizon), (x + width // 2, top), (x + width, horizon)])
            x += width - 8
        strip.fill(palette.color("ink"),
                   (0, horizon, INTERNAL_WIDTH, BAND_HEIGHT - horizon))
        # Birkac ev - kucuk dikdortgen ve isikli pencere.
        for _ in range(7):
            hx = rng.randrange(10, INTERNAL_WIDTH - 20)
            hw, hh = rng.randrange(9, 16), rng.randrange(7, 13)
            hy = horizon - hh
            strip.fill(palette.color("earth_dark"), (hx, hy, hw, hh))
            strip.fill(palette.color("ember"), (hx + hw // 2, hy + hh // 2, 2, 2))

    # --- Cizim -------------------------------------------------------------
    def draw_cinematic(self, surface: pygame.Surface, progress: float) -> None:
        height = self._strip.get_height()
        travel = height - INTERNAL_HEIGHT

        if self.direction == "up":
            # Basta en altta (alev), sonda en ustte (koy).
            offset = travel * (1.0 - progress)
        else:
            offset = travel * progress

        # **Tam sayiya yuvarla** - ondalik ofset dokuyu titretir.
        offset_i = int(round(offset))
        speed = abs(offset_i - self._last_offset)
        self._last_offset = offset_i

        surface.blit(self._strip, (0, -offset_i))

        if speed >= MOTION_BLUR_AT:
            self._motion_blur(surface, offset_i, speed)

        self._draw_vignette(surface, progress)

    def _motion_blur(self, surface: pygame.Surface, offset: int,
                     speed: float) -> None:
        """Ayni yuzey birkac kez, birer piksel kaydirilarak, dusuk alfa ile."""
        ghost = self._strip.copy()
        ghost.set_alpha(70)
        step = max(1, int(speed) // 3)
        for i in (1, 2, 3):
            surface.blit(ghost, (0, -offset + i * step))

    def _draw_vignette(self, surface: pygame.Surface, progress: float) -> None:
        """Uclarda karartma: yolculuk karanliktan cikip karanliga girer."""
        # Yalnizca ilk ve son %12'de kararma. Ilk denemede daha genisti ve
        # yolun yarisi karanlikta geciyordu - gecilen katmanlar hic
        # gorunmuyordu.
        edge = min(progress, 1.0 - progress)
        darkness = int(255 * max(0.0, 1.0 - edge / 0.12))
        if darkness <= 0:
            return
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        veil.set_alpha(darkness)
        surface.blit(veil, (0, 0))

    # --- Gecis -------------------------------------------------------------
    def on_finished(self) -> None:
        # Bolum verisi bu gecis oynarken yuklenmis olurdu; su an Bolum 1
        # henuz yazilmadi, dovus odasina gidiyoruz.
        from src.scenes.combat_room import CombatRoomScene
        self.scenes.replace(CombatRoomScene, transition=False,
                            character=self.character)

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"yolculuk {self.direction}  bolum {self.chapter}"]
