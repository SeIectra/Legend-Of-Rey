"""Bolum 13'un dort ara sahnesi - Cemo'nun bolumu.

`docs/yapi.md` B13: *"Cemo. Kafeste, canli, sana bakiyor - **ulasamadan
tasinir.** Kacmayi denemis, muhafizi yaralamis, duvara isaret
kazimis."*

Uc cumle, dort sahne:

    1 Kafes     "canli, sana bakiyor - ulasamadan tasinir"
    2 Isaret    "kacmayi denemis, muhafizi yaralamis, isaret kazimis"
    3 Zindanci  boss girisi
    4 Kapi      boss'tan sonra: kafes bos, Cemo hala onde

## Kafes sahnesi bu bolumun tamami

On uc bolumdur Cemo bir **sebep**ti - gorulmeyen, hatirlanan bir sey.
Burada ilk kez ekranda ve **bakiyor**. Sahnenin tek isi o bakisi
kurmak, sonra elinden almak.

Bu yuzden sahnede kavusma yok, konusma yok, kurtarma denemesi yok.
Cemo goturuluyor ve Rey hicbir sey yapamiyor - eger bir sey
yapabilseydi bolum bir basarisizlik olurdu; yapamayinca bir **kayip**
oluyor. Ikisi cok farkli duygular.

## Yuze kesme iki kez, ve ikisi de sessiz

`closeup` iki panelde: once Cemo, sonra oyuncu. Arada replik yok.
`docs/gdd.md` 11 - anlatim jestle; en yuksek sesli an konusmadigi
zaman calisiyor.

Bu sahne **atlanamaz** (`skippable=False`). Bolum 3'un "Mor" sahnesi
disinda bunu yapan ikinci sahne. Gerekce ayni: burada gecen sey bir
bilgi degil bir kayip, ve iki saniye tuşa basmayla gecilebilseydi
oyuncu neyi kaybettigini fark etmeden gecerdi.
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
LEDGE_Y = 96             # Cemo'nun kafesinin durdugu ust kat


class _Chapter13Cinematic(StagedScene):
    background = "void"
    wait_for_input = True

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        # ACTORS `super().on_enter()`ten ONCE kurulmali: orasi
        # `_start_panel` -> `on_panel_start` -> cue zincirini tetikliyor
        # ve o zincir `self.actors`i ariyor. Ters sirada sahne aktorler
        # daha yokken cue isliyordu.
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

    def _write(self, beats: dict[str, Line]) -> None:
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues,
                  fade_in=p.fade_in, fade_out=p.fade_out, closeup=p.closeup,
                  shake=p.shake, wait_for_input=p.wait_for_input)
            if p.name in beats else p
            for p in self.panels)

    def on_finished(self) -> None:
        self.scenes.pop()


# --- Ara Sahne 1: "Kafes" ★ ---------------------------------------------------
class CageCinematic(_Chapter13Cinematic):
    """Cemo gorunuyor, bakiyor, tasiniyor.

    **Atlanamaz.** Gerekce modul basliginda.
    """

    skippable = False

    PANELS = (
        # Oyuncu geliyor ve duruyor. Kafes yukarida, karanlikta.
        Panel(52, "varis", wait_for_input=False, fade_in=16, cues=(
            Cue("player", state="run", face=1,
                move_to=(196.0, GROUND_Y), move_frames=40),
            Cue("player", delay=40, state="idle"),
            Cue("cemo", visible=True, alpha=70, silhouette=True),
        )),
        # Kafes aydinlaniyor: Cemo bir siluetten bir COCUGA doniyor.
        Panel(46, "gorus", cues=(
            Cue("cemo", silhouette=False, alpha=255, sound="necklace_warm"),
            Cue("player", state="idle", face=1),
        )),
        # Cemo'nun yuzu. Replik YOK - en yuksek sesli an sessiz olan.
        Panel(56, "cemo_yuz", closeup="cemo", fade_in=10),
        # Oyuncunun yuzu. Ayni sessizlik, oteki taraftan.
        Panel(50, "rey_yuz", closeup="player", fade_in=8, fade_out=8),
        # Kosuyor - ve duvara carpiyor. Yapabilecegi tek sey bu.
        Panel(44, "kosu", wait_for_input=False, shake=0.8, cues=(
            Cue("player", state="run", face=1,
                move_to=(250.0, GROUND_Y), move_frames=22),
            Cue("player", delay=22, state="hurt", flash=0.25,
                sound="enemy_blocked", shake=1.4),
        )),
        # Kafes cekiliyor. Cemo'nun elini uzatmasi tek jesti.
        Panel(58, "tasiniyor", wait_for_input=False, cues=(
            Cue("cemo", state="hurt", face=-1),
            Cue("cemo", delay=10, state="run",
                move_to=(INTERNAL_WIDTH + 50.0, LEDGE_Y), move_frames=46,
                move_ease="in", sound="rift_close"),
            Cue("player", state="idle", face=1),
        )),
        Panel(54, "bos", fade_out=14, cues=(
            Cue("cemo", visible=False),
            Cue("player", state="idle"),
        )),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (
            ActorSpec("player", self.character, 120.0, GROUND_Y, facing=1,
                      scale=2),
            # Cemo ust katta ve **daha kucuk cizilmiyor**: uzaklik
            # olcek degil YUKSEKLIK ile anlatiliyor. Kucultseydik
            # "uzakta" degil "kucuk" okunurdu.
            ActorSpec("cemo", "cemo", 300.0, LEDGE_Y, facing=-1, scale=2,
                      shadow=False, depth=0.85),
        )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.motes = MoteField(20, drift=-0.16, sway=0.8, tone="stone_dark")
        self.vignette = 0.42
        # Kafesin isigi - sahnenin tek sicak kaynagi, ve o da gidiyor.
        self.add_light(300, LEDGE_Y - 26, 70,
                       palette.color("ember_light"), peak=0.5)
        self.add_light(160, GROUND_Y - 30, 54,
                       palette.color("violet" if character != "ardo"
                                     else "bone"), peak=0.22)
        self.game.music.hold("sad", 900)
        self._write({
            "gorus": Line("cemo", "line.ch13_cemo_sees"),
            "kosu": Line(character, "line.ch13_rey_reach"
                         if character != "ardo" else "line.ch13_ardo_reach"),
            "bos": self.voice("line.ch13_echo_cage", "line.ch13_trace_cage"),
        })

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_cellblock(surface, self.frame)


# --- Ara Sahne 2: "Isaret" ----------------------------------------------------
class MarkCinematic(_Chapter13Cinematic):
    """Cemo'nun duvara kazidigi isaret. Kisa, sessiz, dovussuz.

    `docs/yapi.md` B13'un ikinci ve ucuncu cumlesi: *"Kacmayi denemis,
    muhafizi yaralamis, duvara isaret kazimis."* Ucu de burada ve
    hicbiri soylenmiyor - kazinmis cizgi, kurumus kan, kirik zincir.
    """

    PANELS = (
        Panel(44, "durus", wait_for_input=False, fade_in=12, cues=(
            Cue("player", state="run", face=1,
                move_to=(228.0, GROUND_Y), move_frames=26),
            Cue("player", delay=26, state="idle"),
        )),
        Panel(46, "isaret", cues=(
            Cue("player", state="idle", face=1, sound="echo_reveal",
                burst="spark", burst_count=8),
        )),
        Panel(48, "kan"),
        Panel(46, "yuz", closeup="player", fade_in=10, fade_out=12),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (ActorSpec("player", self.character, 170.0, GROUND_Y,
                          facing=1, scale=2),)

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.motes = MoteField(14, drift=-0.1, sway=0.6, tone="stone_dark")
        self.vignette = 0.46
        self.add_light(240, GROUND_Y - 40, 62,
                       palette.color("bone"), peak=0.3)
        self.game.music.hold("sad", 620)
        self._write({
            "isaret": Line(character, "line.ch13_rey_sign"
                           if character != "ardo" else "line.ch13_ardo_sign"),
            "kan": self.voice("line.ch13_echo_blood",
                              "line.ch13_trace_blood"),
        })

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_cellblock(surface, self.frame, bars=False)
        _draw_wall_mark(surface, self.frame, panel.name)


# --- Ara Sahne 3: "Zindanci" --------------------------------------------------
class GaolerCinematic(_Chapter13Cinematic):
    """BOSS 2 girisi.

    Boss'un girisini **feneri** yapiyor: once karanlikta bir isik
    yaklasiyor, sonra isigi tasiyan sey gorunuyor. Sirasi onemli -
    boss'u once gosterip sonra feneri aciklamak "buyuk adam +
    aksesuar" olurdu; tersi "karanlikta bir isik var, ve o isik BIRI"
    oluyor.

    Silueti son panele kadar acilmiyor: `silhouette=True` ile geliyor,
    tam gorunmesi tek bir karede.
    """

    PANELS = (
        Panel(50, "karanlik", wait_for_input=False, fade_in=18, cues=(
            Cue("player", state="idle", face=1),
            Cue("gaoler", visible=True, silhouette=True, alpha=40),
        )),
        # Fener yaklasiyor - govde hala bir leke.
        Panel(52, "fener", wait_for_input=False, cues=(
            Cue("gaoler", alpha=140, state="run", face=-1,
                move_to=(322.0, GROUND_Y), move_frames=44,
                move_ease="out", sound="rift_open"),
        )),
        # Ve duruyor. Isigi tasiyan sey gorunuyor.
        Panel(54, "govde", shake=0.6, cues=(
            Cue("gaoler", silhouette=False, alpha=255, state="idle",
                flash=0.3, shake=1.6, sound="enemy_tell"),
        )),
        Panel(48, "yuz", closeup="gaoler", fade_in=10),
        # Surgu iniyor - arena muhurlendi.
        Panel(46, "muhur", wait_for_input=False, fade_out=12, shake=1.0, cues=(
            Cue("player", state="idle", face=1),
            Cue("gaoler", state="attack1", sound="rift_close", shake=2.0),
        )),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (
            ActorSpec("player", self.character, 150.0, GROUND_Y, facing=1,
                      scale=2),
            ActorSpec("gaoler", "gaoler", 470.0, GROUND_Y, facing=-1,
                      scale=2),
        )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.motes = MoteField(24, drift=-0.2, sway=1.0, tone="stone_darkest")
        self.vignette = 0.58          # Arenanin karanligi burada basliyor
        self.add_light(470, GROUND_Y - 34, 60,
                       palette.color("ember_light"), peak=0.55)
        self.game.music.hold("boss", 900)
        self._write({
            "govde": self.voice("line.ch13_echo_gaoler",
                                "line.ch13_trace_gaoler"),
            "muhur": Line(character, "line.ch13_rey_gaoler"
                          if character != "ardo" else "line.ch13_ardo_gaoler"),
        })

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_cellblock(surface, self.frame)


# --- Ara Sahne 4: "Kapi" ------------------------------------------------------
class GateCinematic(_Chapter13Cinematic):
    """Boss oldu, kapi acildi - ve arkasi bos.

    Bolumun son darbesi. On uc bolumdur kovalanan sey burada bir kez
    daha kaciyor, ama bu sefer oyuncu **kazanmisken** kaciyor. Boss'u
    yenmek yetmedi.

    `docs/yapi.md` B14 bunun uzerine geliyor: *"Rey anlar: Yanki lanet
    degil, asagidaki seyin sesi."* Yani bu bosluk bir hayal kirikligi
    degil bir **yon degistirme** - asagi inmenin sebebi artik yalnizca
    Cemo degil.
    """

    PANELS = (
        Panel(46, "acilis", wait_for_input=False, fade_in=14, cues=(
            Cue("player", state="run", face=1,
                move_to=(268.0, GROUND_Y), move_frames=30),
            Cue("player", delay=30, state="idle"),
        )),
        Panel(50, "bos_kafes", cues=(
            Cue("player", state="idle", face=1, sound="echo_close"),
        )),
        Panel(52, "yuz", closeup="player", fade_in=10),
        Panel(48, "asagi", fade_out=16, cues=(
            Cue("player", state="idle", face=1, burst="violet",
                burst_count=14, sound="necklace_conflict"),
        )),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (ActorSpec("player", self.character, 200.0, GROUND_Y,
                          facing=1, scale=2),)

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.motes = MoteField(18, drift=-0.24, sway=1.2, tone="violet_dark")
        self.vignette = 0.5
        self.add_light(268, GROUND_Y - 34, 66,
                       palette.color("violet" if character != "ardo"
                                     else "bone"), peak=0.34)
        self.game.music.hold("echo" if character != "ardo" else "sad", 760)
        self._write({
            "bos_kafes": Line(character, "line.ch13_rey_empty"
                              if character != "ardo"
                              else "line.ch13_ardo_empty"),
            "asagi": self.voice("line.ch13_echo_deeper",
                                "line.ch13_trace_deeper"),
        })

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_cellblock(surface, self.frame, empty_cage=True)


# --- Ortak arka plan -----------------------------------------------------------
def _draw_cellblock(surface: pygame.Surface, frame: int, bars: bool = True,
                    empty_cage: bool = False) -> None:
    """Hucre blogu - Bolum 13'un tek mekani.

    Dikey demirler tekrar ediyor ve **ritmi bozulmuyor**: bir zindanin
    en okunur ozelligi tekdüzeligi. Bolum 10'un catal magarasi
    (`chapter10_cinematics._draw_fork`) organikti; burasi insan
    yapimi, ve fark bir bakista anlasilmali.
    """
    surface.fill(palette.color("ink"))

    # Arka duvar - tas siralari.
    back = palette.color("stone_darkest")
    for y in range(40, GROUND_Y, 14):
        surface.fill(back, (0, y, INTERNAL_WIDTH, 11))
        for x in range((y // 14 % 2) * 16, INTERNAL_WIDTH, 32):
            surface.fill(palette.color("ink_soft"), (x, y, 2, 11))

    if bars:
        # Hucre parmakliklari - duzenli, sonsuz.
        bar = palette.color("stone_dark")
        for x in range(24, INTERNAL_WIDTH, 26):
            surface.fill(bar, (x, 52, 3, GROUND_Y - 52))
        surface.fill(bar, (0, 50, INTERNAL_WIDTH, 4))

    if empty_cage:
        # Acik ve bos bir kapi - bolumun son goruntusu.
        surface.fill(palette.color("ink"), (250, 78, 44, GROUND_Y - 78))
        glow = 0.5 + 0.5 * math.sin(frame * 0.05)
        edge = tuple(int(c * glow) for c in palette.color("ember_dark"))
        surface.fill(edge, (250, 78, 2, GROUND_Y - 78))
        surface.fill(edge, (292, 78, 2, GROUND_Y - 78))

    surface.fill(palette.color("ink_soft"),
                 (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
    surface.fill(palette.color("stone_dark"), (0, GROUND_Y, INTERNAL_WIDTH, 1))


def _draw_wall_mark(surface: pygame.Surface, frame: int, panel: str) -> None:
    """Kazinmis isaret + kan + kirik zincir - panele gore SIRAYLA.

    Uc sey ayni anda gosterilseydi hicbiri okunmazdi. Panel adina gore
    ekleniyor: once isaret, sonra kan. Oyuncunun gozu tek bir seye
    gidiyor ve sahne kendini anlatiyor.
    """
    x, y = 236, GROUND_Y - 52
    pulse = 0.55 + 0.45 * math.sin(frame * 0.06)
    mark = tuple(int(c * pulse) for c in palette.color("bone"))
    if panel in ("isaret", "kan", "yuz"):
        # Bolum 2'de gorulen isaretin ayni (`docs/bolum-02.md`:
        # *"Cemo'nun sembolu degil, baska birinin"*) - orada bir
        # bilmeceydi, burada bir imza.
        for index in range(5):
            surface.fill(mark, (x + index * 3, y + abs(2 - index) * 3, 3, 3))
        surface.fill(mark, (x - 4, y + 16, 22, 2))
    if panel in ("kan", "yuz"):
        blood = palette.color("blood_dark")
        for index, (dx, dy) in enumerate(((26, 10), (31, 15), (28, 22),
                                          (35, 19))):
            surface.fill(blood, (x + dx, y + dy, 3 - index % 2, 2))
        # Kirik zincir - muhafizi yaralarken kopmus olan.
        for index in range(4):
            surface.fill(palette.color("stone_light"),
                         (x - 18 - index * 4, y + 26 + index * 2, 3, 3))
