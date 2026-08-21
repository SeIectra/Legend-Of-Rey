"""Faz 0 dogrulama sahnesi.

Temelin dogru kuruldugunu **gozle** kanitlar: Turkce fontun tamami, Turkce
buyuk/kucuk harf donusumu, 32 renklik palet ve kare sayaci tek ekranda.

Kalici bir hata ayiklama araci - palet ya da fonta dokunuldugunda buraya
bakilir. Oyun akisinin parcasi degildir.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.ui import text
from src.ui.font_data import GLYPH_HEIGHT

# Turkce'nin sinav karakterleri. Bunlarin hepsi cizilmezse font eksik demektir.
TURKISH_UPPER = "ÇĞİIÖŞÜ"
TURKISH_LOWER = "çğıiöşü"

# tr_upper/tr_lower'in Python'dan ayristigi ornekler.
CASE_SAMPLES: tuple[tuple[str, str], ...] = (
    ("ışık", "IŞIK"),
    ("İstanbul", "İSTANBUL"),
    ("Iğdır", "IĞDIR"),
)

SWATCH_SIZE = 10
SWATCH_GAP = 2
SWATCH_COLUMNS = 16


class FoundationCheckScene(Scene):
    def on_enter(self, **kwargs: object) -> None:
        self.tick = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and self.game.input.pressed(Action.CANCEL):
            self.game.quit()

    def update(self) -> None:
        self.tick += 1

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("abyss_dark"))
        y = 8
        y = self._draw_title(surface, y)
        y = self._draw_turkish(surface, y)
        y = self._draw_case(surface, y)
        self._draw_palette(surface, y)
        self._draw_footer(surface)

    # --- Bolumler -----------------------------------------------------------
    def _draw_title(self, surface: pygame.Surface, y: int) -> int:
        text.draw(surface, text.tr_upper("Legend of Rey"), INTERNAL_WIDTH // 2, y,
                  color=palette.role("ui_text_bright"), align="center",
                  outline=True, tracking=3)
        text.draw(surface, "Faz 0 · temel doğrulama", INTERNAL_WIDTH // 2,
                  y + GLYPH_HEIGHT + 3, color=palette.role("ui_text_dim"),
                  align="center")
        return y + GLYPH_HEIGHT * 2 + 8

    def _draw_turkish(self, surface: pygame.Surface, y: int) -> int:
        text.draw(surface, "Türkçe karakterler", 10, y,
                  color=palette.role("ui_text_dim"))
        y += GLYPH_HEIGHT + 3
        text.draw(surface, TURKISH_UPPER, 10, y,
                  color=palette.role("ui_text"), tracking=2)
        text.draw(surface, TURKISH_LOWER, 120, y,
                  color=palette.role("ui_text"), tracking=2)
        y += GLYPH_HEIGHT + 3
        text.draw(surface, "Ağır kılıç, şişkin gölge, çürüyen ışık.", 10, y,
                  color=palette.role("ui_text"))
        return y + GLYPH_HEIGHT + 8

    def _draw_case(self, surface: pygame.Surface, y: int) -> int:
        text.draw(surface, "tr_upper / tr_lower", 10, y,
                  color=palette.role("ui_text_dim"))
        y += GLYPH_HEIGHT + 3
        for source, expected in CASE_SAMPLES:
            produced = text.tr_upper(source)
            correct = produced == expected
            colour = (palette.color("echo_bright") if correct
                      else palette.color("danger_bright"))
            mark = "✓" if correct else "✗"
            line = f"{mark} {source} → {produced}   (geri: {text.tr_lower(produced)})"
            text.draw(surface, line, 10, y, color=colour)
            y += GLYPH_HEIGHT + 2
        return y + 6

    def _draw_palette(self, surface: pygame.Surface, y: int) -> None:
        text.draw(surface, f"Palet · {len(palette.COLORS)} renk", 10, y,
                  color=palette.role("ui_text_dim"))
        y += GLYPH_HEIGHT + 3
        for index, name in enumerate(palette.ORDERED_NAMES):
            column = index % SWATCH_COLUMNS
            row = index // SWATCH_COLUMNS
            x = 10 + column * (SWATCH_SIZE + SWATCH_GAP)
            swatch_y = y + row * (SWATCH_SIZE + SWATCH_GAP)
            rect = pygame.Rect(x, swatch_y, SWATCH_SIZE, SWATCH_SIZE)
            surface.fill(palette.color(name), rect)
            pygame.draw.rect(surface, palette.outline(), rect, 1)

        rows = (len(palette.ORDERED_NAMES) + SWATCH_COLUMNS - 1) // SWATCH_COLUMNS
        legend_y = y + rows * (SWATCH_SIZE + SWATCH_GAP) + 3
        text.draw(surface, f"kontur: {palette.OUTLINE_NAME} (en koyu 2. renk)",
                  10, legend_y, color=palette.role("ui_text_dim"))

    def _draw_footer(self, surface: pygame.Surface) -> None:
        # Kare sayaci: sabit adimin gercekten sabit oldugunu gosterir.
        info = (f"FPS {self.game.fps:5.1f}   oyun karesi {self.game.frame}   "
                f"gerçek kare {self.game.real_frame}")
        text.draw(surface, info, INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 24,
                  color=palette.role("ui_text_bright"), align="center")
        text.draw(surface, "F3 hata ayıklama · F4 siluet · F11 tam ekran · Esc çıkış",
                  INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 12,
                  color=palette.role("ui_text_dim"), align="center")

    def debug_lines(self) -> list[str]:
        return [palette.describe()]
