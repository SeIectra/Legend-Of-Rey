"""Anlatim katmani - panelli ara sahnelerin ortak altyapisi.

`CinematicScene` "sureli, hizlandirilabilir sahne"yi cozuyordu; burasi onun
uzerine bir **sahneleme** dili koyuyor. Bir ara sahne artik kare esiklerini
elle karsilastiran bir `draw_cinematic` govdesi degil, sirali `Panel`
listesi:

    PANELS = (
        Panel(90,  "uyanis"),
        Panel(120, "kolye", line=Line("cemo", "line.ch01_cemo_gift")),
        Panel(60,  "yarik", shake=2.0),
    )

Kazanc yalnizca derli topluluk degil - **her panel ayni kurallari bedavaya
aliyor**: letterbox, kamera, replik zamanlamasi, gecis yumusatma. Bunlar
tek tek yazilsaydi biri mutlaka unuturdu (Bolum 3'un iki sinematigi bu
yuzden birbirinden farkli davraniyordu).

## Letterbox anlatimin noktalama isareti

Ust/alt siyah seritler "burasi anlatim" der. Acilis ve kapanis
**yumusatilmis** - sert acilan bir bant kesme gibi okunur, ki
CLAUDE.md 9'un yasakladigi sey tam olarak bu.

## Replik sinematiklerde de var

Arda'nin karari (23.08.2026): *"sinematiklerde de konusma"*. `Dialogue`
o zamana kadar yalnizca `PlayScene`'e bagliydi. Panel'e `line` verilince
replik panelin **basinda** baslar ve panel suresi replik bitmeden dolarsa
panel bekler (`Panel.wait_for_line`) - Bolum 1 prologunda ogrenilen ders
(bkz. chapter01.py::DIALOGUE_GRACE_FRAMES): zamanlayiciyla yarisan bir
replik sessizce kaybolur.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.cinematic import CinematicScene, smoothstep
from src.ui.dialogue import Dialogue, Line

# Letterbox seritlerinin tam yuksekligi (ic cozunurlukte piksel).
LETTERBOX_HEIGHT = 22
# Seritlerin acilma/kapanma suresi. 12 kare = 200ms, CLAUDE.md 9'un
# menu gecisleri icin koydugu ust sinirla ayni - anlatim da hizli acilir.
LETTERBOX_FRAMES = 12
# Panel arasi karartma. Kesme degil: bir panel sonerken oteki aciliyor.
PANEL_FADE_FRAMES = 10
# Bir replik panel suresini en fazla bu kadar uzatabilir.
LINE_GRACE_FRAMES = 120


@dataclass(frozen=True)
class Panel:
    """Tek bir anlatim vurusu.

    `frames` panelin taban suresi; `line` verilirse replik panelin
    basinda baslar. `camera` panel boyunca kameranin gidecegi hedef
    (piksel, ic cozunurlukte); `shake` radyal sarsinti genligi.
    """

    frames: int
    name: str = ""
    line: Line | None = None
    lines: tuple[Line, ...] = ()
    camera: tuple[float, float] | None = None
    shake: float = 0.0
    # Replik bitmeden panel gecmesin. Varsayilan True: repligi olan bir
    # panelin isi o repligi gostermek.
    wait_for_line: bool = True
    # **Oyuncu onaylayana kadar bekle.** Varsayilan True.
    #
    # Arda, canli oynanis (30.08.2026): *"Introdaki sinematik cok hizli
    # geciyor, cumleler okunmuyor. Kullanicinin bir tusa basmasi
    # beklenmeli."* Hakliydi: replikler `auto_advance=True` ile
    # zamanlayiciya bagliydi ve prologun ucuncu goz panelinde YEDI replik
    # dort saniyeye sikisiyordu.
    #
    # Okuma hizi oyuncunun; bir zamanlayicinin degil.
    #
    # **`None` = sahnenin varsayilanini kullan.** Varsayilan KAPALI ve bu
    # bilincli: her sinematik bir konusma degil. Bolum 1 -> 2 inis
    # sahnesinde replik DUSUS aninda geciyor, bir beat; orada tus
    # beklemek dususu donduruyordu (test yakaladi - "ara sahne
    # kendiliginden bitti" kontrolu kirildi ve haklyidi, oyuncu havada
    # asili kalirdi).
    #
    # Prolog bir konusma, o yuzden `ReyPrologue.wait_for_input = True`.
    wait_for_input: bool | None = None

    # Sahneleme talimatlari - kim ne yapiyor. `StagedScene` okuyor
    # (`src/scenes/staging.py`); duz `StoryScene` gormezden geliyor.
    #
    # Tur ipucu bilerek gevsek: `Cue` staging.py'de tanimli ve staging.py
    # buradan tureyen bir sinif iceriyor. Sikı tur ipucu dairesel import
    # yaratirdi; `Panel` sahneleme bilmeden de calismali - Bolum 1-6'nin
    # butun ara sahneleri cue'suz.
    cues: tuple = ()

    # **Yakin plan.** Aktorun adi verilirse panel boyunca ekrani onun
    # PORTRESI kapliyor (`src/art/portrait.py` - 64x96, kafa 40 piksel).
    #
    # Neden: oyunun en iyi yuz sanati diyalog kutusunun kosesinde
    # 1x cizilen kucuk bir resim olarak duruyordu ve baska hicbir yerde
    # kullanilmiyordu. Duygusal bir beat'te yuze kesmek sinemanin en
    # temel cumlesi - ve burada bedava, cunku sanat zaten var.
    closeup: str = ""

    # Panel basinda siyahtan acilma / sonunda siyaha kapanma (kare).
    # 0 = sert kesme. Sert kesme ucuz degil, sadece FARKLI bir dil:
    # bir dususte kesme dogru, bir sessizlik aninda kararma dogru.
    fade_in: int = 0
    fade_out: int = 0

    @property
    def dialogue_lines(self) -> tuple[Line, ...]:
        if self.lines:
            return self.lines
        return (self.line,) if self.line is not None else ()


@dataclass
class _CameraState:
    x: float = 0.0
    y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    # Yumusak takip - sert atlama "kesme" gibi okunur.
    ease: float = 0.06

    def retarget(self, x: float, y: float) -> None:
        self.target_x, self.target_y = x, y

    def snap(self, x: float, y: float) -> None:
        self.x = self.target_x = x
        self.y = self.target_y = y

    def update(self) -> None:
        self.x += (self.target_x - self.x) * self.ease
        self.y += (self.target_y - self.y) * self.ease

    @property
    def offset(self) -> tuple[int, int]:
        """Kamera ofseti **tam sayiya yuvarlanir**.

        CLAUDE.md 9: ondalik ofset piksel art dokusunu titretir. Bu tek
        satir olmadan butun panelli anlatim kaynar.
        """
        return (int(round(self.x)), int(round(self.y)))


class StoryScene(CinematicScene):
    """Panel dizisi oynatan ara sahne.

    Alt sinif `PANELS` verir ve `draw_panel(surface, panel, progress)`
    yazar. Sure `PANELS`'ten otomatik hesaplanir - `duration_frames`
    elle verilmez.
    """

    PANELS: tuple[Panel, ...] = ()
    letterbox: bool = True
    background: str = "void"
    # Panellerin varsayilani: replik oyuncuyu bekler mi. KAPALI - her
    # sinematik bir konusma degil. Konusma olan sahneler (prolog) acar.
    wait_for_input: bool = False

    # --- Kurulum ------------------------------------------------------------
    def on_enter(self, **kwargs: object) -> None:
        super().on_enter(**kwargs)
        self.panels = self.PANELS
        self.panel_index = 0
        self.panel_frames = 0
        self.dialogue = Dialogue()
        self.camera = _CameraState()
        self.shake_seed = 0.0
        self._start_panel()

    @property
    def duration_frames(self) -> int:            # type: ignore[override]
        """Panellerin toplami. `wait_for_line` bunu asabilir - bilerek:
        sure bir ust sinir degil, taban."""
        return max(1, sum(p.frames for p in self.PANELS))

    @property
    def panel(self) -> Panel | None:
        if self.panel_index >= len(self.panels):
            return None
        return self.panels[self.panel_index]

    @property
    def panel_progress(self) -> float:
        """Panelin kendi ilerlemesi (0..1), yumusatilmis."""
        panel = self.panel
        if panel is None or panel.frames <= 0:
            return 1.0
        return smoothstep(min(1.0, self.panel_frames / panel.frames))

    # --- Panel akisi --------------------------------------------------------
    def _panel_waits(self, panel: Panel) -> bool:
        """Bu panel oyuncuyu bekliyor mu - panel degeri, yoksa sahnenin."""
        if panel.wait_for_input is None:
            return self.wait_for_input
        return panel.wait_for_input

    def _start_panel(self) -> None:
        panel = self.panel
        if panel is None:
            return
        self.panel_frames = 0
        lines = panel.dialogue_lines
        if lines:
            # Repligi olan panel **oyuncuyu bekler**. Bir donem
            # `auto_advance=True` idi ve gerekcesi "yoksa panel sonsuza
            # dek bekler" diye yazilmisti - ama `update()` bitisi zaten
            # `finished_panels`'a bagliyor, yani sonsuz bekleme diye bir
            # sey yok: panel bekler, sahne bekler, oyuncu okur.
            self.dialogue.start(lines,
                                auto_advance=not self._panel_waits(panel))
        if panel.camera is not None:
            self.camera.retarget(*panel.camera)
        self.on_panel_start(panel)

    def _advance_panels(self) -> None:
        panel = self.panel
        if panel is None:
            return
        self.panel_frames += 1

        # Repligi olan ve tus bekleyen panel **yalnizca replik bitince**
        # geciyor - sure onu ilgilendirmiyor. `panel.frames` o panelde
        # gorselin ne kadar surede olgunlastigini soyluyor (isik, goz
        # acilmasi), bittikten sonra sahne oyuncuyu bekliyor.
        if panel.dialogue_lines and self._panel_waits(panel):
            if not self.dialogue.done:
                return
        else:
            if self.panel_frames < panel.frames:
                return
            # Sure doldu - replik hala akiyorsa bekle (ust sinirla).
            if (panel.wait_for_line and not self.dialogue.done
                    and self.panel_frames < panel.frames + LINE_GRACE_FRAMES):
                return
        self.panel_index += 1
        self._start_panel()

    # --- Dongu --------------------------------------------------------------
    def update_cinematic(self) -> None:
        self._advance_panels()
        self.dialogue.update(self.game)
        self.camera.update()
        self.shake_seed += 1.0

    @property
    def finished_panels(self) -> bool:
        return self.panel_index >= len(self.panels)

    @property
    def skippable(self) -> bool:                 # type: ignore[override]
        """Replik ekrandayken hizlandirma KAPALI.

        `CinematicScene._advance` CONFIRM/JUMP/ATTACK basiliyken ilerlemeyi
        3x hizlandiriyor; `Dialogue` ise ayni CONFIRM ile yaziyi hizli
        akitiyor ve satiri ilerletiyor. Ucu ayni tusta olunca oyuncu
        okumaya calisirken sahneyi de kosturuyordu.

        Okunmamis metin atlanmaz. Gorsel paneller (repliksiz) yine
        hizlandirilabiliyor - `CLAUDE.md` 9'un "sert kesme yok, basili
        tutunca 3x" kurali orada aynen gecerli.
        """
        return self.dialogue.done

    def update(self) -> None:
        # `CinematicScene.update` bitisi `raw_progress`'e bakarak veriyor;
        # panelli sahnede gercek bitis **son panelin bitmesi**. Replik
        # bekleyen bir panel sureyi asabilir, o yuzden ikisi ayni degil.
        self.frame += 1
        self._advance()
        self.update_cinematic()
        if self.finished_panels and not self.finished:
            self.finished = True
            self.on_finished()

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color(self.background))
        panel = self.panel
        if panel is not None:
            self.draw_panel(surface, panel, self.panel_progress)
            if panel.shake > 0.0:
                self._apply_shake(surface, panel)
        self.draw_story_overlay(surface)
        if self.letterbox:
            self._draw_letterbox(surface)
        self.dialogue.draw(surface, self.game.frame)

    def _apply_shake(self, surface: pygame.Surface, panel: Panel) -> None:
        """Radyal sarsinti - panelin sonuna dogru soner."""
        amount = panel.shake * max(0.0, 1.0 - self.panel_progress)
        if amount < 0.5:
            return
        ox = int(math.sin(self.shake_seed * 1.7) * amount)
        oy = int(math.cos(self.shake_seed * 2.3) * amount)
        surface.scroll(ox, oy)

    def _draw_letterbox(self, surface: pygame.Surface) -> None:
        """Ust/alt seritler. Acilis ve kapanis yumusatilmis."""
        opening = smoothstep(min(1.0, self.elapsed / LETTERBOX_FRAMES))
        # Kapanis: son panelin son karelerinde geri cekilir.
        remaining = self.duration_frames - self.elapsed
        closing = smoothstep(min(1.0, max(0.0, remaining) / LETTERBOX_FRAMES))
        height = int(LETTERBOX_HEIGHT * opening * closing)
        if height <= 0:
            return
        band = palette.color("void")
        surface.fill(band, (0, 0, INTERNAL_WIDTH, height))
        surface.fill(band, (0, INTERNAL_HEIGHT - height,
                            INTERNAL_WIDTH, height))

    # --- Alt sinif kancalari ------------------------------------------------
    def draw_panel(self, surface: pygame.Surface, panel: Panel,
                   progress: float) -> None:
        """Panelin govdesi. Alt sinif yazar."""

    def draw_story_overlay(self, surface: pygame.Surface) -> None:
        """Letterbox'in ALTINDA kalan ek cizim (nadiren gerekir)."""

    def on_panel_start(self, panel: Panel) -> None:
        """Panel basladi - ses/sarsinti tetiklemek icin."""

    def debug_lines(self) -> list[str]:
        panel = self.panel
        name = panel.name if panel else "-"
        return [f"panel {self.panel_index + 1}/{len(self.panels)} {name}"
                f"  {self.panel_frames}k"]
