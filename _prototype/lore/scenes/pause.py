"""Duraklatma menusu.

Oyunun ustune *biner*: altaki sahne cizilmeye devam eder ama guncellenmez.
Eski koddaki gibi ayri bir dongu acmiyoruz - bu yuzden ESC her zaman calisir,
pencere her zaman kapanir ve muzik kesilmez.
"""
from __future__ import annotations

import pygame

from lore.constants import VIRTUAL_H, VIRTUAL_W
from lore.core.save import save_slot
from lore.core.scene import Scene
from lore.gfx import text as gfx_text
from lore.gfx.palette import RAMPS, UI_TEXT, UI_TEXT_DIM
from lore.gfx.ui import Menu, MenuItem, panel


class PauseScene(Scene):
    blocks_update = True        # Altaki oyun donar
    blocks_draw = False         # ...ama gorunur kalir
    transparent_bg = True

    def on_enter(self, save=None, **kwargs) -> None:
        self.save = save
        self.app.audio.duck(0.45)
        self.menu = Menu([
            MenuItem("Devam", self._resume),
            MenuItem("Ayarlar", self._settings),
            MenuItem("Kaydet", self._save, enabled=save is not None),
            MenuItem("Ana Menu", self._to_title,
                     hint="Kaydedilmemis ilerleme kaybolur"),
        ], VIRTUAL_W // 2, 118)

    def on_exit(self) -> None:
        self.app.audio.unduck()

    # --- Eylemler -----------------------------------------------------------
    def _resume(self) -> None:
        self.manager.pop()

    def _settings(self) -> None:
        from lore.scenes.settings import SettingsScene
        self.manager.push(SettingsScene)

    def _save(self) -> None:
        if self.save is None:
            return
        # Yigindaki oyun sahnesini bul ve guncel oyuncu durumunu kayda yaz.
        for scene in reversed(self.manager.stack):
            player = getattr(scene, "player", None)
            if player is not None:
                player.write_save(self.save)
                break
        save_slot(getattr(self.save, "slot", 0), self.save)
        self.app.audio.play("checkpoint")

    def _to_title(self) -> None:
        from lore.scenes.title import TitleScene
        self.manager.set_root(TitleScene)

    # --- Dongu --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.menu.click(self.app, self.app.audio)

    def update(self, dt: float) -> None:
        self.menu.update(dt)
        self.menu.handle_mouse(self.app, self.app.audio)
        self.menu.handle_input(self.app.input, self.app.audio)

    def draw(self, surface: pygame.Surface) -> None:
        veil = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        veil.fill((*RAMPS["ink"][0], 175))
        surface.blit(veil, (0, 0))

        rect = pygame.Rect(VIRTUAL_W // 2 - 90, 84, 180, 110)
        panel(surface, rect)
        gfx_text.draw_text(surface, "DURAKLATILDI", VIRTUAL_W // 2, 94,
                           color=UI_TEXT, align="center", shadow=True,
                           tracking=2)
        self.menu.draw(surface)

        if self.save is not None:
            minutes = int(self.save.playtime // 60)
            info = (f"Act {self.save.act}  |  {minutes} dk  |  "
                    f"{self.save.essence} oz  |  {self.save.deaths} olum")
            gfx_text.draw_text(surface, info, VIRTUAL_W // 2, VIRTUAL_H - 34,
                               color=UI_TEXT_DIM, align="center")
