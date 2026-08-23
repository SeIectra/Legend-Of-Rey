"""Bolum 2'nin ara sahneleri.

`docs/bolum-02.md` Oda 1: *"Rey yariktan asagi duser, yuvarlanarak iner.
Dar bir dehliz."* Kodda bu dususu hicbir sey anlatmiyordu - Bolum 1'in
sonu dogrudan Bolum 2'ye atliyordu ve oyuncu kendini bir anda baska bir
yerde buluyordu.

## Ilk gercek `StoryScene` kullanimi

`src/scenes/story.py` yazilmisti ama **hicbir yerden cagrilmiyordu**.
DEVIR.md'nin kendi dersi: *"yazilip hic calistirilmayan kod hatasiz
gorunur, hatasiz degildir"* (tileset.py ve Boss.draw_health_bar ayni
tuzaga dusmustu). Bu dosya o altyapiyi gercek bir sahnede kullaniyor.

## Dusus asagi degil YUKARI anlatiliyor

Kamera Rey'i takip etmiyor - Rey ekranda sabit, **dunya yukari kaciyor**.
Yarigin isigi kucule kucule tepeye gidiyor, toz zerreleri yukari
suzuluyor. Dususu boyle anlatmak hem daha okunur (goz sabit bir noktada
kaliyor) hem de "kontrol sende degil" hissini veriyor - ki prologun
butun meselesi buydu.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.story import Panel, StoryScene
from src.ui.dialogue import Line

# Panel sureleri (kare). Toplam ~7 saniye - "nefes" icin yeterli, sabri
# zorlamayacak kadar kisa. Basili tutan 3x hizlanir (CinematicScene).
FALL_FRAMES = int(2.6 * FPS)
IMPACT_FRAMES = int(0.9 * FPS)
SETTLE_FRAMES = int(3.2 * FPS)

# Dususte yukari kacan toz zerresi sayisi.
DUST_COUNT = 34


class DescentCinematic(StoryScene):
    """Bolum 1 -> Bolum 2 gecisi: yariktan asagi dusus."""

    background = "void"

    PANELS = (
        Panel(FALL_FRAMES, "dusus"),
        Panel(IMPACT_FRAMES, "carpma", shake=3.0),
        Panel(SETTLE_FRAMES, "dehliz",
              lines=(Line("echo", "line.ch02_echo_fall"),)),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(**kwargs)
        self.character = character
        # Toz: (x, baslangic_y, hiz, boyut). `random` yok - deterministik
        # dagilim, ayni sahne her acilista ayni (cave_backdrop deseni).
        self.dust = tuple(
            (
                (index * 137 + 41) % INTERNAL_WIDTH,
                (index * 89) % INTERNAL_HEIGHT,
                1.6 + (index % 5) * 0.7,
                1 + (index % 3) // 2,
            )
            for index in range(DUST_COUNT)
        )

    # --- Cizim --------------------------------------------------------------
    def draw_panel(self, surface: pygame.Surface, panel: Panel,
                   progress: float) -> None:
        if panel.name == "dusus":
            self._draw_fall(surface, progress)
        elif panel.name == "carpma":
            self._draw_impact(surface, progress)
        else:
            self._draw_corridor(surface, progress)

    def _draw_fall(self, surface: pygame.Surface, progress: float) -> None:
        """Yarigin isigi kucule kucule tepeye gidiyor, toz yukari kaciyor."""
        # Isik: hem kuculuyor hem yukari cikiyor. Ikisi birlikte
        # "uzaklasiyor" demek; yalniz kuculseydi "sonuyor" olurdu.
        radius = int(46 * (1.0 - progress * 0.85))
        light_y = int(INTERNAL_HEIGHT * 0.42 - progress * 62)
        if radius > 1:
            glow = radial_glow(radius, palette.color("violet"),
                               peak=0.55 * (1.0 - progress * 0.6))
            surface.blit(glow, (INTERNAL_WIDTH // 2 - radius, light_y - radius),
                         special_flags=pygame.BLEND_RGB_ADD)

        self._draw_rising_dust(surface, speed_scale=1.0 + progress * 1.6)

        # Duvar cizgileri: yanlardan gecen dikey seritler. Hiz hissi
        # zerrelerden degil, gecen DUVARDAN geliyor.
        tone = palette.color("stone_darkest")
        for index in range(7):
            x = 6 + index * 9 if index < 4 else INTERNAL_WIDTH - 12 - (index - 4) * 9
            offset = int((self.elapsed * (5 + index * 2)) % (INTERNAL_HEIGHT + 40))
            for repeat in range(-1, 2):
                y = offset + repeat * (INTERNAL_HEIGHT + 40) - 40
                surface.fill(tone, (x, y, 1, 26))

    def _draw_impact(self, surface: pygame.Surface, progress: float) -> None:
        """Carpma - tek kare beyaz degil, hizla sonen bir toz bulutu.

        Tam ekran beyaz flas denendi ve kotu: fotosensitivite riski
        (CLAUDE.md 10) ve ucuz gorunuyor. Yerden kalkan toz ayni "darbe"
        bilgisini veriyor, gozu yormadan.
        """
        ground_y = int(INTERNAL_HEIGHT * 0.72)
        spread = 20 + progress * 130
        height = 26 * (1.0 - progress * 0.55)
        tone = palette.color("stone_dark" if progress < 0.5 else "stone_darkest")
        for index in range(18):
            t = index / 17.0
            x = int(INTERNAL_WIDTH * 0.5 + (t - 0.5) * spread)
            lift = math.sin(t * math.pi) * height
            size = 2 if abs(t - 0.5) < 0.3 else 1
            surface.fill(tone, (x, int(ground_y - lift), size, size))
        surface.fill(palette.color("stone_darkest"),
                     (0, ground_y + 2, INTERNAL_WIDTH, INTERNAL_HEIGHT))

    def _draw_corridor(self, surface: pygame.Surface, progress: float) -> None:
        """Dehliz yavasca beliriyor - karanliktan sekil cikiyor."""
        reveal = min(1.0, progress * 1.4)
        ground_y = int(INTERNAL_HEIGHT * 0.72)

        # Tavan ve zemin disaridan iceri kapaniyor: dar bir dehliz hissi.
        margin = int((1.0 - reveal) * 40)
        wall = palette.color("stone_darkest")
        surface.fill(wall, (0, 0, INTERNAL_WIDTH, 30 + margin))
        surface.fill(wall, (0, ground_y - margin, INTERNAL_WIDTH,
                            INTERNAL_HEIGHT))

        # Yukaridan sizan tek isik huzmesi - geldigi yeri hatirlatiyor.
        beam = int(28 * reveal)
        if beam > 0:
            glow = radial_glow(beam, palette.color("violet_dark"),
                               peak=0.28 * reveal)
            surface.blit(glow, (INTERNAL_WIDTH // 2 - beam, 30 - beam),
                         special_flags=pygame.BLEND_RGB_ADD)

        self._draw_rising_dust(surface, speed_scale=0.22)

    def _draw_rising_dust(self, surface: pygame.Surface,
                          speed_scale: float) -> None:
        tone = palette.color("stone_dark")
        for x, start_y, speed, size in self.dust:
            y = int(start_y - self.elapsed * speed * speed_scale) % INTERNAL_HEIGHT
            surface.fill(tone, (x, y, size, size))

    # --- Akis ---------------------------------------------------------------
    def on_panel_start(self, panel: Panel) -> None:
        if panel.name == "carpma":
            self.game.play_sound("land_hard")

    def on_finished(self) -> None:
        from src.scenes.chapter02 import Chapter02Scene
        self.scenes.replace(Chapter02Scene, transition=False,
                            character=self.character)
