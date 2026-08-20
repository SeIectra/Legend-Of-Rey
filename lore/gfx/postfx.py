"""Kare sonrasi efektler: vinyet, renk derecelendirme, hasar flasi.

Bunlar oynanisi degistirmez ama oyunun "yapim degeri" algisini en cok
degistiren katmandir. Ucu de tek bir tam ekran blit'i kadar ucuz.

  * **Vinyet** kenarlari karartir, gozu merkeze toplar.
  * **Renk derecelendirme** her Act'e kendi atmosferini verir - sprite'lari
    yeniden uretmeden Emberfall'i yesil, Drowned Vault'u mavi yapar.
  * **Hasar flasi** ekrani bir kare kirmiziya boyar; can azaldiginda kenarlar
    kalici olarak nabiz atar.

Erisilebilirlik: `flash_intensity` ayari 0'a cekilirse tum tam ekran cakmalari
kapanir. Fotosensitivite bir tercih degil, bir gereklilik.
"""
from __future__ import annotations

import math

import numpy as np
import pygame

from lore.constants import VIRTUAL_H, VIRTUAL_W
from lore.core.mathx import clamp
from lore.gfx.palette import act_grade


class PostFX:
    def __init__(self, config) -> None:
        self.config = config
        self.act = 1
        self.grade = act_grade(1)

        self._vignette: pygame.Surface | None = None
        self._vignette_strength = -1.0
        self._tint = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        self._flash = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)

        self.flash_timer = 0.0
        self.flash_color = (255, 60, 60)
        self.flash_peak = 0.0
        self.low_health = False
        self._pulse = 0.0

    # --- Ayarlar ------------------------------------------------------------
    def set_act(self, act: int) -> None:
        self.act = act
        self.grade = act_grade(act)
        self._vignette_strength = -1.0      # Yeniden uretilsin

    @property
    def intensity(self) -> float:
        return float(self.config.get("flash_intensity", 1.0))

    # --- Tetikleyiciler -----------------------------------------------------
    def flash(self, color=(255, 60, 60), strength: float = 0.5,
              duration: float = 0.18) -> None:
        if self.intensity <= 0.0:
            return
        self.flash_color = color
        self.flash_peak = strength * self.intensity
        self.flash_timer = duration
        self._flash_duration = duration

    def update(self, dt: float) -> None:
        self._pulse += dt
        if self.flash_timer > 0.0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

    # --- Cizim --------------------------------------------------------------
    def _build_vignette(self, strength: float) -> pygame.Surface:
        yy, xx = np.mgrid[0:VIRTUAL_H, 0:VIRTUAL_W]
        nx = (xx / VIRTUAL_W - 0.5) * 2.0
        ny = (yy / VIRTUAL_H - 0.5) * 2.0
        # Kare degil elips: 16:9 ekranda kose karartmasi dengeli dagilir.
        dist = np.sqrt(nx * nx * 0.85 + ny * ny)
        alpha = np.clip((dist - 0.55) / 0.75, 0.0, 1.0) ** 1.6 * 255 * strength

        surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        pygame.surfarray.pixels3d(surface)[:] = 0
        pygame.surfarray.pixels_alpha(surface)[:] = np.transpose(
            alpha.astype(np.uint8), (1, 0))
        return surface

    def render(self, surface: pygame.Surface) -> None:
        grade = self.grade

        # 1) Act renk tonu
        strength = grade.get("tint_strength", 0.0)
        if strength > 0.0:
            color = grade["tint"]
            self._tint.fill((*color, int(255 * strength)))
            surface.blit(self._tint, (0, 0))

        # 2) Vinyet
        v_strength = grade.get("vignette", 0.3)
        if self.low_health:
            v_strength += 0.18 + math.sin(self._pulse * 4.0) * 0.08
        if abs(v_strength - self._vignette_strength) > 0.01 or self._vignette is None:
            self._vignette = self._build_vignette(clamp(v_strength, 0.0, 1.0))
            self._vignette_strength = v_strength
        surface.blit(self._vignette, (0, 0))

        # 3) Dusuk can kirmizi nabzi
        if self.low_health and self.intensity > 0.0:
            pulse = (math.sin(self._pulse * 4.0) * 0.5 + 0.5) * 0.16 * self.intensity
            if pulse > 0.01:
                self._flash.fill((190, 30, 40, int(255 * pulse)))
                surface.blit(self._flash, (0, 0))

        # 4) Anlik flas
        if self.flash_timer > 0.0:
            ratio = self.flash_timer / max(1e-4, getattr(self, "_flash_duration", 0.18))
            alpha = int(255 * self.flash_peak * ratio * ratio)
            if alpha > 2:
                self._flash.fill((*self.flash_color, alpha))
                surface.blit(self._flash, (0, 0))


def scanlines(surface: pygame.Surface, strength: int = 22) -> None:
    """Isteğe bagli CRT tarama cizgileri. Nostalji dokunusu."""
    overlay = pygame.Surface((surface.get_width(), 2), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, strength), (0, 0, surface.get_width(), 1))
    for y in range(0, surface.get_height(), 2):
        surface.blit(overlay, (0, y))
