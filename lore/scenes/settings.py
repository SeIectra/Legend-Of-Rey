"""Ayarlar ekrani.

Ses, goruntu ve erisilebilirlik. Her degisiklik aninda uygulanir ve diske
yazilir - "Kaydet" butonu yok, cunku oyuncunun ayar yaptigini unutup cikmasi
her zaman kendi hatasi degildir.

Erisilebilirlik secenekleri (ekran sarsintisi, flas siddeti) burada birinci
sinif vatandas. Kapatilabilir olmalari bir luks degil.
"""
from __future__ import annotations

import pygame

from lore.constants import VIRTUAL_H, VIRTUAL_W
from lore.core.input import Action
from lore.core.scene import Scene
from lore.gfx import text as gfx_text
from lore.gfx.palette import RAMPS, UI_TEXT, UI_TEXT_DIM, UI_TEXT_HILITE
from lore.gfx.ui import Slider, panel

ROW_H = 16
TOP = 62


class SettingsScene(Scene):
    blocks_update = True
    blocks_draw = False
    transparent_bg = True

    def on_enter(self, **kwargs) -> None:
        config = self.app.config
        audio = self.app.audio

        def set_master(v):
            config.set("master_volume", v)
            audio.apply_config()

        def set_music(v):
            config.set("music_volume", v)
            audio.apply_config()

        def set_sfx(v):
            config.set("sfx_volume", v)
            audio.apply_config()

        self.sliders = {
            "master": Slider("Ana Ses", config.get("master_volume"), set_master),
            "music": Slider("Muzik", config.get("music_volume"), set_music),
            "sfx": Slider("Efektler", config.get("sfx_volume"), set_sfx),
            "shake": Slider("Ekran Sarsintisi", config.get("screen_shake"),
                            self._set_shake),
            "flash": Slider("Flas Siddeti", config.get("flash_intensity"),
                            lambda v: config.set("flash_intensity", v)),
        }
        # (anahtar, tur) - tur: slider | toggle | action
        self.rows = [
            ("master", "slider"), ("music", "slider"), ("sfx", "slider"),
            ("shake", "slider"), ("flash", "slider"),
            ("fullscreen", "toggle"), ("vsync", "toggle"),
            ("show_fps", "toggle"), ("damage_numbers", "toggle"),
            ("rumble", "toggle"),
            ("back", "action"),
        ]
        self.labels = {
            "fullscreen": "Tam Ekran", "vsync": "V-Sync",
            "show_fps": "FPS Goster", "damage_numbers": "Hasar Sayilari",
            "rumble": "Kol Titresimi", "back": "Geri",
        }
        self.index = 0

    def _set_shake(self, value: float) -> None:
        self.app.config.set("screen_shake", value)
        for scene in self.manager.stack:
            camera = getattr(scene, "camera", None)
            if camera is not None and hasattr(camera, "shake_scale"):
                camera.shake_scale = value

    # --- Girdi --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._close()

    def update(self, dt: float) -> None:
        inp = self.app.input
        audio = self.app.audio

        if inp.pressed(Action.UP):
            self.index = (self.index - 1) % len(self.rows)
            audio.play("ui_move")
        elif inp.pressed(Action.DOWN):
            self.index = (self.index + 1) % len(self.rows)
            audio.play("ui_move")

        key, kind = self.rows[self.index]
        if kind == "slider":
            if inp.held(Action.LEFT):
                self.sliders[key].adjust(-1, audio if inp.pressed(Action.LEFT) else None)
            elif inp.held(Action.RIGHT):
                self.sliders[key].adjust(1, audio if inp.pressed(Action.RIGHT) else None)
        elif kind == "toggle":
            if inp.pressed(Action.CONFIRM) or inp.pressed(Action.LEFT) \
                    or inp.pressed(Action.RIGHT):
                self._toggle(key)
        elif kind == "action" and inp.pressed(Action.CONFIRM):
            self._close()

    def _toggle(self, key: str) -> None:
        self.app.audio.play("ui_select")
        if key == "fullscreen":
            # toggle_fullscreen ayari kendisi cevirir ve pencereyi yeniden kurar.
            self.app.toggle_fullscreen()
            return
        self.app.config.toggle(key)
        if key == "vsync":
            self.app.config.save()
            self.app.rebuild_window()

    def _close(self) -> None:
        self.app.config.save(force=True)
        self.app.audio.play("ui_back")
        self.manager.pop()

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        veil = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        veil.fill((*RAMPS["ink"][0], 205))
        surface.blit(veil, (0, 0))

        rect = pygame.Rect(VIRTUAL_W // 2 - 130, 40, 260, ROW_H * len(self.rows) + 34)
        panel(surface, rect)
        gfx_text.draw_text(surface, "AYARLAR", VIRTUAL_W // 2, 48,
                           color=UI_TEXT, align="center", shadow=True, tracking=2)

        x = rect.x + 14
        for i, (key, kind) in enumerate(self.rows):
            y = TOP + i * ROW_H
            selected = i == self.index
            color = UI_TEXT_HILITE if selected else UI_TEXT_DIM
            if selected:
                gfx_text.draw_text(surface, ">", x - 10, y, color=UI_TEXT_HILITE)

            if kind == "slider":
                self.sliders[key].draw(surface, pygame.Rect(x, y, 220, ROW_H),
                                       selected)
            elif kind == "toggle":
                gfx_text.draw_text(surface, self.labels[key], x, y, color=color)
                state = "ACIK" if self.app.config.get(key) else "KAPALI"
                on = bool(self.app.config.get(key))
                gfx_text.draw_text(
                    surface, state, x + 220, y, align="right",
                    color=RAMPS["moss"][4] if on else RAMPS["stone"][2])
            else:
                gfx_text.draw_text(surface, self.labels[key], x, y, color=color)

        gfx_text.draw_text(surface, "[<>] degistir   [Esc] kapat",
                           VIRTUAL_W // 2, rect.bottom + 8, color=UI_TEXT_DIM,
                           align="center")
