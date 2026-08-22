"""Duraklatma menusu.

Oyunun **ustune biner**: altaki sahne cizilmeye devam eder ama guncellenmez.
Arka plan karartilir ve hafif bulaniklastirilir (4x kucult, 4x buyut -
Gaussian gerekmez).

**Kritik UX (docs/menu-ui.md 7):** ANA MENU'ye basinca kaydedildigi
*acikca* yazilir. "Kaydedilmemis ilerleme" belirsizligi oyuncuda soru
firtinasi yaratir: Kaydetmedi mi? O boss dovusunu tekrar mi oynayacagim?
Bu tuzaga dusmuyoruz.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.systems.save import read_save, write_save
from src.ui import text
from src.ui.i18n import t
from src.ui.widgets import Menu, MenuItem, blur, panel

PANEL_WIDTH = 168
# Dort oge + ANA MENU oncesindeki bosluk. Kisa tutunca son satir cerceveyi
# kesiyordu - panel yuksekligi menu icerigiyle birlikte hesaplanmali.
PANEL_HEIGHT = 128
BLUR_FACTOR = 4


class PauseScene(Scene):
    blocks_update = True        # Altaki oyun donar
    blocks_draw = False         # ...ama gorunur kalir
    transparent_bg = True

    def on_enter(self, save_data=None, **kwargs: object) -> None:
        self.save_data = save_data
        self.confirm_quit: Menu | None = None
        self.saved_notice = 0
        self._blurred: pygame.Surface | None = None

        self.menu = Menu([
            MenuItem("pause.resume", self._resume),
            MenuItem("pause.equipment", None, enabled=False,
                     hint="pause.equipment_hint"),
            MenuItem("pause.settings", self._open_settings),
            MenuItem("pause.main_menu", self._ask_quit, gap_before=True),
        ], INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 - 30, width=120,
            centered=True, on_sound=self.game.play_sound)

    # --- Eylemler -----------------------------------------------------------
    def _resume(self) -> None:
        self.scenes.pop()

    def _open_settings(self) -> None:
        from src.ui.settings_scene import SettingsScene
        self.scenes.push(SettingsScene)

    def _ask_quit(self) -> None:
        # Once kaydet, sonra sor. Oyuncu "kaydedildi" yazisini gordugunde
        # bu gercekten olmus olmali.
        self._save_progress()
        self.confirm_quit = Menu([
            MenuItem("common.cancel", self._cancel_quit),
            MenuItem("pause.quit_confirm", self._to_main_menu, danger=True),
        ], INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 + 18, width=140,
            centered=True, on_sound=self.game.play_sound)

    def _cancel_quit(self) -> None:
        self.confirm_quit = None

    def _save_progress(self) -> None:
        data = self.save_data
        if data is None:
            data, _ = read_save()
        if data is not None:
            write_save(data)
            self.saved_notice = 180
            self.game.play_sound("save_written")

    def _to_main_menu(self) -> None:
        from src.ui.menu import MainMenuScene
        self.scenes.set_root(MainMenuScene)

    # --- Dongu --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if self.game.input.pressed(Action.CANCEL):
                if self.confirm_quit:
                    self._cancel_quit()
                else:
                    self._resume()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            (self.confirm_quit or self.menu).click(self.game)

    def update(self) -> None:
        self.saved_notice = max(0, self.saved_notice - 1)
        (self.confirm_quit or self.menu).update(self.game)

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_backdrop(surface)

        rect = pygame.Rect(INTERNAL_WIDTH // 2 - PANEL_WIDTH // 2,
                           INTERNAL_HEIGHT // 2 - PANEL_HEIGHT // 2 - 6,
                           PANEL_WIDTH, PANEL_HEIGHT)
        panel(surface, rect)
        text.draw(surface, t("pause.heading"), INTERNAL_WIDTH // 2,
                  rect.y + 8, color=palette.role("ui_text"), align="center",
                  tracking=2)

        self.menu.draw(surface)
        self._draw_status(surface)

        if self.confirm_quit:
            self._draw_quit_dialog(surface)

        (self.confirm_quit or self.menu).draw_cursor(surface, self.game)

    # --- Cizim yardimcilari -------------------------------------------------
    def _draw_backdrop(self, surface: pygame.Surface) -> None:
        """Oyun arkada gorunur ama karartilmis ve bulanik."""
        if self._blurred is None:
            self._blurred = blur(surface.copy(), BLUR_FACTOR)
        surface.blit(self._blurred, (0, 0))

        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 150))
        surface.blit(veil, (0, 0))

    def _draw_status(self, surface: pygame.Surface) -> None:
        data = self.save_data
        if data is None:
            return
        dots = "●" * (data.echo_tier + 1) + "○" * (2 - data.echo_tier)
        info = t("pause.status", chapter=data.chapter, dots=dots, gold=data.gold)
        text.draw(surface, info, INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 30,
                  color=palette.role("ui_text_dim"), align="center")

    def _draw_quit_dialog(self, surface: pygame.Surface) -> None:
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 190))
        surface.blit(veil, (0, 0))

        rect = pygame.Rect(INTERNAL_WIDTH // 2 - 100,
                           INTERNAL_HEIGHT // 2 - 40, 200, 80)
        panel(surface, rect)
        text.draw(surface, t("pause.quit_question"), INTERNAL_WIDTH // 2, rect.y + 10,
                  color=palette.role("ui_text"), align="center")
        # Belirsizlik birakmiyoruz - kaydedildigini acikca soyluyoruz.
        text.draw(surface, t("pause.quit_saved"), INTERNAL_WIDTH // 2,
                  rect.y + 24, color=palette.color("echo_bright"),
                  align="center")
        self.confirm_quit.draw(surface)

    def debug_lines(self) -> list[str]:
        return [f"duraklatma · seçili: {self.menu.selected.text}"]
