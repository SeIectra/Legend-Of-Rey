"""Bolum 7'nin dort ara sahnesi. Hepsi **sahnelenmis** - `staging.py`.

Bugune kadarki ara sahnelerde tek bir karakter cizilmemisti (bkz.
`staging.py` modul basligi). Bunlar ilk: gercek sprite'lar, gercek
animasyon durumlari, parcacik, isik, kenar isigi.

    1  MUHUR      bolum acilisi - kapi ve Katman 2'nin isareti
    2  SIGMIYOR   yoldas catlaga giremiyor. Kelime yok.
    3  YALNIZ     obur taraf. Vinyet kapaniyor.
    4  EL     ★   `docs/gdd.md` 11'in B7 satiri: ilk fiziksel temas

## "Balon yok"

`docs/yapi.md` B7: *"Balon yok - sadece bir saniye fazla tutulan el."*
Dorduncu sahnede **tek replik yok** ve bu bir eksiklik degil, belgenin
acik talimati. Anlam suredeu: eller birlestikten sonra sahne bir saniye
daha bekliyor (`HOLD_TOO_LONG`). O bir saniye butun sahne.

`docs/derinlestirme.md` 150: *"B7 (el tutma), B8 (yara sarma), B16
(kurtarma), B18 (final) - dort an yeter."* Az sayida an, her biri tam.

## Roller karaktere gore donuyor

Rey oynanirken catlaktan sen geciyorsun, eli **yoldas** uzatiyor.
Ardo oynanirken gecen yoldas, eli uzatan **sen**siniz. Sahne ayni; kimin
nerede durdugu `character`'dan turuyor. Iki ayri sahne yazmak ayni
seyin iki kopyasini bakim yuku yapardi.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.entities.companion import other_character
from src.scenes.staging import ActorSpec, Cue, StagedScene
from src.scenes.story import Panel
from src.ui.dialogue import Line

# Sahnedeki zemin hizasi (ic cozunurlukte piksel). Aktorler ayaklarindan
# konumlaniyor, yani hepsi bu satirda duruyor.
GROUND_Y = 176
# Kapinin sahnedeki yeri.
DOOR_X = 356
DOOR_WIDTH = 40
DOOR_TOP = 96

# --- Ara Sahne 4: "El" -------------------------------------------------------
# Eller birlestikten sonra sahnenin bekledigi sure. **Bir saniye fazla** -
# belgenin cumlesi bu. 60 kare = 1 saniye (CLAUDE.md 4: sabit 60 FPS).
HOLD_TOO_LONG = 60


class _Chapter07Cinematic(StagedScene):
    """Ortak kurulum: kim oyuncu, kim yoldas.

    `ACTORS` sinif duzeyinde sabit olamiyor - kimin hangi sprite'i
    kullandigi `character`'a bagli. `on_enter` onu kurup uste veriyor.
    """

    background = "void"

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.companion_key = other_character(character)
        self.ACTORS = self.build_actors()
        super().on_enter(**kwargs)

    def build_actors(self) -> tuple[ActorSpec, ...]:
        raise NotImplementedError

    def _torchlight(self, x: int, y: int, radius: int = 46) -> None:
        # Iki isik: dar ve sicak cekirdek + genis, zayif ortam.
        # Yalniz cekirdek olsaydi disi tamamen siyah kalirdi ve mekan
        # yine okunmazdi - vinyet zaten kenarlari karartiyor.
        self.add_light(x, y, radius, palette.color("ember_light"), peak=0.55)
        self.add_light(x, y - 6, radius * 3, palette.color("ember"),
                       peak=0.16)

    # --- Roller --------------------------------------------------------------
    # Iki sahne (Sigmiyor, El) "oyuncu/yoldas" ile kurulamiyor cunku kimin
    # ne yaptigi oynanan karaktere degil **kanona** bagli: catlaktan her
    # zaman Rey geciyor, eli her zaman Ardo uzatiyor (`docs/yapi.md` B7).
    #
    # Ardo oynanirken gecemeyen oyuncunun kendisi oluyor. Aktorleri
    # "ince/genis" diye adlandirmak bunu tek yerde cozuyor; alternatif
    # her sahnenin iki kopyasini yazmakti.
    @property
    def slim(self) -> str:
        """Ince olan - catlaktan gecen. Kanon: Rey."""
        return "rey"

    @property
    def wide(self) -> str:
        """Genis omuzlu - gecemeyen, eli uzatan. Kanon: Ardo."""
        return "ardo"

    def set_line(self, panel_name: str, rey_key: str, ardo_key: str) -> None:
        """Adi verilen panele oynanan karakterin repligini koyar.

        Replik `PANELS`'e sabit yazilamiyor: konusan kisi `character`'a
        bagli ve sinif govdesi calisirken o bilinmiyor. `PlayScene`
        ayni sorunu `say_player(key, ardo_key)` ile cozuyor; bu onun
        sinematik karsiligi.

        Anahtarlar **duz dize** olarak cagirana birakildi. F-string ile
        kurulan anahtari `test_lang.py` goremiyor ve bu tuzaga proje
        alti kereden fazla dustu.
        """
        key = ardo_key if self.character == "ardo" else rey_key
        speaker = self.character
        self.panels = tuple(
            Panel(p.frames, p.name, line=Line(speaker, key),
                  wait_for_input=True, cues=p.cues)
            if p.name == panel_name else p
            for p in self.panels)


# --- 1. "Muhur" - bolum acilisi ---------------------------------------------
class SealCinematic(_Chapter07Cinematic):
    """Iki siluet karanlikta yurur, kapi mesale isiginda belirir.

    Katman 2'nin ilk goruntusu: muhurlu bir kapi. `docs/gdd.md` 79 -
    Orta Zindan, Lanetli Muhafizlar.
    """

    PANELS = (
        # Panel A: karanlik, uzakta iki siluet yaklasir.
        Panel(80, "yaklasma", cues=(
            Cue("player", move_to=(150.0, GROUND_Y), move_frames=80,
                state="run"),
            Cue("companion", move_to=(112.0, GROUND_Y), move_frames=80,
                state="run"),
        )),
        # Panel B: dururlar, mesale yanar, kapi gorunur.
        Panel(70, "kapi", cues=(
            Cue("player", state="idle", face=1),
            Cue("companion", state="idle", face=1),
            Cue("player", delay=10, sound="torch_light", flash=0.25),
        )),
        # Panel C: oyuncunun ici konusur.
        Panel(60, "muhur", cues=(
            Cue("player", state="idle"),
        )),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (
            ActorSpec("companion", self.companion_key, 40.0, GROUND_Y,
                      silhouette=True),
            ActorSpec("player", self.character, 74.0, GROUND_Y,
                      silhouette=True),
        )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.vignette = 0.34
        self.game.music.play("explore")
        self.set_line("muhur", "line.ch07_rey_seal", "line.ch07_ardo_seal")

    def on_stage_panel(self, panel: Panel) -> None:
        if panel.name != "kapi":
            return
        # Mesale yanınca siluetler cozuluyor: karanlikta kim oldugu belli
        # degildi, isikta belli oluyor.
        for name in ("player", "companion"):
            actor = self.actor(name)
            if actor is not None:
                actor.silhouette = False
        # Isik oyuncunun DURDUGU yerde. Ortada birakildiginda
        # karakterler karanlikta, isik bosluktaydi - mesaleyi
        # tasiyan onlar oldugu icin bu bir hataydi.
        self._torchlight(150, GROUND_Y - 24, 52)
        # Kapinin muhru kendi isigini veriyor: uzaktaki tehdit
        # karanlikta durmuyor, **bakiyor**.
        self.add_light(DOOR_X, DOOR_TOP + 40, 46,
                       palette.color("violet"), peak=0.42)
        self.burst(150.0, GROUND_Y - 30, "spark", 14, speed=(0.4, 1.4))

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_cavern(surface, self.frame)
        if panel.name != "yaklasma":
            _draw_sealed_door(surface, self.frame)

    def on_finished(self) -> None:
        from src.scenes.chapter07 import Chapter07Scene
        self.scenes.replace(Chapter07Scene, transition=False,
                            character=self.character)


# --- 2. "Sigmiyor" - yoldas catlaga giremiyor -------------------------------
class GapCinematic(_Chapter07Cinematic):
    """Yoldas catlaga girmeye calisir, omzu takilir, geri ceker.

    **Tek kelime yok.** B6'nin dilinin devami (`docs/gdd.md` 11: bakisma,
    soru isareti). Bu sahne bir bilgi veriyor - "o gecemez" - ve bunu
    soyleyerek degil gostererek veriyor.
    """

    PANELS = (
        Panel(50, "deneme", cues=(
            Cue("wide", move_to=(268.0, GROUND_Y), move_frames=45,
                state="run", face=1),
        )),
        # Omuz takiliyor: bir kare "hurt", sarsinti, toz.
        Panel(34, "takilma", shake=2.4, cues=(
            Cue("wide", state="hurt", sound="enemy_blocked",
                burst="dust", burst_count=10),
            Cue("wide", delay=8, move_to=(238.0, GROUND_Y),
                move_frames=22, state="idle"),
        )),
        # Bakisma: ikisi birbirine doner. Cozum konusulmadan anlasiliyor.
        Panel(46, "bakis", cues=(
            Cue("wide", state="idle", face=-1),
            Cue("slim", state="idle", face=1),
        )),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (
            ActorSpec("slim", self.slim, 150.0, GROUND_Y, facing=1, scale=2),
            ActorSpec("wide", self.wide, 214.0, GROUND_Y, facing=1, scale=2),
        )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.vignette = 0.26
        self._torchlight(150, GROUND_Y - 26, 50)

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_cavern(surface, self.frame)
        _draw_crack(surface, 286)

    def on_finished(self) -> None:
        self.scenes.pop()


# --- 3. "Yalniz" - obur taraf ------------------------------------------------
class AloneCinematic(_Chapter07Cinematic):
    """Catlaktan gecildi. Yoldas arkada kaldi.

    Vinyet **kapaniyor**: yalnizlik bir bilgi degil bir his ve ekranin
    daralmasiyla anlatiliyor. Bolum 3'un karanligiyla ayni dil.
    """

    PANELS = (
        Panel(56, "cikis", cues=(
            Cue("player", move_to=(196.0, GROUND_Y), move_frames=50,
                state="run", face=1),
        )),
        Panel(50, "arkana_bak", cues=(
            Cue("player", state="turn", face=-1),
            Cue("player", delay=14, state="idle"),
        )),
        Panel(70, "yalniz", wait_for_input=True, cues=(
            Cue("player", state="idle", face=1),
        )),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (ActorSpec("player", self.character, 140.0, GROUND_Y,
                          facing=1),)

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.vignette = 0.24
        self._torchlight(196, GROUND_Y - 26, 42)
        # Yalnizlik parcasi: Yanki/iz surme degil, uzucu olan.
        self.game.music.hold("sad", 480)
        self.set_line("yalniz", "line.ch07_rey_alone", "line.ch07_ardo_alone")

    def update_cinematic(self) -> None:
        super().update_cinematic()
        # Panel ilerledikce vinyet kapaniyor - 0.30'dan 0.62'ye.
        self.vignette = 0.24 + 0.30 * self.raw_progress

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_cavern(surface, self.frame)
        _draw_crack(surface, 96)

    def on_finished(self) -> None:
        self.scenes.pop()


# --- 4. "El" ★ ---------------------------------------------------------------
class HandCinematic(_Chapter07Cinematic):
    """Uzanan el, tutulan el, **bir saniye fazla.**

    `docs/yapi.md` B7 romantik an. Sahnenin tamami sessiz: replik yok,
    balon yok, ses efekti bir tane (temas). Anlam sürede.
    """

    PANELS = (
        # A: ince olan asagida, cikintida. Yukari bakiyor.
        Panel(56, "asagida", cues=(
            Cue("below", state="idle", face=1),
            Cue("above", state="run", face=-1,
                move_to=(266.0, GROUND_Y), move_frames=50),
        )),
        # B: yukaridaki kenara gelir, diz coker, elini uzatir.
        Panel(54, "uzatma", cues=(
            Cue("above", state="idle", face=-1),
            Cue("above", delay=18, sound="ui_tick"),
        )),
        # C: temas. Tek ses, tek flas, parcacik.
        Panel(30, "temas", cues=(
            Cue("below", state="jump", sound="item_pickup",
                burst="echo", burst_count=16),
            Cue("below", flash=0.35),
        )),
        # D: cekme - asagidaki yukari cikiyor.
        Panel(44, "cekme", cues=(
            Cue("below", move_to=(222.0, GROUND_Y), move_frames=40,
                state="jump"),
            Cue("below", delay=40, state="land"),
        )),
        # E: **bir saniye fazla.** Ikisi de duruyor, eller hala birlesik.
        Panel(HOLD_TOO_LONG, "fazla", cues=(
            Cue("below", state="idle", face=1),
            Cue("above", state="idle", face=-1),
        )),
        # E2: **yuze kesme.** Sahnenin tamami iki kucuk figurdu; o bir
        # saniyenin ne demek oldugu yuzden okunur. `docs/yapi.md` B7
        # kelimeyi yasakliyor, bakisi yasaklamiyor.
        Panel(46, "yuz", closeup="below", fade_in=8),
        # F: ayrilirlar. Kimse bir sey soylemiyor.
        Panel(40, "birakma", fade_in=8, cues=(
            Cue("below", state="idle"),
            Cue("above", state="idle", face=1),
        )),
    )

    def build_actors(self) -> tuple[ActorSpec, ...]:
        # Asagidaki **cukurda**: ayak hizasi 34 piksel asagida.
        # `docs/yapi.md` B7: *"Ardo elini uzatir, Rey tutar."* Yani
        # asagida olan her zaman Rey, uzanan her zaman Ardo - oynanan
        # karakter hangisi olursa olsun.
        return (
            ActorSpec("below", self.slim, 208.0, GROUND_Y + 40, facing=1,
                      scale=2),
            ActorSpec("above", self.wide, 306.0, GROUND_Y, facing=-1,
                      scale=2),
        )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.vignette = 0.30
        self._torchlight(276, GROUND_Y - 40, 56)
        # `Raze` - Arda'nin talimati: *"cok nadir duygusal kisimlar icin
        # Raze kullan."* Bolum boyunca bir kez calan parca bu.
        self.game.music.hold("emotional", 720)
        self.contact = False

    def on_stage_panel(self, panel: Panel) -> None:
        if panel.name == "temas":
            self.contact = True
        elif panel.name == "birakma":
            self.contact = False

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_cavern(surface, self.frame)
        _draw_chasm(surface)

    def draw_stage_foreground(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        """Birlesen eller: iki govde arasinda tek parlak kume.

        Sprite'a el cizmek 32 pikselde okunmuyor (`CLAUDE.md` 6 -
        yuz/el detayi portrede yasiyor). Temasi **isikla** anlatiyoruz:
        iki karakterin arasinda, omuz hizasinda, nabiz gibi atan bir
        kume. Az piksel, cok anlam.
        """
        if not self.contact:
            return
        below = self.actor("below")
        above = self.actor("above")
        if below is None or above is None:
            return
        mid_x = int((below.x + above.x) * 0.5)
        mid_y = int(min(below.y, above.y)) - 18
        pulse = 0.72 + 0.28 * math.sin(self.frame * 0.18)
        colour = palette.color("echo_bright")
        surface.fill(tuple(int(c * pulse) for c in colour),
                     (mid_x - 2, mid_y, 4, 3))
        surface.fill(palette.color("white_flash"), (mid_x - 1, mid_y + 1, 2, 1))

    def on_finished(self) -> None:
        self.scenes.pop()


# --- Ortak arka plan parcalari ----------------------------------------------
def _draw_cavern(surface: pygame.Surface, frame: int) -> None:
    """Magara ici: arka duvar, sarkitler, dikitler, zemin.

    Ilk surum uc sinus bandiydi ve ekranda **hicbir sey** okunmuyordu -
    hepsi paletin en koyu uc rengindeydi ve uzerine vinyet biniyordu.
    Sonuc: iki karakter siyah bir bosluktaki iki leke.

    Ders: sinematigin arka plani oynanisinkinden **daha aydinlik**
    olmali. Oynanista mekani kamera hareketi ve tanidik tile'lar
    anlatiyor; sabit bir karede o yardimcilar yok, mekani yalnizca
    kontrast anlatiyor.
    """
    surface.fill(palette.color("ink_soft"))

    # Arka duvar - en uzak katman, dalgali ust kenar.
    back = palette.color("stone_dark")
    for x in range(0, INTERNAL_WIDTH, 4):
        top = 52 + int(math.sin(x * 0.021) * 14 + math.sin(x * 0.008) * 9)
        surface.fill(back, (x, top, 4, GROUND_Y - top))

    # Orta katman - biraz daha yakin ve koyu, derinlik veriyor.
    mid = palette.color("stone_darkest")
    for x in range(0, INTERNAL_WIDTH, 4):
        top = 92 + int(math.sin(x * 0.033 + 1.7) * 16)
        surface.fill(mid, (x, top, 4, GROUND_Y - top))

    _draw_stalactites(surface)

    # Zemin: koyu govde + acik ust kenar. Kenar olmasa karakterler
    # zemine basmiyor, havada duruyor gibi okunuyor.
    surface.fill(palette.color("ink_soft"),
                 (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
    surface.fill(palette.color("stone"), (0, GROUND_Y, INTERNAL_WIDTH, 1))
    surface.fill(palette.color("stone_dark"),
                 (0, GROUND_Y + 1, INTERNAL_WIDTH, 2))


def _draw_stalactites(surface: pygame.Surface) -> None:
    """Tavandan sarkan kaya disleri - magara oldugu buradan okunuyor."""
    rock = palette.color("stone_dark")
    edge = palette.color("stone")
    for index in range(14):
        x = 8 + index * 34
        length = 12 + (index * 7) % 26
        for step in range(length):
            width = max(1, (length - step) // 3)
            surface.fill(rock, (x - width // 2, 44 + step, width, 1))
        surface.fill(edge, (x - 1, 44, 1, length // 2))


def _draw_sealed_door(surface: pygame.Surface, frame: int) -> None:
    """Muhurlu kapi - Katman 2'nin ilk goruntusu.

    Muhur **mor**: Bolum 3'un Mor Alev'iyle ayni renk ailesi. Oyuncu o
    rengi "buranin gucu" olarak zaten ogrendi; yeni bir renk ogretmek
    yerine var olani kullaniyoruz.
    """
    left = DOOR_X - DOOR_WIDTH // 2
    surface.fill(palette.color("stone_darkest"),
                 (left, DOOR_TOP, DOOR_WIDTH, GROUND_Y - DOOR_TOP))
    surface.fill(palette.color("stone_dark"),
                 (left + 2, DOOR_TOP + 2, DOOR_WIDTH - 4, GROUND_Y - DOOR_TOP - 2))
    # Muhur halkasi: yavas doner, nefes alir.
    cx = DOOR_X
    cy = DOOR_TOP + (GROUND_Y - DOOR_TOP) // 2
    breath = 0.6 + 0.4 * math.sin(frame * 0.04)
    colour = tuple(int(c * breath) for c in palette.color("violet_bright"))
    for index in range(6):
        angle = frame * 0.012 + index * math.tau / 6
        x = cx + int(round(math.cos(angle) * 11))
        y = cy + int(round(math.sin(angle) * 11))
        surface.fill(colour, (x, y, 2, 2))
    surface.fill(palette.color("violet"), (cx - 1, cy - 1, 3, 3))


def _draw_crack(surface: pygame.Surface, x: int) -> None:
    """Catlak - dar oldugu goruluyor."""
    top = GROUND_Y - 34
    surface.fill(palette.color("stone_dark"), (x - 14, top - 40, 28, 74))
    surface.fill(palette.color("stone_darkest"), (x - 12, top - 38, 24, 70))
    surface.fill(palette.color("void"), (x - 5, top, 10, 34))
    # Kaya disleri: yarigin DAR oldugu goruluyor. Ilk surumde disler
    # arka planla ayni koyuluktaydi ve catlak duz bir siyah cubuk gibi
    # okunuyordu - "neden gecemiyorum" sorusunun cevabi gorunmuyordu.
    for index in range(6):
        y = top + index * 6
        depth = 4 - int(abs(index - 2.5))
        surface.fill(palette.color("stone_dark"), (x - 5, y, depth, 3))
        surface.fill(palette.color("stone_dark"), (x + 5 - depth, y, depth, 3))
        surface.fill(palette.color("stone"), (x - 5, y, 1, 3))
        surface.fill(palette.color("stone"), (x + 4, y, 1, 3))


def _draw_chasm(surface: pygame.Surface) -> None:
    """Kirik zemin - ucurum ziplamayla gecilmez, goruluyor."""
    left, right = 208, 296
    surface.fill(palette.color("void"), (left, GROUND_Y, right - left,
                                         INTERNAL_HEIGHT - GROUND_Y))
    # Kenarlarda kirik tas dişleri.
    for index in range(5):
        surface.fill(palette.color("stone_darkest"),
                     (left - 4 + index * 2, GROUND_Y + index * 3, 6, 3))
        surface.fill(palette.color("stone_darkest"),
                     (right - 2 - index * 2, GROUND_Y + index * 3, 6, 3))


CINEMATIC_DURATION_HINT = int(6.0 * FPS)
