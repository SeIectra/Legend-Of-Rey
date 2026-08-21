"""Parallax arka planlar.

Bes katman, farkli hizlarda kayar. Uzaktaki katman neredeyse sabit, yakindaki
kamerayla neredeyse birlikte hareket eder; arada olusan hiz farki derinlik
yanilsamasini yaratir.

Katmanlar prosedurel uretilir ve yatayda dongusel doseme yapilir: seviye ne
kadar genis olursa olsun arka plan bellekte tek bir serit olarak durur.

Silueti okunur tutmak icin uzak katmanlar hem koyu hem dusuk kontrastli
ciziliyor. Arka plan asla oynanisi bogmamali.
"""
from __future__ import annotations

import math

import numpy as np
import pygame

from lore.constants import VIRTUAL_H, VIRTUAL_W
from lore.gfx.forge import Canvas
from lore.gfx.palette import mix

STRIP_W = VIRTUAL_W * 2          # Dongusel serit genisligi


def _ridge(canvas: Canvas, seed: int, base_y: int, amplitude: float,
           roughness: float, ramp: str, step: int, fill_to: int) -> None:
    """Sahte-fraktal dag/tepe silueti cizer."""
    rng = np.random.default_rng(seed)
    w = canvas.w
    heights = np.zeros(w)
    # Ust uste binen sinus dalgalari: ucuz ama inandirici bir siluet.
    for octave in range(4):
        freq = (2 ** octave) * roughness
        phase = rng.uniform(0, math.tau)
        amp = amplitude / (1.6 ** octave)
        heights += np.sin(np.linspace(0, math.tau * freq, w, endpoint=False)
                          + phase) * amp
    for x in range(w):
        top = int(base_y + heights[x])
        canvas.fill_rect(x, top, 1, max(0, fill_to - top), ramp, step)


def _pillars(canvas: Canvas, seed: int, base_y: int, ramp: str, step: int,
             count: int = 7) -> None:
    rng = np.random.default_rng(seed)
    for _ in range(count):
        x = int(rng.integers(0, canvas.w))
        width = int(rng.integers(7, 15))
        height = int(rng.integers(40, 100))
        canvas.fill_rect(x, base_y - height, width, height, ramp, step)
        canvas.fill_rect(x - 2, base_y - height - 4, width + 4, 5, ramp, step + 1)
        canvas.fill_rect(x - 2, base_y - 4, width + 4, 5, ramp, step + 1)


def _trees(canvas: Canvas, seed: int, base_y: int, ramp: str, step: int,
           count: int = 16) -> None:
    rng = np.random.default_rng(seed)
    for _ in range(count):
        x = int(rng.integers(0, canvas.w))
        height = int(rng.integers(30, 76))
        canvas.fill_rect(x, base_y - height, 3, height, "earth", max(0, step - 1))
        for tier in range(3):
            r = (10 - tier * 2.4)
            cy = base_y - height + 6 + tier * 9
            canvas.ellipse(x + 1, cy, r, r * 0.72, ramp, step)


def _crystals(canvas: Canvas, seed: int, base_y: int, ramp: str, step: int,
              count: int = 10) -> None:
    rng = np.random.default_rng(seed)
    for _ in range(count):
        x = int(rng.integers(0, canvas.w))
        height = int(rng.integers(18, 54))
        width = int(rng.integers(4, 10))
        canvas.polygon([(x, base_y), (x + width, base_y),
                        (x + width * 0.5, base_y - height)], ramp, step)


# --- Tema receteleri --------------------------------------------------------
# (cizici, taban y, rampa, basamak, kaydirma carpani)
LAYER_RECIPES: dict[str, list[dict]] = {
    "hollow": [
        {"kind": "ridge", "y": 96, "amp": 22, "rough": 0.7, "ramp": "ink", "step": 2, "factor": 0.06},
        {"kind": "ridge", "y": 128, "amp": 16, "rough": 1.3, "ramp": "ink", "step": 3, "factor": 0.14},
        {"kind": "pillars", "y": 190, "ramp": "stone", "step": 1, "factor": 0.28},
        {"kind": "pillars", "y": 230, "ramp": "stone", "step": 2, "factor": 0.46},
    ],
    "forest": [
        {"kind": "ridge", "y": 88, "amp": 26, "rough": 0.6, "ramp": "ink", "step": 2, "factor": 0.05},
        {"kind": "trees", "y": 176, "ramp": "moss", "step": 1, "factor": 0.18},
        {"kind": "trees", "y": 214, "ramp": "moss", "step": 2, "factor": 0.34},
        {"kind": "trees", "y": 250, "ramp": "moss", "step": 0, "factor": 0.55},
    ],
    "vault": [
        {"kind": "ridge", "y": 110, "amp": 14, "rough": 0.9, "ramp": "ink", "step": 2, "factor": 0.07},
        {"kind": "pillars", "y": 200, "ramp": "azure", "step": 1, "factor": 0.22},
        {"kind": "crystals", "y": 238, "ramp": "azure", "step": 2, "factor": 0.42},
    ],
    "spire": [
        {"kind": "ridge", "y": 80, "amp": 30, "rough": 0.5, "ramp": "ink", "step": 2, "factor": 0.05},
        {"kind": "ridge", "y": 130, "amp": 20, "rough": 1.1, "ramp": "ash", "step": 1, "factor": 0.15},
        {"kind": "pillars", "y": 226, "ramp": "ash", "step": 2, "factor": 0.40},
    ],
    "sundered": [
        {"kind": "ridge", "y": 100, "amp": 24, "rough": 0.8, "ramp": "ink", "step": 2, "factor": 0.06},
        {"kind": "crystals", "y": 190, "ramp": "violet", "step": 1, "factor": 0.24},
        {"kind": "crystals", "y": 244, "ramp": "violet", "step": 3, "factor": 0.48},
    ],
}

SKY_GRADIENTS: dict[str, tuple] = {
    "hollow": ((16, 16, 34), (44, 34, 58)),
    "forest": ((18, 30, 34), (58, 68, 52)),
    "vault": ((8, 20, 40), (26, 62, 92)),
    "spire": ((30, 20, 22), (96, 56, 40)),
    "sundered": ((22, 10, 34), (78, 36, 96)),
}


class Parallax:
    def __init__(self, theme: str, assets) -> None:
        self.theme = theme if theme in LAYER_RECIPES else "hollow"
        self.assets = assets
        self.sky = assets.generated(f"sky:{self.theme}",
                                    lambda: self._build_sky(self.theme))
        recipes = LAYER_RECIPES[self.theme]
        self.layers: list[tuple[pygame.Surface, float]] = []
        for i, recipe in enumerate(recipes):
            surface = assets.generated(
                f"parallax:{self.theme}:{i}",
                lambda r=recipe, s=i: self._build_layer(r, s))
            self.layers.append((surface, recipe["factor"]))

    @staticmethod
    def _build_sky(theme: str) -> pygame.Surface:
        top, bottom = SKY_GRADIENTS.get(theme, SKY_GRADIENTS["hollow"])
        sky = pygame.Surface((1, VIRTUAL_H)).convert()
        for y in range(VIRTUAL_H):
            sky.set_at((0, y), mix(top, bottom, y / VIRTUAL_H))
        return pygame.transform.scale(sky, (VIRTUAL_W, VIRTUAL_H))

    @staticmethod
    def _build_layer(recipe: dict, seed: int) -> pygame.Surface:
        canvas = Canvas(STRIP_W, VIRTUAL_H + 60)
        kind = recipe["kind"]
        ramp, step = recipe["ramp"], recipe["step"]
        base_y = recipe["y"]
        if kind == "ridge":
            _ridge(canvas, seed * 91 + 7, base_y, recipe["amp"], recipe["rough"],
                   ramp, step, canvas.h)
        elif kind == "pillars":
            _pillars(canvas, seed * 131 + 13, base_y, ramp, step)
        elif kind == "trees":
            _trees(canvas, seed * 177 + 3, base_y, ramp, step)
        elif kind == "crystals":
            _crystals(canvas, seed * 211 + 5, base_y, ramp, step)
        return canvas.resolve()

    def draw(self, surface: pygame.Surface, camera) -> None:
        surface.blit(self.sky, (0, 0))
        ox, oy = camera.offset
        for image, factor in self.layers:
            # Kaydirmayi serit genisligine gore sarmalıyoruz: sonsuz doseme.
            shift = int(ox * factor) % STRIP_W
            y = int(-oy * factor * 0.35) - 30
            surface.blit(image, (-shift, y))
            if shift > STRIP_W - VIRTUAL_W:
                surface.blit(image, (STRIP_W - shift, y))


class Weather:
    """Yagmur / kar / kul. Basit ama atmosferi tasiyan bir katman."""

    def __init__(self, kind: str = "none", count: int = 90) -> None:
        self.kind = kind
        self.count = count if kind != "none" else 0
        rng = np.random.default_rng(4242)
        self.x = rng.uniform(0, VIRTUAL_W, self.count)
        self.y = rng.uniform(0, VIRTUAL_H, self.count)
        self.speed = rng.uniform(0.6, 1.4, self.count)
        self.drift = rng.uniform(-0.4, 0.4, self.count)

    def update(self, dt: float) -> None:
        if not self.count:
            return
        if self.kind == "rain":
            self.y += 340.0 * self.speed * dt
            self.x += 46.0 * dt
        elif self.kind == "snow":
            self.y += 44.0 * self.speed * dt
            self.x += np.sin(self.y * 0.05) * 12.0 * dt
        elif self.kind == "ash":
            self.y += 26.0 * self.speed * dt
            self.x += self.drift * 20.0 * dt
        # Ekrandan cikanlari tepeden geri sok.
        wrapped = self.y > VIRTUAL_H
        self.y[wrapped] = -4.0
        self.x = np.mod(self.x, VIRTUAL_W)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.count:
            return
        if self.kind == "rain":
            color = (140, 170, 210)
            for i in range(self.count):
                x, y = int(self.x[i]), int(self.y[i])
                pygame.draw.line(surface, color, (x, y), (x - 1, y + 5))
        else:
            color = (220, 220, 230) if self.kind == "snow" else (150, 140, 135)
            for i in range(self.count):
                x, y = int(self.x[i]), int(self.y[i])
                if 0 <= x < VIRTUAL_W and 0 <= y < VIRTUAL_H:
                    surface.set_at((x, y), color)
