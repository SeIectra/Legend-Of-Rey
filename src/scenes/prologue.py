"""Acilis prologu - "mor konusan sey senin Yankin".

Arda'nin istegi (29.08.2026): *"Oyun basinda Rey'i anlatan bir ara sahne.
Mor yazilarin Rey'in icindeki yankilar oldugunu, ona ucuncu goz acip
yardim ettigini anlatan bir ara sahne. Kisa film hatta."*

Ve daha once (24.08.2026), tasarimin cekirdegi: *"Rey'in Yankilari sanki
bir kutsal ruh gibi... 3. bir goz olup yardimci olan bir ruh veya sesler
gibi. Ama bu yankilari kullanici oyunun basinda bilmiyor. Oyunda mor
konusan seyin senin Yankin oldugunu anlamasi lazim."*

## Cozmesi gereken sorun

Oyun boyunca ekranda **cerceve olmadan, mor, titrek** bir yazi cikiyor
(`ui/dialogue.py::_draw_echo`). Kutusu bilerek yok: kafanin icindeki ses
cerceveli bir kutuya konmaz. Ama bu, ilk kez oynayan icin bir bilmece -
kim konusuyor? Bir anlatici mi? Bir hayalet mi?

Prolog o soruyu **oynanmadan once** kapatiyor. Uc sey ogretiyor:

    1. Rey kimsenin duymadigi sesler duyuyor
    2. Koy buna "lanet" diyor
    3. Sesler ona GORMEDIGINI gosteriyor - ve bunun bir bedeli var

Ucuncusu en onemlisi: Yanki bir anlatici degil bir **mekanik**. Prolog
onu ekranin kararmasiyla gosteriyor, cunku oyunda da tam olarak oyle
oluyor (`echo_view.draw_dim`).

## Twist KORUNUYOR

`docs/gdd.md`: sesler ona yardim ederken **aslinda onu cagiriyor**.
Prolog bunu ele vermiyor. Bir tek yerde kokusu var - son panelde Yanki'nin
"asagi" demesi - ama ilk oynayista yol tarifi gibi okunuyor. Sonradan
donup bakinca baska bir sey.

## Ardo icin AYRI prolog

`docs/gdd.md` 3: Ardo'nun Yankisi yok. Ona Rey'in laneti anlatilamaz, o
yuzden uc panellik kendi acilisi var: iz surme, oluler, ve kendi gerekcesi
(DEVIR 3.7 kanonu: *"Asagida ne oldugunu biliyorum. Onu orada
birakamam."*). Ayni sinif, farkli panel listesi.

## Gorsel dil

Portreler (`src/art/portrait.py`) burada asil isini yapiyor: 64x96'lik
yuz, bir kisiyi tanitmanin en dogrudan yolu. Koy silueti ve isik
prosedurel - yeni asset gerekmiyor.

**Ucuncu goz**, kavramin gorsel karsiligi: Rey'in kasinin arasinda mor bir
nokta yaniyor ve aciliyor. Metafor degil, ekranda gorunen sey.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette, portrait
from src.art.glow import radial_glow
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.story import Panel, StoryScene
from src.ui import text
from src.ui.dialogue import Line

# --- Panel sureleri (kare) ---------------------------------------------------
# Uzun tutuldu: bu bir kisa film, bir bildirim degil. Sabirsiz oyuncu zaten
# basili tutup 3x hizlandirabiliyor (`CinematicScene`) - ve o yol
# **sessiz**, yani kimseye "atla" denmiyor.
DARK_FRAMES = 150
VILLAGE_FRAMES = 210
CURSED_FRAMES = 190
EYE_FRAMES = 240
COST_FRAMES = 200
FEAR_FRAMES = 200
# Ardo'nun iz takip paneli.
TRACE_FRAMES = 210
TODAY_FRAMES = 190

# Koy siluetindeki ev sayisi. Deterministik dagilim - `random` yok, ayni
# sahne her acilista ayni (`cave_backdrop` deseni).
HOUSE_COUNT = 7
# Sirtini donen koyluler.
VILLAGER_COUNT = 5

# Ucuncu gozun yeri **portre modulunden** geliyor, burada sabit degil.
#
# Eskiden `EYE_X = 31, EYE_Y = 23` yaziyordu ve o sayilar prosedurel
# portrenin semasindan (`FACE_CX`, `BROW`) turemisti. Arda elle
# cizilmis portreleri koyunca goz **saclarin arasinda** cikti: sema
# artik gecerli degildi. `portrait.eye_anchor()` yuzu bulup olcuyor.


class ReyPrologue(StoryScene):
    """Rey'in acilisi - Yankinin ne oldugunu ogreten kisa film."""

    background = "void"
    # **Oyuncu okuyup basar.** Arda, canli oynanis (30.08.2026): *"Introdaki
    # sinematik cok hizli geciyor, cumleler okunmuyor."* Prolog bir
    # KONUSMA; okuma hizi oyuncunun. Diger sinematikler (Bolum 1->2 inisi
    # gibi) beat, orada zamanlayici dogru.
    wait_for_input = True

    PANELS = (
        # 1. Once SES, sonra goruntu. Oyunun ilk yasattigi sey Yanki
        #    olmali - oyun zaten onun uzerine kurulu.
        Panel(DARK_FRAMES, "karanlik",
              lines=(Line("echo", "line.prologue_echo_1"),
                     Line("rey", "line.prologue_rey_1"),
                     Line("echo", "line.prologue_echo_2"))),
        # 2. Koy. Duyan bir kisi, duymayan bir koy.
        Panel(VILLAGE_FRAMES, "koy",
              lines=(Line("rey", "line.prologue_rey_2"),
                     Line("echo", "line.prologue_echo_3"))),
        # 3. **Celiski** - prologun duygusal kalbi. Yanki bir arac degil
        #    bir ILISKI; Rey ondan hem nefret ediyor hem kaybetmekten
        #    korkuyor. Bu satir olmadan Yanki sadece bir yetenek olurdu.
        Panel(CURSED_FRAMES, "lanet",
              lines=(Line("rey", "line.prologue_rey_3"),)),
        # 4. Ucuncu goz - MEKANIGIN kalbi.
        Panel(EYE_FRAMES, "ucuncu_goz",
              lines=(Line("echo", "line.prologue_echo_4"),
                     Line("rey", "line.prologue_rey_4"),
                     Line("echo", "line.prologue_echo_5"),
                     Line("echo", "line.prologue_echo_5b"),
                     Line("rey", "line.prologue_rey_5"),
                     Line("echo", "line.prologue_echo_6"),
                     Line("rey", "line.prologue_rey_6"),
                     Line("echo", "line.prologue_echo_7"))),
        # 5. Bedel. Oyunda da bedava degil.
        Panel(COST_FRAMES, "bedel",
              lines=(Line("rey", "line.prologue_rey_7"),
                     Line("echo", "line.prologue_echo_8"),
                     Line("rey", "line.prologue_rey_8"),
                     Line("echo", "line.prologue_echo_9"))),
        # 6. Korku. Yanki oyuncuyu **rahatlatmiyor** - "Kork." diyor.
        #    Bu, oyun boyunca surecek guvensizligin tohumu.
        Panel(FEAR_FRAMES, "korku",
              lines=(Line("rey", "line.prologue_rey_9"),
                     Line("echo", "line.prologue_echo_10"),
                     Line("rey", "line.prologue_rey_10"),
                     Line("echo", "line.prologue_echo_11"))),
        # 7. Cagri. Twist'in tek kokusu - ilk oynayista yol tarifi gibi
        #    okunuyor, sonradan donup bakinca baska bir sey.
        Panel(TODAY_FRAMES, "bugun",
              lines=(Line("echo", "line.prologue_echo_12"),
                     Line("echo", "line.prologue_echo_13"))),
    )

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(**kwargs)
        self.character = character
        # Portre adi ayrica tutuluyor: ucuncu gozun yeri ondan
        # olculuyor (`portrait.eye_anchor`).
        self._portrait_name = "rey"
        self.portrait = portrait.portrait("rey")
        # **Rey.mp3** - Arda: "butun Yanki kisimlari icin REY KULLAN".
        # Prolog bastan sona Yanki'nin ne oldugunu anlatiyor; parcanin
        # ait oldugu yer tam burasi.
        self.game.music.play("echo")
        # Diyalog kutusunun kucuk portresi KAPALI: paneller zaten yuzu
        # tam ekran gosteriyor. Ayni yuzu iki olcekte ayni anda gostermek
        # anlatimi degil karmasayi artiriyor - ilk surumde tam oyle
        # gorunuyordu.
        self.dialogue.show_portrait = False
        self.houses = tuple(
            (
                (index * 71 + 23) % (INTERNAL_WIDTH - 40) + 20,
                26 + (index % 3) * 7,
                20 + (index % 4) * 5,
            )
            for index in range(HOUSE_COUNT)
        )

    # --- Bitis --------------------------------------------------------------
    def on_finished(self) -> None:
        """Prolog bitti - kamera mor alevden yukari cikip koye variyor.

        `set_root` ile geciliyor: prolog yigina geri donulecek bir sey
        degil, bir kez oynanip biten bir acilis.
        """
        from src.scenes.vertical_journey import VerticalJourneyScene
        self.scenes.set_root(VerticalJourneyScene, transition=False,
                             direction="up", chapter=1,
                             character=self.character)

    # --- Cizim --------------------------------------------------------------
    def draw_panel(self, surface: pygame.Surface, panel: Panel,
                   progress: float) -> None:
        drawer = {
            "karanlik": self._draw_dark,
            "koy": self._draw_village,
            "lanet": self._draw_cursed,
            "ucuncu_goz": self._draw_third_eye,
            "bedel": self._draw_cost,
            "korku": self._draw_fear,
            "bugun": self._draw_today,
        }.get(panel.name)
        if drawer:
            drawer(surface, progress)

    # --- 1. Karanlik --------------------------------------------------------
    def _draw_dark(self, surface: pygame.Surface, progress: float) -> None:
        """Hicbir sey yok - yalnizca uzakta nefes alan mor bir isik.

        Oyunun ilk karesi bos: oyuncunun **once duymasi**, sonra gormesi
        gerekiyor. Bir goruntu koysaydik ses ona ait sanilirdi.
        """
        breath = 0.5 + 0.5 * math.sin(progress * math.pi * 2.4)
        radius = int(30 + breath * 18)
        glow = radial_glow(radius, palette.color("violet"),
                           peak=0.28 + breath * 0.14)
        surface.blit(glow, (INTERNAL_WIDTH // 2 - radius,
                            INTERNAL_HEIGHT // 2 - radius),
                     special_flags=pygame.BLEND_RGB_ADD)

    # --- 2. Koy -------------------------------------------------------------
    def _draw_village(self, surface: pygame.Surface, progress: float) -> None:
        """Gece koyu. Rey ortada, koyluler **sirtlari donuk**.

        Sirt donmek tek bir cizimle "dislanmis" diyor - bir replik
        gerekmiyor. `docs/gdd.md` 11'in dili bu: jest ya da mekanik.
        """
        self._draw_night_sky(surface)
        self._draw_houses(surface)

        ground = INTERNAL_HEIGHT - 54
        surface.fill(palette.color("ink"),
                     (0, ground, INTERNAL_WIDTH, INTERNAL_HEIGHT - ground))

        # Koyluler: kucuk, koyu, hepsi ayni yone bakiyor - Rey'e degil.
        for index in range(VILLAGER_COUNT):
            x = 60 + index * 74
            if abs(x - INTERNAL_WIDTH // 2) < 40:
                continue                     # Rey'in yeri bos kalsin
            self._draw_figure(surface, x, ground, height=20,
                              chain="ink_soft")

        # Rey: biraz daha buyuk ve mor bir hale iceriyor - onu ayiran sey
        # kiyafeti degil, duydugu sey.
        rey_x = INTERNAL_WIDTH // 2
        halo = int(14 + progress * 10)
        glow = radial_glow(halo, palette.color("violet"), peak=0.30)
        surface.blit(glow, (rey_x - halo, ground - 24 - halo),
                     special_flags=pygame.BLEND_RGB_ADD)
        self._draw_figure(surface, rey_x, ground, height=26,
                          chain="abyss_light")

    # --- 3. Lanet -----------------------------------------------------------
    def _draw_cursed(self, surface: pygame.Surface, progress: float) -> None:
        """Rey'in yuzu, yakin. Kimse yok - yalnizlik kadrajda.

        Portre burada asil isini yapiyor: bir kisiyi tanitmanin en
        dogrudan yolu yuzu. Oyun ici sprite'ta kafa 7 piksel; bu olcekte
        ifade okunuyor (`src/art/portrait.py` basligindaki olcum).
        """
        self._draw_portrait(surface, scale=2, lift=int(progress * 6))

    # --- 4. Ucuncu goz ------------------------------------------------------
    def _draw_third_eye(self, surface: pygame.Surface,
                        progress: float) -> None:
        """**Prologun kalbi.** Kaslarin arasinda mor bir nokta aciliyor.

        Metafor degil: ekranda gorunen sey. "Ucuncu goz" sozu hic
        gecmiyor - gecmesine gerek yok, resim zaten onu soyluyor.

        Uc asamada aciliyor: nokta -> yariq -> tam goz. Aninda acilsaydi
        bir efekt olurdu; yavas acilinca bir **olay** oluyor.
        """
        scale = 2
        origin = self._draw_portrait(surface, scale=scale)

        anchor_x, anchor_y = portrait.eye_anchor(self._portrait_name)
        eye_x = origin[0] + anchor_x * scale
        eye_y = origin[1] + anchor_y * scale

        # 0.0-0.35 nokta, 0.35-0.7 aciliyor, 0.7+ tam ve nabizli.
        if progress < 0.35:
            grow = progress / 0.35
            radius = max(1, int(2 + grow * 3))
            colour = palette.color("violet")
        elif progress < 0.7:
            grow = (progress - 0.35) / 0.35
            radius = int(5 + grow * 7)
            colour = palette.color("violet_bright")
        else:
            pulse = 0.5 + 0.5 * math.sin((progress - 0.7) * 26.0)
            radius = int(12 + pulse * 4)
            colour = palette.color("violet_bright")

        glow = radial_glow(radius, colour, peak=0.85)
        surface.blit(glow, (eye_x - radius, eye_y - radius),
                     special_flags=pygame.BLEND_RGB_ADD)
        # Gozun kendisi: dikey badem - yatay olsaydi "isik" gibi okurdu.
        if progress > 0.3:
            height = int(3 + progress * 7)
            surface.fill(colour, (eye_x - 1, eye_y - height // 2, 2, height))
            surface.fill(palette.color("bone"), (eye_x, eye_y - 1, 1, 2))

    # --- 5. Bedel -----------------------------------------------------------
    def _draw_cost(self, surface: pygame.Surface, progress: float) -> None:
        """Goz acik - ama dunya kararıyor.

        Oyundaki bedelin **birebir ayni gorseli** (`echo_view.draw_dim`).
        Prolog bir sey ogretiyorsa oyunun kullandigi dilde ogretmeli;
        baska bir gorsel kullansaydi oyuncu bagi kurmazdi.
        """
        origin = self._draw_portrait(surface, scale=2)
        anchor_x, anchor_y = portrait.eye_anchor(self._portrait_name)
        eye_x = origin[0] + anchor_x * 2
        eye_y = origin[1] + anchor_y * 2

        glow = radial_glow(14, palette.color("violet_bright"), peak=0.9)
        surface.blit(glow, (eye_x - 14, eye_y - 14),
                     special_flags=pygame.BLEND_RGB_ADD)

        # Vinyet kapaniyor: gorulen sey artiyor, gorunen alan azaliyor.
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT),
                              pygame.SRCALPHA)
        veil.fill((*palette.color("violet_dark"), int(150 * progress)))
        surface.blit(veil, (0, 0))
        edge = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT),
                              pygame.SRCALPHA)
        band = int(INTERNAL_HEIGHT * 0.5 * progress)
        edge.fill((*palette.color("void"), 200), (0, 0, INTERNAL_WIDTH, band))
        edge.fill((*palette.color("void"), 200),
                  (0, INTERNAL_HEIGHT - band, INTERNAL_WIDTH, band))
        surface.blit(edge, (0, 0))

    # --- 6. Korku -----------------------------------------------------------
    def _draw_fear(self, surface: pygame.Surface, progress: float) -> None:
        """Rey gozlerini aciyor. Goz soner, karanlik KALIR.

        Arda'nin metnindeki en sert donus burada: Rey "sizden
        korkuyorum" diyor ve Yanki **rahatlatmiyor** - "Kork." diyor.
        Panel de rahatlatmiyor: mor sonuyor ama ekran acilmiyor. Bedel
        kalici, kazanc gecici.
        """
        origin = self._draw_portrait(surface, scale=2)
        anchor_x, anchor_y = portrait.eye_anchor(self._portrait_name)
        eye_x = origin[0] + anchor_x * 2
        eye_y = origin[1] + anchor_y * 2

        # Goz soneyor - ama tamamen degil. Bir daha hic kapanmayacak.
        fade = max(0.15, 1.0 - progress)
        radius = max(3, int(12 * fade))
        glow = radial_glow(radius, palette.color("violet_bright"),
                           peak=0.75 * fade)
        surface.blit(glow, (eye_x - radius, eye_y - radius),
                     special_flags=pygame.BLEND_RGB_ADD)

        # Karanlik geri cekilmiyor: `_draw_cost`'un birakip gittigi
        # yerden devam ediyor.
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT),
                              pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 120))
        surface.blit(veil, (0, 0))

    # --- 7. Bugun -----------------------------------------------------------
    def _draw_today(self, surface: pygame.Surface, progress: float) -> None:
        """Kolye, ve asagidan gelen isik. Oyuna baglanan panel."""
        self._draw_night_sky(surface)
        ground = INTERNAL_HEIGHT - 40
        surface.fill(palette.color("ink"),
                     (0, ground, INTERNAL_WIDTH, INTERNAL_HEIGHT - ground))

        # Yarik: yerden yukari acilan mor bir cizgi. Bolum 1'in sonunda
        # olacak seyin **on isareti** - ama henuz kucuk.
        crack_h = int(6 + progress * 34)
        crack_x = INTERNAL_WIDTH // 2 + 70
        for offset in range(crack_h):
            width = max(1, 3 - offset // 12)
            surface.fill(palette.color("violet"),
                         (crack_x - width // 2, ground - offset, width, 1))
        glow = radial_glow(int(10 + progress * 18),
                           palette.color("violet"), peak=0.5)
        radius = glow.get_width() // 2
        surface.blit(glow, (crack_x - radius, ground - crack_h // 2 - radius),
                     special_flags=pygame.BLEND_RGB_ADD)

        # Figur buyuk ve **hale iceriyor**: ilk surumde 26 piksellik koyu
        # bir siluet gece zeminine karisiyordu ve panel bos gorunuyordu.
        figure_x = INTERNAL_WIDTH // 2 - 40
        halo = radial_glow(20, palette.color("abyss_light"), peak=0.32)
        surface.blit(halo, (figure_x - 20, ground - 30 - 20),
                     special_flags=pygame.BLEND_RGB_ADD)
        self._draw_figure(surface, figure_x, ground, height=34,
                          chain="stone_light")
        # Kolye: gogsunde altin bir parilti. Bolum 1'de Cemo'nun verecegi
        # sey - oyuncu onu once BURADA goruyor.
        necklace = radial_glow(6, palette.color("gold"), peak=0.85)
        surface.blit(necklace, (figure_x - 6, ground - 20 - 6),
                     special_flags=pygame.BLEND_RGB_ADD)
        surface.fill(palette.color("gold"), (figure_x, ground - 20, 1, 2))

    # --- Yardimcilar --------------------------------------------------------
    def _draw_portrait(self, surface: pygame.Surface, scale: int = 2,
                       lift: int = 0) -> tuple[int, int]:
        """Portreyi ortalar, sol-ust kosesini doner (goz konumu icin)."""
        if self.portrait is None:
            return (0, 0)
        width = self.portrait.get_width() * scale
        height = self.portrait.get_height() * scale
        image = pygame.transform.scale(self.portrait, (width, height))
        x = INTERNAL_WIDTH // 2 - width // 2
        y = INTERNAL_HEIGHT - height + 14 - lift
        surface.blit(image, (x, y))
        return (x, y)

    def _draw_night_sky(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("abyss_dark"))
        for index in range(40):
            x = (index * 97 + 13) % INTERNAL_WIDTH
            y = (index * 53) % 70
            surface.fill(palette.color("stone_light"), (x, y, 1, 1))

    def _draw_houses(self, surface: pygame.Surface) -> None:
        base = INTERNAL_HEIGHT - 54
        for x, height, width in self.houses:
            surface.fill(palette.color("void"),
                         (x, base - height, width, height))
            # Cati: ucgen yerine iki basamak - piksel olcekte daha temiz.
            surface.fill(palette.color("void"),
                         (x + 2, base - height - 3, width - 4, 3))
            # Tek pencere, sicak - koy yasiyor.
            surface.fill(palette.color("ember"),
                         (x + width // 2, base - height // 2, 2, 2))

    def _draw_figure(self, surface: pygame.Surface, x: int, ground: int,
                     height: int, chain: str) -> None:
        """Basit siluet: kafa + govde. Uzaktan bir insan bu kadar."""
        colour = palette.color(chain)
        body_h = height - 6
        surface.fill(colour, (x - 3, ground - body_h, 6, body_h))
        surface.fill(colour, (x - 2, ground - height, 5, 5))


class ArdoPrologue(ReyPrologue):
    """Ardo'nun acilisi - **Yanki yok**, iz var.

    `docs/gdd.md` 3: Ardo'nun Yankisi yok. Ona Rey'in lanetini anlatmak
    yanlis olurdu; kendi duyusu var (`src/systems/tracking.py`, Iz Surme)
    ve kendi gerekcesi (DEVIR 3.7): *"Asagida ne oldugunu biliyorum. Onu
    orada birakamam."*

    Uc panel - Rey'inki alti. Kisa olmasi bilincli: Ardo'nun hikayesi
    saklaniyor, oyun boyunca aciliyor. Rey'in laneti bastan anlatilmali
    cunku oyunun MEKANIGI o; Ardo'nunki bir sir.
    """

    PANELS = (
        Panel(DARK_FRAMES, "iz",
              lines=(Line("ardo", "line.prologue_ardo_1"),)),
        Panel(TRACE_FRAMES, "iz",
              lines=(Line("ardo", "line.prologue_ardo_2"),
                     Line("ardo", "line.prologue_ardo_3"))),
        Panel(VILLAGE_FRAMES, "koy",
              lines=(Line("ardo", "line.prologue_ardo_4"),)),
        Panel(TODAY_FRAMES, "bugun",
              lines=(Line("ardo", "line.prologue_ardo_5"),)),
    )

    def on_enter(self, character: str = "ardo", **kwargs: object) -> None:
        super().on_enter(character=character, **kwargs)
        self._portrait_name = "ardo"
        self.portrait = portrait.portrait("ardo")
        # Yankisi yok - Yanki parcasi da yok. **Ardo.mp3**.
        self.game.music.play("companion")

    def draw_panel(self, surface: pygame.Surface, panel: Panel,
                   progress: float) -> None:
        if panel.name == "iz":
            self._draw_traces(surface, progress)
            return
        super().draw_panel(surface, panel, progress)

    def _draw_traces(self, surface: pygame.Surface, progress: float) -> None:
        """Karanlikta beliren ayak izleri - Iz Surme'nin gorsel dili.

        Rey'in ilk paneli bir SES; Ardo'nunki bir IZ. Ikisi de karanlikta
        basliyor ve fark tam olarak burada okunuyor.
        """
        surface.fill(palette.color("void"))
        ground = INTERNAL_HEIGHT - 60
        count = int(progress * 12)
        for index in range(count):
            x = 40 + index * 34
            fade = 1.0 - index / 12.0
            colour = palette.color("bone")
            veil = pygame.Surface((4, 2), pygame.SRCALPHA)
            veil.fill((*colour, int(200 * fade)))
            surface.blit(veil, (x, ground + (index % 2) * 3))
        if progress > 0.4:
            self._draw_figure(surface, 40 + count * 34, ground + 4,
                              height=24, chain="stone")
