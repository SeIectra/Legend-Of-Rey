"""Bolum 14'un uc ara sahnesi - oyunun donus noktasi.

`docs/yapi.md` B14: *"Rey anlar: **Yanki lanet degil, asagidaki seyin
sesi.** Hep yardim ediyordu cunku onu cagiriyordu."*

## "Kaynak" sahnesi bu oyunun en onemli ani

On uc bolumdur oyuncu bir sesi dinledi. Ses ona yol gosterdi, duvar
ardini gosterdi, bazen yalan soyledi, ama hep **onun kafasindaydi**.

Sahnenin tek isi o cumleyi bozmak: ses disaridan geliyor.

Bunu bir metin soylemiyor - **isik soyluyor.** On uc bolumdur Yanki
Rey'in etrafindan yayilan bir vinyetti; burada ayni mor asagidan,
onun ONUNDEN geliyor. Oyuncu Yanki'yi aciyor ve isik **cevap
veriyor**. Anlatimin tamami bir isik kaynaginin yer degistirmesi.

Sahne **atlanamaz** (`skippable=False`). Bolum 3'un "Mor"u ve Bolum
13'un "Kafes"inden sonra bunu yapan ucuncu sahne - ve gerekce en
guclu burada: gecen sey bir bilgi degil, oyuncunun on uc bolumluk
iliskisinin yeniden tanimlanmasi.

## Ardo'da ayni sahne, baska cumle

Ardo ses duymuyor, **iz okuyor**. Onun icin donus noktasi sudur:
izler dogal degil, **birakilmis**. On uc bolumdur takip ettigi yol
onun icin dosenmis. Ayni dehset, onun dilinde.
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


class _Chapter14Cinematic(StagedScene):
    background = "void"
    wait_for_input = True

    def on_enter(self, character: str = "rey", on_done=None,
                 **kwargs: object) -> None:
        self.character = character
        # Sahne bitince cagrilacak. Bolum donus noktasini buradan
        # tetikliyor - sahne "bitti" demeyi bilir, bolumun ne yapacagini
        # bilmez. Ters kurgu (sahne bolume el atmasi) B10'da denendi ve
        # kirilgan cikti.
        self._on_done = on_done
        self.ACTORS = self.build_actors()
        super().on_enter(**kwargs)

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (ActorSpec("player", self.character, 200.0, GROUND_Y,
                          facing=1, scale=2),)

    def voice(self, echo_key: str, ardo_key: str) -> Line:
        """Anahtarlar **duz dize** - hesaplanani test goremiyor."""
        if self.character == "ardo":
            return Line("ardo", ardo_key)
        return Line("echo", echo_key)

    def _write(self, beats: dict[str, Line]) -> None:
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues,
                  fade_in=p.fade_in, fade_out=p.fade_out, closeup=p.closeup,
                  shake=p.shake, wait_for_input=p.wait_for_input)
            if p.name in beats else p
            for p in self.panels)

    def on_finished(self) -> None:
        if self._on_done is not None:
            self._on_done()
        self.scenes.pop()


# --- Ara Sahne 1: "Kaynak" ★★ -------------------------------------------------
class SourceCinematic(_Chapter14Cinematic):
    """Ses disaridan geliyor. **Atlanamaz.**"""

    skippable = False

    PANELS = (
        Panel(52, "durus", wait_for_input=False, fade_in=18, cues=(
            Cue("player", state="idle", face=1),
        )),
        # Yanki aciliyor - on uc bolumdur oldugu gibi.
        Panel(50, "acilis", cues=(
            Cue("player", state="idle", sound="echo_open", flash=0.15),
        )),
        # Ve **cevap geliyor.** Bu panelin isi tek bir sey: isigin
        # yerinin degistigini gostermek.
        Panel(56, "cevap", shake=1.2, cues=(
            Cue("player", state="hurt", flash=0.35, shake=2.0,
                sound="echo_answer_truth"),
        )),
        # Geri cekiliyor. Kacacak yer yok ama beden yine de deniyor.
        Panel(46, "geri", wait_for_input=False, cues=(
            Cue("player", state="dodge", face=1,
                move_to=(150.0, GROUND_Y), move_frames=22),
            Cue("player", delay=22, state="idle", face=1),
        )),
        # Yuze kesme. Anlama ani - ve sessiz.
        Panel(60, "yuz", closeup="player", fade_in=12),
        Panel(54, "kabul", fade_out=16, cues=(
            Cue("player", state="idle", face=1, burst="violet",
                burst_count=18, sound="necklace_conflict"),
        )),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.motes = MoteField(26, drift=-0.22, sway=1.1, tone="violet_dark")
        self.vignette = 0.55
        violet = character != "ardo"
        # ★ **Iki isik, ve anlatim ikisinin yerinde.**
        #
        # Ilki oyuncunun etrafinda - on uc bolumdur Yanki'nin oldugu
        # yer. Ikincisi ONUNDE ve daha guclu: sesin gercek kaynagi.
        # Sahne boyunca hicbir replik "ses disaridan geliyor" demiyor;
        # ikinci isik soyluyor.
        self.add_light(200, GROUND_Y - 30, 52,
                       palette.color("violet" if violet else "bone"),
                       peak=0.24)
        self.add_light(400, GROUND_Y - 40, 130,
                       palette.color("violet_bright" if violet else "echo"),
                       peak=0.62)
        self.game.music.hold("echo" if violet else "sad", 1100)
        self._write({
            "acilis": Line(character, "line.ch14_cine_open"
                           if violet else "line.ch14_cine_open_ardo"),
            "cevap": self.voice("line.ch14_echo_answer",
                                "line.ch14_trace_answer"),
            "geri": Line(character, "line.ch14_cine_back"
                         if violet else "line.ch14_cine_back_ardo"),
            "kabul": Line(character, "line.ch14_cine_accept"
                          if violet else "line.ch14_cine_accept_ardo"),
        })

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        # Panel adina gore **yarik aciliyor**: ilk panellerde koridor,
        # "cevap"tan sonra dipsiz bir agiz. Mekan degismiyor, oyuncunun
        # gordugu degisiyor.
        opened = panel.name in ("cevap", "geri", "yuz", "kabul")
        _draw_deep(surface, self.frame, opened)


# --- Ara Sahne 2: "Arena" -----------------------------------------------------
class ArenaCinematic(_Chapter14Cinematic):
    """Kaynak'in odasi. Boss girisi.

    Zindanci'nin girisi **fenerle** yapiliyordu (once isik, sonra
    tasiyan). Burada tersi: once **ses**, sonra sesi cikaran. Iki boss
    da karanliktan cikiyor ama biri getirdigi isikla, oteki aldigiyla.
    """

    PANELS = (
        Panel(48, "esik", wait_for_input=False, fade_in=16, cues=(
            Cue("player", state="run", face=1,
                move_to=(180.0, GROUND_Y), move_frames=28),
            Cue("player", delay=28, state="idle"),
            Cue("kaynak", visible=True, silhouette=True, alpha=0),
        )),
        Panel(52, "ses", shake=1.0, cues=(
            Cue("player", state="idle", face=1, sound="echo_loop"),
            Cue("kaynak", alpha=90, silhouette=True),
        )),
        Panel(54, "govde", shake=1.6, cues=(
            Cue("kaynak", alpha=255, silhouette=False, state="idle",
                flash=0.3, shake=2.2, sound="rift_open"),
        )),
        Panel(50, "yuz", closeup="kaynak", fade_in=10, fade_out=12),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (
            ActorSpec("player", self.character, 130.0, GROUND_Y, facing=1,
                      scale=2),
            # Golgesi YOK ve depth daha uzakta: yerde durmuyor.
            ActorSpec("kaynak", "source", 380.0, GROUND_Y - 24, facing=-1,
                      scale=2, shadow=False, depth=0.9),
        )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.motes = MoteField(28, drift=-0.26, sway=1.3, tone="violet_dark")
        self.vignette = 0.6
        self.add_light(380, GROUND_Y - 60, 96,
                       palette.color("violet_bright"), peak=0.5)
        self.game.music.hold("boss", 1000)
        self._write({
            "ses": self.voice("line.ch14_echo_arena",
                              "line.ch14_trace_arena"),
            "govde": Line(character, "line.ch14_rey_arena"
                          if character != "ardo"
                          else "line.ch14_ardo_arena"),
        })

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_deep(surface, self.frame, True)


# --- Ara Sahne 3: "Olmedi" ----------------------------------------------------
class AfterCinematic(_Chapter14Cinematic):
    """Boss dustu - ama olmedi.

    `docs/yapi.md` B18: *"Yaratik, Yanki'yi kullanarak Cemo'nun sesiyle
    konusur."* Yani bu sey final bolumunde geri geliyor; burada
    yenilen bir surettir.

    Bu ayrim bolumun sonunu bir zafer degil bir **bilgi** yapiyor ve
    B15'in sebebi oluyor: Yanki'yi kapali oynamak artik bir secim
    degil zorunluluk.
    """

    PANELS = (
        Panel(46, "dagilma", wait_for_input=False, fade_in=12, cues=(
            Cue("player", state="idle", face=1, burst="echo",
                burst_count=20, sound="echo_close"),
        )),
        Panel(50, "sessizlik", cues=(
            Cue("player", state="idle", face=1),
        )),
        # Ve yeniden konusuyor. Yenilen sey oradaydi degil, buradaydi.
        Panel(52, "yine", shake=1.4, cues=(
            Cue("player", state="hurt", flash=0.3, shake=1.8,
                sound="echo_answer_partial"),
        )),
        Panel(50, "karar", closeup="player", fade_in=10, fade_out=16),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.motes = MoteField(20, drift=-0.2, sway=1.0, tone="violet_dark")
        self.vignette = 0.52
        self.add_light(240, GROUND_Y - 30, 60,
                       palette.color("violet" if character != "ardo"
                                     else "bone"), peak=0.3)
        self.game.music.hold("sad", 900)
        self._write({
            "sessizlik": Line(character, "line.ch14_rey_quiet"
                              if character != "ardo"
                              else "line.ch14_ardo_quiet"),
            "yine": self.voice("line.ch14_echo_again",
                               "line.ch14_trace_again"),
            "karar": Line(character, "line.ch14_rey_decide"
                          if character != "ardo"
                          else "line.ch14_ardo_decide"),
        })

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_deep(surface, self.frame, True)


# --- Ortak arka plan -----------------------------------------------------------
def _draw_deep(surface: pygame.Surface, frame: int, opened: bool) -> None:
    """Derin zindan - Katman 3'un mekani.

    Katman 1 curume (yesil, organik), Katman 2 demir (gri, insan
    yapimi). Katman 3 **ne ikisi**: tas hala orada ama aralarindan
    mor bir sey siziyor. Zindan burada bitiyor ve baska bir sey
    basliyor.

    `opened` yarigin acilip acilmadigi: sahnenin ilk panellerinde
    duvar, "cevap"tan sonra dipsiz bir agiz. Mekan degismiyor -
    oyuncunun gordugu degisiyor.
    """
    surface.fill(palette.color("void"))

    back = palette.color("stone_darkest")
    for y in range(30, GROUND_Y, 12):
        surface.fill(back, (0, y, INTERNAL_WIDTH, 9))
        for x in range((y // 12 % 2) * 18, INTERNAL_WIDTH, 36):
            surface.fill(palette.color("ink"), (x, y, 2, 9))

    # Tasin aralarindan sizan mor - Katman 3'un imzasi.
    for index in range(7):
        x = 34 + index * 62
        wave = math.sin(frame * 0.03 + index * 1.1)
        glow = 0.35 + 0.35 * wave
        colour = tuple(int(c * glow) for c in palette.color("violet_dark"))
        surface.fill(colour, (x, 40 + index % 3 * 22, 2, 34))

    if opened:
        # Dipsiz agiz. Kenarlari mor, ici hicbir sey.
        mouth = pygame.Rect(300, 52, 150, GROUND_Y - 52)
        surface.fill(palette.color("void"), mouth)
        pulse = 0.5 + 0.5 * math.sin(frame * 0.045)
        edge = tuple(int(c * pulse) for c in palette.color("violet_bright"))
        surface.fill(edge, (mouth.left, mouth.top, 2, mouth.height))
        surface.fill(edge, (mouth.right - 2, mouth.top, 2, mouth.height))
        surface.fill(edge, (mouth.left, mouth.top, mouth.width, 2))

    surface.fill(palette.color("ink_soft"),
                 (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
    surface.fill(palette.color("violet_dark"), (0, GROUND_Y, INTERNAL_WIDTH, 1))
