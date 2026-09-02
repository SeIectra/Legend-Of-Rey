"""Bolum 16'nin ara sahneleri - "Donus", "Kaldir", "Kalp".

`docs/yapi.md` B16: *"Ardo geri doner, **havali giris**. Ama bu sefer
**Rey de onu kurtarir.** Karsilikli. [...] Bolum sonu: **kalp
balonu**."*

Uc sahne, uc is:

    Donus   yalnizligi bitiriyor - kurtarilan sensin
    Kaldir  mekanigi OGRETIYOR - kurtaran sensin
    Kalp    secim - iliski senin

## Kim gelir? Oynamadigin taraf

`docs/gdd.md` 3 kanon: *"SECMEDIGIN, ara sahnelerde havali girisi
yapan taraf olur."* Uc sahne de `other_character()` uzerinden
turuyor; hicbiri "Ardo" diye sabit yazilmiyor.

Ve fark bir palet degisiminden ibaret DEGIL. Ardo agir: dususte toz,
sarsinti, `land_hard`. Rey hafif: daha hizli iniyor, daha az sarsiyor
ama kolye mor bir flas veriyor - Yanki'yi tasiyan o. Ayni koreografi,
iki farkli **agirlik**.

## Kaldir sahnesi neden gerekli

Arda 02.09.2026: *"Kendi kalkamasin. Ama bir sinematikle oyuncuya bu
mekanik ogretilsin."* Hakli - yoldas bu bolumde kendi kendine
kalkmiyor (`Companion.self_recovers = False`) ve ogretilmeseydi
oyuncu onu yerde birakip bolumun yarisini yoldassiz oynardi. Sahne
mekanigi **gostererek** ogretiyor: yoldas duruyor, oyuncu yanina
cokuyor, sonra kontrol geri veriliyor ve ayni sey oyuncudan
isteniyor.

## Kalp sahnesi: uc jest, yanlis cevap YOK

`docs/derinlestirme.md` 3.3 (`src/ui/gesture.py`). Kalp balonu ucunde
de cikiyor - belge onu acikca soyluyor - ama **kimin ustunde** ve
etrafinda ne oldugu degisiyor:

    elini uzat   yoldas kalbi gosteriyor, eller birlesiyor
    basini salla kalp ikisinin ARASINDA, daha sessiz
    geri cekil   yoldas yine gosteriyor, ama sen bakmiyorsun

Ucuncusu bir ceza degil; en dokunakli olani o olabilir. Secim tona
sahip cikiyor, puana degil.
"""
from __future__ import annotations

import math
from typing import Callable

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.entities.companion import other_character
from src.scenes.staging import ActorSpec, Cue, MoteField, StagedScene
from src.scenes.story import Panel
from src.ui import balloon, gesture
from src.ui.dialogue import Line

GROUND_Y = 190

# Yoldasin dusup indigi nokta - oyuncunun onunde, tehlikeyle arasinda.
DROP_X = 268.0
PLAYER_X = 196.0

# Dususun basladigi yukseklik (ekranin ustunun uzerinde).
DROP_TOP = -40.0


class _Chapter16Cinematic(StagedScene):
    """Uc sahnenin ortak zemini: magara duvari ve iki figur.

    Ortak taban ayri bir sinif cunku uc sahne de ayni odada geciyor ve
    arka plan uc kez yazilsaydi biri gunun birinde otekilerden ayrilir,
    ayni mekan uc farkli yer gibi gorunurdu.
    """

    background = "void"
    wait_for_input = True

    def setup_stage(self, character: str) -> None:
        """Iki aktoru kurar. `on_enter` bunu `super()` ONCESI cagirir."""
        self.character = character
        self.ally = other_character(character)
        # Ardo agir, Rey hafif. Sahnelerin sayilari bundan turuyor.
        self.ally_heavy = self.ally == "ardo"

    def ally_tone(self) -> palette.RGB:
        """Yoldasin isik rengi - Rey moru tasir, Ardo kemik beyazi."""
        return palette.color("violet" if self.ally == "rey" else "bone")

    # Duvar mesaleleri. Ilk surumde yoktu ve sahne render edilince
    # neredeyse tamamen SIYAHTI: `stone_darkest` orgu + `ink` zemin +
    # 0.42 vinyet ust uste binince iki figur zar zor secilyordu.
    # Cozum karanligi azaltmak degil, ona bir **kaynak** vermek oldu -
    # zindan hala karanlik ama artik bir odaya benziyor.
    TORCHES = ((72, 96), (208, 88), (344, 96), (440, 88))

    def light_torches(self) -> None:
        """Mesalelerin isigini sahneye ekler - uc sahne de cagiriyor."""
        for x, y in self.TORCHES:
            self.add_light(x, y, 54, palette.color("ember"), peak=0.30)

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Zindanin dovus odasi - tas orgu, sutunlar, duvar mesaleleri."""
        surface.fill(palette.color("ink"))
        for y in range(28, GROUND_Y, 14):
            surface.fill(palette.color("stone_dark"),
                         (0, y, INTERNAL_WIDTH, 11))
            for x in range((y // 14 % 2) * 18, INTERNAL_WIDTH, 36):
                surface.fill(palette.color("stone_darkest"), (x, y, 2, 11))

        # Kirik sutunlar - derinlik icin, ikisi arkada birer siluet.
        for x, height in ((44, 78), (410, 96)):
            surface.fill(palette.color("stone_darkest"),
                         (x, GROUND_Y - height, 18, height))
            surface.fill(palette.color("stone"),
                         (x, GROUND_Y - height, 2, height))

        # Mesaleler: sap ve alev. Isik **elle cizilmiyor** -
        # `add_light` zaten var ve dogru isi yapiyor. Ilk surumde alevin
        # altina ust uste dikdortgenler koyup "havuz" yapmaya
        # calismistim; render edilince isik gibi degil ekran hatasi gibi
        # okuyordu (yatay seritler). Sistem varken elle taklit etmek
        # yanlisti.
        for x, y in self.TORCHES:
            flicker = int(math.sin(self.frame * 0.19 + x) * 1.5)
            surface.fill(palette.color("earth_dark"), (x, y, 2, 8))
            surface.fill(palette.color("ember_dark"),
                         (x - 2, y - 5 + flicker, 6, 6))
            surface.fill(palette.color("ember"),
                         (x - 1, y - 5 + flicker, 4, 5))
            surface.fill(palette.color("ember_light"),
                         (x, y - 4 + flicker, 2, 2))

        surface.fill(palette.color("stone_darkest"),
                     (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
        surface.fill(palette.color("stone"),
                     (0, GROUND_Y, INTERNAL_WIDTH, 1))


# --- 1. Donus - "havali giris" ------------------------------------------------
class ReturnCinematic(_Chapter16Cinematic):
    """Yoldas yukaridan iniyor. Bu sefer kurtarilan **sensin**."""

    PANELS = (
        Panel(46, "sikisti", wait_for_input=False, fade_in=14, cues=(
            Cue("player", state="idle", face=1),
        )),
        # Siluet duser - kim oldugu HENUZ belli degil. Ayni dil B6'da
        # ilk karsilasmada kullanildi.
        Panel(30, "golge", wait_for_input=False, cues=(
            Cue("ally", visible=True, silhouette=True),
            Cue("ally", move_to=(DROP_X, GROUND_Y), move_frames=16,
                move_ease="in"),
        )),
        Panel(38, "inis", wait_for_input=False),
        Panel(46, "kim", cues=(
            Cue("ally", silhouette=False, face=1),
            Cue("player", face=1),
        )),
        Panel(48, "yuz", closeup="player", fade_in=10, fade_out=14),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.setup_stage(character)
        self.ACTORS = (
            ActorSpec("player", character, PLAYER_X, GROUND_Y, facing=1),
            # Havada baslıyor: `shadow=False` sart - havadaki aktore
            # temas golgesi cizmek onu bir yuzeyin ustunde gosterirdi
            # (`staging.py` bu tuzagi acikca not ediyor).
            ActorSpec("ally", self.ally, DROP_X, DROP_TOP, facing=-1,
                      visible=False, silhouette=True, shadow=False),
        )
        super().on_enter(**kwargs)
        self.motes = MoteField(16, drift=-0.14, sway=0.7, tone="stone_dark")
        self.vignette = 0.26
        self.add_light(int(PLAYER_X), GROUND_Y - 30, 74,
                       palette.color("violet"), peak=0.38)
        self.light_torches()
        self.game.music.hold("combat", 700)
        self._write()

    def _write(self) -> None:
        """Anahtarlar **duz dize** - hesaplanmis ad testten kaciyor."""
        ardo = self.character == "ardo"
        alone = ("line.ch16_ardo_alone" if ardo else "line.ch16_rey_alone")
        face = ("line.ch16_ardo_return_face" if ardo
                else "line.ch16_rey_return_face")
        beats = {
            "sikisti": Line(self.character, alone),
            "yuz": Line(self.character, face),
        }
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues,
                  fade_in=p.fade_in, fade_out=p.fade_out, closeup=p.closeup,
                  wait_for_input=p.wait_for_input)
            if p.name in beats else p
            for p in self.panels)

    def on_stage_panel(self, panel: Panel) -> None:
        """Inisin **agirligi** kimin dustugune bagli.

        Ardo agir: buyuk sarsinti, bol toz, `land_hard`. Rey hafif:
        yarim sarsinti, az toz, ama kolyeden mor bir flas. Ayni
        koreografi, farkli kutle.
        """
        if panel.name != "inis":
            return
        ally = self.actor("ally")
        if ally is not None:
            ally.ground(GROUND_Y)            # artik yerde - golge geri
        if self.ally_heavy:
            self.burst(DROP_X, GROUND_Y, "dust", count=22)
            self.extra_shake = max(self.extra_shake, 4.2)
            self.game.play_sound("land_hard")
        else:
            self.burst(DROP_X, GROUND_Y, "echo", count=14)
            self.extra_shake = max(self.extra_shake, 2.1)
            self.flash(0.30)
            self.game.play_sound("land_soft")
        self.add_light(int(DROP_X), GROUND_Y - 28, 68, self.ally_tone(),
                       peak=0.44)

    def on_finished(self) -> None:
        self.scenes.pop()


# --- 2. Kaldir - mekanigi ogreten sahne ---------------------------------------
class LiftCinematic(_Chapter16Cinematic):
    """Yoldas diz cokuyor. Sahne bitince **oyuncu** onu kaldiracak.

    Sahnenin isi bir duygu degil bir **fiil** ogretmek: yaklas, tut,
    kalksin. O yuzden son panel bir yakin plan degil, iki figuru yan
    yana gosteren genis bir plan - oyuncu birazdan yapacagi seyi
    goruyor.
    """

    LIFT_X = 250.0

    PANELS = (
        # Darbe. `freeze` panelin kendisini donduruyor - `CLAUDE.md` 7
        # dovuste zaten bunu istiyor, burada da bir carpmanin agirligi.
        Panel(26, "darbe", wait_for_input=False, shake=3.0, cues=(
            Cue("ally", state="hurt", face=1, flash=0.55, freeze=8,
                shake=0.8, burst="spark", burst_count=14,
                sound="hit_heavy"),
        )),
        Panel(40, "dizler", wait_for_input=False, cues=(
            Cue("player", face=1),
            # Irkilmeden YIGILMAYA. Ders bunu gormeye bagli.
            Cue("ally", state="death", face=-1, sound="player_hurt"),
        )),
        Panel(52, "yanina", cues=(
            Cue("player", move_to=(LIFT_X - 38.0, GROUND_Y), move_frames=22,
                move_ease="out", face=1),
        )),
        Panel(56, "tut", fade_out=12),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.setup_stage(character)
        self.ACTORS = (
            ActorSpec("player", character, 176.0, GROUND_Y, facing=1,
                      scale=2),
            ActorSpec("ally", self.ally, self.LIFT_X, GROUND_Y, facing=-1,
                      scale=2),
        )
        super().on_enter(**kwargs)
        self.motes = MoteField(12, drift=-0.1, sway=0.5, tone="stone_dark")
        self.vignette = 0.30
        self.add_light(int(self.LIFT_X), GROUND_Y - 24, 70, self.ally_tone(),
                       peak=0.42)
        self.add_light(190, GROUND_Y - 28, 58, palette.color("violet"),
                       peak=0.26)
        self.light_torches()
        self.game.music.hold("sad", 600)
        self._write()

    def _write(self) -> None:
        ardo = self.character == "ardo"
        fell = ("line.ch16_ardo_fell" if ardo else "line.ch16_rey_fell")
        hold = ("line.ch16_ardo_hold" if ardo else "line.ch16_rey_hold")
        beats = {
            "yanina": Line(self.character, fell),
            "tut": Line(self.character, hold),
        }
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues,
                  fade_in=p.fade_in, fade_out=p.fade_out, closeup=p.closeup,
                  shake=p.shake, wait_for_input=p.wait_for_input)
            if p.name in beats else p
            for p in self.panels)

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Son panelde **el** ikonu - ogretilen fiilin resmi.

        Metin degil ikon: oyunun anlatim dili kelimesiz
        (`docs/gdd.md` 2) ve bir tus adi yazmak sahneyi arayuze
        cevirirdi. Tus ipucunu sahne kendisi gosteriyor
        (`chapter16.py`, oynanis geri gelince).
        """
        if panel.name != "tut":
            return
        ox, oy = offset
        pulse = 0.5 + 0.5 * math.sin(self.frame * 0.12)
        balloon.draw(surface, "hand",
                     int(self.LIFT_X) - ox, int(GROUND_Y) - 34 - oy,
                     frame=self.frame,
                     colour=palette.color("violet_bright"),
                     alpha=int(150 + 105 * pulse))

    def on_finished(self) -> None:
        self.scenes.pop()


# --- 3. Kalp - secim ve kapanis -----------------------------------------------
class HeartCinematic(_Chapter16Cinematic):
    """Uc jest, bir secim, bir kalp.

    Secim paneli **oyuncuyu bekliyor** ve bunun icin panel akisi
    duruyor (`update_cinematic` ezildi): panel suresi dolsa bile
    secim yapilmadan ilerlemiyor. Zamana birakilsaydi karari
    zamanlayici verirdi.
    """

    PAIR_X = 224.0
    GAP = 26.0

    PANELS = (
        Panel(44, "durus", wait_for_input=False, fade_in=16, cues=(
            Cue("player", state="idle", face=1),
            Cue("ally", state="idle", face=-1),
        )),
        Panel(40, "bak", cues=(
            Cue("player", face=1),
            Cue("ally", face=-1),
        )),
        Panel(1, "secim", wait_for_input=False),
        Panel(64, "cevap", wait_for_input=False),
        Panel(50, "yuz", closeup="player", fade_out=16),
    )

    def on_enter(self, character: str = "rey",
                 on_picked: Callable[[gesture.Gesture | None], None] | None
                 = None, **kwargs: object) -> None:
        self.setup_stage(character)
        # **Cagirandan** geliyor ve sonuc ona donuyor. `ScenesManager`
        # kwarg'lari dogrudan `on_enter`a geciriyor - "bitince sunu
        # cagir" diye ayri bir kanca yok, o yuzden geri cagri burada
        # adi konmus bir parametre. Ayni kalibin tersi B15'te vardi
        # (`ghost=`): orada veri sahneye giriyordu, burada cikiyor.
        self.on_picked = on_picked
        self.ACTORS = (
            ActorSpec("player", character, self.PAIR_X - self.GAP, GROUND_Y,
                      facing=1, scale=2),
            ActorSpec("ally", self.ally, self.PAIR_X + self.GAP, GROUND_Y,
                      facing=-1, scale=2),
        )
        super().on_enter(**kwargs)
        self.motes = MoteField(18, drift=-0.08, sway=0.5, tone="stone_light")
        self.vignette = 0.28
        self.add_light(int(self.PAIR_X), GROUND_Y - 34, 88,
                       self.ally_tone(), peak=0.40)
        self.light_torches()
        self.game.music.hold("sad", 800)
        self.choice = gesture.GestureChoice()
        # Secilen jest sahneye ve kayda gidiyor - `on_finished` okuyor.
        self.picked: gesture.Gesture | None = None
        self._write()

    def _write(self) -> None:
        ardo = self.character == "ardo"
        stand = ("line.ch16_ardo_stand" if ardo else "line.ch16_rey_stand")
        beats = {"durus": Line(self.character, stand)}
        self.panels = tuple(
            Panel(p.frames, p.name, line=beats[p.name], cues=p.cues,
                  fade_in=p.fade_in, fade_out=p.fade_out, closeup=p.closeup,
                  wait_for_input=p.wait_for_input)
            if p.name in beats else p
            for p in self.panels)

    # --- Secim akisi --------------------------------------------------------
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
        """Secim paneli **oyuncuyu bekler** - yalnizca ilerleme durur.

        Ilk surum butun `update_cinematic`i kesiyordu; o zaman
        parcaciklar ve tozlar da donuyordu ve sahne secim aninda
        cansiz gorunuyordu. Duran tek sey panel sayaci olmali.
        """
        if self.choosing:
            self.choice.update()
            if not self.choice.done:
                return
        super()._advance_panels()

    def on_stage_panel(self, panel: Panel) -> None:
        if panel.name != "cevap":
            return
        # Kalp UC secimde de cikiyor - `docs/yapi.md` "bolum sonu: kalp
        # balonu" diyor ve o baglayici. Degisen sey kimin gosterdigi ve
        # etrafinda ne oldugu.
        self.game.play_sound("necklace_warm")
        key = self.picked.key if self.picked else gesture.NOD.key
        if key == gesture.REACH.key:
            # Eller birlesiyor: ikisi birbirine bir adim atiyor.
            player = self.actor("player")
            ally = self.actor("ally")
            if player is not None:
                player.move_to(self.PAIR_X - self.GAP + 8.0, GROUND_Y, 24)
            if ally is not None:
                ally.move_to(self.PAIR_X + self.GAP - 8.0, GROUND_Y, 24)
            self.burst(self.PAIR_X, GROUND_Y - 30, "echo", count=16)
        elif key == gesture.WITHDRAW.key:
            # Sen bakmiyorsun - ama o yine de gosteriyor.
            player = self.actor("player")
            if player is not None:
                player.facing = -1
                player.move_to(self.PAIR_X - self.GAP - 14.0, GROUND_Y, 26)
        else:
            self.burst(self.PAIR_X, GROUND_Y - 34, "echo", count=10)

    # --- Cizim --------------------------------------------------------------
    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        ox, oy = offset
        if panel.name == "secim":
            # Balonlar iki figurun **uzerinde**, kafalarina degil.
            # 62'de render edildi ve secili balon yoldasin kafasina
            # biniyordu (aktorler bu sahnede scale 2).
            self.choice.draw(surface, INTERNAL_WIDTH // 2,
                             GROUND_Y - 104 - oy)
            return
        if panel.name != "cevap":
            return

        key = self.picked.key if self.picked else gesture.NOD.key
        if key == gesture.NOD.key:
            # Kalp **ikisinin arasinda** - kimseye ait degil, ortak.
            x = int(self.PAIR_X) - ox
            y = int(GROUND_Y) - 48 - oy
        else:
            # Yoldasin ustunde: o gosteriyor. Geri cekilmis olsan bile.
            ally = self.actor("ally")
            x = int(ally.x if ally else self.PAIR_X + self.GAP) - ox
            y = int(GROUND_Y) - 46 - oy
        balloon.draw(surface, "heart", x, y, frame=self.frame,
                     colour=palette.color("blood_bright"))

    def on_finished(self) -> None:
        # Once haber ver, sonra kapan: pop sirada bekliyor ve cagiran
        # sahne bir sonraki karede yeniden calisiyor - secim o karede
        # elinde olmali.
        if self.on_picked is not None:
            self.on_picked(self.picked)
        self.scenes.pop()
