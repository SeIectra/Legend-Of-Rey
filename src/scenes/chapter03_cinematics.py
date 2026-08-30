"""Bolum 3'un iki ara sahnesi - "Inis" ve "Mor".

`docs/bolum-03.md` panel panel yazili.

## Yeniden yazildi (30.08.2026)

Iki sahne de birer **daireden** ibaretti: "Inis" kuculen bir hale,
"Mor" buyuyen bir hale. Ekranda karakter yoktu, mekan yoktu, olay
yoktu - yalnizca `radial_glow` cagrilari.

Arda: *"Ara sahnelerin gorsel yazim bicimini yeni sahneleme katmani
ile, hatta daha iyisi ile guncelle."*

Ikisi de artik `StagedScene`: gercek sprite, animasyon durumlari,
parcacik, ortam zerreleri, kenar isigi. Cizim degil **sahne**.

## Ama iki sey aynen korundu

1. **"Inis"te kelime yok.** `docs/bolum-03.md`: *"Kelime yok. Sadece
   isigin kucuklugu ve karanligin buyuklugu."* Sahne sessiz kaldi;
   eklenen sey karakterin kendisi, konusma degil.

2. **"Mor" hizlandirilamiyor** (`skippable = False`). Iki saniyelik
   tam karanlik zamanlamaya bagli: hizlanirsa etkisi olmuyor. Oyuncu
   o iki saniyede *"oyun mu dondu?"* diye dusunmeli - sahnenin butun
   isi bu.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.ui.dialogue import Line

GROUND_Y = 184

# --- Ara Sahne 1: "Inis" (bolum acilisi, ~8 saniye) --------------------------
WALK_FRAMES = int(2.2 * FPS)
STAIR_FRAMES = int(2.4 * FPS)
SWALLOW_FRAMES = int(3.4 * FPS)


class DescentCinematic(StagedScene):
    """Mesaleyle inis - isik kuculur, karanlik buyur.

    *"Kelime yok. Sadece isigin kucuklugu ve karanligin buyuklugu."*
    """

    background = "void"
    wait_for_input = False

    PANELS = (
        # A: soldan yururken girer. Mesale elinde, isik genis.
        Panel(WALK_FRAMES, "giris", cues=(
            Cue("player", state="run", face=1,
                move_to=(210.0, GROUND_Y), move_frames=WALK_FRAMES - 12,
                move_ease="out"),
        )),
        # B: basamaklardan **asagi**. Sahne kayiyor, o iniyor.
        Panel(STAIR_FRAMES, "basamak", cues=(
            Cue("player", state="fall", face=1,
                move_to=(268.0, GROUND_Y + 26), move_frames=STAIR_FRAMES,
                move_ease="in"),
        )),
        # C: yutulma. Isik sonuyor, karanlik kapaniyor.
        Panel(SWALLOW_FRAMES, "yutulma", cues=(
            Cue("player", state="idle", face=1),
        )),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.ACTORS = (
            ActorSpec("player", character, 44.0, GROUND_Y, facing=1,
                      state="run", scale=2),
        )
        self.motes = MoteField(26, drift=-0.22, sway=0.9, tone="stone_dark")
        super().on_enter(**kwargs)
        self.vignette = 0.28
        self.game.music.play("explore")
        self.torch_radius = 62.0

    def update_cinematic(self) -> None:
        super().update_cinematic()
        # Mesale isigi **oyuncuyu takip ediyor** ve son panelde soner.
        # Sabit bir isik olsaydi karakter kendi isiginin disina cikardi
        # ve sahne "isigi tasiyor" demezdi.
        actor = self.actor("player")
        if actor is None:
            return
        panel = self.panel
        if panel is not None and panel.name == "yutulma":
            self.torch_radius = max(0.0, self.torch_radius - 0.42)
            self.vignette = min(0.86, self.vignette + 0.004)
        self.clear_lights()
        if self.torch_radius > 2.0:
            self.add_light(int(actor.x), int(actor.y) - 28,
                           int(self.torch_radius),
                           palette.color("ember_light"), peak=0.52)
            self.add_light(int(actor.x), int(actor.y) - 34,
                           int(self.torch_radius * 2.6),
                           palette.color("ember"), peak=0.15)

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_crypt(surface, self.frame, stairs=panel.name != "giris")

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Elde tasinan mesale - tek piksellik bir alev kumesi.

        Sprite'ta mesale yok (`animation.CHARACTERS` genel bir
        insansi); tasidigi sey burada, elinin hizasinda ciziliyor.
        Isik zaten oradan geliyor, yani kaynak gorunur oluyor.
        """
        if self.torch_radius <= 2.0:
            return
        actor = self.actor("player")
        if actor is None:
            return
        x = int(actor.x) + 10
        y = int(actor.y) - 26
        flicker = 0.6 + 0.4 * math.sin(self.frame * 0.27)
        surface.fill(palette.color("earth_dark"), (x, y + 3, 2, 7))
        height = max(1, int(5 * flicker))
        surface.fill(palette.color("ember_light"), (x, y - height, 2, height))
        surface.fill(palette.color("gold"), (x, y - height, 2, 1))

    def on_finished(self) -> None:
        from src.scenes.chapter03 import Chapter03Scene
        self.scenes.replace(Chapter03Scene, transition=False,
                            character=self.character)


# --- Ara Sahne 2: "Mor" (~10 saniye) - bolumun kalbi -------------------------
FLICKER_FRAMES = int(1.2 * FPS)
BLACKOUT_FRAMES = int(2.0 * FPS)       # tam karanlik + tam sessizlik
APPEAR_FRAMES = int(1.6 * FPS)
APPROACH_FRAMES = int(3.0 * FPS)
ROAR_FRAMES = int(2.4 * FPS)


class PurpleCinematic(StagedScene):
    """Mesale soner, iki saniye hicbir sey, sonra Mor Alev.

    **Hizlandirilamaz.** `StoryScene.skippable` bir ozellik ve
    `dialogue.done` donuyor; burada sinif duzeyinde `False` ile
    eziliyor. Iki saniyelik karanlik zamanlamaya bagli - hizlanirsa
    etkisi olmuyor.
    """

    background = "void"
    wait_for_input = False
    skippable = False

    PANELS = (
        # A: mesale titresir ve soner.
        Panel(FLICKER_FRAMES, "titreme", cues=(
            Cue("player", state="idle", face=1),
            Cue("player", delay=FLICKER_FRAMES - 14, sound="torch_light"),
        )),
        # B: **hicbir sey.** Iki saniye. Oyuncu bile gorunmuyor.
        Panel(BLACKOUT_FRAMES, "karanlik", cues=(
            Cue("player", visible=False),
        )),
        # C: uzakta bir nokta belirir.
        Panel(APPEAR_FRAMES, "beliris", cues=(
            Cue("player", visible=True, silhouette=True, state="idle"),
        )),
        # D: yaklasir. Oyuncu ona doner.
        Panel(APPROACH_FRAMES, "yaklasma", cues=(
            Cue("player", face=-1, state="turn"),
            Cue("player", delay=16, state="idle", silhouette=False),
        )),
        # E: Yanki bagirir. Sarsinti + geri cekilme.
        Panel(ROAR_FRAMES, "kukreme", shake=3.4, cues=(
            Cue("player", state="hurt", shake=3.4, flash=0.3,
                freeze=8, sound="echo_open", burst="violet",
                burst_count=16),
        )),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.ACTORS = (
            # Golge acik: bu sahnede yerde duruyor. (`shadow=False`
            # yalnizca havadaki aktorler icin - Bolum 2'nin dususu.)
            ActorSpec("player", character, 168.0, GROUND_Y, facing=1,
                      scale=2),
        )
        self.motes = MoteField(20, drift=-0.15, sway=1.2, tone="violet_dark")
        super().on_enter(**kwargs)
        self.vignette = 0.5
        self.flame_x = float(INTERNAL_WIDTH + 30)
        self.flame_radius = 0.0
        # Sessizlik bir enstruman (`docs/derinlestirme.md` 6.3): iki
        # saniyelik karanlikta muzik de kesiliyor.
        self.game.music.stop(fade_ms=600)

    def update_cinematic(self) -> None:
        super().update_cinematic()
        panel = self.panel
        name = panel.name if panel is not None else ""
        self.clear_lights()

        if name == "titreme":
            # Sonen mesale.
            fade = 1.0 - self.panel_progress
            radius = int(46 * fade)
            if radius > 2:
                self.add_light(168, GROUND_Y - 28, radius,
                               palette.color("ember"), peak=0.45 * fade)
            return
        if name == "karanlik":
            return                      # hicbir isik. Bilerek.

        # Mor Alev yaklasiyor: sagdan geliyor ve buyuyor.
        if name == "beliris":
            self.flame_radius = 4.0 + self.panel_progress * 8.0
        elif name in ("yaklasma", "kukreme"):
            self.flame_x += (250.0 - self.flame_x) * 0.024
            self.flame_radius = min(58.0, self.flame_radius + 0.42)
        self.add_light(int(self.flame_x), GROUND_Y - 40,
                       int(self.flame_radius), palette.color("violet"),
                       peak=0.55)
        if self.flame_radius > 20:
            self.add_light(int(self.flame_x), GROUND_Y - 40,
                           int(self.flame_radius * 2.4),
                           palette.color("violet_dark"), peak=0.2)

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        if panel.name == "karanlik":
            surface.fill(palette.color("void"))
            return
        _draw_crypt(surface, self.frame, stairs=False)

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Mor Alev'in govdesi - isik degil, **sey**.

        Hale onu cevreleyen atmosfer; bu onun kendisi. Ikisi ayri
        cizilmezse alev bir isik lekesi gibi okunuyor ve "orada bir
        sey var" bilgisi kaybolıyor.
        """
        if panel.name in ("titreme", "karanlik") or self.flame_radius < 3:
            return
        x = int(self.flame_x)
        y = GROUND_Y - 40
        for index in range(7):
            phase = self.frame * (0.13 + index * 0.021) + index * 1.3
            height = int((5 - abs(index - 3)) * 2.6
                         * (0.6 + 0.4 * math.sin(phase)))
            if height <= 0:
                continue
            tone = "violet_bright" if abs(index - 3) <= 1 else "violet"
            surface.fill(palette.color(tone),
                         (x - 6 + index * 2, y - height, 2, height))
        surface.fill(palette.color("white_flash"), (x - 1, y - 2, 2, 2))

    def on_finished(self) -> None:
        # `push` ile acildi (Chapter03Scene altta dondurulmus bekliyor) -
        # `pop` onu kaldigi yerden aynen surduruyor.
        self.scenes.pop()


# --- Ortak arka plan ---------------------------------------------------------
def _draw_crypt(surface: pygame.Surface, frame: int,
                stairs: bool = False) -> None:
    """Mesale Mahzeni - tonozlu tavan, tas duvar, istege bagli basamak.

    Bolum 3'un mekani: insan yapimi ve eski. Bolum 7/8'in dogal kaya
    oyugundan farkli olmali, yoksa butun zindan tek bir odaya benziyor.
    """
    surface.fill(palette.color("ink"))

    # Tonoz: tekrarlanan kemerler. Bir magara degil bir **yapi**.
    arch_colour = palette.color("stone_darkest")
    for start in range(-20, INTERNAL_WIDTH + 40, 60):
        for x in range(start, start + 60, 3):
            t = (x - start) / 60.0
            top = int(26 + math.sin(t * math.pi) * -18) + 18
            surface.fill(arch_colour, (x, 0, 3, max(0, top)))

    # Duvar: yatay tas siralari, kaydirmalı.
    wall = palette.color("stone_darkest")
    edge = palette.color("stone_dark")
    for index, row in enumerate(range(48, GROUND_Y, 11)):
        surface.fill(wall, (0, row, INTERNAL_WIDTH, 9))
        surface.fill(edge, (0, row, INTERNAL_WIDTH, 1))
        offset = 14 if index % 2 else 0
        for x in range(offset, INTERNAL_WIDTH, 28):
            surface.fill(edge, (x, row, 1, 9))

    if stairs:
        # Sagda asagi inen basamaklar - "iniyoruz" bilgisinin sekli.
        for step in range(6):
            x = 250 + step * 18
            y = GROUND_Y + step * 5
            surface.fill(palette.color("stone_dark"),
                         (x, y, 20, INTERNAL_HEIGHT - y))
            surface.fill(palette.color("stone"), (x, y, 20, 1))

    surface.fill(palette.color("ink_soft"),
                 (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
    surface.fill(palette.color("stone_dark"), (0, GROUND_Y, INTERNAL_WIDTH, 1))


CINEMATIC_DURATION_HINT = int(6.0 * FPS)
