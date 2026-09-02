"""Sessiz diyalog - kelimesiz secim.

`docs/derinlestirme.md` 3.3, **baglayici**:

    "Ardo ile iletisim: konusma yok ama **jest secimi** var. Bir anda uc
     ikon cikar (elini uzat / basini salla / geri cekil). Secimin
     iliskiyi sekillendirir.
       - Kelime yok -> ceviri sifir maliyet
       - Secim var  -> oyuncu iliskiye sahip olur
       - 3-4 kritik anda kullanilir, her sahnede degil
     **B7 (el tutma), B8 (yara sarma), B16 (kurtarma), B18 (final)** -
     dort an yeter."

Dort andan ikisi (B7, B8) bu sistem yazilmadan gecti; B16 ve B18 kaldi.
Arda 02.09.2026'da B16'da kurulmasina karar verdi.

## Neden hicbir sey "dogru" degil

Bir secim ekrani genellikle bir bilmecedir: biri dogru, otekiler yanlis.
Burasi oyle degil. Uc jestin ucu de gecerli ve hicbiri bolumu
kaybettirmiyor - degisen sey **ton**. Yanlis cevabi olan bir secim
oyuncuyu iliskinin sahibi degil bir sinav ogrencisi yapardi ve belgenin
"oyuncu iliskiye sahip olur" cumlesini tersine cevirirdi.

O yuzden burada puan, kilit ya da basari yok. Yalnizca ne sectigin
kaydediliyor (`SaveData.flags`) ve sonraki sahneler ona bakabiliyor.

## Kelime yok - **gercekten** yok

Ikonlar `src/ui/balloon.py`'nin desenleri; font glifi degil. Ekranda tek
bir cumle bile gecmiyor, secim tamamen sekil uzerinden okunuyor. Bu
hem belgenin "ceviri sifir maliyet" gerekcesi hem de oyunun anlatim
dili (`docs/gdd.md` 2: oyunda hicbir replik yok).

Erisilebilirlik: secili jest hem **parliyor** hem **buyuyor** hem
altinda bir imlec tasiyor. Uc kanal, cunku renk tek basina yeterli
degil (`CLAUDE.md` 10).
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.art import palette
from src.ui import balloon

# Balonlar arasi yatay mesafe (piksel). Ikon 7, balon 13 genis.
# 34 ile render edildi ve uc balon birbirine yapisik okunuyordu; 46
# aralarina bir balon genisligi kadar bosluk koyuyor ve uclusu hala
# 480 piksellik ekranin ortasinda rahat duruyor.
SPACING = 46

# Secili balonun ne kadar yukari kalktigi - **konum** kanali.
LIFT = 5

# Imlec isareti seciliyi gosteren ucuncu kanal.
CURSOR_WIDTH = 9

# Secim acilirken balonlar sirayla geliyor (kare). Hepsi ayni anda
# gelseydi bir menu gibi okunurdu; sirali gelis onlari bir dusunce
# gibi gosteriyor.
REVEAL_STEP = 7

# Secimden sonra bu kadar kare boyunca secilen balon ekranda kaliyor,
# otekiler soluyor. Anin oturmasi icin.
SETTLE_FRAMES = 26


@dataclass(frozen=True)
class Gesture:
    """Bir jest. `key` kayda yazilan ad, `icon` balon deseni."""

    key: str
    icon: str


# Bolum 16'nin uclusu. Sira anlamli: uzanmak solda, geri cekilmek
# sagda, ortada tarafsiz olan. Oyuncu ilk defa D-pad'e bastiginda
# hangi yone gittigi bir sey ifade etsin.
REACH = Gesture("reach", "hand")     # elini uzat
NOD = Gesture("nod", "nod")          # basini salla
WITHDRAW = Gesture("withdraw", "back")  # geri cekil

THREE = (REACH, NOD, WITHDRAW)


class GestureChoice:
    """Uc jest, bir secim. Kelime yok."""

    def __init__(self, options: tuple[Gesture, ...] = THREE,
                 start: int = 1) -> None:
        if not options:
            raise ValueError("jest secimi bos olamaz")
        self.options = options
        # Varsayilan ORTA. Soldaki onceden secili olsaydi acele eden
        # oyuncu farkinda olmadan "elini uzat" derdi - secimin anlami
        # kalmazdi.
        self.index = max(0, min(len(options) - 1, start))
        self.chosen: Gesture | None = None
        self.frames = 0
        self.settle = 0

    # --- Durum --------------------------------------------------------------
    @property
    def done(self) -> bool:
        """Secim yapildi ve oturma suresi de doldu."""
        return self.chosen is not None and self.settle <= 0

    @property
    def current(self) -> Gesture:
        return self.options[self.index]

    def visible_count(self) -> int:
        """Kac balon acildi - sirayla geliyorlar."""
        return min(len(self.options), 1 + self.frames // REVEAL_STEP)

    @property
    def ready(self) -> bool:
        """Hepsi acildi mi - onaydan once beklenmeli."""
        return self.visible_count() >= len(self.options)

    # --- Girdi --------------------------------------------------------------
    def move(self, delta: int) -> bool:
        """Imleci kaydirir. Gercekten degistiyse True (ses icin)."""
        if self.chosen is not None or not self.ready:
            return False
        # **Sarmiyor.** Uc secenekte sarmalama, oyuncunun nerede
        # oldugunu kaybetmesine yol acar; kenarda durmak daha okunur.
        new_index = max(0, min(len(self.options) - 1, self.index + delta))
        if new_index == self.index:
            return False
        self.index = new_index
        return True

    def confirm(self) -> Gesture | None:
        """Secer. Zaten secilmisse None."""
        if self.chosen is not None or not self.ready:
            return None
        self.chosen = self.current
        self.settle = SETTLE_FRAMES
        return self.chosen

    def update(self) -> None:
        self.frames += 1
        if self.chosen is not None and self.settle > 0:
            self.settle -= 1

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, x: int, y: int) -> None:
        """Balonlari (x, y) etrafinda **yatay** dizer.

        (x, y) dizinin ortasi ve balonlarin **alt** hizasi -
        `balloon.draw` verilen noktanin ustune ciziyor.
        """
        shown = self.visible_count()
        total = len(self.options)
        left = x - (total - 1) * SPACING // 2
        for index, gesture in enumerate(self.options):
            if index >= shown:
                continue
            selected = index == self.index
            if self.chosen is not None:
                # Secimden sonra secilmeyenler soluyor - goz secilene
                # gidiyor ve an oturuyor.
                alpha = 255 if gesture is self.chosen else 70
                selected = gesture is self.chosen
            else:
                alpha = 255 if selected else 150
            colour = (palette.color("violet_bright") if selected
                      else palette.role("ui_text_dim"))
            bx = left + index * SPACING
            by = y - (LIFT if selected else 0)
            balloon.draw(surface, gesture.icon, bx, by,
                         frame=self.frames, colour=colour, alpha=alpha)
            if selected:
                # Imlec iki piksel kalin: bir piksellik cizgi 480x270'te
                # render edilince neredeyse gorunmuyordu.
                surface.fill(colour,
                             (bx - CURSOR_WIDTH // 2, y + 3, CURSOR_WIDTH, 2))
