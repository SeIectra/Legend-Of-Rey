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
from src.systems import bindings as binds
from src.systems.bindings import Binding, ResetBindings
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

# Tus sekmesi IKI SUTUN. On bir tus + "varsayilanlara don" = on iki satir;
# tek sutunda panele sigmiyordu (yer var: 10 satir). Kaydirma eklemek
# yerine iki sutun: tus listesi zaten boyle okunuyor ve hicbir satir
# gorunmez olmuyor.
CONTROL_ROWS = 6
CONTROL_COLUMN_WIDTH = (PANEL_WIDTH - 16) // 2
# Yakalama sirasinda "bir tusa bas" kutusu.
CAPTURE_BOX = (200, 54)
# Hata mesaji bu kadar kare duruyor (~3 saniye).
ERROR_FRAMES = 180


class SettingsScene(Scene):
    blocks_update = True
    blocks_draw = True

    def on_enter(self, **kwargs: object) -> None:
        self.settings = self.game.settings
        self.tabs = TabBar([t(key) for key, _ in TABS],
                           PANEL_X + 8, PANEL_Y + 8, PANEL_WIDTH - 16)
        self.row = 0
        self.mouse_visible = False
        # Yakalama kipi: bir tus satiri secildi ve oyuncunun tusa
        # basmasi bekleniyor. `None` = normal gezinme.
        self.capturing: Binding | None = None
        self.capture_error = ""
        self.error_frames = 0

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

    @property
    def controls_tab(self) -> bool:
        return TABS[self.tabs.index][0] == "settings.tab_controls"

    def _row_rect(self, index: int) -> pygame.Rect:
        rect = self._panel_rect()
        if self.controls_tab:
            # Once birinci sutun yukaridan asagi, sonra ikinci: yukari/asagi
            # bir sutunu geziyor, sag/sol sutun degistiriyor.
            column, row = divmod(index, CONTROL_ROWS)
            x = rect.x + 4 + column * CONTROL_COLUMN_WIDTH
            y = rect.y + ROW_START_Y + row * ROW_HEIGHT
            return pygame.Rect(x, y - 2, CONTROL_COLUMN_WIDTH - 4,
                               ROW_HEIGHT - 2)
        y = rect.y + ROW_START_Y + index * ROW_HEIGHT
        return pygame.Rect(rect.x + 4, y - 2, rect.width - 8, ROW_HEIGHT - 2)

    # --- Girdi --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.capturing is not None:
            self._capture_event(event)
            return
        if event.type == pygame.KEYDOWN and self.game.input.pressed(Action.CANCEL):
            self._close()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._click()

    def _capture_event(self, event: pygame.event.Event) -> None:
        """Yakalama sirasindaki HAM olay.

        Burada `Action` kullanilmiyor, ham tus kodu okunuyor - amac zaten
        aksiyonlarin altindaki katmani degistirmek. `pressed(CONFIRM)`
        dinlenseydi oyuncu Enter'i Enter'a baglayamazdi.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._end_capture()             # ESC: vazgec
                self.game.play_sound("ui_back")
                return
            self._commit_capture(event.key, gamepad=False)
        elif event.type == pygame.JOYBUTTONDOWN:
            self._commit_capture(event.button, gamepad=True)

    def _commit_capture(self, code: int, gamepad: bool) -> None:
        entry = self.capturing
        if entry is None:
            return
        error = binds.assign(self.settings, entry.action, code, gamepad)
        if error:
            self.capture_error = t(error)
            self.error_frames = ERROR_FRAMES
            self.game.play_sound("ui_back")
            return                              # Kutu acik kaliyor, tekrar dene
        self._end_capture()
        self.game.play_sound("ui_tick")

    def _begin_capture(self, entry: Binding) -> None:
        self.capturing = entry
        self.capture_error = ""
        self.error_frames = 0
        self.game.play_sound("ui_tick")

    def _end_capture(self) -> None:
        self.capturing = None
        self.capture_error = ""
        self.error_frames = 0

    def update(self) -> None:
        self.error_frames = max(0, self.error_frames - 1)
        if self.capturing is not None:
            # Yakalarken gezinme YOK: yon tuslari da atanabilir olmali.
            return
        inp = self.game.input

        if inp.pressed(Action.UP):
            self._move_row(-1)
        elif inp.pressed(Action.DOWN):
            self._move_row(1)

        if inp.pressed(Action.NEXT_TAB):
            self._switch_tab(1)

        if self.controls_tab:
            # Tus satirinin "degeri" yok; sag/sol burada SUTUN degistiriyor.
            if inp.pressed(Action.LEFT):
                self._move_column(-1)
            elif inp.pressed(Action.RIGHT):
                self._move_column(1)
            elif inp.pressed(Action.CONFIRM):
                self._adjust(1)
        elif inp.pressed(Action.LEFT):
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

    def _move_column(self, direction: int) -> None:
        target = self.row + direction * CONTROL_ROWS
        if 0 <= target < len(self.entries):
            self.row = target
            self.game.play_sound("ui_tick")

    def _switch_tab(self, direction: int) -> None:
        self.tabs.move(direction)
        self.row = 0
        self.game.play_sound("ui_tab")

    def _adjust(self, direction: int) -> None:
        entry = self.current
        if isinstance(entry, Binding):
            self._begin_capture(entry)
            return
        if isinstance(entry, ResetBindings):
            binds.reset(self.settings)
            self.game.play_sound("ui_back")
            self.capture_error = t("controls.reset_done")
            self.error_frames = ERROR_FRAMES
            return
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
        self._draw_error(surface, rect)

        # Ipucu sekmeye gore: tus sekmesinde sag/sol "degistir" degil
        # **sutun** degistiriyor ve degisiklik CONFIRM ile basliyor.
        # Tek bir ipucu yazmak oyuncuya yanlis tusu ogretirdi.
        hint = ("settings.controls_binding" if self.controls_tab
                else "settings.controls")
        text.draw(surface, t(hint),
                  INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 16,
                  color=palette.role("ui_text_dim"), align="center")
        # Yakalama kutusu EN USTTE: modal oldugu goruntuden de anlasilmali.
        self._draw_capture_box(surface)

    def _draw_error(self, surface: pygame.Surface,
                    panel_rect: pygame.Rect) -> None:
        """Catisma / sifirlama bildirimi.

        Notun yerine degil **ustune** ciziliyor ve kendiliginden soluyor:
        kalici bir uyari sonraki oyuncuya "bir sey bozuk" der.
        """
        if self.error_frames <= 0 or not self.capture_error:
            return
        text.draw(surface, self.capture_error, panel_rect.centerx,
                  panel_rect.bottom - GLYPH_HEIGHT * 2 - 8,
                  color=palette.color("danger_bright"), align="center")

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
        for index, entry in enumerate(self.entries):
            selected = index == self.row
            colour = (palette.role("ui_text") if selected
                      else palette.role("ui_text_dim"))
            # Satirin yeri **tek kaynaktan**: `_row_rect`. Cizim kendi
            # `y`'sini sayiyordu; tek sutunda ikisi ayni sonucu veriyordu
            # ama tus sekmesi iki sutunlu ve orada butun satirlar ust uste
            # binerdi - fare vurusu ise dogru yerde olurdu.
            row_rect = self._row_rect(index)
            y = row_rect.y + 2

            if selected:
                surface.fill(palette.color("ink_soft"), row_rect)
                pygame.draw.rect(surface, palette.color("violet_bright"),
                                 row_rect, 1)
                text.draw(surface, "▸", row_rect.x + 4, y,
                          color=palette.color("violet_bright"))

            text.draw(surface, entry.label, row_rect.x + 16, y, color=colour)
            self._draw_value(surface, entry, y, colour, selected)

    def _draw_value(self, surface: pygame.Surface, entry, y: int,
                    colour, selected: bool) -> None:
        """Deger + sag/sol degistirilebilir oldugunu gosteren ok isaretleri.

        Oklar yalnizca **secili satirda** gorunur - her zaman acik olsaydi
        gezinme oku ile "su an buradasin" isareti birbirine karisirdi.
        """
        if isinstance(entry, ResetBindings):
            return
        if isinstance(entry, Binding):
            self._draw_binding_value(surface, entry, y, colour, selected)
            return
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

    def _draw_binding_value(self, surface: pygame.Surface, entry: Binding,
                            y: int, colour, selected: bool) -> None:
        """Atanmis tus - satirin SAG ucunda, sutun genisligine gore.

        Sabit bir `VALUE_X` kullanilamiyor: iki sutun var ve ikincisi
        ekranin sagina dusuyor.
        """
        rect = self._row_rect(self.entries.index(entry))
        capturing = self.capturing is entry
        table = binds.read(self.settings)
        label = ("..." if capturing
                 else binds.labels_for(table, entry.action))
        bright = (palette.color("violet_bright") if capturing
                  else palette.role("ui_text_bright") if selected else colour)
        text.draw(surface, label, rect.right - 6, y, color=bright,
                  align="right")

    def _draw_capture_box(self, surface: pygame.Surface) -> None:
        """"Bir tusa bas" kutusu.

        Ekranin ortasinda ve **modal**: yakalama sirasinda gezinme kapali
        oldugu icin oyuncunun neden hicbir seyin hareket etmedigini
        anlamasi gerekiyor.
        """
        if self.capturing is None:
            return
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 180))
        surface.blit(veil, (0, 0))

        box = pygame.Rect(0, 0, *CAPTURE_BOX)
        box.center = (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2)
        # **Once opak dolgu, sonra cerceve.** `panel()` yari saydam
        # ciziyor ve arkadaki satirlar kutunun icinden okunuyordu -
        # "bir tusa bas" yazisi baska bir satirin uzerine binmis gibi
        # gorunuyordu.
        surface.fill(palette.color("void"), box)
        panel(surface, box)
        text.draw(surface, self.capturing.label, box.centerx, box.y + 8,
                  color=palette.role("ui_text_dim"), align="center")
        text.draw(surface, t("controls.press_key"), box.centerx, box.y + 22,
                  color=palette.color("violet_bright"), align="center")
        # Ipucu kutunun ICINDE: disarida cizilince arkadaki satirlarin
        # arasinda kayboluyordu.
        text.draw(surface, t("controls.cancel_hint"), box.centerx,
                  box.bottom - GLYPH_HEIGHT - 6,
                  color=palette.role("ui_text_dim"), align="center")

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
