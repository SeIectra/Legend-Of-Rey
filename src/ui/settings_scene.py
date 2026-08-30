"""Ayarlar ekrani - uc sekme, hepsi `docs/menu-ui.md` 5'ten.

**Erisilebilirlik felsefesi:** Zorluk on ayari yok. "Kolay/Normal/Zor"
secmiyorsun; mucadelenin hangi parcasini tutacagini seciyorsun. Hicbir ayar
"Kolay Mod" diye etiketlenmez, hicbir basarim kilitlenmez (CLAUDE.md 10).

Her degisiklik aninda uygulanir ve diske yazilir - "Kaydet" butonu yok.

Ekran, ayar listesini gezerek kendini kurar (`systems/settings.py`). Yeni bir
ayar eklemek tek satirlik is; bu dosya hic degismez.

## Sekmeler arasi DOGRUDAN gecis (22.08.2026)

Arda'nin geri bildirimi: "Ses'e gitmek icin en asagiya inmek gerekiyor
sacma." Kok neden: sekme degisimi yalnizca **listenin ucundan tasarak**
oluyordu (yukari/asagi ile Goruntu sekmesinin butun satirlarini gecmeden
Ses'e ulasilamiyordu) - dogrudan bir sekme atlama yolu yoktu. Uc yol
eklendi:
  * Fare: sekme basligina tikla.
  * Klavye/gamepad: `Action.NEXT_TAB` (Tab tusu / RB) her satirdan
    bagimsiz olarak dogrudan sonraki sekmeye atlar.
  * Sol/sag hala deger degistiriyor (bu ekranda en sik kullanilan islem);
    sekme gecisi ayri bir tusla, cakisma yok.
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
ROW_HEIGHT = 17
VALUE_X = 244
BAR_WIDTH = 70
ROW_START_Y = 30           # Sekme seridinin altinda birakilan bosluk


class SettingsScene(Scene):
    blocks_update = True
    blocks_draw = True

    def on_enter(self, **kwargs: object) -> None:
        self.settings = self.game.settings
        self.tabs = TabBar([t(key) for key, _ in TABS],
                           PANEL_X + 8, PANEL_Y + 8, PANEL_WIDTH - 16)
        self.row = 0
        self.mouse_visible = False

    # --- Sorgular -----------------------------------------------------------
    @property
    def entries(self) -> tuple:
        return TABS[self.tabs.index][1]

    @property
    def current(self):
        return self.entries[self.row]

    def _panel_rect(self) -> pygame.Rect:
        return pygame.Rect(PANEL_X, PANEL_Y, PANEL_WIDTH,
                           INTERNAL_HEIGHT - PANEL_Y * 2)

    def _row_rect(self, index: int) -> pygame.Rect:
        rect = self._panel_rect()
        y = rect.y + ROW_START_Y + index * ROW_HEIGHT
        return pygame.Rect(rect.x + 4, y - 2, rect.width - 8, ROW_HEIGHT - 2)

    # --- Girdi --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and self.game.input.pressed(Action.CANCEL):
            self._close()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._click()

    def update(self) -> None:
        inp = self.game.input

        if inp.pressed(Action.UP):
            self._move_row(-1)
        elif inp.pressed(Action.DOWN):
            self._move_row(1)

        if inp.pressed(Action.NEXT_TAB):
            self._switch_tab(1)

        if inp.pressed(Action.LEFT):
            self._adjust(-1)
        elif inp.pressed(Action.RIGHT):
            self._adjust(1)
        elif inp.pressed(Action.CONFIRM):
            self._adjust(1)

        # Fare hareket edince imlec gorunur, klavye kullanilinca kaybolur -
        # ayni kural `widgets.Menu` ile (docs/menu-ui.md 8.4).
        if inp.mouse_moved:
            self.mouse_visible = True
        elif inp.last_device == "keyboard":
            self.mouse_visible = False
        if self.mouse_visible:
            self._hover()

    def _virtual_mouse(self) -> tuple[float, float] | None:
        mx, my = pygame.mouse.get_pos()
        view = self.game.viewport
        if not view.collidepoint(mx, my) or self.game.scale <= 0:
            return None
        return ((mx - view.x) / self.game.scale, (my - view.y) / self.game.scale)

    def _hover(self) -> None:
        position = self._virtual_mouse()
        if position is None:
            return
        for index in range(len(self.entries)):
            if self._row_rect(index).collidepoint(position):
                if index != self.row:
                    self.row = index
                    self.game.play_sound("ui_tick")
                return

    def _click(self) -> None:
        position = self._virtual_mouse()
        if position is None:
            return
        for index in range(len(self.tabs.labels)):
            if self.tabs.tab_rect(index).collidepoint(position):
                self._switch_tab(index - self.tabs.index)
                return
        for index in range(len(self.entries)):
            if self._row_rect(index).collidepoint(position):
                self.row = index
                self._adjust(1)
                return

    def _move_row(self, direction: int) -> None:
        count = len(self.entries)
        new_row = self.row + direction
        if new_row < 0 or new_row >= count:
            # Listenin ucundan cikinca sekme degistir - dogal his. Artik
            # tek yol degil (bkz. _switch_tab / Action.NEXT_TAB / tik),
            # ama hala calisiyor - kimse "asagi tusuna basip sekme
            # degisti" diye saskin kalmasin.
            self._switch_tab(direction)
            self.row = 0 if direction > 0 else len(self.entries) - 1
        else:
            self.row = new_row
            self.game.play_sound("ui_tick")

    def _switch_tab(self, direction: int) -> None:
        self.tabs.move(direction)
        self.row = 0
        self.game.play_sound("ui_tab")

    def _adjust(self, direction: int) -> None:
        entry = self.current
        if isinstance(entry, Option):
            self._warn_if_slow(entry, direction)
            self.settings.cycle(entry, direction)
        else:
            self.settings.adjust(entry, direction)
        self.game.play_sound("ui_slider" if isinstance(entry, Slider)
                             else "ui_tick")

    def _warn_if_slow(self, entry: Option, direction: int) -> None:
        """Uzun surecek bir ayar acilmadan ONCE ekrana yazi bas.

        Kol taramasi bu makinede 40 saniye suruyor ve `settings.cycle`
        onu **hemen** tetikliyor. Yazi sonra cizilseydi oyuncu 40 saniye
        donmus bir ekrana bakardi ve oyunun cocktugunu sanardi - nitekim
        acilista tam olarak oyle goruniyordu.

        Bu yuzden kare burada elle ciziliyor ve ekrana **basiliyor**;
        blokli cagri ondan sonra geliyor.
        """
        if entry.key != "gamepad":
            return
        index = entry.index_of(self.settings.get(entry.key))
        turning_on = entry.values[(index + direction) % len(entry.values)]
        if not turning_on:
            return

        surface = self.game.canvas
        self.draw(surface)
        box = pygame.Rect(0, 0, 260, 34)
        box.center = (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2)
        panel(surface, box)
        text.draw(surface, t("settings.gamepad_scanning"),
                  INTERNAL_WIDTH // 2, box.y + 12,
                  color=palette.color("gold"), align="center")
        self.game.present()

    def _close(self) -> None:
        self.game.play_sound("ui_back")
        self.scenes.pop()

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 220))
        surface.blit(veil, (0, 0))

        rect = self._panel_rect()
        panel(surface, rect)
        text.draw(surface, t("settings.heading"), INTERNAL_WIDTH // 2,
                  PANEL_Y - 16, color=palette.role("ui_text"),
                  align="center", tracking=2)

        # Dil bu ekrandan degistirilebiliyor; sekme adlari o anki dilde
        # olsun diye her karede tazelenir.
        self.tabs.labels = [t(key) for key, _ in TABS]
        self._draw_tab_strip(surface, rect)
        self._draw_rows(surface, rect)
        self._draw_note(surface, rect)

        text.draw(surface, t("settings.controls"),
                  INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 16,
                  color=palette.role("ui_text_dim"), align="center")

    def _draw_tab_strip(self, surface: pygame.Surface,
                        panel_rect: pygame.Rect) -> None:
        """Tam genislik bir serit + her sekme kendi bolmesinde - eskiden
        sekmeler bosluktaki metinlerdi, tek bir parca gibi okunmuyordu."""
        strip = pygame.Rect(panel_rect.x + 4, PANEL_Y + 4,
                            panel_rect.width - 8, GLYPH_HEIGHT + 10)
        surface.fill(palette.color("void"), strip)
        self.tabs.draw(surface)
        pygame.draw.line(surface, palette.role("ui_border"),
                         (strip.left, strip.bottom), (strip.right, strip.bottom))

    def _draw_rows(self, surface: pygame.Surface, panel_rect: pygame.Rect) -> None:
        y = panel_rect.y + ROW_START_Y
        for index, entry in enumerate(self.entries):
            selected = index == self.row
            colour = (palette.role("ui_text") if selected
                      else palette.role("ui_text_dim"))

            if selected:
                highlight = self._row_rect(index)
                surface.fill(palette.color("ink_soft"), highlight)
                pygame.draw.rect(surface, palette.color("violet_bright"),
                                 highlight, 1)
                text.draw(surface, "▸", panel_rect.x + 8, y,
                          color=palette.color("violet_bright"))

            text.draw(surface, entry.label, panel_rect.x + 20, y, color=colour)
            self._draw_value(surface, entry, y, colour, selected)
            y += ROW_HEIGHT

    def _draw_value(self, surface: pygame.Surface, entry, y: int,
                    colour, selected: bool) -> None:
        """Deger + sag/sol degistirilebilir oldugunu gosteren ok isaretleri.

        Oklar yalnizca **secili satirda** gorunur - her zaman acik olsaydi
        gezinme oku ile "su an buradasin" isareti birbirine karisirdi.
        """
        if isinstance(entry, Option):
            value = self.settings.get(entry.key)
            label = entry.label_for(value)
            bright = palette.role("ui_text_bright") if selected else colour
            text.draw(surface, label, VALUE_X, y, color=bright)
            if selected:
                width = text.text_width(label)
                text.draw(surface, "<", VALUE_X - 8, y, color=colour)
                text.draw(surface, ">", VALUE_X + width + 4, y, color=colour)
        else:
            ratio = float(self.settings.get(entry.key, entry.default))
            value_bar(surface, pygame.Rect(VALUE_X, y + 3, BAR_WIDTH, 5),
                      ratio, colour=palette.color("violet_bright")
                      if selected else None)
            text.draw(surface, t("settings.percent", value=int(ratio * 100)),
                      VALUE_X + BAR_WIDTH + 6, y, color=colour)
            if selected:
                text.draw(surface, "<", VALUE_X - 8, y, color=colour)

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
