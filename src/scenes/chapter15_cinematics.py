"""Bolum 15'in kapanis sahnesi - "Gectin".

`docs/yapi.md` B15: *"Tamamen dovussuz gecilebilir - ve daha iyi odul
verir."*

## Iki varyant, tek sahne

Sahne oyuncunun **nasil** gectigini biliyor:

    hayalet   hic uyandirmadan, hic oldurmeden
    normal    biri uyandi ya da biri oldu

Ikisinde de suclama yok. Fark bir puan degil bir **ton**: hayalet
gecen oyuncuya sessizlik bir beceri gibi geri donuyor, oteki icin
bolum yalnizca bitiyor.

Bolum 14 Yanki'yi elinden aldi; bu bolum onsuz gecilebildigini
gosteriyor. O yuzden kapanisin isi bir kutlama degil bir **fark
etme**: Rey ilk kez kendi basina bir sey yapti.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.ui.dialogue import Line

GROUND_Y = 186


class PassedCinematic(StagedScene):
    """Suru arkada kaldi. Uyanmadilar - ya da uyandilar."""

    background = "void"
    wait_for_input = True

    PANELS = (
        Panel(46, "durus", wait_for_input=False, fade_in=14, cues=(
            Cue("player", state="idle", face=1),
        )),
        Panel(48, "arkana_bak", cues=(
            Cue("player", state="turn", face=-1),
        )),
        Panel(50, "sessizlik", cues=(
            Cue("player", state="idle", face=-1),
        )),
        Panel(48, "yuz", closeup="player", fade_in=10, fade_out=14),
    )

    def on_enter(self, character: str = "rey", ghost: bool = False,
                 **kwargs: object) -> None:
        self.character = character
        # **Cagirandan** geliyor. Sahnenin `self.scenes.stack[-2]` ile
        # alttaki bolume el yordamiyla bakmasi calisir ama kirilgan -
        # ayni ders B10'da yazildi.
        self.ghost = ghost
        self.ACTORS = (ActorSpec("player", character, 220.0, GROUND_Y,
                                 facing=1, scale=2),)
        super().on_enter(**kwargs)
        self.motes = MoteField(14, drift=-0.1, sway=0.6, tone="stone_dark")
        self.vignette = 0.44
        self.add_light(220, GROUND_Y - 30, 56,
                       palette.color("violet" if character != "ardo"
                                     else "bone"), peak=0.26)
        self.game.music.hold("sad", 700)
        self._write()

    def _write(self) -> None:
        """Iki varyant - anahtarlar **duz dize**.

        `key + "_ardo"` gibi hesaplanmis bir ad `tests/test_lang.py`
        tarafindan gorulmuyor ve "olu anahtar" diye raporlaniyor;
        projede bu tuzaga uc kez dusuldu.
        """
        ardo = self.character == "ardo"
        if self.ghost:
            look = ("line.ch15_ardo_ghost" if ardo
                    else "line.ch15_rey_ghost")
            face = ("line.ch15_ardo_ghost_face" if ardo
                    else "line.ch15_rey_ghost_face")
        else:
            look = ("line.ch15_ardo_woke" if ardo
                    else "line.ch15_rey_woke")
            face = ("line.ch15_ardo_woke_face" if ardo
                    else "line.ch15_rey_woke_face")
        beats = {
            "sessizlik": Line(self.character, look),
            "yuz": Line(self.character, face),
        }
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues,
                  fade_in=p.fade_in, fade_out=p.fade_out, closeup=p.closeup,
                  wait_for_input=p.wait_for_input)
            if p.name in beats else p
            for p in self.panels)

    def on_finished(self) -> None:
        self.scenes.pop()

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Arkada **uyuyan sinirler**.

        Suru ekranda degil ama birakildigi yer gorunuyor: geride
        kalan koridorda birkac kambur golge. Uyandirmadan gecen
        oyuncu icin bu bir zafer isareti; uyandiran icin bir
        hatirlatma. Ayni goruntu, iki anlam.
        """
        surface.fill(palette.color("ink"))
        for y in range(36, GROUND_Y, 13):
            surface.fill(palette.color("stone_darkest"),
                         (0, y, INTERNAL_WIDTH, 10))
            for x in range((y // 13 % 2) * 16, INTERNAL_WIDTH, 32):
                surface.fill(palette.color("ink_soft"), (x, y, 2, 10))

        # Geride kalan koridor ve icindeki kambur siluetler.
        surface.fill(palette.color("void"), (0, 96, 150, GROUND_Y - 96))
        for index in range(3):
            x = 22 + index * 42
            breath = int(math.sin(self.frame * 0.03 + index) * 1.5)
            surface.fill(palette.color("stone_darkest"),
                         (x, GROUND_Y - 12 + breath, 20, 12))

        surface.fill(palette.color("ink_soft"),
                     (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
        surface.fill(palette.color("stone_dark"),
                     (0, GROUND_Y, INTERNAL_WIDTH, 1))
