"""Bolum 10'un iki ara sahnesi - "Ayrilik" ve "Yalan".

`docs/yapi.md` B10: *"Yol ikiye ayrilir. Yalniz devam. Yanki yukselir,
yorum yapmaya baslar, ilk kez yanlis bilgi verip seni tuzaga sokar."*

## "Yalan" sahnesi **dorda** ayriliyor

Oyuncu ne yaptiysa sahne onu biliyor:

    guvendi + tuzaga dustu   -> Yanki aciklama yapiyor, ozur DEGIL
    guvendi + tuzaktan kacti -> "gordun mu, hallettin"  (sahiplenme)
    guvenmedi                -> Yanki alinmis, sogumus
    hic secmedi (nadir)      -> notr

Dort varyant pahali degil: ayni sahne, degisen tek sey uc replik.
`docs/derinlestirme.md` 2.2'nin ilkesi - *"ayni sahne, iki farkli
duygu"* - burada dorde cikiyor cunku secim ikili degil.

## Yanki ozur dilemiyor

En onemli yazim karari bu. Ozur dileyen bir Yanki "hata yapti"
demektir; ozur dilemeyen bir Yanki **niyetli** demektir. B14'un
twist'i (*"Yanki lanet degil, asagidaki seyin sesi"*) ikincisini
gerektiriyor - burada ozur dilerse oradaki aciga cikma bir surpriz
degil bir tutarsizlik olur.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.entities.companion import other_character
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.ui.dialogue import Line

GROUND_Y = 184


class _Chapter10Cinematic(StagedScene):
    background = "void"
    wait_for_input = True

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.companion_key = other_character(character)
        self.ACTORS = self.build_actors()
        super().on_enter(**kwargs)

    def build_actors(self) -> tuple[ActorSpec, ...]:
        raise NotImplementedError

    def voice(self, echo_key: str, ardo_key: str) -> Line:
        """Rey'de Yanki, Ardo'da kendi ici.

        Anahtarlar **duz dize** - f-string ile kurulani test goremiyor.
        """
        if self.character == "ardo":
            return Line("ardo", ardo_key)
        return Line("echo", echo_key)

    def on_finished(self) -> None:
        self.scenes.pop()


# --- Ara Sahne 1: "Ayrilik" -------------------------------------------------
class PartingCinematic(_Chapter10Cinematic):
    """Yol ikiye ayriliyor. Yoldas obur yoldan gidiyor.

    **Kavga yok, veda yok.** `docs/gdd.md` 11: romantik yay jestle
    anlatilir. Burada jest bir *duraksama*: yoldas gitmeden once bir
    kez donup bakiyor, sonra gidiyor.
    """

    PANELS = (
        Panel(60, "catal", wait_for_input=False, cues=(
            Cue("player", state="idle", face=1),
            Cue("companion", state="idle", face=1),
        )),
        Panel(44, "isaret"),
        # Yoldas gidiyor - ama once **duruyor ve donuyor**. O duraksama
        # butun veda.
        Panel(40, "duraksama", wait_for_input=False, cues=(
            Cue("companion", state="run", face=1,
                move_to=(360.0, GROUND_Y), move_frames=32),
            Cue("companion", delay=32, state="turn", face=-1),
        )),
        Panel(46, "bakis", cues=(
            Cue("companion", state="idle", face=-1),
        )),
        # Ve gider. Oyuncu yalniz kaliyor.
        Panel(56, "gidis", wait_for_input=False, fade_out=14, cues=(
            Cue("companion", state="run", face=1,
                move_to=(INTERNAL_WIDTH + 40.0, GROUND_Y), move_frames=48),
            Cue("player", state="idle", face=1),
        )),
        Panel(50, "yalniz", fade_in=14, cues=(
            Cue("companion", visible=False),
        )),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (
            ActorSpec("player", self.character, 180.0, GROUND_Y, facing=1,
                      scale=2),
            ActorSpec("companion", self.companion_key, 232.0, GROUND_Y,
                      facing=1, scale=2),
        )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.motes = MoteField(22, drift=-0.2, sway=0.9, tone="stone_dark")
        self.vignette = 0.32
        self.add_light(200, GROUND_Y - 30, 66,
                       palette.color("ember_light"), peak=0.46)
        self.add_light(200, GROUND_Y - 36, 190,
                       palette.color("ember"), peak=0.15)
        self.game.music.hold("sad", 720)
        played, other = self.character, self.companion_key
        beats = {
            "isaret": Line(other, "line.ch10_part_ardo"
                           if other == "ardo" else "line.ch10_part_rey"),
            "bakis": Line(played, "line.ch10_part_look_ardo"
                          if played == "ardo" else "line.ch10_part_look_rey"),
            "yalniz": self.voice("line.ch10_echo_rises",
                                 "line.ch10_trace_rises"),
        }
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues,
                  fade_in=p.fade_in, fade_out=p.fade_out)
            if p.name in beats else p
            for p in self.panels)

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_fork(surface, self.frame)


# --- Ara Sahne 2: "Yalan" ---------------------------------------------------
class LieCinematic(_Chapter10Cinematic):
    """Tuzaktan sonra. Yanki konusuyor ve **ozur dilemiyor.**"""

    PANELS = (
        Panel(50, "durus", wait_for_input=False, fade_in=12, cues=(
            Cue("player", state="idle", face=1),
        )),
        Panel(48, "yanki", shake=1.0, cues=(
            Cue("player", state="idle", flash=0.2, sound="echo_open"),
        )),
        Panel(46, "tepki", cues=(
            Cue("player", state="hurt"),
        )),
        # Yuze kesme: guvenin kirilmasi bir yuz ifadesi.
        Panel(48, "yuz", closeup="player", fade_in=10, fade_out=12),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (ActorSpec("player", self.character, 240.0, GROUND_Y,
                          facing=1, scale=2),)

    def on_enter(self, character: str = "rey", followed: bool = False,
                 ignored: bool = False, sprung: bool = False,
                 **kwargs: object) -> None:
        # Uc bayrak da **cagirandan** geliyor. Ilk surumde sahne
        # `self.scenes.stack[-2]` ile alttaki bolume el yordamiyla
        # bakiyordu - calisir ama kirilgan: sahne yigininin duzeni
        # degistigi gun sessizce yanlis varyanti oynatirdi.
        self.followed = followed
        self.ignored = ignored
        self.sprung = sprung
        super().on_enter(character=character, **kwargs)
        self.motes = MoteField(18, drift=-0.14, sway=1.1, tone="violet_dark")
        self.vignette = 0.5
        violet = self.character != "ardo"
        self.add_light(240, GROUND_Y - 30, 74,
                       palette.color("violet" if violet else "bone"),
                       peak=0.36)
        self.game.music.hold("echo" if violet else "sad", 600)
        self._write_dialogue()

    def _write_dialogue(self) -> None:
        """Dort varyant. Anahtarlar **duz dize** - gerekce modul basliginda."""
        if self.followed and self.sprung:
            said, react = "line.ch10_lie_sprung", "line.ch10_lie_sprung_react"
            ardo_said = "line.ch10_trace_sprung"
        elif self.followed:
            said, react = "line.ch10_lie_survived", "line.ch10_lie_survived_react"
            ardo_said = "line.ch10_trace_survived"
        elif self.ignored:
            said, react = "line.ch10_lie_ignored", "line.ch10_lie_ignored_react"
            ardo_said = "line.ch10_trace_ignored_after"
        else:
            said, react = "line.ch10_lie_neutral", "line.ch10_lie_neutral_react"
            ardo_said = "line.ch10_trace_neutral"
        beats = {
            "yanki": self.voice(said, ardo_said),
            "tepki": Line(self.character, react),
        }
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues,
                  fade_in=p.fade_in, fade_out=p.fade_out, closeup=p.closeup)
            if p.name in beats else p
            for p in self.panels)

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_fork(surface, self.frame, split=False)


# --- Ortak arka plan ---------------------------------------------------------
def _draw_fork(surface: pygame.Surface, frame: int, split: bool = True) -> None:
    """Yolun ikiye ayrildigi yer.

    `split=True` iken **iki agiz** ciziliyor - ayrilik bir metafor
    degil, ekranda duran bir sey. Ikinci sahnede (tuzaktan sonra) tek
    agiz: secim yapildi, geri donus yok.
    """
    surface.fill(palette.color("ink"))

    back = palette.color("stone_darkest")
    for x in range(0, INTERNAL_WIDTH, 4):
        top = 44 + int(math.sin(x * 0.023) * 12)
        surface.fill(back, (x, top, 4, GROUND_Y - top))

    if split:
        # Iki koridor agzi - ortada bir kaya sirti onlari ayiriyor.
        mid = palette.color("ink_soft")
        surface.fill(mid, (86, 96, 96, GROUND_Y - 96))
        surface.fill(mid, (298, 96, 96, GROUND_Y - 96))
        surface.fill(palette.color("stone_dark"), (196, 70, 88, GROUND_Y - 70))
        surface.fill(palette.color("stone"), (196, 70, 2, GROUND_Y - 70))
    else:
        surface.fill(palette.color("ink_soft"),
                     (150, 92, 180, GROUND_Y - 92))

    surface.fill(palette.color("ink_soft"),
                 (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
    surface.fill(palette.color("stone_dark"), (0, GROUND_Y, INTERNAL_WIDTH, 1))
