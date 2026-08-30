"""Bolum 9'un ara sahnesi - "Guven".

`docs/gdd.md` 155 (romantik yay): *"B9 | Guven | Firlatma - kendini
ona birakiyorsun."*
`docs/yapi.md` 101: ayni satir.

## Romantik yayin ucuncu halkasi

    B6  bakisma        iki yabanci
    B7  el             ilk temas - biri yardim ediyor
    B8  yara sarma     kirilganlik - biri bakiyor
    B9  firlatma       **guven** - biri kontrolu birakiyor

Ilk uc an bir jestti; bu bir **mekanik**. Sahne yalnizca onu
tanitiyor, sonra oyuncu bolum boyunca kendisi yapiyor - ve romantik
yayin en guclu halkasi tam olarak bu: anlatilmiyor, oynatiliyor.

## Kelime az

Iki replik. `docs/gdd.md` 11'in kurali hala gecerli: *"Hicbir romantik
an diyalogla anlatilmaz. Hepsi ya jest ya mekanik."* Buradaki
replikler ani anlatmiyor, **mekanigi** anlatiyor - yoldas ne yapacagini
soyluyor, oyuncu kabul ediyor. Anin kendisi soylenmeyen sey.
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

GROUND_Y = 190
LEDGE_Y = 96                     # ulasilamayan cikinti
PLAYER_X = 214.0
COMPANION_X = 254.0


class TrustCinematic(StagedScene):
    """Yoldas ellerini kenetliyor, oyuncu ustune basiyor, yukari."""

    background = "void"
    wait_for_input = True

    PANELS = (
        # A: yukariya bakis. Cikinti ulasilamaz - sorun goruluyor.
        Panel(56, "yukari", wait_for_input=False, cues=(
            Cue("player", state="idle", face=1),
            Cue("companion", state="idle", face=-1),
        )),
        # B: yoldas hazirlaniyor. Replik mekanigi soyluyor.
        Panel(44, "teklif"),
        # C: kabul. Tek replik, kisa.
        Panel(40, "kabul"),
        # D: ATLAYIS. Hizlanarak yukari - `move_ease="out"` degil
        # cunku firlatilan bir govde yavaslayarak degil **hizla**
        # cikar, tepede yavaslar. Yer cekimi geri kalanini yapiyor.
        Panel(46, "firlatma", shake=2.6, wait_for_input=False, cues=(
            Cue("player", state="jump", sound="swing_heavy",
                move_to=(PLAYER_X + 22, LEDGE_Y), move_frames=38,
                move_ease="out", burst="dust", burst_count=16,
                shake=2.6),
            Cue("companion", state="attack1"),
        )),
        # E: cikintida. Asagi bakiyor - **kim attiysa ona.**
        Panel(48, "varis", wait_for_input=False, cues=(
            Cue("player", state="land", face=-1),
            Cue("companion", state="idle", face=1),
        )),
        # F: yuze kesme. Guven bir yuz ifadesi.
        Panel(44, "yuz", closeup="player", fade_in=10, fade_out=10),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.companion_key = other_character(character)
        self.ACTORS = (
            ActorSpec("player", character, PLAYER_X, GROUND_Y, facing=1,
                      scale=2),
            ActorSpec("companion", self.companion_key, COMPANION_X, GROUND_Y,
                      facing=-1, scale=2),
        )
        self.motes = MoteField(22, drift=-0.3, sway=0.8, tone="stone_dark")
        super().on_enter(**kwargs)
        self.vignette = 0.30
        self.add_light(int(COMPANION_X) - 20, GROUND_Y - 26, 60,
                       palette.color("ember_light"), peak=0.5)
        self.add_light(int(COMPANION_X) - 20, GROUND_Y - 32, 170,
                       palette.color("ember"), peak=0.17)
        self._write_dialogue()

    def _write_dialogue(self) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        played, other = self.character, self.companion_key
        beats = {
            "teklif": Line(other, "line.ch09_trust_offer_ardo"
                           if other == "ardo" else "line.ch09_trust_offer_rey"),
            "kabul": Line(played, "line.ch09_trust_accept_ardo"
                          if played == "ardo" else "line.ch09_trust_accept_rey"),
        }
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues)
            if p.name in beats else p
            for p in self.panels)

    def on_stage_panel(self, panel: Panel) -> None:
        if panel.name == "firlatma":
            # Havadayken zemin golgesi olmamali (Bolum 2'nin dersi).
            actor = self.actor("player")
            if actor is not None:
                actor.shadow = False
        elif panel.name == "varis":
            actor = self.actor("player")
            if actor is not None:
                actor.ground(LEDGE_Y)

    # --- Cizim --------------------------------------------------------------
    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_tower(surface, self.frame)

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Kenetlenen eller - firlatmanin **temas** ani.

        Bolum 7'nin birlesen elleriyle ayni dil: sprite'ta el yok, isik
        var. Aradaki fark yon - orada yatay bir cekme, burada dikey bir
        kaldirma.
        """
        if panel.name not in ("kabul", "firlatma"):
            return
        companion = self.actor("companion")
        if companion is None:
            return
        x = int(companion.x) - 16
        y = int(companion.y) - 20
        pulse = 0.65 + 0.35 * math.sin(self.frame * 0.2)
        colour = tuple(int(c * pulse) for c in palette.color("gold"))
        surface.fill(colour, (x - 3, y, 6, 2))
        surface.fill(palette.color("white_flash"), (x - 1, y, 2, 1))

    def on_finished(self) -> None:
        self.scenes.pop()


def _draw_tower(surface: pygame.Surface, frame: int) -> None:
    """Kule ici - **dikey** bir mekan.

    Yatay bolumlerin arka planlarindan farki bilincli: burada goz
    yukari bakiyor. Duvarlar daralarak yukselirken tepede bir isik
    var - "gidilecek yer orasi" bilgisi mekandan geliyor.
    """
    surface.fill(palette.color("ink"))

    # Daralan duvarlar: perspektif, kule yukselirken kapaniyor.
    wall = palette.color("stone_darkest")
    edge = palette.color("stone_dark")
    for y in range(0, INTERNAL_HEIGHT, 2):
        inset = int((INTERNAL_HEIGHT - y) * 0.16)
        surface.fill(wall, (0, y, 60 + inset, 2))
        surface.fill(wall, (INTERNAL_WIDTH - 60 - inset, y,
                            60 + inset, 2))
        surface.fill(edge, (60 + inset - 1, y, 1, 2))
        surface.fill(edge, (INTERNAL_WIDTH - 60 - inset, y, 1, 2))

    # Tepedeki isik - kulenin ustu.
    for index in range(5):
        width = 40 - index * 6
        surface.fill(palette.color("stone_dark"),
                     (INTERNAL_WIDTH // 2 - width // 2, index * 3, width, 3))

    # Ulasilamayan cikinti.
    surface.fill(palette.color("stone_dark"),
                 (int(PLAYER_X) - 10, LEDGE_Y, 74, 6))
    surface.fill(palette.color("stone"), (int(PLAYER_X) - 10, LEDGE_Y, 74, 1))

    # Zemin
    surface.fill(palette.color("ink_soft"),
                 (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
    surface.fill(palette.color("stone_dark"), (0, GROUND_Y, INTERNAL_WIDTH, 1))
