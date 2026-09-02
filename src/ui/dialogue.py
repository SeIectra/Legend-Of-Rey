"""Diyalog - konusan karakterler ve kafadaki ses.

`docs/gdd.md` 2 oyunu **diyalogsuz** tasarlamisti (statik panel, jest, ikon
balonu). Arda bu karari degistirdi (22.08.2026): konusma eklenebilir.

## Yanki'nin kutusu yok

En onemli tasarim karari bu. Yanki bir karakter degil, **Rey'in kafasinin
icindeki ses**. Onu diger konusmacilarla ayni cerceveli kutuya koymak onu
"odadaki bir baska kisi" yapardi ve butun tekinsizligini oldururdu.

    Rey / Ardo / Cemo   cerceveli kutu, ad etiketi, sabit
    Yanki               cerceve yok, mor, hafifce suzuluyor, harfler titrek

Oyuncu ikisini **bakmadan** ayirt ediyor. B14'te ses susunca o bosluk da
gorsel olarak hissedilecek.

## Jest kaybolmuyor

Diyalog bir kanal **ekliyor**, digerlerini degistirmiyor. Cemo'nun yariga
cekildigi an hala kelimesiz - orada bir replik yazmak ani ucuzlatirdi.
Kelimeler sesin kendisi konustugunda ve iki kisi karsi karsiya geldiginde
devreye giriyor.

## Ceviri yuku

Bu karar ceviri yukunu buyutuyor: her replik iki dilde. Altyapi zaten
hazir (JSON tablolari, parite testi), yalnizca satir sayisi artiyor.
Repliker dil anahtari olarak yaziliyor, metin olarak degil.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from src.art import palette
from src.art import portrait as portrait_art
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.ui import text
from src.ui.font_data import GLYPH_HEIGHT, GLYPH_WIDTH, TRACKING
from src.ui.i18n import t
from src.ui.widgets import panel

# Yazim hizi: kare basina karakter. 2.0 = saniyede 120 karakter, okunakli
# ama beklemeye zorlamiyor. Basili tutunca aninda tamamlaniyor.
TYPE_SPEED = 2.0
ADVANCE_LOCK_FRAMES = 8          # Yanlislikla iki repligi birden gecme

# Tamamlanmis bir replik onaylanmadan bu kadar kare beklerse **kendiliginden**
# ilerler/kapanir - ama yalnizca `start(..., auto_advance=True)` ile
# baslatilmis dizilerde (bkz. asagidaki `auto_advance` parametresi).
# Sinematik beatler zamanlayiciyla ilerliyor ve oyuncu "onayla" tusunun
# repligi ilerlettigini bilmeyebilir (ilk oturum, ilk dakika) - onaysiz
# kalan bir cok-replikli dizinin ikinci satiri (`ch01_gift` beatindeki
# Rey'in tesekkuru gibi) boylece hicbir zaman ekrana gelmeden bir sonraki
# `say()` cagrisiyla sessizce kayboluyordu. Arda'nin "bunlar cok anlamsiz
# cumleler" geri bildirimi bunun sonucuydu. Basili tutmak/onaylamak hala
# daha hizli gecisi saglar - bu yalnizca bir alt sinir.
#
# Bilerek **varsayilan degil**: bir zamanlayicinin yarisamadigi normal
# kesif/dovus repligi (orn. chapter02'nin boss karsilasma satiri) oyuncu
# onaylamadan kendiliginden kapanirsa, meskul oyuncunun hic okumadigi
# metin sessizce kaybolur - `AUTO_ADVANCE_HOLD_FRAMES` o senaryo icin
# tasarlanmadi, yalnizca beat-zamanlayicisiyla yarisan diyaloglar icin.
AUTO_ADVANCE_HOLD_FRAMES = 50

BOX_X = 24
BOX_WIDTH = INTERNAL_WIDTH - 48
BOX_BOTTOM = INTERNAL_HEIGHT - 16
BOX_PADDING = 8
LINE_STEP = GLYPH_HEIGHT + 3
MAX_LINES = 3
CHAR_ADVANCE = GLYPH_WIDTH + TRACKING
WRAP_WIDTH = (BOX_WIDTH - 20) // CHAR_ADVANCE

# --- Portre ------------------------------------------------------------------
# Konusan kisinin bustu kutunun **solunda**, alt kenari kutuyla hizali ve
# uzeri kutunun ustune tasiyor - klasik JRPG kadraji.
#
# Neden portre: oyun ici sprite'ta kafa 7 piksel ve yuz ifadesi
# okunamiyor (`src/art/portrait.py` basligindaki olcum). Konusan kisinin
# YUZUNU gormek anlatimin yarisi; Arda'nin 29.08.2026 istegi tam olarak
# buydu ve tek karsilanabilecegi yer burasi.
PORTRAIT_X = 6
PORTRAIT_GAP = 4
# Portre varken metin bu kadar iceri kayiyor ve satir genisligi daraliyor.
PORTRAIT_INSET = 56
WRAP_WIDTH_PORTRAIT = (BOX_WIDTH - 20 - PORTRAIT_INSET) // CHAR_ADVANCE

# Konusmaci kimligi renkle tasiniyor - ad etiketi okunmadan da anlasilsin.
SPEAKER_COLOURS = {
    "rey": "abyss_light",
    "ardo": "stone_light",
    "cemo": "gold",
    "echo": "violet_bright",
}

# Ad etiketlerinin dil anahtarlari **acikca** yazili. f-string ile
# kurulani tests/test_lang.py kaynak taramasinda goremiyor ve "olu
# anahtar" sayiyor. Bu tuzaga dorduncu kez dusuldu; artik her yerde
# anahtarlar duz yaziliyor.
SPEAKER_KEYS = {
    "rey": "speaker.rey",
    "ardo": "speaker.ardo",
    "cemo": "speaker.cemo",
    "echo": "speaker.echo",
}
ECHO = "echo"


@dataclass(frozen=True)
class Line:
    """Tek bir replik. `key` dil anahtari, metin degil."""

    speaker: str
    key: str


class Dialogue:
    """Bir replik dizisini oynatir.

    Sahne `start()` ile baslatir, `update()` her karede cagrilir, `done`
    olunca sahne devam eder. Oynanisi **durdurmuyor**: oyuncu konusma
    surerken yuruyebilir. Durdursaydik her replik bir kesinti olurdu ve
    oyuncu okumak yerine gecmeye calisirdi.
    """

    def __init__(self) -> None:
        # Sinematiklerde kapatilabilir - bkz. `_portrait_name`.
        self.show_portrait = True
        self.lines: tuple[Line, ...] = ()
        self.index = 0
        self.revealed = 0.0
        self.lock = 0
        self.hold = 0
        self.auto_advance = False
        self.active = False

    # --- Denetim ------------------------------------------------------------
    def start(self, lines: tuple[Line, ...], auto_advance: bool = False) -> None:
        """`auto_advance=True` yalnizca bir sahne-zamanlayicisiyla yarisan
        dizilerde kullanilir (bkz. `AUTO_ADVANCE_HOLD_FRAMES`). Normal
        kesif/dovus repligi varsayilanla oynar: oyuncu onaylayana kadar
        ekranda kalir, sessizce kaybolmaz.
        """
        if not lines:
            return
        self.lines = lines
        self.index = 0
        self.revealed = 0.0
        self.lock = ADVANCE_LOCK_FRAMES
        self.hold = 0
        self.auto_advance = auto_advance
        self.active = True

    def stop(self) -> None:
        self.active = False
        self.lines = ()

    @property
    def done(self) -> bool:
        return not self.active

    @property
    def current(self) -> Line | None:
        if not self.active or self.index >= len(self.lines):
            return None
        return self.lines[self.index]

    @property
    def full_text(self) -> str:
        line = self.current
        return t(line.key) if line else ""

    @property
    def complete(self) -> bool:
        """Replik tamamen yazildi mi?"""
        return self.revealed >= len(self.full_text)

    # --- Dongu --------------------------------------------------------------
    def update(self, game) -> None:
        if not self.active:
            return
        if self.lock > 0:
            self.lock -= 1

        pressed = game.input.pressed(Action.CONFIRM) or \
            game.input.pressed(Action.INTERACT)

        if not self.complete:
            # Basili tutmak yazimi hizlandirir; **atlamaz**. Ayni kural
            # sinematiklerde de gecerli (src/scenes/cinematic.py).
            fast = game.input.held(Action.CONFIRM) or \
                game.input.held(Action.INTERACT)
            self.revealed += TYPE_SPEED * (4.0 if fast else 1.0)
            return

        # Tamamlandi - onayla hemen ilerler; `auto_advance` acikken bir
        # sure sonra kendiliginden de ilerler (bkz. AUTO_ADVANCE_HOLD_FRAMES).
        self.hold += 1
        if (pressed and self.lock <= 0) or (
                self.auto_advance and self.hold >= AUTO_ADVANCE_HOLD_FRAMES):
            self._advance()

    def _advance(self) -> None:
        self.index += 1
        self.revealed = 0.0
        self.lock = ADVANCE_LOCK_FRAMES
        self.hold = 0
        if self.index >= len(self.lines):
            self.stop()

    # --- Cizim --------------------------------------------------------------
    def _box_rect(self) -> pygame.Rect:
        """Kutu **tam metne** gore boyutlanir, yazilana gore degil.

        Yazilana gore olcseydik kutu her yeni satirda buyur ve metin
        zaplardi. Tam metne gore olcunce kutu bastan dogru boyda duruyor,
        icine yazi akiyor.
        """
        rows = _wrap(self.full_text, self._wrap_width())[:MAX_LINES]
        height = len(rows) * LINE_STEP + BOX_PADDING * 2 - 3
        return pygame.Rect(BOX_X, BOX_BOTTOM - height, BOX_WIDTH, height)

    def _portrait_name(self) -> str:
        """Bu replikte gosterilecek portre. Yoksa bos dize.

        Yanki'nin portresi **yok** ve bu bilincli: kafanin icindeki sesin
        yuzu olmaz. Ayni gerekce onun kutusunu da kaldirmisti.

        `show_portrait=False` sinematikler icin: prolog panelleri zaten
        yuzu **tam ekran** gosteriyor ve kutunun yaninda ikinci bir kucuk
        kopya cikinca hata gibi okunuyordu. Ayni yuzu iki olcekte ayni
        anda gostermek anlatimi degil karmasayi artiriyor.
        """
        line = self.current
        if line is None or line.speaker == ECHO or not self.show_portrait:
            return ""
        return line.speaker if portrait_art.PORTRAITS.get(line.speaker) else ""

    def _wrap_width(self) -> int:
        """Satir genisligi portre varken daralir - metin bustun altina
        akmamali."""
        return WRAP_WIDTH_PORTRAIT if self._portrait_name() else WRAP_WIDTH

    def draw(self, surface: pygame.Surface, frame: int = 0) -> None:
        line = self.current
        if line is None:
            return
        shown = self.full_text[:int(self.revealed)]
        rows = _wrap(shown, self._wrap_width())[:MAX_LINES]

        if line.speaker == ECHO:
            self._draw_echo(surface, rows, frame)
        else:
            self._draw_box(surface, line, rows)

    def _draw_box(self, surface: pygame.Surface, line: Line,
                  rows: list[str]) -> None:
        """Odadaki bir kisi konusuyor - portre + cerceveli kutu + ad."""
        box = self._box_rect()
        panel(surface, box)
        colour = palette.color(SPEAKER_COLOURS.get(line.speaker, "bone"))

        inset = 0
        name = self._portrait_name()
        if name:
            bust = portrait_art.portrait(name)
            if bust is not None:
                # Alt kenar kutuyla hizali, ust kismi kutunun UZERINE
                # tasiyor - portre kutunun icine sigmiyor (96 > 55) ve
                # sigdirmak icin kirpmak yuzu kesip atardi.
                surface.blit(bust, (PORTRAIT_X,
                                    box.bottom - bust.get_height()))
                inset = PORTRAIT_INSET

        label = SPEAKER_KEYS.get(line.speaker, "speaker.rey")
        text.draw(surface, t(label), box.x + 8 + inset, box.y - 11,
                  color=colour, outline=True)

        y = box.y + BOX_PADDING
        for row in rows:
            text.draw(surface, row, box.x + 10 + inset, y,
                      color=palette.role("ui_text"))
            y += LINE_STEP

        if self.complete:
            self._draw_prompt(surface, box)

    def _draw_echo(self, surface: pygame.Surface, rows: list[str],
                   frame: int) -> None:
        """Kafanin icindeki ses - **cerceve yok**.

        Mor, ortalanmis, hafifce suzulen ve harf harf titreyen metin.
        Cerceveli kutuya koymak onu odadaki bir baska kisi yapardi.
        """
        box = self._box_rect()
        drift = int(round(math.sin(frame * 0.05) * 2))
        y = box.y + BOX_PADDING + drift
        colour = palette.color("violet_bright")

        for row_index, row in enumerate(rows):
            width = text.text_width(row)
            x = INTERNAL_WIDTH // 2 - width // 2
            # Harfler bagimsiz titrer - tek parca metin "arayuz" gibi
            # okunuyordu, titrek harfler "ses" gibi okunuyor.
            for i, char in enumerate(row):
                wobble = int(round(math.sin(frame * 0.13 + i * 0.9
                                            + row_index) * 0.8))
                text.draw(surface, char, x + i * CHAR_ADVANCE, y + wobble,
                          color=colour)
            y += LINE_STEP

        if self.complete:
            self._draw_prompt(surface, box)

    def _draw_prompt(self, surface: pygame.Surface,
                     box: pygame.Rect) -> None:
        """Devam isareti - yanip sonuyor, oyuncu bekledigini bilsin.

        Arda, canli oynanis (31.08.2026): prolog artik oyuncuyu
        bekliyor ve ilk tepki "donmus mu?" olabiliyor. Isaret zaten
        vardi ama **fark edilmiyordu**: `ui_text_dim` ile tek bir
        karakter, koyu bir zeminde.

        Iki degisiklik. Rengi metnin kendisiyle ayni oldu - hala kucuk
        ve hala yanip sonuyor, yani goze batmiyor ama goruluyor. Ve
        ucgenin altina ince bir cizgi geldi: **sekil kanali**, cunku
        `CLAUDE.md` 10 hicbir seyin yalnizca renkle anlatilmamasini
        istiyor.

        Tusun **adi** burada yazmiyor: o `PlayScene`in bir kerelik
        ipucunda, ve orada tus tablosundan okunuyor (tuslar yeniden
        atanabiliyor - sabit yazmak yalan olurdu).
        """
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            return
        x = box.right - 12
        y = box.bottom - 12
        text.draw(surface, "▸", x, y, color=palette.role("ui_text"))
        surface.fill(palette.role("ui_text_dim"), (x, y + 7, 5, 1))


def _wrap(value: str, width: int) -> list[str]:
    """Kelime bazli satir kirma.

    Karakter bazli kirsaydik kelimeler ortadan bolunurdu ve yazim
    animasyonu sirasinda satirlar surekli yeniden duzenlenirdi.
    """
    rows: list[str] = []
    current = ""
    for word in value.split(" "):
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                rows.append(current)
            current = word
    if current:
        rows.append(current)
    return rows or [""]
