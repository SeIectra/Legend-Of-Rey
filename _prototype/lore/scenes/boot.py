"""Acilis sahnesi: sanat uretimini onden yapar ve stüdyo logosunu gosterir.

Prosedurel sanat ucuz degil - Rey'in tum animasyonlarini uretmek birkac yuz
milisaniye surer. Bunu oyunun ortasinda yapmak takilma yaratir. Burada, logo
ekrandayken, kare kare uretiyoruz: oyuncu bekleme hissetmeden hazir oluyoruz.
"""
from __future__ import annotations

import pygame

from lore.constants import GAME_SHORT, VIRTUAL_H, VIRTUAL_W
from lore.core.input import Action
from lore.core.mathx import clamp, ease_out_cubic
from lore.core.scene import Scene
from lore.gfx import text as gfx_text
from lore.gfx.palette import RAMPS, UI_TEXT, UI_TEXT_DIM
from lore.gfx.sprites import ARCHETYPES, build_sprite_set
from lore.gfx.tiles import build_tileset

# (etiket, uretici) ciftleri. Sirayla, kare basina birer tane calistirilir.
WARMUP: list[tuple[str, str]] = [
    ("Rey uyaniyor", "sprites:rey"),
    ("Echobrand doveluyor", "sprites:rey_armed"),
    ("Goblinler toplaniyor", "sprites:goblin"),
    ("Okcular mevzileniyor", "sprites:archer"),
    ("Kemikler diriliyor", "sprites:skeleton"),
    ("Zindan orluyor", "tiles:hollow"),
    ("Orman buyuyor", "tiles:forest"),
]


class BootScene(Scene):
    def on_enter(self, **kwargs) -> None:
        self.timer = 0.0
        self.step = 0
        self.done = False
        self.status = WARMUP[0][0] if WARMUP else ""

    def update(self, dt: float) -> None:
        self.timer += dt

        # Kare basina tek bir uretim: logo animasyonu akici kalir.
        if self.step < len(WARMUP):
            label, key = WARMUP[self.step]
            self.status = label
            self._warm(key)
            self.step += 1
            return

        if self.timer > 1.6 or self.app.input.pressed(Action.CONFIRM):
            if not self.done:
                self.done = True
                from lore.scenes.title import TitleScene
                self.manager.replace(TitleScene)

    def _warm(self, key: str) -> None:
        if key.startswith("sprites:"):
            name = key.split(":", 1)[1]
            spec = ARCHETYPES.get(name)
            if spec is not None:
                self.app.assets.generated(key, lambda: build_sprite_set(spec))
        elif key.startswith("tiles:"):
            theme = key.split(":", 1)[1]
            self.app.assets.generated(key, lambda: build_tileset(theme))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(RAMPS["ink"][0])
        cx, cy = VIRTUAL_W // 2, VIRTUAL_H // 2

        fade = clamp(self.timer * 1.8, 0.0, 1.0)
        alpha = int(255 * ease_out_cubic(fade))

        gfx_text.draw_text(surface, GAME_SHORT, cx, cy - 22, color=UI_TEXT,
                           align="center", outline=True, alpha=alpha,
                           tracking=4)
        gfx_text.draw_text(surface, "Legend of Rey", cx, cy - 4,
                           color=UI_TEXT_DIM, align="center", alpha=alpha)

        # Yukleme cubugu
        total = max(1, len(WARMUP))
        ratio = clamp(self.step / total, 0.0, 1.0)
        bar_rect = pygame.Rect(cx - 60, cy + 22, 120, 3)
        pygame.draw.rect(surface, RAMPS["ink"][2], bar_rect)
        pygame.draw.rect(surface, RAMPS["azure"][3],
                         (bar_rect.x, bar_rect.y, int(bar_rect.w * ratio),
                          bar_rect.h))
        if ratio < 1.0:
            gfx_text.draw_text(surface, self.status, cx, cy + 32,
                               color=UI_TEXT_DIM, align="center")
