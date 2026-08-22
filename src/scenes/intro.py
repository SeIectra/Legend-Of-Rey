"""Ardeko Studios intro - oyunun ilk dort buçuk saniyesi.

`docs/menu-ui.md` 0.1. Profesyonel ile amator arasindaki fark bu ilk
saniyelerde goruluyor.

    0.0-0.8 sn   Tam siyah. Sessizlik.
    0.8 sn       Bir kivilcim. Tek kare beyaz flas, sonra sonen bir kor.
    0.8-2.0 sn   Kordan mor alev dogar, buyur. Isigi yayilir.
    2.0-3.5 sn   Logo, alevin isigiyla karanliktan **belirir**
    3.5-4.5 sn   Alev soner, logo bir an karanlikta kalir, kararma

**Logo fade ile gelmiyor, isikla beliriyor.** Fark ince ama onemli: fade
"bir goruntu gosteriliyor" der, isik yayilimi "orada bir sey vardi ve
simdi goruyorsun" der. Ikincisi mekan hissi kurar.

**Neden mor alev:** Logoyu oyunun gorsel imzasina bagliyor. Oyuncu B3'te
mor alevi buldugunda "bu seyi ilk acilista gormustum" der. Bedava bir bag.

**Palet muafiyeti:** Intro paletten muaf, projedeki tek istisna
(CLAUDE.md 6). Logo disaridan gelen bir marka varligi.
"""
from __future__ import annotations

import math
from pathlib import Path

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.cinematic import CinematicScene
from src.ui import text

LOGO_PATH = Path(__file__).resolve().parents[2] / "assets" / "logo" / "ardeko.png"

# Kilometre taslari - kare cinsinden (CLAUDE.md 4).
SPARK_FRAME = int(0.8 * FPS)
FLAME_END = int(2.0 * FPS)
LOGO_END = int(3.5 * FPS)
TOTAL = int(4.5 * FPS)

# Logo ustte, alev altinda - ust uste binmesinler.
LOGO_CENTRE = (INTERNAL_WIDTH // 2, 112)
FLAME_BASE = (INTERNAL_WIDTH // 2, 206)

# Logo bu kutuya sigar. Ic cozunurluk 480x270; marka varligi ekrani
# kaplamamali, nefes alani birakmali.
LOGO_BOX = (INTERNAL_WIDTH * 55 // 100, INTERNAL_HEIGHT * 42 // 100)


def _fit(image: pygame.Surface, box: tuple[int, int]) -> pygame.Surface:
    """Logoyu kutuya sigdirir, en-boy oranini korur.

    **Kucultme de gerekiyor.** Ilk surumde yalnizca buyutmeyi hesaplamistim;
    512x512'lik gercek logo `scale=1` ile oldugu gibi ciziliyor ve 480x270
    ekrani tasiyordu.

    Buyutmede tam sayi kat (piksel izgarasi korunur). Kucultmede
    `smoothscale`: kaynak piksel art degil, yuksek cozunurluklu bir marka
    varligi. CLAUDE.md 12'deki yasak **piksel art** icin - 512 pikselden
    100 piksele nearest-neighbour ile inmek logoyu tirtikli ve kirik
    gosterirdi. Intro zaten paletten muaf tutulan tek yer (CLAUDE.md 6).
    """
    box_w, box_h = box
    width, height = image.get_size()
    if width <= box_w and height <= box_h:
        factor = min(box_w // max(1, width), box_h // max(1, height))
        if factor <= 1:
            return image
        return pygame.transform.scale(image, (width * factor, height * factor))

    ratio = min(box_w / width, box_h / height)
    return pygame.transform.smoothscale(
        image, (max(1, int(width * ratio)), max(1, int(height * ratio))))


class IntroScene(CinematicScene):
    duration_frames = TOTAL

    def on_enter(self, **kwargs: object) -> None:
        super().on_enter(**kwargs)
        self.logo = self._load_logo()
        self._spark_played = False

    def update_cinematic(self) -> None:
        # Kivilcim tam SPARK_FRAME'de - `draw_cinematic`'in tek kare beyaz
        # flas ciziyle **ayni an**. `intro_hum` donguluk sesi kaldirildi
        # (Arda'nin canli oynanis geri bildirimi: sentezlenmis surekli
        # sesler rahatsiz edici).
        if not self._spark_played and self.elapsed >= SPARK_FRAME:
            self._spark_played = True
            self.game.play_sound("intro_spark")

    def _load_logo(self) -> pygame.Surface | None:
        """Marka varligi diskten gelir. Yoksa placeholder cizilir.

        Placeholder **acikca placeholder** (CLAUDE.md 12): kirmizi cerceve
        ve "LOGO YOK" yazisi. Sessizce guzel bir sey cizip birakmak, o
        seyin bir gun surume sizmasi demek.
        """
        if not LOGO_PATH.is_file():
            return None
        try:
            image = pygame.image.load(str(LOGO_PATH)).convert_alpha()
        except pygame.error:
            return None
        return _fit(image, LOGO_BOX)

    # --- Cizim --------------------------------------------------------------
    def draw_cinematic(self, surface: pygame.Surface, progress: float) -> None:
        surface.fill((0, 0, 0))
        elapsed = self.elapsed

        if elapsed < SPARK_FRAME:
            return                                  # Tam siyah, sessizlik

        if elapsed < SPARK_FRAME + 2:
            surface.fill(palette.color("white_flash"))   # Tek kare flas
            return

        light = self._light_strength(elapsed)
        self._draw_flame(surface, elapsed, light)
        self._draw_logo(surface, light, elapsed)

    def _light_strength(self, elapsed: float) -> float:
        """Alevin isik gucu 0..1. Once buyur, sonda soner."""
        if elapsed < FLAME_END:
            return min(1.0, (elapsed - SPARK_FRAME) / (FLAME_END - SPARK_FRAME))
        if elapsed < LOGO_END:
            return 1.0
        fade = (elapsed - LOGO_END) / max(1, TOTAL - LOGO_END)
        return max(0.0, 1.0 - fade)

    def _draw_flame(self, surface: pygame.Surface, elapsed: float,
                    light: float) -> None:
        if light <= 0.0:
            return
        base_x, base_y = FLAME_BASE

        radius = int(20 + 54 * light)
        glow = radial_glow(radius, palette.color("violet"), peak=0.55 * light)
        surface.blit(glow, (base_x - radius, base_y - radius),
                     special_flags=pygame.BLEND_RGB_ADD)

        height = int(4 + 26 * light)
        body = palette.color("violet")
        core = palette.color("violet_bright")
        step = int(elapsed // 7)
        for i in range(height):
            t_value = i / max(1, height)
            width = max(1, int((1.0 - t_value) * 9 * (
                1.0 + 0.14 * math.sin(step * 1.1 + t_value * 5.5))))
            sway = int(round(2.0 * t_value * math.sin(step * 0.9 + t_value * 3.0)))
            y = base_y - i
            surface.fill(body, (base_x - width // 2 + sway, y, width, 1))
            if t_value < 0.6 and width > 2:
                inner = max(1, width // 2)
                surface.fill(core, (base_x - inner // 2 + sway, y, inner, 1))

    def _draw_logo(self, surface: pygame.Surface, light: float,
                   elapsed: float) -> None:
        """Logo **isikla belirir** - fade degil.

        Karanliktan cikma hissi icin logo, alevin isik gucuyle orantili
        parlaklikta ciziliyor. Isik yayildikca gorunur hale geliyor.
        """
        if elapsed < FLAME_END * 0.75:
            return
        reveal = min(1.0, (elapsed - FLAME_END * 0.75) /
                     max(1, LOGO_END - FLAME_END * 0.75))
        strength = reveal * max(0.25, light)

        if self.logo is not None:
            image = self.logo.copy()
            image.set_alpha(int(255 * strength))
            rect = image.get_rect(center=LOGO_CENTRE)
            surface.blit(image, rect.topleft)
            return

        self._draw_logo_placeholder(surface, strength)

    def _draw_logo_placeholder(self, surface: pygame.Surface,
                               strength: float) -> None:
        """Logo dosyasi yok. **Acikca** placeholder ciz.

        assets/logo/ardeko.png konulunca burasi kendiliginden devre disi
        kalir - kod degisikligi gerekmez.
        """
        alpha = int(255 * strength)
        text.draw(surface, "ARDEKO STUDIOS", LOGO_CENTRE[0], LOGO_CENTRE[1] - 6,
                  color=palette.role("ui_text"), align="center", tracking=3,
                  alpha=alpha)
        label = "[ assets/logo/ardeko.png YOK - placeholder ]"
        text.draw(surface, label, LOGO_CENTRE[0], LOGO_CENTRE[1] + 8,
                  color=palette.color("danger_bright"), align="center",
                  alpha=alpha)
        width = text.text_width(label) + 10
        pygame.draw.rect(surface, palette.color("danger"),
                         pygame.Rect(LOGO_CENTRE[0] - width // 2, LOGO_CENTRE[1] - 12,
                                     width, 26), 1)

    # --- Gecis --------------------------------------------------------------
    def on_finished(self) -> None:
        # Intro karardiktan sonra ekran **dogrudan menuye kesmez**:
        # menunun kurulmasi introyu devraliyor (docs/menu-ui.md 0.2).
        from src.scenes.menu_reveal import MenuRevealScene
        self.scenes.replace(MenuRevealScene, transition=False)
