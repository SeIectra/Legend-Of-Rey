"""HUD - asamali aciga cikarma.

Bilgi **yalnizca ilgili oldugunda** gorunur (docs/menu-ui.md 8.2):

  * Can gostergesi  : hasar aldiktan sonra 3 saniye
  * Altin sayaci    : altin toplayinca birkac saniye
  * Yanki gostergesi: kademe degisince yanip soner
  * Combo sayaci    : zincir surerken

**Kesif sirasinda ekran tamamen temiz olabilir.** Bu, karanlik atmosferi
guclendirir; bos ekran yalnizlik demektir.

Diegetik tercih (8.1): Yanki kademesi bir HUD cubugu degil, ekran kenarindaki
vinyet yogunlugudur. Buradaki gosterge yalnizca kademe *degisirken* kisa bir
onay olarak cikar.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import (
    COMBO_THRESHOLD_HIGH, COMBO_THRESHOLD_LOW, COMBO_THRESHOLD_MID,
    HUD_HEALTH_VISIBLE_FRAMES, INTERNAL_WIDTH,
)
from src.ui import text
from src.ui.font_data import GLYPH_HEIGHT

MARGIN = 6
HEALTH_WIDTH = 62
HEALTH_HEIGHT = 5
# Can cubugu **bolmeli**: duz bir dolgu "ne kadar kaldi" sorusunu
# ancak goz karariyla cevapliyordu. Bolmeler "kac vurus kaldi"yi bir
# bakista veriyor - okuma degil sayma isi.
HEALTH_SEGMENTS = 8
# Kaybedilen kisim ANINDA silinmiyor: soluk bir "hayalet" olarak durup
# geriden bosaliyor. Oyuncu boylece NE KADAR yedigini goruyor; anlik
# silinmede darbenin buyuklugu hic okunmuyordu.
GHOST_DELAY_FRAMES = 14       # Bosalmaya baslamadan once bekleme
GHOST_DRAIN_PER_FRAME = 0.012 # Kare basina bosalan oran
FADE_FRAMES = 20              # Gorunurluk bitiminde yumusak sonme
GOLD_VISIBLE_FRAMES = 150
ECHO_VISIBLE_FRAMES = 120
TOAST_FRAMES = 150


class HUD:
    def __init__(self, game) -> None:
        self.game = game
        self.health_frames = 0
        # Hayalet can: gercek canin gerisinden gelen soluk bant.
        self.ghost_ratio = 1.0
        self.ghost_hold = 0
        self.frame = 0
        self.gold_frames = 0
        self.echo_frames = 0
        self.toast = ""
        self.toast_frames = 0
        self.frame = 0

        self._last_health: int | None = None
        self._last_gold: int | None = None
        self._last_echo: int | None = None
        self._shown_gold = 0.0

    # --- Bildirimler --------------------------------------------------------
    def show_toast(self, message: str, frames: int = TOAST_FRAMES) -> None:
        self.toast = message
        self.toast_frames = frames

    def reveal_health(self) -> None:
        self.health_frames = HUD_HEALTH_VISIBLE_FRAMES

    def reveal_gold(self) -> None:
        self.gold_frames = GOLD_VISIBLE_FRAMES

    def reveal_echo(self) -> None:
        self.echo_frames = ECHO_VISIBLE_FRAMES

    # --- Dongu --------------------------------------------------------------
    def update(self, player=None, gold: int = 0, echo_tier: int = 2) -> None:
        self.frame += 1
        self.frame += 1
        self._update_ghost(player)
        self.health_frames = max(0, self.health_frames - 1)
        self.gold_frames = max(0, self.gold_frames - 1)
        self.echo_frames = max(0, self.echo_frames - 1)
        self.toast_frames = max(0, self.toast_frames - 1)

        if player is not None:
            if self._last_health is not None and player.health < self._last_health:
                self.reveal_health()
            self._last_health = player.health

        if self._last_gold is not None and gold != self._last_gold:
            self.reveal_gold()
        self._last_gold = gold

        if self._last_echo is not None and echo_tier != self._last_echo:
            self.reveal_echo()
        self._last_echo = echo_tier

        # Sayac hedefe kayarak gider: artis gorunur, hissedilir.
        difference = gold - self._shown_gold
        if abs(difference) > 0.5:
            self._shown_gold += max(1.0, abs(difference) * 0.15) * (
                1 if difference > 0 else -1)
        else:
            self._shown_gold = float(gold)

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, player=None, gold: int = 0,
             echo_tier: int = 2) -> None:
        if player is not None:
            self._draw_health(surface, player)
            self._draw_combo(surface, player)
        self._draw_gold(surface, gold)
        self._draw_echo(surface, echo_tier)
        self._draw_toast(surface)

    def _update_ghost(self, player) -> None:
        """Hayalet cani gercek canin ardindan surukler.

        Can ARTINCA hayalet aninda yetisiyor (iyilesme geriden gelmemeli -
        kazanc hemen okunmali); AZALINCA once bekliyor, sonra yavasca
        bosaliyor.
        """
        if player is None:
            return
        ratio = player.health_ratio
        if ratio >= self.ghost_ratio:
            self.ghost_ratio = ratio
            self.ghost_hold = 0
            return
        if self.ghost_hold < GHOST_DELAY_FRAMES:
            self.ghost_hold += 1
            return
        self.ghost_ratio = max(ratio, self.ghost_ratio - GHOST_DRAIN_PER_FRAME)

    @staticmethod
    def _fade_alpha(frames_left: int) -> int:
        if frames_left <= 0:
            return 0
        if frames_left >= FADE_FRAMES:
            return 255
        return int(255 * frames_left / FADE_FRAMES)

    def _draw_health(self, surface: pygame.Surface, player) -> None:
        """Bolmeli can cubugu + geriden bosalan hayalet.

        Uc bilgi ayni anda okunuyor:
          * **Ne kadar var**   - dolu bolme sayisi
          * **Ne kadar yedin** - hayaletle dolu arasindaki soluk bant
          * **Tehlikede misin**- %25 altinda nabiz atiyor
        """
        alpha = self._fade_alpha(self.health_frames)
        if alpha <= 0:
            return
        ratio = player.health_ratio
        rect = pygame.Rect(MARGIN, MARGIN, HEALTH_WIDTH, HEALTH_HEIGHT)
        layer = pygame.Surface((rect.width + 2, rect.height + 2),
                               pygame.SRCALPHA)
        layer.fill((*palette.color("ink"), alpha))

        # Hayalet once (altta), gercek can ustune biner.
        ghost = int(rect.width * self.ghost_ratio)
        if ghost > 0:
            layer.fill((*palette.color("blood_dark"), alpha),
                       (1, 1, ghost, rect.height))

        colour = palette.color("blood_bright")
        if ratio < 0.25:
            # Az can: nabiz. Sabit kirmizi "tehlikedeyim" demiyordu,
            # yalnizca "kirmizi bir cubuk" diyordu.
            pulse = 0.5 + 0.5 * math.sin(self.frame * 0.22)
            colour = (palette.color("danger") if pulse > 0.5
                      else palette.color("danger_bright"))
        filled = int(rect.width * ratio)
        if filled > 0:
            layer.fill((*colour, alpha), (1, 1, filled, rect.height))

        # Bolme cizgileri EN USTTE - dolgunun uzerine oyuluyor.
        step = rect.width / HEALTH_SEGMENTS
        for index in range(1, HEALTH_SEGMENTS):
            x = 1 + int(index * step)
            layer.fill((*palette.color("ink"), alpha), (x, 1, 1, rect.height))

        surface.blit(layer, (rect.x - 1, rect.y - 1))

    def _draw_combo(self, surface: pygame.Surface, player) -> None:
        combo = getattr(player, "combo", None)
        if combo is None or combo.count < 2:
            return
        colour = palette.role("ui_text")
        if combo.count >= COMBO_THRESHOLD_HIGH:
            colour = palette.color("violet_bright")
        elif combo.count >= COMBO_THRESHOLD_MID:
            colour = palette.color("gold")
        elif combo.count >= COMBO_THRESHOLD_LOW:
            colour = palette.color("ember_light")

        # Esik asildiginda kisa bir buyume - sayiyi izlemeye gerek kalmadan
        # ilerlemeyi hissedersin.
        pop = 0
        if combo.frames_since_hit < 6:
            pop = 1
        text.draw(surface, str(combo.count),
                  INTERNAL_WIDTH - MARGIN, MARGIN - pop,
                  color=colour, align="right", outline=True)

    def _draw_gold(self, surface: pygame.Surface, gold: int) -> None:
        alpha = self._fade_alpha(self.gold_frames)
        if alpha <= 0:
            return
        y = MARGIN + HEALTH_HEIGHT + 6
        pygame.draw.circle(surface, palette.color("gold"),
                           (MARGIN + 3, y + 4), 3)
        text.draw(surface, str(int(self._shown_gold)), MARGIN + 10, y,
                  color=palette.role("ui_text_bright"), alpha=alpha)

    def _draw_echo(self, surface: pygame.Surface, echo_tier: int) -> None:
        alpha = self._fade_alpha(self.echo_frames)
        if alpha <= 0:
            return
        # Kademe degisince kisa bir yanip sonme.
        blink = (math.sin(self.frame * 0.3) * 0.5 + 0.5)
        alpha = int(alpha * (0.55 + blink * 0.45))
        dots = "●" * (echo_tier + 1) + "○" * (2 - echo_tier)
        colour = (palette.color("echo_bright") if echo_tier > 0
                  else palette.color("stone_dark"))
        text.draw(surface, dots, INTERNAL_WIDTH - MARGIN,
                  MARGIN + GLYPH_HEIGHT + 4, color=colour, align="right",
                  alpha=alpha)

    def _draw_toast(self, surface: pygame.Surface) -> None:
        alpha = self._fade_alpha(self.toast_frames)
        if alpha <= 0 or not self.toast:
            return
        text.draw(surface, self.toast, INTERNAL_WIDTH // 2, 42,
                  color=palette.color("violet_bright"), align="center",
                  outline=True, alpha=alpha)
