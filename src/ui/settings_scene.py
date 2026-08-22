"""Ayarlar ekrani - uc sekme, hepsi `docs/menu-ui.md` 5'ten.

**Erisilebilirlik felsefesi:** Zorluk on ayari yok. "Kolay/Normal/Zor"
secmiyorsun; mucadelenin hangi parcasini tutacagini seciyorsun. Hicbir ayar
"Kolay Mod" diye etiketlenmez, hicbir basarim kilitlenmez (CLAUDE.md 10).

Her degisiklik aninda uygulanir ve diske yazilir - "Kaydet" butonu yok.

Ekran, ayar listesini gezerek kendini kurar (`systems/settings.py`). Yeni bir
ayar eklemek tek satirlik is; bu dosya hic degismez.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.systems.settings import Option, Slider, TABS
from src.ui import text
from src.ui.font_data import GLYPH_HEIGHT
from src.ui.i18n import t
from src.ui.widgets import TabBar, panel, value_bar

PANEL_X = 34
PANEL_Y = 34
PANEL_WIDTH = INTERNAL_WIDTH - PANEL_X * 2
ROW_HEIGHT = 16
VALUE_X = 250
BAR_WIDTH = 84


class SettingsScene(Scene):
    blocks_update = True
    blocks_draw = True

    def on_enter(self, **kwargs: object) -> None:
        self.settings = self.game.settings
        self.tabs = TabBar([t(key) for key, _ in TABS],
                           PANEL_X + 8, PANEL_Y + 6, PANEL_WIDTH - 16)
        self.row = 0

    # --- Sorgular -----------------------------------------------------------
    @property
    def entries(self) -> tuple:
        return TABS[self.tabs.index][1]

    @property
    def current(self):
        return self.entries[self.row]

    # --- Girdi --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and self.game.input.pressed(Action.CANCEL):
            self._close()

    def update(self) -> None:
        inp = self.game.input

        if inp.pressed(Action.UP):
            self._move_row(-1)
        elif inp.pressed(Action.DOWN):
            self._move_row(1)

        # Sekme degisimi: sol/sag ilk satirdayken sekme gezer, degilse deger
        # degistirir. Iki islevi tek eksene sigdirmanin en okunur yolu.
        if inp.pressed(Action.LEFT):
            self._adjust(-1)
        elif inp.pressed(Action.RIGHT):
            self._adjust(1)
        elif inp.pressed(Action.CONFIRM):
            self._adjust(1)

    def _move_row(self, direction: int) -> None:
        count = len(self.entries)
        new_row = self.row + direction
        if new_row < 0 or new_row >= count:
            # Listenin ucundan cikinca sekme degistir - dogal his.
            self.tabs.move(direction)
            self.row = 0 if direction > 0 else len(self.entries) - 1
            self.game.play_sound("ui_tab")
        else:
            self.row = new_row
            self.game.play_sound("ui_tick")

    def _adjust(self, direction: int) -> None:
        entry = self.current
        if isinstance(entry, Option):
            self.settings.cycle(entry, direction)
        else:
            self.settings.adjust(entry, direction)
        self.game.play_sound("ui_slider" if isinstance(entry, Slider)
                             else "ui_tick")

    def _close(self) -> None:
        self.game.play_sound("ui_back")
        self.scenes.pop()

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 220))
        surface.blit(veil, (0, 0))

        rect = pygame.Rect(PANEL_X, PANEL_Y, PANEL_WIDTH,
                           INTERNAL_HEIGHT - PANEL_Y * 2)
        panel(surface, rect)
        text.draw(surface, t("settings.heading"), INTERNAL_WIDTH // 2,
                  PANEL_Y - 16, color=palette.role("ui_text"),
                  align="center", tracking=2)

        # Dil bu ekrandan degistirilebiliyor; sekme adlari o anki dilde
        # olsun diye her karede tazelenir.
        self.tabs.labels = [t(key) for key, _ in TABS]
        self.tabs.draw(surface)
        self._draw_rows(surface, rect)
        self._draw_note(surface, rect)

        text.draw(surface, t("settings.controls"),
                  INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 16,
                  color=palette.role("ui_text_dim"), align="center")

    def _draw_rows(self, surface: pygame.Surface, panel_rect: pygame.Rect) -> None:
        y = PANEL_Y + 28
        for index, entry in enumerate(self.entries):
            selected = index == self.row
            colour = (palette.role("ui_text") if selected
                      else palette.role("ui_text_dim"))

            if selected:
                highlight = pygame.Rect(panel_rect.x + 4, y - 2,
                                        panel_rect.width - 8, ROW_HEIGHT - 2)
                surface.fill(palette.color("ink_soft"), highlight)
                text.draw(surface, "▸", panel_rect.x + 8, y,
                          color=palette.color("violet_bright"))

            text.draw(surface, entry.label, panel_rect.x + 20, y, color=colour)

            if isinstance(entry, Option):
                value = self.settings.get(entry.key)
                text.draw(surface, entry.label_for(value), VALUE_X, y,
                          color=(palette.role("ui_text_bright") if selected
                                 else palette.role("ui_text_dim")))
            else:
                ratio = float(self.settings.get(entry.key, entry.default))
                value_bar(surface, pygame.Rect(VALUE_X, y + 3, BAR_WIDTH, 5),
                          ratio)
                text.draw(surface, t("settings.percent", value=int(ratio * 100)),
                          VALUE_X + BAR_WIDTH + 6, y, color=colour)
            y += ROW_HEIGHT

    def _draw_note(self, surface: pygame.Surface,
                   panel_rect: pygame.Rect) -> None:
        note = getattr(self.current, "note", "")
        if not note:
            return
        text.draw(surface, note, panel_rect.centerx,
                  panel_rect.bottom - GLYPH_HEIGHT - 6,
                  color=palette.color("stone_light"), align="center")

    def debug_lines(self) -> list[str]:
        return [f"sekme: {t(TABS[self.tabs.index][0])}  "
                f"satır: {self.current.label}"]
