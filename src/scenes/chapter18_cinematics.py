"""Bolum 18'in ara sahneleri - oyunun sonu.

`docs/yapi.md` B18: *"Yaratik, Yanki'yi kullanarak Cemo'nun sesiyle
konusur. Rey sesi susturmayi secer - sessizlikte, yardimsiz savasir.
Kazanir. Cemo kurtulur. Gun isigi. Rey kolyeyi Cemo'ya geri takar,
Ardo arkalarinda. **Rey'in kafasi ilk kez sessiz.**"*

## Bes sahne, biri otekilerden farkli

    Inis      zindanin dibi - final bir gurultuyle degil sessizlikle acilir
    Ses       Cemo'yu duyuyorsun, ona kosuyorsun, o degil
    Ad        Cagiran aciga cikiyor - on sekiz bolumluk sorunun cevabi
    Sessizlik ★ KARAR ani. Jest secimi burada.
    Safak     kapanis: uclu son panel

Dorduncusu otekilerden farkli cunku oyuncu orada bir sey **seciyor**;
otekiler anlatiyor, o soruyor. `docs/derinlestirme.md` 3.3 jest
seciminin dort aninden sonuncusu tam olarak burasi.

## Kapanis dort bayragi okuyor

`ch15_ghost`, `ch16_lifted`, `ch16_gesture`, `ch17_tidy`. Hicbiri
kapanisi **kilitlemiyor** - degistirdikleri sey kimin nerede durdugu
ve son panelin tonu. `docs/gdd.md` 11'in kurali: *"Hicbir romantik an
diyalogla anlatilmaz."* Bayraklar da diyaloga degil **duruma**
donusuyor.

Ozellikle `ch16_gesture`: B16'da geri cekildiysen Ardo son panelde bir
adim geride duruyor. Ceza degil - iki bolum once verilmis bir cevabin
hala duruyor olmasi.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.entities.companion import other_character
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.ui import balloon, gesture
from src.ui.dialogue import Line

GROUND_Y = 196
CENTRE_X = INTERNAL_WIDTH // 2


class _Chapter18Cinematic(StagedScene):
    """Ortak zemin: zindanin dibi. Tas yok, kaya var.

    Arka plan oteki bolumlerin orgulu duvarindan bilerek farkli:
    burasi insan yapimi degil. On yedi bolum boyunca inilen sey bir
    zindandi; dip bir zindan degil, bir **yer**.
    """

    background = "void"
    wait_for_input = True

    def setup_stage(self, character: str) -> None:
        self.character = character
        self.ally = other_character(character)

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        surface.fill(palette.color("ink"))
        # Kaya katmanlari - duz degil, dalgali. Orgu yok.
        #
        # Ilk surum `void` zemin + `ink` katman kullaniyordu ve render
        # edilince neredeyse tamamen SIYAHTI: ne kaya ne figur
        # secilmiyordu. Bir ton yukari alindi; dip hala karanlik ama
        # artik bir **yer**.
        for index in range(7):
            y = 30 + index * 22
            for x in range(0, INTERNAL_WIDTH, 4):
                wave = int(math.sin(x * 0.03 + index * 1.7) * 5)
                surface.fill(palette.color("abyss_dark"), (x, y + wave, 4, 20))
                surface.fill(palette.color("abyss"), (x, y + wave, 4, 2))
        surface.fill(palette.color("abyss"),
                     (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
        surface.fill(palette.color("abyss_light"),
                     (0, GROUND_Y, INTERNAL_WIDTH, 1))


# --- 1. Inis - final sessizlikle basliyor -------------------------------------
class DescentCinematic(_Chapter18Cinematic):
    """Zindanin sonu. Dusman yok, ses yok, yalnizca dip."""

    PANELS = (
        Panel(56, "dip", wait_for_input=False, fade_in=24, cues=(
            Cue("player", state="idle", face=1),
        )),
        Panel(50, "bak", cues=(Cue("player", face=1),)),
        Panel(48, "yuz", closeup="player", fade_in=12, fade_out=16),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.setup_stage(character)
        self.ACTORS = (
            ActorSpec("player", character, CENTRE_X - 40.0, GROUND_Y,
                      facing=1, scale=2),
        )
        super().on_enter(**kwargs)
        self.motes = MoteField(20, drift=-0.06, sway=0.4, tone="abyss_light")
        self.vignette = 0.42
        self.add_light(CENTRE_X - 40, GROUND_Y - 32, 66,
                       palette.color("violet"), peak=0.36)
        self.game.music.hold("sad", 900)
        self._write()

    def _write(self) -> None:
        """Anahtarlar **duz dize** - hesaplanmis ad testten kaciyor."""
        ardo = self.character == "ardo"
        deep = ("line.ch18_ardo_deep" if ardo else "line.ch18_rey_deep")
        face = ("line.ch18_ardo_deep_face" if ardo
                else "line.ch18_rey_deep_face")
        beats = {"dip": Line(self.character, deep),
                 "yuz": Line(self.character, face)}
        self.panels = _rewrite(self.panels, beats, self.character)

    def on_finished(self) -> None:
        self.scenes.pop()


# --- 2. Ses - Cemo'yu duyuyorsun ---------------------------------------------
class VoiceCinematic(_Chapter18Cinematic):
    """Cemo'nun sesi. Kosuyorsun. O degil.

    Sahnenin isi bir **kirilma**: once umut, sonra bosluk. O yuzden
    kosma paneli hizli ve repliksiz, duran panel uzun ve replikli -
    ritim duyguyu tasiyor.
    """

    LURE_X = CENTRE_X + 96.0

    PANELS = (
        Panel(44, "duy", wait_for_input=False, fade_in=14, cues=(
            Cue("player", state="idle", face=1),
        )),
        # Kosu: kisa, repliksiz, hizli. Umut aceleci olur.
        Panel(34, "kos", wait_for_input=False, cues=(
            Cue("player", state="run", face=1,
                move_to=(CENTRE_X + 46.0, GROUND_Y), move_frames=30,
                move_ease="linear"),
        )),
        # Ve durus. Uzun, replikli.
        Panel(58, "dur", cues=(
            Cue("player", state="idle", face=1, freeze=6),
        )),
        Panel(52, "yuz", closeup="player", fade_in=10, fade_out=18),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.setup_stage(character)
        self.ACTORS = (
            ActorSpec("player", character, CENTRE_X - 90.0, GROUND_Y,
                      facing=1, scale=2),
        )
        super().on_enter(**kwargs)
        self.motes = MoteField(16, drift=-0.08, sway=0.5, tone="echo_dark")
        self.vignette = 0.40
        self.add_light(int(self.LURE_X), GROUND_Y - 26, 58,
                       palette.color("echo"), peak=0.40)
        self.game.music.hold("sad", 700)
        self.faded = 0
        self._write()

    def _write(self) -> None:
        ardo = self.character == "ardo"
        hear = ("line.ch18_ardo_hear" if ardo else "line.ch18_rey_hear")
        empty = ("line.ch18_ardo_empty" if ardo else "line.ch18_rey_empty")
        face = ("line.ch18_ardo_empty_face" if ardo
                else "line.ch18_rey_empty_face")
        beats = {"duy": Line(self.character, hear),
                 "dur": Line(self.character, empty),
                 "yuz": Line(self.character, face)}
        self.panels = _rewrite(self.panels, beats, self.character)

    def on_stage_panel(self, panel: Panel) -> None:
        if panel.name == "dur":
            # Yalan **oyuncunun gozunun onunde** dagiliyor.
            self.faded = 1
            self.burst(self.LURE_X, GROUND_Y - 14, "echo", count=20)
            self.game.play_sound("echo_close")

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Cemo'ya benzeyen sekil - **oyunun icindeki yemin ayni cizimi.**

        `Caller.Lure` ile ayni dil bilerek: oyuncu bu sekli burada
        goruyor ve arenada tekrar gordugunde ne oldugunu biliyor.
        Ogretmek icin bir ders degil, bir **hatirlatma** yetiyor.
        """
        if panel.name in ("yuz",):
            return
        ox, oy = offset
        alpha = 190
        if self.faded and panel.name == "dur":
            alpha = max(0, 190 - int(self.panel_frames * 8))
        if alpha <= 0:
            return
        rect = pygame.Rect(int(self.LURE_X) - 7 - ox,
                           int(GROUND_Y) - 30 - oy, 14, 30)
        wobble = int(math.sin(self.frame * 0.17) * 1.5)
        body = pygame.Surface(rect.size, pygame.SRCALPHA)
        body.fill((*palette.color("echo"), alpha))
        body.fill((*palette.color("echo_bright"), min(255, alpha + 50)),
                  (4, 0, 6, 7))
        surface.blit(body, (rect.x + wobble, rect.y))

    def on_finished(self) -> None:
        self.scenes.pop()


# --- 3. Ad - Cagiran aciga cikiyor -------------------------------------------
class NameCinematic(_Chapter18Cinematic):
    """On sekiz bolumluk sorunun cevabi.

    `docs/gdd.md` 1: *"...o sesler ona yardim ederken, aslinda onu
    cagiriyordur."* Bu cumle oyunun ilk satiri ve burada kapaniyor.
    """

    PANELS = (
        Panel(40, "karanlik", wait_for_input=False, fade_in=20),
        Panel(46, "yukseliyor", wait_for_input=False, cues=(
            Cue("player", state="idle", face=1, shake=2.0),
        )),
        Panel(54, "ad", cues=(
            Cue("player", face=1, flash=0.4, freeze=10, shake=4.0,
                sound="echo_open"),
        )),
        Panel(50, "yuz", closeup="player", fade_in=10, fade_out=16),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.setup_stage(character)
        self.ACTORS = (
            ActorSpec("player", character, CENTRE_X - 96.0, GROUND_Y,
                      facing=1, scale=2),
        )
        super().on_enter(**kwargs)
        self.motes = MoteField(24, drift=-0.14, sway=0.7, tone="echo_dark")
        self.vignette = 0.52
        self.add_light(CENTRE_X + 70, GROUND_Y - 60, 92,
                       palette.color("echo"), peak=0.46)
        self.game.music.hold("boss", 500)
        self.reveal = 0
        self._write()

    def _write(self) -> None:
        ardo = self.character == "ardo"
        name = ("line.ch18_ardo_name" if ardo else "line.ch18_rey_name")
        face = ("line.ch18_ardo_name_face" if ardo
                else "line.ch18_rey_name_face")
        beats = {"ad": Line(self.character, name),
                 "yuz": Line(self.character, face)}
        self.panels = _rewrite(self.panels, beats, self.character)

    def on_stage_panel(self, panel: Panel) -> None:
        if panel.name == "yukseliyor":
            self.reveal = 1

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Cagiran karanliktan **yukseliyor** - siluet, sonra govde.

        Yuz yok. On sekiz bolumdur duyulan sey bir yuz degil bir
        **ses**ti; ona bir surat vermek onu kuculturdu.
        """
        if not self.reveal or panel.name == "yuz":
            return
        ox, oy = offset
        grow = progress if panel.name == "yukseliyor" else 1.0
        height = int(120 * grow)
        if height <= 0:
            return
        cx = CENTRE_X + 70 - ox
        top = int(GROUND_Y) - height - oy

        # **Arkadan isik.** Ilk surumde siluet `void` rengiyle karanlik
        # bir zemine ciziliyordu ve hicbir sey gorunmuyordu - render
        # edilip bakilinca cikti. Cozum silueti aydinlatmak degil
        # ARKASINI aydinlatmak: yaratik hala karanlik, ama artik bir
        # seyin onunde duruyor.
        for ring in range(5, 0, -1):
            radius = height // 2 + ring * 14
            tone = ("echo_dark", "echo_dark", "echo", "echo", "echo_bright")
            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*palette.color(tone[ring - 1]),
                                      26 + ring * 4),
                               (radius, radius), radius)
            surface.blit(glow, (cx - radius, top + height // 2 - radius))

        for row in range(height):
            ratio = row / max(1, height)
            half = int(6 + 26 * ratio + math.sin(self.frame * 0.05 + row * 0.2)
                       * 2)
            surface.fill(palette.color("void"),
                         (cx - half, top + row, half * 2, 1))
        # Kenarinda titreyen Yanki isigi - onu goren sey oyuncunun
        # kendi araci.
        for step in range(10):
            angle = self.frame * 0.05 + step * math.tau / 10
            radius = 34 + int(math.sin(self.frame * 0.09 + step) * 6)
            surface.fill(palette.color("echo_dark"),
                         (cx + int(math.cos(angle) * radius),
                          int(GROUND_Y) - 60 - oy
                          + int(math.sin(angle) * radius * 0.6), 2, 2))

    def on_finished(self) -> None:
        self.scenes.pop()


# --- 4. Sessizlik ★ - KARAR ---------------------------------------------------
class SilenceCinematic(_Chapter18Cinematic):
    """Karar ani. Jest secimi - `docs/derinlestirme.md` 3.3'un dorduncusu.

    Sahne bir sey **soruyor**: sesi ne yapacaksin? Uc jest de gecerli
    ve hicbiri bolumu kaybettirmiyor - ama burada, otekilerden farkli
    olarak, secim oynanisa **doniyor**: kontrol geri gelince oyuncu
    sesi susturmak icin tusu basili tutacak.

    Yani jest bir niyet, susturma o niyetin eylemi. Ikisini ayirmak
    bilincli: "istiyorum" demek ile yapmak ayni sey degil, ve bu
    oyunun butun temasi.
    """

    PANELS = (
        Panel(46, "duruyor", wait_for_input=False, fade_in=16, cues=(
            Cue("player", state="idle", face=1),
        )),
        Panel(44, "soru", cues=(Cue("player", face=1),)),
        Panel(1, "secim", wait_for_input=False),
        Panel(56, "cevap", wait_for_input=False),
        Panel(48, "yuz", closeup="player", fade_in=10, fade_out=16),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.setup_stage(character)
        self.ACTORS = (
            ActorSpec("player", character, CENTRE_X, GROUND_Y, facing=1,
                      scale=2),
        )
        super().on_enter(**kwargs)
        self.motes = MoteField(18, drift=-0.1, sway=0.5, tone="echo_dark")
        self.vignette = 0.46
        self.add_light(CENTRE_X, GROUND_Y - 34, 78,
                       palette.color("violet"), peak=0.38)
        self.game.music.hold("sad", 700)
        self.choice = gesture.GestureChoice()
        self.picked: gesture.Gesture | None = None
        self._write()

    def _write(self) -> None:
        ardo = self.character == "ardo"
        ask = ("line.ch18_ardo_ask" if ardo else "line.ch18_rey_ask")
        face = ("line.ch18_ardo_ask_face" if ardo
                else "line.ch18_rey_ask_face")
        beats = {"duruyor": Line(self.character, ask),
                 "yuz": Line(self.character, face)}
        self.panels = _rewrite(self.panels, beats, self.character)

    @property
    def choosing(self) -> bool:
        panel = self.panel
        return panel is not None and panel.name == "secim"

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.choosing or event.type != pygame.KEYDOWN:
            return
        if self.choice.chosen is not None:
            return
        pressed = self.game.input.pressed
        if pressed(Action.LEFT) and self.choice.move(-1):
            self.game.play_sound("ui_tick")
        elif pressed(Action.RIGHT) and self.choice.move(1):
            self.game.play_sound("ui_tick")
        elif pressed(Action.CONFIRM) or pressed(Action.INTERACT):
            picked = self.choice.confirm()
            if picked is not None:
                self.picked = picked
                self.game.play_sound("ui_confirm")

    def _advance_panels(self) -> None:
        """Secim paneli oyuncuyu bekler - yalnizca ILERLEME durur.

        B16'nin ayni dersi: butun `update_cinematic`i kesmek
        parcaciklari da donduruyordu ve sahne cansiz gorunuyordu.
        """
        if self.choosing:
            self.choice.update()
            if not self.choice.done:
                return
        super()._advance_panels()

    def on_stage_panel(self, panel: Panel) -> None:
        if panel.name != "cevap":
            return
        self.game.play_sound("necklace_warm")
        self.burst(CENTRE_X, GROUND_Y - 34, "echo", count=18)

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        ox, oy = offset
        if panel.name == "secim":
            self.choice.draw(surface, CENTRE_X, GROUND_Y - 104 - oy)

    def on_finished(self) -> None:
        self.scenes.pop()


def _rewrite(panels, beats, character):
    """Panellere replik yerlestirir - uc sahnede ayni is.

    Anahtarlar cagirandan **duz dize** olarak geliyor; burada
    yalnizca yerlestiriliyor.
    """
    return tuple(
        Panel(p.frames, p.name, line=beats[p.name], cues=p.cues,
              fade_in=p.fade_in, fade_out=p.fade_out, closeup=p.closeup,
              shake=p.shake, wait_for_input=p.wait_for_input)
        if p.name in beats else p
        for p in panels)
