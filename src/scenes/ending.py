"""Oyunun sonu - "Safak" ve jenerik.

`docs/yapi.md` B18: *"Kazanir. Cemo kurtulur. **Gun isigi.** Rey
kolyeyi Cemo'ya geri takar, Ardo arkalarinda. Rey'in kafasi ilk kez
sessiz."*
`docs/gdd.md` 11: *"B18 | Kapanis | **Uclu son panel**."*

## Isik yon degistiriyor

On sekiz bolum boyunca isik hep yukaridan geliyordu ve oyuncu hep
asagi iniyordu. Burada kamera yukari bakiyor ve isik **karsidan**
geliyor - gun isigi bir aydinlatma degil bir **yon**. Bolum
sonlarindaki mor/kemik isiklarin yerini ilk kez `ember_light` aliyor.

## Uclu son panel

Uc figur, uc mesafe:

    Cemo    onde    - kurtarilan, ve artik kolyeyi tasiyan
    Rey     ortada  - kolyeyi TAKAN, ve ilk kez sessiz
    Ardo    arkada  - "arkalarinda" (belgenin kendi kelimesi)

Ardo'nun ne kadar arkada durdugu **B16'da secilen jeste** bagli. Ceza
degil: iki bolum once verilmis bir cevabin hala duruyor olmasi.
`docs/gdd.md` 11'in kurali geciyor - romantik an diyalogla degil
**duruma** anlatiliyor.

## Sessizlik bir SES olarak anlatiliyor

Butun oyun boyunca Yanki'nin bir vinyeti vardi (`EchoState.vignette`)
ve oyuncu onu gormeye alisti. Kapanista vinyet **yok** - ve yokluğu
fark ediliyor. "Rey'in kafasi ilk kez sessiz" cumlesi bir replikle
degil, on sekiz bolumdur ekranin kenarinda duran bir karartmanin
kalkmasiyla soyleniyor.

## Jenerik

Ayri bir sahne degil, kapanisin devami: paneller bitince isim listesi
ayni gun isigi uzerinde yukari suzuluyor. Kesme yok - `CLAUDE.md` 9:
*"Sinematik gecisler ani kesilmez."*
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.entities.companion import other_character
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.ui import balloon, text
from src.ui.dialogue import Line
from src.ui.i18n import t

GROUND_Y = 200
CENTRE_X = INTERNAL_WIDTH // 2

# Uc figurun yerleri. Cemo onde ve **kucuk** - tek olcek 2 degil 1
# olan o, cunku cocuk.
CEMO_X = CENTRE_X - 34.0
REY_X = CENTRE_X + 6.0

# Ardo'nun mesafesi B16'daki jeste bagli.
#
#   reach     elini uzatmistin  -> yaninda
#   nod       basini sallamistin -> bir adim geride
#   withdraw  geri cekilmistin   -> uc adim geride
#
# Ceza degil: iki bolum once verilmis bir cevabin hala duruyor olmasi.
ALLY_DISTANCE = {"reach": 44.0, "nod": 62.0, "withdraw": 88.0}


class DawnCinematic(StagedScene):
    """Gun isigi. Uclu son panel. Ve sessizlik."""

    background = "void"
    wait_for_input = True

    PANELS = (
        Panel(64, "isik", wait_for_input=False, fade_in=40),
        Panel(52, "kolye", cues=(
            Cue("player", state="idle", face=-1),
            Cue("cemo", state="idle", face=1),
        )),
        Panel(56, "uclu", cues=(
            Cue("player", face=1),
            Cue("ally", face=-1),
        )),
        Panel(60, "sessiz", closeup="player", fade_in=14),
        # Jenerik uzun ve tus beklemiyor: on dort satirin ekranin
        # altindan ustune suzulmesi ~850 kare (14 saniye). `CLAUDE.md`
        # 9: sert kesme yok, ama basili tutunca 3x hizlaniyor.
        Panel(900, "jenerik", wait_for_input=False, fade_in=20),
    )

    def on_enter(self, character: str = "rey", ghost: bool = False,
                 lifted: bool = False, gesture_key: str = "nod",
                 tidy: bool = False, clean: bool = False,
                 **kwargs: object) -> None:
        """Dort bayrak **cagirandan** geliyor.

        Sahnenin `save_data`ya elini uzatmasi kirilgan olurdu (ayni
        ders B10 ve B15'te yazildi); bolum okuyor, sahne yalnizca
        gosteriyor.
        """
        self.character = character
        self.ally = other_character(character)
        self.ghost = ghost              # B15: hic uyandirmadan gecti
        self.lifted = lifted            # B16: yoldasi kaldirdi
        self.gesture_key = gesture_key  # B16: hangi jest
        self.tidy = tidy                # B17: az gecisle cozdu
        self.clean = clean              # B18: az diriltmeyle bitirdi

        ally_x = REY_X + ALLY_DISTANCE.get(gesture_key,
                                           ALLY_DISTANCE["nod"])
        self.ACTORS = (
            # Cemo tek olcek 1 olan - cocuk oldugu boyle soyleniyor.
            ActorSpec("cemo", "cemo", CEMO_X, GROUND_Y, facing=1, scale=2),
            ActorSpec("player", character, REY_X, GROUND_Y, facing=-1,
                      scale=2),
            ActorSpec("ally", self.ally, ally_x, GROUND_Y, facing=-1,
                      scale=2),
        )
        super().on_enter(**kwargs)
        self.motes = MoteField(26, drift=-0.05, sway=0.3, tone="ember_light")
        # **Vinyet YOK.** On sekiz bolumdur ekranin kenarinda duran
        # karartma kalkti; "Rey'in kafasi ilk kez sessiz" cumlesi
        # boyle soyleniyor.
        self.vignette = 0.0
        self.add_light(CENTRE_X + 150, GROUND_Y - 90, 190,
                       palette.color("ember_light"), peak=0.55)
        # "Raze" - `music.py`nin kendi notu: *"cok nadir
        # duygusal anlar."* On sekiz bolumde ilk kez calıyor.
        self.game.music.hold("emotional", 1400)
        self.credit_offset = 0.0
        self._write()

    def _write(self) -> None:
        """Anahtarlar **duz dize** - hesaplanmis ad testten kaciyor."""
        ardo = self.character == "ardo"
        light = ("line.ch18_ardo_dawn" if ardo else "line.ch18_rey_dawn")
        three = ("line.ch18_ardo_three" if ardo else "line.ch18_rey_three")
        quiet = ("line.ch18_ardo_quiet" if ardo else "line.ch18_rey_quiet")
        beats = {"kolye": Line(self.character, light),
                 "uclu": Line(self.character, three),
                 "sessiz": Line(self.character, quiet)}
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues,
                  fade_in=p.fade_in, fade_out=p.fade_out, closeup=p.closeup,
                  wait_for_input=p.wait_for_input)
            if p.name in beats else p
            for p in self.panels)

    def on_stage_panel(self, panel: Panel) -> None:
        if panel.name == "kolye":
            self.game.play_sound("necklace_warm")
            self.burst(CEMO_X, GROUND_Y - 30, "echo", count=12)

    def update_cinematic(self) -> None:
        super().update_cinematic()
        panel = self.panel
        if panel is not None and panel.name == "jenerik":
            self.credit_offset += 0.55

    # --- Cizim --------------------------------------------------------------
    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Magara agzi ve **karsidan** gelen gun isigi.

        On sekiz bolum boyunca isik yukaridan geliyordu. Burada
        karsidan geliyor - cikis o yonde ve oyuncu ilk kez asagi degil
        ileri bakiyor.
        """
        surface.fill(palette.color("ink"))
        # Magara agzi: sagda genis bir aciklik, icinden isik doluyor.
        mouth_x = CENTRE_X + 74
        for row in range(0, GROUND_Y):
            ratio = row / max(1, GROUND_Y)
            edge = mouth_x + int(math.sin(ratio * 3.0) * 10)
            surface.fill(palette.color("abyss_dark"), (0, row, edge, 1))
        # Isik katmanlari - disaridan iceri, gittikce soluyor.
        for step in range(6):
            width = INTERNAL_WIDTH - mouth_x + step * 14
            tone = ("ember_light", "ember", "gold", "bone",
                    "stone_light", "stone")[step]
            surface.fill(palette.color(tone),
                         (INTERNAL_WIDTH - width, 0, width, GROUND_Y))
        surface.fill(palette.color("earth_dark"),
                     (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
        surface.fill(palette.color("earth"),
                     (0, GROUND_Y, INTERNAL_WIDTH, 1))

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        ox, oy = offset
        if panel.name == "kolye":
            # Kolye Cemo'ya geri gidiyor - balonla, kelimesiz.
            balloon.draw(surface, "necklace", int(CEMO_X) - ox,
                         int(GROUND_Y) - 40 - oy, frame=self.frame,
                         colour=palette.color("gold"))
        elif panel.name == "uclu" and self.lifted:
            # B16'da onu kaldirdiysan burada bir kalp var. Kaldirmadiysan
            # yok - sahne yalan soylemiyor.
            balloon.draw(surface, "heart", int(REY_X + 22) - ox,
                         int(GROUND_Y) - 44 - oy, frame=self.frame,
                         colour=palette.color("blood_bright"))
        elif panel.name == "jenerik":
            self._draw_credits(surface)

    def _draw_credits(self, surface: pygame.Surface) -> None:
        """Isim listesi gun isiginin uzerinde suzuluyor.

        Ayri bir sahne DEGIL: kapanisin devami. Kesme yok
        (`CLAUDE.md` 9 - sinematik gecisler ani kesilmez).
        """
        lines = [
            t("credits.title"), "",
            t("credits.studio"), "",
            t("credits.design"), t("credits.code"), t("credits.art"),
            "", t("credits.thanks"),
        ]
        # Oyuncunun **kendi** yolu: dort bayrak burada bir cumleye
        # doniyor. Puan tablosu degil bir hatirlatma.
        path = [key for flag, key in (
            (self.ghost, "credits.path_ghost"),
            (self.lifted, "credits.path_lifted"),
            (self.tidy, "credits.path_tidy"),
            (self.clean, "credits.path_clean"),
        ) if flag]
        if path:
            lines += ["", t("credits.path")] + [t(key) for key in path]

        # **Kontur sart.** Ilk surum `ink` (neredeyse siyah) kullaniyordu
        # ve yazi karanlik zeminde tamamen kayboluyordu - render edilip
        # bakilinca cikti. Sahne hem cok aydinlik (sag) hem cok karanlik
        # (sol alt) bolgeler tasiyor, yani tek bir duz renk her yerde
        # okunamaz. Acik renk + kontur ikisinde de okunuyor.
        y = INTERNAL_HEIGHT - int(self.credit_offset)
        for line in lines:
            if -12 < y < INTERNAL_HEIGHT:
                text.draw(surface, line, CENTRE_X, y,
                          color=palette.color("bone"), align="center",
                          outline=True)
            y += 14

    def on_finished(self) -> None:
        from src.ui.menu import MainMenuScene
        self.scenes.set_root(MainMenuScene)
