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

## Rey nihayet ekranda (30.08.2026)

Yukaridaki paragraf *"Rey ekranda sabit"* diyordu ama **Rey hic
cizilmiyordu.** Sahne bir isik, biraz toz ve gecen duvar
cizgilerinden ibaretti; dusen kimse yoktu.

Arda: *"Ara sahnelerin gorsel yazim bicimini yeni sahneleme katmani
ile guncelle."* Sahne artik `StagedScene`: Rey gercek sprite'iyla,
`fall` durumunda, carpmada `land` ve hitstop ile. Cizim iyi olan
kismini (uzaklasan isik, hiz cizgileri, toz bulutu) aynen koruyor -
eksik olan tek sey karakterdi.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.ui.dialogue import Line

# Panel sureleri (kare). Toplam ~7 saniye - "nefes" icin yeterli, sabri
# zorlamayacak kadar kisa. Basili tutan 3x hizlanir (CinematicScene).
FALL_FRAMES = int(2.6 * FPS)
IMPACT_FRAMES = int(0.9 * FPS)
SETTLE_FRAMES = int(3.2 * FPS)

# Dususte yukari kacan toz zerresi sayisi.
DUST_COUNT = 34


class DescentCinematic(StagedScene):
    """Bolum 1 -> Bolum 2 gecisi: yariktan asagi dusus."""

    background = "void"

    # Rey ekranin ortasinda, biraz ust yarida: altinda inecegi yer
    # gorunsun. Zemin `GROUND_Y`'de ve carpma orada oluyor.
    FALL_X = INTERNAL_WIDTH * 0.5
    FALL_Y = INTERNAL_HEIGHT * 0.46
    GROUND_Y = INTERNAL_HEIGHT * 0.72

    PANELS = (
        Panel(FALL_FRAMES, "dusus", cues=(
            Cue("player", state="fall", face=1),
        )),
        # Carpma: `land` + hitstop + toz. `CLAUDE.md` 7'nin uclu senkronu -
        # sarsinti, durus ve parcacik tek cagridan.
        Panel(IMPACT_FRAMES, "carpma", shake=3.0, cues=(
            Cue("player", state="land", freeze=7, shake=3.0,
                burst="dust", burst_count=16, sound="land_hard"),
        )),
        Panel(SETTLE_FRAMES, "dehliz",
              lines=(Line("echo", "line.ch02_echo_fall"),), cues=(
                  Cue("player", state="idle", delay=20),
              )),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.ACTORS = (
            # 2x: dusen bir govde 32 pikselde bir leke; sinematikte
            # okunmali. Ayni gerekce Bolum 7'nin "El" sahnesinde.
            # `shadow=False`: havada. Carpmada `ground()` geri aciyor.
            ActorSpec("player", character, self.FALL_X, self.FALL_Y,
                      facing=1, state="fall", scale=2, shadow=False),
        )
        # Toz artik ortak katmandan - `_draw_rising_dust`in yerini
        # aliyor ama YALNIZCA dusus/dehliz icin; carpma bulutu kendi
        # cizimi (o bir olay, ortam degil).
        self.motes = MoteField(DUST_COUNT, drift=-1.4, sway=0.4,
                               tone="stone_dark")
        super().on_enter(**kwargs)
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
    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        surface.fill(palette.color("void"))
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



    # --- Akis ---------------------------------------------------------------
    def on_stage_panel(self, panel: Panel) -> None:
        """Carpmada Rey **zemine** konuyor.

        Dusus panelinde havada duruyor (dunya yukari kaciyor, o sabit);
        carpma aninda ayaklari yere degmeli, yoksa toz bulutu onun
        altindan degil ortasindan cikar.
        """
        actor = self.actor("player")
        if actor is None:
            return
        if panel.name in ("carpma", "dehliz"):
            actor.ground(self.GROUND_Y)
        # Zerreler dehlizde neredeyse duruyor - dusus bitti.
        if panel.name == "dehliz" and self.motes is not None:
            self.motes.drift = -0.18

    def on_finished(self) -> None:
        from src.scenes.chapter02 import Chapter02Scene
        self.scenes.replace(Chapter02Scene, transition=False,
                            character=self.character)
