"""Bolum 8'in iki ara sahnesi - "Ates Basi" ve "Fisilti".

`docs/yapi.md` B8: *"Ates, iki siluet. Rey kolyeyi cevirir, Ardo
omzundaki yarayi sarar, Rey uzanir."*
`docs/gdd.md` 154 (romantik yay): *"B8 | Kirilganlik | Yara sarma"*.
`docs/derinlestirme.md` 150: *"B7 (el tutma), B8 (yara sarma), B16
(kurtarma), B18 (final) - dort an yeter."*

## Kirilganlik - B7'nin tersi

Bolum 7'de uzanan el **yardim** ediyordu: biri asagida, oteki cekiyor.
Burada uzanan el **bakim**: biri yarali, oteki sariyor. Ayni jest, ters
guc iliskisi - ve romantik yayin bir sonraki halkasi tam olarak bu.

Sahne yine sessiz baslamiyor: B6'da tanistilar, artik konusuyorlar.
Ama az konusuyorlar; anlatan sey hala jest.

## Yanki ilk kez Ardo hakkinda konusuyor

`docs/gdd.md` 134: *"Yanki ilk kez Ardo hakkinda konusur"*, `yapi.md`
B8: *"Rey rahatsiz olur."* Bolum 6'nin sessizligi
(`chapter06_cinematics.py`'de korunan satir) buraya kadardi.

**Bu sahne Ardo oynanirken FARKLI.** Ardo'nun Yanki'si yok; onun
karsiligi Iz Surme ve o gecmisi okuyor. Ayni beat, oteki duyu: Ardo
Rey'in izini goruyor ve gordugu sey onu rahatsiz ediyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.entities.companion import other_character
from src.scenes.staging import ActorSpec, Cue, StagedScene
from src.scenes.story import Panel
from src.ui.dialogue import Line

GROUND_Y = 182
FIRE_X = 240
# Iki figur atesin iki yaninda - **karsilikli**, yan yana degil.
# Yan yana oturmak bir yolculuk arkadasligi; karsilikli oturmak bir
# konusma. `docs/gdd.md` 154 burada bir konusma istiyor.
LEFT_X = 186.0
RIGHT_X = 296.0


class _FiresideBase(StagedScene):
    """Ortak: ates isigi, iki figur, sicak vinyet."""

    background = "void"
    wait_for_input = True

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.companion_key = other_character(character)
        self.ACTORS = self.build_actors()
        super().on_enter(**kwargs)
        self.vignette = 0.30
        # Ates: dar sicak cekirdek + genis zayif ortam. Tek isik
        # kaynagi ve sahnenin adi.
        self.add_light(FIRE_X, GROUND_Y - 14, 62,
                       palette.color("ember_light"), peak=0.58)
        self.add_light(FIRE_X, GROUND_Y - 22, 180,
                       palette.color("ember"), peak=0.17)

    def build_actors(self) -> tuple[ActorSpec, ...]:
        raise NotImplementedError

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_hollow(surface)

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Ates **isiktan SONRA** ciziliyor.

        Arka planda cizildiginde uzerine kendi eklemeli halesi biniyordu
        ve alev beyaza doyuyordu - turuncu bir ates degil, kucuk beyaz
        bir kume gorunuyordu. Isik kaynagi kendi isiginin altinda
        kalmamali.
        """
        _draw_fire(surface, self.frame)

    def on_finished(self) -> None:
        self.scenes.pop()


# --- Ara Sahne 1: "Ates Basi" ★ ---------------------------------------------
class FiresideCinematic(_FiresideBase):
    """Yara sarma, kolye, uzanan el - ve rezonans dersi."""

    PANELS = (
        # A: iki siluet, ates. Kimse konusmuyor.
        Panel(70, "otururlar", wait_for_input=False, cues=(
            Cue("player", state="idle", face=1),
            Cue("other", state="idle", face=-1),
        )),
        # B: yara. Yoldas omzunu tutuyor.
        Panel(50, "yara", cues=(
            Cue("other", state="hurt", sound="player_hurt"),
        )),
        # C: uzanma - **oyuncu** kalkip ona gidiyor.
        Panel(48, "uzanma", wait_for_input=False, cues=(
            Cue("player", state="run", face=1,
                move_to=(RIGHT_X - 40, GROUND_Y), move_frames=40,
                move_ease="out"),
            Cue("player", delay=40, state="idle"),
        )),
        # D: sarma. Tek ses, tek parlama - dokunus.
        Panel(56, "sarma", cues=(
            Cue("other", state="idle", sound="item_pickup",
                burst="spark", burst_count=10),
            Cue("player", flash=0.18),
        )),
        # E: kolye. Rey'in aliskanligi (`docs/yapi.md` B4'te de var).
        Panel(52, "kolye"),
        # F-G: rezonans dersi. Ogreten taraf **yoldas**.
        Panel(46, "ders"),
        Panel(46, "ders_cevap"),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (
            ActorSpec("player", self.character, LEFT_X, GROUND_Y,
                      facing=1, scale=2),
            ActorSpec("other", self.companion_key, RIGHT_X, GROUND_Y,
                      facing=-1, scale=2),
        )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        # `Raze` - Arda: *"cok nadir duygusal kisimlar icin Raze."*
        # Bolum 7'nin "El" sahnesinden sonraki ikinci ve son kullanim.
        self.game.music.hold("emotional", 900)
        self._write_dialogue()

    def _write_dialogue(self) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        played, other = self.character, self.companion_key
        if self.character == "ardo":
            beats = {
                "yara": Line(other, "line.ch08_fire_rey_wound"),
                "kolye": Line(played, "line.ch08_fire_ardo_necklace"),
                "ders": Line(played, "line.ch08_fire_ardo_teach"),
                "ders_cevap": Line(other, "line.ch08_fire_rey_learn"),
            }
        else:
            beats = {
                "yara": Line(other, "line.ch08_fire_ardo_wound"),
                "kolye": Line(played, "line.ch08_fire_rey_necklace"),
                "ders": Line(other, "line.ch08_fire_ardo_teach"),
                "ders_cevap": Line(played, "line.ch08_fire_rey_learn"),
            }
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues)
            if p.name in beats else p
            for p in self.panels)

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Kolye - Rey'in gogsunde, cevrildiginde parliyor.

        Sprite'a cizilecek kadar buyuk degil (`CLAUDE.md` 6: detay
        portrede). Isikla anlatiliyor, `chapter07`'nin birlesen elleri
        gibi: az piksel, cok anlam.
        """
        super().draw_stage_foreground(surface, panel, progress, offset)
        if panel.name != "kolye":
            return
        rey = self.actor("player" if self.character != "ardo" else "other")
        if rey is None:
            return
        pulse = 0.55 + 0.45 * math.sin(self.frame * 0.15)
        colour = tuple(int(c * pulse) for c in palette.color("echo_bright"))
        x = int(rey.x)
        y = int(rey.y) - 34
        surface.fill(colour, (x - 1, y, 3, 3))
        surface.fill(palette.color("white_flash"), (x, y + 1, 1, 1))


# --- Ara Sahne 2: "Fisilti" -------------------------------------------------
class WhisperCinematic(_FiresideBase):
    """Yanki ilk kez yoldas hakkinda konusuyor. Oyuncu rahatsiz olur.

    Ardo oynanirken **ayni beat, oteki duyu**: onun Yanki'si yok, Iz
    Surme'si var - Rey'in izini goruyor ve gordugu sey rahatsiz edici.
    """

    PANELS = (
        Panel(52, "durus", wait_for_input=False, cues=(
            Cue("player", state="idle", face=1),
        )),
        Panel(46, "fisilti", shake=1.2, cues=(
            Cue("player", state="idle", flash=0.22, sound="echo_open"),
        )),
        Panel(46, "tepki", cues=(
            Cue("player", state="hurt"),
        )),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        # Yoldas sahnede **yok**: fisilti onun arkasindan geliyor ve
        # rahatsizligin kaynagi tam olarak bu.
        return (ActorSpec("player", self.character, 240.0, GROUND_Y,
                          facing=1, scale=2),)

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.clear_lights()
        violet = self.character != "ardo"
        # Yanki mor/camgobegi, Iz Surme kemik beyazi - iki duyu, iki renk.
        self.add_light(240, GROUND_Y - 30, 70,
                       palette.color("violet" if violet else "bone"),
                       peak=0.34)
        self.vignette = 0.52
        self.game.music.hold("echo" if violet else "sad", 600)
        self._write_dialogue()

    def _write_dialogue(self) -> None:
        if self.character == "ardo":
            beats = {
                "fisilti": Line("ardo", "line.ch08_trace_ardo"),
                "tepki": Line("ardo", "line.ch08_trace_ardo_react"),
            }
        else:
            beats = {
                "fisilti": Line("echo", "line.ch08_echo_ardo"),
                "tepki": Line("rey", "line.ch08_echo_rey_react"),
            }
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues)
            if p.name in beats else p
            for p in self.panels)

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_hollow(surface)          # ates yok - burasi baska bir oda

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Tabani **cagirmiyor**: bu odada ates yok."""


# --- Ortak arka plan --------------------------------------------------------
def _draw_hollow(surface: pygame.Surface) -> None:
    """Kaya oyugu - kucuk, kapali, korunakli.

    Bir dinlenme yeri **dar** olmali. Genis bir oda "burada bir sey
    olacak" der; kapali bir oyuk "burada duruluyor" der.
    """
    surface.fill(palette.color("ink_soft"))
    # Tavan kemeri - iki yandan inen egri.
    arch = palette.color("stone_dark")
    for x in range(0, INTERNAL_WIDTH, 4):
        offset = abs(x - INTERNAL_WIDTH * 0.5) / (INTERNAL_WIDTH * 0.5)
        top = int(30 + offset * offset * 70)
        surface.fill(arch, (x, 0, 4, top))
    # Arka duvar dokusu - **seyrek ve kesikli**. Ilk surumde her 12
    # pikselde tam genislikte bir cizgi vardi ve sahne cizgili kagit
    # gibi okunuyordu; doku arka planda kalmali, one cikmamali.
    for index, row in enumerate(range(104, GROUND_Y, 18)):
        start = 24 if index % 2 else 96
        surface.fill(palette.color("stone_darkest"),
                     (start, row, INTERNAL_WIDTH - start - 40, 1))
    # Zemin
    surface.fill(palette.color("ink"),
                 (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
    surface.fill(palette.color("stone_dark"), (0, GROUND_Y, INTERNAL_WIDTH, 1))


def _draw_fire(surface: pygame.Surface, frame: int) -> None:
    """Kamp atesi - bolumun adi.

    Alevler **duzensiz**: her sutun kendi hizinda titriyor. Hepsi ayni
    fazda olsaydi bir alev degil bir zil sesi gibi okunurdu.
    """
    base_y = GROUND_Y
    # Odun yigini
    surface.fill(palette.color("earth_dark"), (FIRE_X - 15, base_y - 4, 30, 5))
    surface.fill(palette.color("earth"), (FIRE_X - 12, base_y - 4, 24, 1))
    surface.fill(palette.color("ink"), (FIRE_X - 17, base_y - 1, 34, 2))

    # Alevler: **kenardan ortaya isiniyor**. Ilk surumde ortadaki sutun
    # `gold`du ve alev kucuk beyaz bir kume gibi okunuyordu - ates
    # turuncudur, ucu saridir.
    for index in range(11):
        distance = abs(index - 5)
        phase = frame * (0.15 + index * 0.027) + index * 1.7
        height = int((6 - distance) * 3.4 * (0.6 + 0.4 * math.sin(phase)))
        if height <= 0:
            continue
        x = FIRE_X - 11 + index * 2
        # Govde turuncu, yalnizca en ustteki iki piksel sari.
        surface.fill(palette.color("ember" if distance > 2 else "ember_light"),
                     (x, base_y - 4 - height, 2, height))
        if distance <= 1 and height > 4:
            surface.fill(palette.color("gold"), (x, base_y - 4 - height, 2, 2))

    # Kivilcimlar - atesin uzerinde, yavas yukselen birkac nokta.
    for index in range(4):
        phase = (frame * 0.9 + index * 37) % 90
        y = base_y - 10 - int(phase * 0.42)
        x = FIRE_X - 6 + int(math.sin(phase * 0.11 + index) * 7) + index * 3
        if phase < 80:
            surface.fill(palette.color("gold" if index % 2 else "ember_light"),
                         (x, y, 1, 1))
