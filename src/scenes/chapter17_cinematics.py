"""Bolum 17'nin kapanis sahnesi - "Tutulan Kapi".

`docs/yapi.md` B17: *"Camdan/parmakliktan birbirini gorursunuz ama
dokunamazsiniz. Romantik an: Mekanik olarak **birbirine bagimli
olmak**. Anlatim degil, oynanis."*

## Sahnenin isi anlatmak DEGIL, gorunur kilmak

Belge acikca "anlatim degil oynanis" diyor ve bu baglayici. O yuzden
burada bir aciklama yok: oyuncu zirveye vardiginda zaten bes kat
boyunca birini plakada birakmis, ve son kapiyi da oteki tutuyor.

Sahnenin yaptigi tek sey **kadraji genisletmek**: o ana kadar kamera
kimi oynuyorsan onu takip ediyordu; burada geri cekilip ikisini bir
arada gosteriyor - biri kapida, oteki cikista, aralarinda parmaklik.
Ayni goruntu, ama artik ikisi de kadrajda.

## Kim nerede duruyor

Oynanan karakter **cikista** (sol saft), oteki **plakada** (sag
saft). Bu bir tercih degil bulmacanin sonucu: cikis solda ve onunu
acan plaka sagda. Sahne yalnizca oldugu yeri gosteriyor.

Ve `other_character()` sayesinde kimin nerede oldugu oynanan
karakterden turuyor - hicbir yerde "Ardo" diye sabit yazmiyor
(`docs/gdd.md` 3 kanonu).
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.entities.companion import other_character
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.ui import balloon
from src.ui.dialogue import Line

# 178 ile render edildi: figurlerin altinda 92 piksel bos zemin
# kaliyordu ve kadraj bosalmis gorunuyordu. 196 ikisini alt
# ucte oturtuyor.
GROUND_Y = 196

# Parmaklik ekranin ortasinda - oyunun icindeki bolmeyle ayni yerde.
BARS_X = INTERNAL_WIDTH // 2
# 22 ile cubuklar ince kaliyordu; 28 parmakligi bir **engel**
# gibi gosteriyor - ki oyunun icinde de oyle.
BARS_WIDTH = 28

# Iki figur parmakligin iki yaninda, **esit** uzaklikta. Esitlik
# kadrajin kendisinde: biri one cikarilsaydi sahne "kim onemli"
# sorusunu sorardi, oysa bolumun cumlesi bagimlilik.
LEFT_X = BARS_X - 54.0
RIGHT_X = BARS_X + 54.0


class HeldDoorCinematic(StagedScene):
    """Biri kapiyi tutuyor, oteki cikiyor. Aralarinda parmaklik."""

    background = "void"
    wait_for_input = True

    PANELS = (
        Panel(48, "genis", wait_for_input=False, fade_in=16, cues=(
            Cue("player", state="idle", face=-1),
            Cue("ally", state="idle", face=1),
        )),
        # Ikisi de parmakliga dogru bir adim atiyor - ve orada
        # duruyorlar. Dokunma YOK; belge acikca "dokunamazsiniz" diyor
        # ve o cumleyi bir kucaklamayla bozmak bolumun butun mekanigini
        # yalanlardi.
        Panel(52, "yaklas", cues=(
            Cue("player", move_to=(LEFT_X + 16.0, GROUND_Y), move_frames=26,
                move_ease="out"),
            Cue("ally", move_to=(RIGHT_X - 16.0, GROUND_Y), move_frames=26,
                move_ease="out", delay=6),
        )),
        Panel(46, "el", cues=(
            Cue("player", face=1),
            Cue("ally", face=-1),
        )),
        Panel(50, "yuz", closeup="player", fade_in=10, fade_out=16),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.ally = other_character(character)
        self.ACTORS = (
            ActorSpec("player", character, LEFT_X, GROUND_Y, facing=-1,
                      scale=2),
            ActorSpec("ally", self.ally, RIGHT_X, GROUND_Y, facing=1,
                      scale=2),
        )
        super().on_enter(**kwargs)
        self.motes = MoteField(14, drift=-0.12, sway=0.5, tone="stone_dark")
        self.vignette = 0.28
        self.add_light(int(LEFT_X), GROUND_Y - 30, 70,
                       palette.color("violet"), peak=0.34)
        self.add_light(int(RIGHT_X), GROUND_Y - 30, 70,
                       palette.color("bone"), peak=0.30)
        self.game.music.hold("sad", 800)
        self._write()

    def _write(self) -> None:
        """Anahtarlar **duz dize** - hesaplanmis ad testten kaciyor."""
        ardo = self.character == "ardo"
        wide = ("line.ch17_ardo_held" if ardo else "line.ch17_rey_held")
        face = ("line.ch17_ardo_held_face" if ardo
                else "line.ch17_rey_held_face")
        beats = {
            "genis": Line(self.character, wide),
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

    # --- Cizim --------------------------------------------------------------
    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Kulenin zirvesi: tas, ve ortada parmaklik."""
        surface.fill(palette.color("ink"))
        for y in range(24, GROUND_Y, 14):
            surface.fill(palette.color("stone_dark"),
                         (0, y, INTERNAL_WIDTH, 11))
            for x in range((y // 14 % 2) * 18, INTERNAL_WIDTH, 36):
                surface.fill(palette.color("stone_darkest"), (x, y, 2, 11))

        surface.fill(palette.color("stone_darkest"),
                     (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
        surface.fill(palette.color("stone"),
                     (0, GROUND_Y, INTERNAL_WIDTH, 1))

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Parmaklik iki figurun **onunden** geciyor.

        Arka plana cizilseydi figurler onunde durur ve engel gibi
        okunmazdi. Onde oldugu icin ikisinin arasindan geciyor: goruyor
        ama dokunamiyorlar.
        """
        ox, oy = offset
        left = BARS_X - BARS_WIDTH // 2 - ox
        top = -oy
        height = INTERNAL_HEIGHT

        # Cerceve.
        surface.fill(palette.color("stone_darkest"),
                     (left, top, BARS_WIDTH, height))
        # Dikey cubuklar - aralarindan arka plan goruluyor.
        for index in range(4):
            surface.fill(palette.color("ink"),
                         (left + 3 + index * 7, top, 4, height))
        # Yatay kusaklar.
        for row in range(0, INTERNAL_HEIGHT, 22):
            surface.fill(palette.color("stone"),
                         (left, row - oy, BARS_WIDTH, 1))

        if panel.name != "el":
            return
        # Iki taraftan birer el parmakliga degiyor - **birbirine
        # degil**. Iki ayri balon, ortada bulusmuyorlar; belgenin
        # "dokunamazsiniz" cumlesi goruntude de duruyor.
        pulse = 0.5 + 0.5 * math.sin(self.frame * 0.1)
        alpha = int(150 + 105 * pulse)
        balloon.draw(surface, "hand", int(LEFT_X + 26) - ox,
                     int(GROUND_Y) - 34 - oy, frame=self.frame,
                     colour=palette.color("violet_bright"), alpha=alpha)
        balloon.draw(surface, "hand", int(RIGHT_X - 26) - ox,
                     int(GROUND_Y) - 34 - oy, frame=self.frame,
                     colour=palette.color("bone"), alpha=alpha)
