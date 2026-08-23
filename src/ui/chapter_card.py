"""Bolum basi karti - "BOLUM 2 · Ilk Inis".

Oyunda hangi bolumde oldugunu soyleyen hicbir sey yoktu; oyuncu ucuncu
bolume geldigini ancak mekan degisiminden anliyordu. Kart bunu bir
**an** haline getiriyor: numara once, ad sonra, ikisi de sonup gidiyor.

Ara sahne degil, **bindirme**. Oynanisi durdurmuyor (CLAUDE.md 9'un
diyalog icin koydugu ayni ilke): oyuncu ilk saniyede yurumeye
baslayabilir, kart onun ustunde sessizce soner.

Zamanlama - toplam 150 kare (2.5 sn):
    0-20    numara belirir (asagidan suzulerek)
    20-40   ad belirir, altina ince cizgi cekilir
    40-110  ikisi de durur
    110-150 hepsi soner
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.ui import text
from src.ui.i18n import t

NUMBER_IN = 20
NAME_IN = 40
HOLD_UNTIL = 110
TOTAL = 150

CENTER_Y = INTERNAL_HEIGHT // 2 - 14
RULE_WIDTH = 96


def _ease_out(value: float) -> float:
    """Hizli baslar, yumusak durur - metin "yerine oturur" gibi okunur."""
    value = max(0.0, min(1.0, value))
    return 1.0 - (1.0 - value) * (1.0 - value)


class ChapterCard:
    """Bir bolumun acilis karti. Sahne `update()`/`draw()` cagirir."""

    def __init__(self, number: int, name_key: str) -> None:
        self.number = number
        self.name_key = name_key
        self.frames = 0
        self.active = True

    @property
    def done(self) -> bool:
        return not self.active

    def skip(self) -> None:
        """Kalan sureyi sonme asamasina atlatir - kart asla ANIDEN
        kaybolmaz (CLAUDE.md 9: sert kesme yok)."""
        self.frames = max(self.frames, HOLD_UNTIL)

    def update(self) -> None:
        if not self.active:
            return
        self.frames += 1
        if self.frames >= TOTAL:
            self.active = False

    # --- Cizim --------------------------------------------------------------
    def _alpha(self) -> float:
        """Kartin genel gorunurlugu (0..1). Sonda dogrusal sonuyor."""
        if self.frames <= HOLD_UNTIL:
            return 1.0
        fade = (self.frames - HOLD_UNTIL) / max(1, TOTAL - HOLD_UNTIL)
        return max(0.0, 1.0 - fade)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        alpha = self._alpha()
        if alpha <= 0.0:
            return

        # Metin arkasina hafif bir karartma - her zemin uzerinde okunur
        # kalsin. Tam ekran degil, yalnizca metnin serit yuksekligi.
        veil = pygame.Surface((INTERNAL_WIDTH, 46), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), int(150 * alpha)))
        surface.blit(veil, (0, CENTER_Y - 8))

        number_t = _ease_out(self.frames / NUMBER_IN)
        label = t("chapter_card.number", number=self.number)
        rise = int(round((1.0 - number_t) * 6))
        text.draw(surface, label, INTERNAL_WIDTH // 2,
                  CENTER_Y + rise, align="center",
                  color=self._tone("ui_text_dim", alpha * number_t))

        if self.frames <= NUMBER_IN:
            return

        name_t = _ease_out((self.frames - NUMBER_IN) / (NAME_IN - NUMBER_IN))
        name = text.tr_upper(t(self.name_key))
        text.draw(surface, name, INTERNAL_WIDTH // 2, CENTER_Y + 12,
                  align="center",
                  color=self._tone("ui_text_bright", alpha * name_t))

        # Adin altindaki cizgi disaridan iceri degil, ortadan disari acilir.
        half = int(RULE_WIDTH * 0.5 * name_t)
        if half > 0:
            colour = self._tone("ui_border", alpha * name_t)
            surface.fill(colour, (INTERNAL_WIDTH // 2 - half,
                                  CENTER_Y + 24, half * 2, 1))

    def _tone(self, role: str, strength: float) -> palette.RGB:
        """Rolu arka plana dogru karistirir.

        `set_alpha` yerine karistirma: metin `text.draw` ile dogrudan
        yuzeye ciziliyor ve alfa desteklemiyor. Void'e karistirmak ayni
        sonucu palet icinde kalarak veriyor.
        """
        r, g, b = palette.role(role)
        vr, vg, vb = palette.color("void")
        k = max(0.0, min(1.0, strength))
        return (int(vr + (r - vr) * k),
                int(vg + (g - vg) * k),
                int(vb + (b - vb) * k))
