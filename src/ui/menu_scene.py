"""Ana menu sahnesi - mor alev, zincirler, Rey ve Ardo.

`docs/menu-ui.md` 1 ve 2. On katman, arkadan one:

    1 derin karanlik    tonoz kemerleri
    2 arka duvar        tas dokusu, catlaklar
    3 sarkan zincirler  farkli fazlarda salinim
    4 toz zerrecikleri  yukari suzulur, alevin isiginda parlar
    5 mor alev + kaide  ana isik kaynagi
    6 aura              nefes gibi buyuyup kuculur
    7 karakterler       Rey ve Ardo, sirt sirta, ruzgarda
    8 zemin             islak tas, alevin yansimasi
    9 on toz            kameraya yakin, hizli - derinlik hissi
   10 vinyet            kenar karartma

Hicbiri pahali degil; 3, 4, 6, 9 tamamen kodla uretiliyor, sprite yok.

## Menu hikayeyle degisir (docs/menu-ui.md 2)

Bes asama. Oyuncu oyunu her actiginda ilerlemesini gorur:

    1 Yalniz      yeni oyun     sadece Rey, alev turuncu, kolye elinde
    2 Ilk Isik    B3 bitti      alev mora doner, arkada belirsiz bir golge
    3 Iki Kisi    B6 bitti      Ardo belirir, sirt sirta, 8 piksel mesafe
    4 Yaklasma    B16 bitti     mesafe 3 piksele iner, ruzgar azalir
    5 Ev          oyun bitti    Cemo da var, alev turuncu, ruzgar durmus

Ayni sprite'lar, farkli konum + palet. Neredeyse bedava, etkisi buyuk.
"""
from __future__ import annotations

import math
import random

import pygame

from src.art import palette
from src.art.animator import Animator
from src.art.glow import radial_glow, rim_light
from src.art.wind import shear, shear_offsets
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH

# --- Sahne yerlesimi --------------------------------------------------------
# Sol ucte bir logo ve butonlar, sag ucte iki sahne (docs/menu-ui.md 1).
# Kayit karti x 250..428 arasini kapliyor. Alev sahnenin kalbi; kartin
# arkasinda kalmamali - bu yuzden kaide kartin **saginda** duruyor.
SCENE_CENTER_X = 382           # Karakterlerin ortasi
FLOOR_Y = 240
PEDESTAL = pygame.Rect(436, 194, 28, 46)
FLAME_BASE = (450, 195)

CHAIN_COLUMNS = ((248, 70), (296, 46), (338, 86), (404, 58), (470, 36))
DUST_COUNT = 40
FRONT_DUST_COUNT = 15

AURA_PERIOD = 150          # 2.5 saniye - nefes
FLAME_FRAME_HOLD = 7       # ~8 FPS (CLAUDE.md 6)

# --- Asamalar ---------------------------------------------------------------
class Stage:
    """Bir menu asamasinin gorunumu."""

    def __init__(self, index: int, flame: str, ardo: bool, cemo: bool,
                 gap: int, wind: float, shadow: bool = False) -> None:
        self.index = index
        self.flame = flame          # "torch" (turuncu) | "violet"
        self.ardo = ardo
        self.cemo = cemo
        self.gap = gap              # Rey ile Ardo arasindaki piksel
        self.wind = wind            # Ruzgar carpani
        self.shadow = shadow        # Arkada belirsiz golge (asama 2)


STAGES = (
    Stage(1, "torch",  ardo=False, cemo=False, gap=0,  wind=1.0),
    Stage(2, "violet", ardo=False, cemo=False, gap=0,  wind=1.0, shadow=True),
    Stage(3, "violet", ardo=True,  cemo=False, gap=8,  wind=1.0),
    Stage(4, "violet", ardo=True,  cemo=False, gap=3,  wind=0.5),
    Stage(5, "torch",  ardo=True,  cemo=True,  gap=3,  wind=0.0),
)


def stage_for(save_data) -> Stage:
    """Kayittaki ilerlemeye gore asama.

    Kayit yoksa 1. asama - yeni baslayan Rey'i yalniz gorur.
    """
    if save_data is None:
        return STAGES[0]
    if getattr(save_data, "finished", False):
        return STAGES[4]
    chapter = getattr(save_data, "chapter", 1)
    if chapter > 16:
        return STAGES[3]
    if chapter > 6:
        return STAGES[2]
    if chapter > 3:
        return STAGES[1]
    return STAGES[0]


# --- Sahne ------------------------------------------------------------------
class MenuBackdrop:
    """Menunun arkasindaki canli sahne.

    Menu sahnesinden ayri tutuldu: `menu.py` butonlarin ve kayit kartinin
    mantigini tasiyor, burasi yalnizca gorunum. Ikisi bir dosyada olsaydi
    600 satiri asardi (CLAUDE.md 11).
    """

    def __init__(self, stage: Stage) -> None:
        self.stage = stage
        self.frame = 0

        self.rey = Animator("rey")
        self.rey.play("idle")
        self.ardo = Animator("ardo")
        self.ardo.play("idle")
        self.cemo = Animator("cemo")
        self.cemo.play("idle")

        # Toz: konum ve hiz bir kez secilir, sonra sabit dolasir. Her karede
        # yeniden rastgele olsaydi titrerdi.
        rng = random.Random(7)
        self.dust = [self._new_mote(rng, front=False) for _ in range(DUST_COUNT)]
        self.front_dust = [self._new_mote(rng, front=True)
                           for _ in range(FRONT_DUST_COUNT)]
        self._rng = rng

        self._aura_cache: dict[tuple, pygame.Surface] = {}
        self._vault = None       # Katman 1-2 bir kez cizilir, sonra blit
        self._vignette = None

    # --- Toz ---------------------------------------------------------------
    def _new_mote(self, rng: random.Random, front: bool) -> list[float]:
        return [
            rng.uniform(170, INTERNAL_WIDTH),
            rng.uniform(0, INTERNAL_HEIGHT),
            rng.uniform(0.10, 0.34) * (3.0 if front else 1.0),   # yukselme
            rng.uniform(0.0, math.tau),                          # salinim fazi
        ]

    def _update_dust(self, motes: list[list[float]], front: bool) -> None:
        for mote in motes:
            mote[1] -= mote[2]
            if mote[1] < -2:
                mote[0] = self._rng.uniform(170, INTERNAL_WIDTH)
                mote[1] = INTERNAL_HEIGHT + 2

    # --- Dongu -------------------------------------------------------------
    def update(self) -> None:
        self.frame += 1
        self.rey.update()
        self.ardo.update()
        self._update_dust(self.dust, front=False)
        self._update_dust(self.front_dust, front=True)

    # --- Cizim -------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        self._draw_vault(surface)
        self._draw_chains(surface)
        self._draw_dust(surface, self.dust, front=False)
        self._draw_pedestal(surface)
        aura_radius = self._draw_aura(surface)
        self._draw_flame(surface)
        self._draw_characters(surface)
        self._draw_floor(surface, aura_radius)
        self._draw_dust(surface, self.front_dust, front=True)
        self._draw_vignette(surface)

    # 1-2: derin karanlik + arka duvar --------------------------------------
    def _draw_vault(self, surface: pygame.Surface) -> None:
        if self._vault is None:
            self._vault = self._build_vault()
        surface.blit(self._vault, (0, 0))

    def _build_vault(self) -> pygame.Surface:
        """Tonoz kemerleri ve tas duvar. Bir kez uretilir."""
        layer = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        layer.fill(palette.color("abyss_dark"))
        rng = random.Random(11)

        # Arka duvar: tas siralari. Ilk denemede tam genislikte donusumlu
        # bantlardi ve tarama cizgisi gibi okunuyordu - menu metnini de
        # okunmaz yapiyordu. Simdi yalnizca ince derz cizgileri var ve
        # sol ucte bir (butonlarin oldugu yer) tamamen sakin.
        for y in range(14, FLOOR_Y, 13):
            layer.fill(palette.color("ink"), (150, y, INTERNAL_WIDTH - 150, 1))
        for x in range(150, INTERNAL_WIDTH, 34):
            for y in range(14, FLOOR_Y, 26):
                layer.fill(palette.color("ink"), (x, y, 1, 13))
        # Catlaklar - duvar duz kalmasin.
        for _ in range(26):
            x = rng.randrange(170, INTERNAL_WIDTH)
            y = rng.randrange(10, FLOOR_Y - 20)
            length = rng.randrange(4, 14)
            for i in range(length):
                layer.set_at((min(INTERNAL_WIDTH - 1, x + i // 3),
                              min(INTERNAL_HEIGHT - 1, y + i)),
                             palette.color("void"))

        # Tonoz kemerleri: ustte silik yarim daireler.
        for cx, radius in ((250, 54), (348, 66), (446, 54)):
            pygame.draw.arc(layer, palette.color("ink"),
                            pygame.Rect(cx - radius, -radius + 8,
                                        radius * 2, radius * 2),
                            0.15, math.pi - 0.15, 2)
        return layer.convert()

    # 3: sarkan zincirler ---------------------------------------------------
    def _draw_chains(self, surface: pygame.Surface) -> None:
        """Her zincir farkli fazda salinir - hepsi ayni anda sallanmasin."""
        dark = palette.color("stone_darkest")
        light = palette.color("stone_dark")
        for index, (x, length) in enumerate(CHAIN_COLUMNS):
            phase = self.frame * 0.015 + index * 1.7
            offsets = shear_offsets(length, phase, amplitude=2.4 + index * 0.3,
                                    wave_length=0.06, anchor="top")
            for y in range(length):
                # Halkalar donusumlu ton - zincir dokusu.
                colour = light if (y // 2) % 2 == 0 else dark
                surface.fill(colour, (x + offsets[y], y, 1, 1))

    # 4 ve 9: toz -----------------------------------------------------------
    def _draw_dust(self, surface: pygame.Surface, motes: list[list[float]],
                   front: bool) -> None:
        # On toz daha parlak ve daha buyuk: kameraya yakin.
        colour = palette.color("stone_light" if front else "stone_dark")
        size = 2 if front else 1
        for x, y, _speed, wobble in motes:
            drift = math.sin(self.frame * 0.02 + wobble) * 3.0
            px = int(x + drift)
            py = int(y)
            if 0 <= px < INTERNAL_WIDTH and 0 <= py < INTERNAL_HEIGHT:
                surface.fill(colour, (px, py, size, size))

    # 5: kaide --------------------------------------------------------------
    def _draw_pedestal(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("stone_dark"), PEDESTAL)
        # Ust yuzey daha aydinlik - alev oradan geliyor.
        surface.fill(palette.color("stone"),
                     (PEDESTAL.x - 3, PEDESTAL.y, PEDESTAL.width + 6, 3))
        pygame.draw.rect(surface, palette.outline(), PEDESTAL, 1)
        # Kaideyi zemine baglayan golge.
        surface.fill(palette.color("void"),
                     (PEDESTAL.x + 2, PEDESTAL.bottom, PEDESTAL.width - 4,
                      FLOOR_Y - PEDESTAL.bottom))

    # 6: aura ---------------------------------------------------------------
    def _draw_aura(self, surface: pygame.Surface) -> int:
        """Radyal isik halesi. Yaricap nefes gibi +-%12 degisir."""
        breath = math.sin(self.frame * math.tau / AURA_PERIOD)
        radius = int(46 * (1.0 + 0.12 * breath))
        colour = self._flame_colour(bright=False)

        cached = self._aura_cache.get((radius, colour))
        if cached is None:
            cached = radial_glow(radius, colour, peak=0.42)
            if len(self._aura_cache) > 32:
                self._aura_cache.clear()
            self._aura_cache[(radius, colour)] = cached
        surface.blit(cached, (FLAME_BASE[0] - radius, FLAME_BASE[1] - radius),
                     special_flags=pygame.BLEND_RGB_ADD)
        return radius

    # 5: alev ---------------------------------------------------------------
    def _flame_colour(self, bright: bool) -> palette.RGB:
        if self.stage.flame == "torch":
            return palette.color("ember_light" if bright else "ember")
        return palette.color("violet_bright" if bright else "violet")

    def _draw_flame(self, surface: pygame.Surface) -> None:
        """Alti karelik dongu, 8 FPS. Kod uretimi - sprite yok."""
        step = (self.frame // FLAME_FRAME_HOLD) % 6
        base_x, base_y = FLAME_BASE
        body = self._flame_colour(bright=False)
        core = self._flame_colour(bright=True)

        height = 24
        for i in range(height):
            t = i / height
            # Yukari dogru daralir; her kare dalga biraz kayar.
            width = max(1, int((1.0 - t) * 9 * (1.0 + 0.12 * math.sin(
                step * 1.05 + t * 5.5))))
            sway = int(round(2.2 * t * math.sin(step * 0.9 + t * 3.1)))
            y = base_y - i
            surface.fill(body, (base_x - width // 2 + sway, y, width, 1))
            if t < 0.62 and width > 2:
                inner = max(1, width // 2)
                surface.fill(core,
                             (base_x - inner // 2 + sway, y, inner, 1))

        # Kivilcimlar: alevden yukari suzulur, yukseldikce soner.
        for i in range(9):
            phase = (self.frame * 0.9 + i * 31) % 90
            if phase > 70:
                continue
            rise = phase * 0.8
            drift = math.sin(self.frame * 0.05 + i) * 4.0
            y = int(base_y - height - rise)
            x = int(base_x + drift)
            if 0 <= y < INTERNAL_HEIGHT and 0 <= x < INTERNAL_WIDTH:
                surface.fill(core if phase < 30 else body, (x, y, 1, 1))

    # 7: karakterler --------------------------------------------------------
    def _draw_characters(self, surface: pygame.Surface) -> None:
        stage = self.stage
        gap = stage.gap
        # Rey solda, one donuk; Ardo saginda, sirt sirta.
        rey_x = SCENE_CENTER_X - (gap // 2) - 10
        ardo_x = SCENE_CENTER_X + (gap // 2) + 10

        if stage.shadow:
            # Asama 2: arkada belirsiz bir golge - Ardo'nun habercisi.
            # Alfa 52 denendi: karanlik duvarda tamamen kayboluyordu.
            # Golge belirsiz olmali ama **gorunur** - habercisi oldugu sey
            # ancak gorulurse anlam tasiyor.
            self._blit_character(surface, self.ardo, ardo_x + 6, facing=1,
                                 wind=stage.wind, alpha=110, flat=True)

        if stage.ardo:
            self._blit_character(surface, self.ardo, ardo_x, facing=1,
                                 wind=stage.wind)
        # Rey daima var. Sola bakiyor: sirt sirta duruslari boyle olusuyor.
        self._blit_character(surface, self.rey, rey_x, facing=-1,
                             wind=stage.wind)

        if stage.cemo:
            # Asama 5: Cemo ikisinin arasinda. Kendi spec'i var - kucultulmus
            # Rey degil. Cocuk oranlari (buyuk kafa, kisa uzuv) ve kivircik
            # sac onu bir bakista ayiriyor.
            self._blit_character(surface, self.cemo, SCENE_CENTER_X, facing=1,
                                 wind=0.0)

    def _blit_character(self, surface: pygame.Surface, animator: Animator,
                        x: int, facing: int, wind: float,
                        alpha: int = 255, flat: bool = False,
                        scale: float = 1.0) -> None:
        image = animator.render(facing, alpha=alpha)
        if image is None:
            return
        if flat:
            from src.art.forge import silhouette
            image = silhouette(image, palette.color("ink"))
            image = image.copy()
            image.set_alpha(alpha)
        if scale != 1.0:
            size = (max(1, int(image.get_width() * scale)),
                    max(1, int(image.get_height() * scale)))
            image = pygame.transform.scale(image, size)

        if wind > 0.0:
            # Ruzgar sagdan sola: Rey'in saci ve Ardo'nun pelerini **ayni**
            # yonde dalgalanir. Kucuk detay, "birlikteler" mesaji.
            phase = self.frame * 0.055
            image = shear(image, phase, amplitude=1.7 * wind,
                          wave_length=0.30, anchor="bottom")

        pos = (x - image.get_width() // 2, FLOOR_Y - image.get_height())
        surface.blit(image, pos)

        if not flat:
            # Isik alevden geliyor: alev karakterin saginda oldugu icin
            # aydinlanan kenar da sag kenar.
            lit_side = 1 if FLAME_BASE[0] > x else -1
            rim = rim_light(image, self._flame_colour(bright=True), lit_side)
            if rim is not None:
                surface.blit(rim, pos, special_flags=pygame.BLEND_RGB_ADD)

    # 8: zemin --------------------------------------------------------------
    def _draw_floor(self, surface: pygame.Surface, aura_radius: int) -> None:
        surface.fill(palette.color("stone_darkest"),
                     (0, FLOOR_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - FLOOR_Y))
        surface.fill(palette.color("stone_dark"), (0, FLOOR_Y, INTERNAL_WIDTH, 2))

        # Islak yansima: alevin isigi zeminde titresir.
        colour = self._flame_colour(bright=False)
        flicker = 1.0 + 0.10 * math.sin(self.frame * 0.11)
        width = max(8, int(aura_radius * 0.8 * flicker))
        # Yuvarlak haleyi yassilastirip zemine yatiriyoruz: islak tasta
        # yansima boyle okunur.
        glow = radial_glow(width, colour, peak=0.22)
        pool = pygame.transform.scale(glow, (width * 2, 14))
        surface.blit(pool, (FLAME_BASE[0] - width, FLOOR_Y - 2),
                     special_flags=pygame.BLEND_RGB_ADD)

    # 10: vinyet ------------------------------------------------------------
    def _draw_vignette(self, surface: pygame.Surface) -> None:
        if self._vignette is None:
            veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT),
                                  pygame.SRCALPHA)
            for i in range(26):
                alpha = int(7 * (1.0 - i / 26))
                pygame.draw.rect(veil, (*palette.color("void"), alpha),
                                 pygame.Rect(i, i, INTERNAL_WIDTH - i * 2,
                                             INTERNAL_HEIGHT - i * 2), 1)
            self._vignette = veil.convert_alpha()
        surface.blit(self._vignette, (0, 0))
