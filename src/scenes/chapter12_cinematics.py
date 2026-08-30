"""Bolum 12'nin iki ara sahnesi - "Kamp" ve "Mektup".

`docs/yapi.md` B12: *"Kamp kalintilari, onun cizdigi isaretler, senin
icin birakilmis erzak, duvara kazinmis kucuk bir figur: sen.
Romantik an: **Yoklugunda anlatilan yakinlik.**"*

## Iki sahne de onu GOSTERMIYOR

Bolumun tek kurali bu. Ardo bu bolumde ekranda yok - B10'da ayrildi,
B16'da donecek. Sahneler onun **birakugi seylerle** konusuyor: sogumus
bir ates, bir denk, kuyuya kurulmus bir duzenek.

Bir "hatirlama" ya da hayalet sahnesi yazmak kolay olurdu ve bolumu
mahvederdi. `docs/gdd.md` 11: romantik yay **mekanikle** anlatiliyor.
Yokluk da bir mekanik: goremedigin biri, birakugi seylerden okunur.

## Kapanis sahnesi ne kadarini gordugunu BILIYOR

`found`/`total` cagirandan geliyor. Alti izin hepsini bulan oyuncu
farkli bir kapanis goruyor - suclama yok, kutlama da yok; yalnizca
**ne kadarini gordugunun** farki. Bir nefes bolumunun olcusu beceri
degil yakinlik.
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

GROUND_Y = 188


class _Chapter12Cinematic(StagedScene):
    background = "void"
    wait_for_input = True

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.absent = other_character(character)
        # ACTORS `super().on_enter()`ten ONCE - orasi cue zincirini
        # tetikliyor ve zincir `self.actors`i ariyor.
        self.ACTORS = self.build_actors()
        super().on_enter(**kwargs)

    def build_actors(self) -> tuple[ActorSpec, ...]:
        return (ActorSpec("player", self.character, 190.0, GROUND_Y,
                          facing=1, scale=2),)

    def voice(self, echo_key: str, ardo_key: str) -> Line:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
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


# --- Ara Sahne 1: "Kamp" ------------------------------------------------------
class CampCinematic(_Chapter12Cinematic):
    """Kuyu basi. Sogumus ates, birakilmis denk, kurulmus duzenek.

    Uc panel, uc nesne, ve **hicbiri konusmuyor**. Oyuncu odaya
    girince zaten gormustu; sahnenin isi onlari bir SIRAYA koymak:
    ates (o buradaydi) -> denk (senin icin birakti) -> duzenek
    (devam etmeni istedi).
    """

    PANELS = (
        Panel(48, "varis", wait_for_input=False, fade_in=16, cues=(
            Cue("player", state="run", face=1,
                move_to=(226.0, GROUND_Y), move_frames=30),
            Cue("player", delay=30, state="idle"),
        )),
        # Sogumus ates - **is** degil kul. Zaman gecmis.
        Panel(46, "ates", cues=(
            Cue("player", state="idle", face=1, burst="soot",
                burst_count=8, sound="echo_close"),
        )),
        Panel(46, "denk", cues=(
            Cue("player", state="idle", face=1, sound="item_pickup"),
        )),
        # Duzenek. Kuyunun agzinda, hazir bekliyor.
        Panel(50, "duzenek", fade_out=14, cues=(
            Cue("player", state="idle", face=1, sound="rift_open",
                burst="dust", burst_count=10),
        )),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self.motes = MoteField(16, drift=-0.12, sway=0.7, tone="stone_dark")
        self.vignette = 0.38
        # Sogumus atesin yerinde **hala biraz sicaklik** var - isik
        # zayif ama var. Tamamen sondurseydik sahne "terk edilmis"
        # olurdu; oysa anlatilan sey "az once buradaydi".
        self.add_light(150, GROUND_Y - 14, 44,
                       palette.color("ember_dark"), peak=0.34)
        self.game.music.hold("emotional", 780)
        self._write({
            "ates": Line(self.character, "line.ch12_cine_fire"
                         if character != "ardo" else "line.ch12_cine_fire_ardo"),
            "denk": Line(self.character, "line.ch12_cine_pack"
                         if character != "ardo" else "line.ch12_cine_pack_ardo"),
            "duzenek": self.voice("line.ch12_echo_rig",
                                  "line.ch12_trace_rig"),
        })

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_camp(surface, self.frame, panel.name)


# --- Ara Sahne 2: "Mektup" ★ --------------------------------------------------
class LetterCinematic(_Chapter12Cinematic):
    """Dip. Bolumun adini burada aliyor.

    `found` kac izin bulundugu. Uc varyant:

        hepsi      -> mektubun tamami okundu
        cogu       -> eksik ama anlasilmis
        az         -> gecip gitmis; **suclama yok**

    Ucuncusu onemli: bir nefes bolumu oyuncuyu azarlamaz. Fark yalnizca
    Rey'in ne kadar sey bildigi - ve bilmedigi sey B16'da geri gelecek.
    """

    PANELS = (
        Panel(44, "inis", wait_for_input=False, fade_in=14, cues=(
            Cue("player", state="fall", face=1),
            Cue("player", delay=20, state="land", sound="land_soft"),
        )),
        Panel(48, "dip", cues=(
            Cue("player", state="idle", face=1),
        )),
        # Yuze kesme: bolumun butun agirligi tek bir ifadede.
        Panel(52, "yuz", closeup="player", fade_in=10),
        Panel(46, "son", cues=(
            Cue("player", state="idle", face=1),
        )),
        Panel(48, "devam", fade_out=16, cues=(
            Cue("player", state="idle", face=1, burst="echo",
                burst_count=12, sound="necklace_warm"),
        )),
    )

    def on_enter(self, character: str = "rey", found: int = 0,
                 total: int = 6, **kwargs: object) -> None:
        # Sayilar **cagirandan** geliyor. Ilk tasarimda sahne
        # `self.scenes.stack[-2]` ile alttaki bolume el yordamiyla
        # bakiyordu - calisir ama kirilgan (ayni ders B10'da yazildi).
        self.found = found
        self.total = total
        super().on_enter(character=character, **kwargs)
        self.motes = MoteField(20, drift=-0.18, sway=0.9, tone="violet_dark")
        self.vignette = 0.46
        self.add_light(240, GROUND_Y - 30, 58,
                       palette.color("violet" if character != "ardo"
                                     else "bone"), peak=0.3)
        self.game.music.hold("emotional", 820)
        self._write_variant()

    # Uc varyant x iki karakter = alti anahtar, ve **altisi da duz
    # dize**. Ilk surum `dip + suffix` ile uretiyordu; `test_lang.py`
    # hesaplanan adi goremedigi icin alti replik "olu anahtar" diye
    # raporlandi. Tablo bunu acikca yaziyor - hem okunur hem taranir.
    VARIANTS = {
        "all": (("line.ch12_letter_all", "line.ch12_letter_all_ardo"),
                ("line.ch12_after_all", "line.ch12_after_all_ardo")),
        "some": (("line.ch12_letter_some", "line.ch12_letter_some_ardo"),
                 ("line.ch12_after_some", "line.ch12_after_some_ardo")),
        "few": (("line.ch12_letter_few", "line.ch12_letter_few_ardo"),
                ("line.ch12_after_few", "line.ch12_after_few_ardo")),
    }

    def _write_variant(self) -> None:
        """Uc varyant, tek sahne. Pahali degil: degisen iki replik.

        Ucuncu varyantta (`few`) **suclama yok**. Bir nefes bolumu
        oyuncuyu azarlamaz; degisen tek sey Rey'in ne kadar sey
        bildigi - ve bilmedigi B16'da geri gelecek.
        """
        if self.found >= self.total:
            band = "all"
        elif self.found >= self.total // 2:
            band = "some"
        else:
            band = "few"
        (dip_rey, dip_ardo), (son_rey, son_ardo) = self.VARIANTS[band]
        ardo = self.character == "ardo"
        self._write({
            "dip": Line(self.character, dip_ardo if ardo else dip_rey),
            "son": Line(self.character, son_ardo if ardo else son_rey),
            "devam": self.voice("line.ch12_echo_deeper",
                                "line.ch12_trace_deeper"),
        })

    def draw_stage_background(self, surface: pygame.Surface, panel: Panel,
                              progress: float,
                              offset: tuple[int, int]) -> None:
        _draw_shaft_bottom(surface, self.frame, self.found, self.total)


# --- Arka planlar --------------------------------------------------------------
def _draw_camp(surface: pygame.Surface, frame: int, panel: str) -> None:
    """Kuyu basi - kamp ve kuyunun agzi.

    Nesneler panele gore **sirayla** vurgulaniyor. Ucu ayni anda
    parlasaydi hicbiri okunmazdi; oyuncunun gozu tek bir seye gitmeli.
    """
    surface.fill(palette.color("ink"))
    for y in range(46, GROUND_Y, 13):
        surface.fill(palette.color("stone_darkest"), (0, y, INTERNAL_WIDTH, 10))
        for x in range((y // 13 % 2) * 14, INTERNAL_WIDTH, 28):
            surface.fill(palette.color("ink_soft"), (x, y, 2, 10))

    # Kuyu agzi - sagda, karanlik. Bolumun gidecegi yer.
    surface.fill(palette.color("void"), (300, GROUND_Y - 6, 120, 40))
    surface.fill(palette.color("stone_dark"), (300, GROUND_Y - 8, 120, 3))

    hot = panel == "ates"
    # Sogumus ates: kul halkasi, ustunde zar zor bir kizillik.
    surface.fill(palette.color("stone_darkest"), (138, GROUND_Y - 5, 26, 5))
    glow = (0.5 + 0.5 * math.sin(frame * 0.06)) * (1.0 if hot else 0.45)
    ember = tuple(int(c * glow) for c in palette.color("ember_dark"))
    surface.fill(ember, (146, GROUND_Y - 7, 9, 3))

    # Denk - birakilmis, agzi acik.
    pack = "ember_light" if panel == "denk" else "earth_dark"
    surface.fill(palette.color(pack), (196, GROUND_Y - 13, 16, 13))
    surface.fill(palette.color("earth"), (198, GROUND_Y - 15, 12, 3))

    # Duzenek - kuyunun agzinda asili zincir ve kafes.
    rig = "gold" if panel == "duzenek" else "stone_dark"
    for chain_x in (326, 394):
        surface.fill(palette.color("stone_dark"), (chain_x, 40, 2,
                                                   GROUND_Y - 44))
    surface.fill(palette.color(rig), (324, GROUND_Y - 8, 72, 4))

    surface.fill(palette.color("ink_soft"),
                 (0, GROUND_Y, 300, INTERNAL_HEIGHT - GROUND_Y))
    surface.fill(palette.color("stone_dark"), (0, GROUND_Y, 300, 1))


def _draw_shaft_bottom(surface: pygame.Surface, frame: int, found: int,
                       total: int) -> None:
    """Kuyunun dibi - ve **yukarida geride biraktigin sey.**

    Bulunan izler tavana dogru uzanan bir dizi olarak duruyor: kac
    tanesini gordugun ekranda, sayi olarak degil **yol olarak**
    okunuyor. Bulunmayanlar da orada, yalnizca sonuk - "kacirdiklarin
    da vardi" demenin sessiz yolu.
    """
    surface.fill(palette.color("void"))
    for y in range(0, GROUND_Y, 16):
        depth = y / GROUND_Y
        tone = tuple(int(c * (0.25 + 0.55 * depth))
                     for c in palette.color("stone_darkest"))
        surface.fill(tone, (0, y, INTERNAL_WIDTH, 13))

    # Yukari uzanan iz dizisi - kuyunun icinde geride kalanlar.
    for index in range(total):
        y = 30 + index * 22
        lit = index < found
        pulse = 0.6 + 0.4 * math.sin(frame * 0.05 + index)
        base = palette.color("gold" if lit else "stone_dark")
        colour = tuple(int(c * (pulse if lit else 0.5)) for c in base)
        x = 120 if index % 2 == 0 else INTERNAL_WIDTH - 128
        surface.fill(colour, (x, y, 4, 4))
        surface.fill(colour, (x - 3, y + 5, 10, 1))

    surface.fill(palette.color("ink_soft"),
                 (0, GROUND_Y, INTERNAL_WIDTH, INTERNAL_HEIGHT - GROUND_Y))
    surface.fill(palette.color("stone_dark"), (0, GROUND_Y, INTERNAL_WIDTH, 1))
