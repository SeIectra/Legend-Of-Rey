"""Ana menu.

Kurallar (docs/menu-ui.md 3, CLAUDE.md 9):
  * DEVAM ET en ustte ve **onceden secili** - oyuncu dusunmeden devam etsin
  * Kayit yoksa DEVAM ET **gorunmez** (gri degil) - gri buton "bir seyi
    kacirdim" hissi verir
  * CIKIS bir boslukla ayrilmis - yanlislikla basma riski azalir
  * YENI OYUN uzerine yazacaksa onay sorulur, **varsayilan secim IPTAL**
  * Hicbir gecis 12 kareyi asmaz

Sahne cilasi (mor alev, sarkan zincirler, dikey yolculuk) Gorev 7'de.
Burada islevsellik onceliklidir: cirkin ama hizli bir menu, guzel ama
kullanilamayan bir menuden iyidir.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.systems.save import has_save, read_save
from src.ui import text
from src.ui.font_data import GLYPH_HEIGHT
from src.ui.widgets import Menu, MenuItem, panel

TITLE_Y = 46
MENU_X = 46
MENU_Y = 116
CARD_X = 250
CARD_Y = 104
CARD_WIDTH = 178
# Baslik + bolum adi + ayrac + dort satir. Kisa tutunca son satir ("Gizli")
# cerceveyi kesiyordu.
CARD_HEIGHT = 96


class MainMenuScene(Scene):
    def on_enter(self, **kwargs: object) -> None:
        self.frame = 0
        self.save_data, self.save_status = read_save()
        self.confirm_overwrite: Menu | None = None
        self.notice = ""
        self.notice_frames = 0

        if self.save_status == "backup":
            self.notice = "Ana kayıt okunamadı, yedekten dönüldü."
            self.notice_frames = 300

        self.menu = self._build_menu()

    def _build_menu(self) -> Menu:
        save_exists = has_save()
        return Menu([
            # Kayit yoksa gorunmez - gri degil, YOK.
            MenuItem("DEVAM ET", self._continue, visible=save_exists,
                     hint="Kaldığın yerden devam et"),
            MenuItem("YENİ OYUN", self._new_game,
                     hint="Rey'in hikâyesini baştan başla"),
            MenuItem("AYARLAR", self._open_settings,
                     hint="Görüntü, ses ve erişilebilirlik"),
            MenuItem("EKSTRALAR", None, enabled=False,
                     hint="Oyun ilerledikçe açılır"),
            MenuItem("ÇIKIŞ", self.game.quit, gap_before=True),
        ], MENU_X, MENU_Y, width=140,
            on_sound=self.game.play_ui_sound)

    # --- Eylemler -----------------------------------------------------------
    def _continue(self) -> None:
        if self.save_data is None:
            return
        from src.scenes.combat_room import CombatRoomScene
        self.scenes.replace(CombatRoomScene,
                            character=self.save_data.character)

    def _new_game(self) -> None:
        if has_save():
            self._ask_overwrite()
            return
        self._go_character_select()

    def _ask_overwrite(self) -> None:
        # Yikici eylem: varsayilan secim daima IPTAL.
        self.confirm_overwrite = Menu([
            MenuItem("İPTAL", self._cancel_overwrite),
            MenuItem("YİNE DE BAŞLA", self._go_character_select, danger=True),
        ], INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 + 14, width=150,
            centered=True, on_sound=self.game.play_ui_sound)

    def _cancel_overwrite(self) -> None:
        self.confirm_overwrite = None

    def _go_character_select(self) -> None:
        self.confirm_overwrite = None
        from src.ui.character_select import CharacterSelectScene
        self.scenes.push(CharacterSelectScene)

    def _open_settings(self) -> None:
        from src.ui.settings_scene import SettingsScene
        self.scenes.push(SettingsScene)

    # --- Dongu --------------------------------------------------------------
    def on_resume(self) -> None:
        # Karakter seciminden ya da ayarlardan donunce kayit degismis olabilir.
        self.save_data, self.save_status = read_save()
        self.menu = self._build_menu()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            active = self.confirm_overwrite or self.menu
            active.click(self.game)
        elif event.type == pygame.KEYDOWN and self.confirm_overwrite:
            if self.game.input.pressed(Action.CANCEL):
                self._cancel_overwrite()

    def update(self) -> None:
        self.frame += 1
        self.notice_frames = max(0, self.notice_frames - 1)
        active = self.confirm_overwrite or self.menu
        active.update(self.game)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("abyss_dark"))
        self._draw_backdrop(surface)
        self._draw_title(surface)

        self.menu.draw(surface)
        self.menu.draw_hint(surface, INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 26)

        if self.save_data is not None and self.menu.index == 0:
            self._draw_save_card(surface)

        if self.confirm_overwrite:
            self._draw_overwrite_dialog(surface)

        self._draw_footer(surface)
        active = self.confirm_overwrite or self.menu
        active.draw_cursor(surface, self.game)

    # --- Cizim yardimcilari -------------------------------------------------
    def _draw_backdrop(self, surface: pygame.Surface) -> None:
        """Gorev 7'de mor alev sahnesi gelecek; simdilik sade bir mahzen."""
        for index in range(5):
            x = 300 + index * 34
            height = 120 + (index % 3) * 26
            surface.fill(palette.color("stone_darkest"),
                         (x, INTERNAL_HEIGHT - height, 12, height))
        surface.fill(palette.color("ink_soft"),
                     (0, INTERNAL_HEIGHT - 34, INTERNAL_WIDTH, 34))
        # Hafif nabiz atan bir isik - sahne "olu" gorunmesin.
        pulse = 0.5 + 0.5 * math.sin(self.frame * 0.02)
        radius = int(26 + pulse * 5)
        pygame.draw.circle(surface, palette.color("violet_dark"),
                           (372, INTERNAL_HEIGHT - 58), radius)
        pygame.draw.circle(surface, palette.color("violet"),
                           (372, INTERNAL_HEIGHT - 58), max(2, radius // 3))

    def _draw_title(self, surface: pygame.Surface) -> None:
        text.draw(surface, text.tr_upper("Legend of"), MENU_X, TITLE_Y,
                  color=palette.role("ui_text_dim"), tracking=2)
        text.draw(surface, text.tr_upper("Rey"), MENU_X, TITLE_Y + 16,
                  color=palette.role("ui_text_bright"), outline=True,
                  tracking=6)
        pygame.draw.line(surface, palette.color("violet"),
                         (MENU_X, TITLE_Y + 34), (MENU_X + 96, TITLE_Y + 34))

    def _draw_save_card(self, surface: pygame.Surface) -> None:
        """DEVAM ET kartı: uc hafta sonra donen oyuncu nerede kaldigini
        hatirlamiyor. Bu kart hatirlatir."""
        data = self.save_data
        rect = pygame.Rect(CARD_X, CARD_Y, CARD_WIDTH, CARD_HEIGHT)
        panel(surface, rect)

        line_y = rect.y + 6
        text.draw(surface, f"BÖLÜM {data.chapter}", rect.x + 8, line_y,
                  color=palette.role("ui_text_bright"))
        line_y += GLYPH_HEIGHT + 2
        text.draw(surface, f"\"{data.chapter_name}\"", rect.x + 8, line_y,
                  color=palette.role("ui_text"))
        line_y += GLYPH_HEIGHT + 4
        pygame.draw.line(surface, palette.color("stone_dark"),
                         (rect.x + 8, line_y), (rect.right - 8, line_y))
        line_y += 4

        rows = (
            ("Süre", data.playtime_text),
            ("Altın", str(data.gold)),
            ("Yankı", "●" * (data.echo_tier + 1) + "○" * (2 - data.echo_tier)),
            ("Gizli", f"{data.secrets_found}/{max(1, data.secrets_total)}"),
        )
        for label, value in rows:
            text.draw(surface, label, rect.x + 8, line_y,
                      color=palette.role("ui_text_dim"))
            text.draw(surface, value, rect.right - 8, line_y,
                      color=palette.role("ui_text"), align="right")
            line_y += GLYPH_HEIGHT + 1

    def _draw_overwrite_dialog(self, surface: pygame.Surface) -> None:
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 190))
        surface.blit(veil, (0, 0))

        rect = pygame.Rect(INTERNAL_WIDTH // 2 - 108,
                           INTERNAL_HEIGHT // 2 - 46, 216, 92)
        panel(surface, rect)
        text.draw(surface, "Mevcut kaydın silinecek.", INTERNAL_WIDTH // 2,
                  rect.y + 10, color=palette.role("ui_text"), align="center")
        if self.save_data:
            detail = (f"BÖLÜM {self.save_data.chapter} · "
                      f"{self.save_data.playtime_text}")
            text.draw(surface, detail, INTERNAL_WIDTH // 2, rect.y + 24,
                      color=palette.role("ui_text_dim"), align="center")
        self.confirm_overwrite.draw(surface)

    def _draw_footer(self, surface: pygame.Surface) -> None:
        if self.notice_frames > 0:
            text.draw(surface, self.notice, INTERNAL_WIDTH // 2,
                      INTERNAL_HEIGHT - 40, color=palette.color("danger_bright"),
                      align="center")
        text.draw(surface, "Ardeko Studios", 6, INTERNAL_HEIGHT - 12,
                  color=palette.color("stone_dark"))

    def debug_lines(self) -> list[str]:
        return [f"kayıt: {self.save_status}  "
                f"seçili: {self.menu.selected.label}"]
