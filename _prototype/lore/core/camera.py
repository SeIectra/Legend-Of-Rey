"""Kamera: takip, olu bolge, ileri bakis, travma tabanli sarsinti.

Eski oyunda kamera yoktu; dunya 800x600'e hapsolmustu. Kamera geldigi anda
seviyeler istedigin kadar buyuyebilir.

Sarsinti icin "travma" modeli kullaniyoruz (Squirrel Eiserloh'un yaklasimi):
carpismalar travmayi artirir, travma her saniye sabit oranda soner ve gercek
kayma travma^2 ile hesaplanir. Boylece kucuk vuruslar hafif, buyuk vuruslar
belirgin hissedilir ve sarsintilar birikince kamera cildirmaz.
"""
from __future__ import annotations

import random

import pygame

from lore.constants import VIRTUAL_H, VIRTUAL_W
from lore.core.mathx import clamp, damp


class Camera:
    def __init__(self, width: int = VIRTUAL_W, height: int = VIRTUAL_H) -> None:
        self.w = width
        self.h = height

        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0

        # Olu bolge: hedef bu dikdortgenin icinde kaldigi surece kamera durur.
        # Kucuk ziplama ve yurumelerde kameranin surekli oynamasini onler.
        self.deadzone_w = 36.0
        self.deadzone_h = 28.0

        # Ileri bakis: oyuncu kostugu yone dogru kamerayi kaydirir, boylece
        # onunu daha genis gorur.
        self.lookahead = 46.0
        self.lookahead_smoothing = 0.0008
        self._look_offset = 0.0

        self.smoothing = 0.0001          # 1 saniyede kalan mesafe orani
        self.vertical_smoothing = 0.002  # Dikeyde daha yumusak (ziplama titremesin)

        # Sinirlar (seviye yuklenince set edilir)
        self.bounds: pygame.Rect | None = None

        # Sarsinti
        self.trauma = 0.0
        self.trauma_decay = 1.6
        self.max_shake = 12.0
        self.max_shake_angle = 0.0
        self.shake_scale = 1.0           # Ayarlardan gelen erisilebilirlik carpani
        self._shake_x = 0.0
        self._shake_y = 0.0
        self._noise_seed = random.random() * 1000.0

        # Anlik odak degisimi (boss girisi, sirlar) icin gecici hedef
        self._focus: tuple[float, float] | None = None
        self._focus_timer = 0.0

    # --- Kurulum ------------------------------------------------------------
    def set_bounds(self, rect: pygame.Rect | None) -> None:
        self.bounds = rect

    def snap_to(self, x: float, y: float) -> None:
        """Yumusatma olmadan aninda konumlan. Seviye baslangicinda kullanilir."""
        self.target_x, self.target_y = x, y
        self.x = x - self.w * 0.5
        self.y = y - self.h * 0.5
        self._look_offset = 0.0
        self._clamp_to_bounds()

    def focus_on(self, x: float, y: float, duration: float) -> None:
        self._focus = (x, y)
        self._focus_timer = duration

    # --- Sarsinti -----------------------------------------------------------
    def add_trauma(self, amount: float) -> None:
        self.trauma = clamp(self.trauma + amount, 0.0, 1.0)

    def shake(self, amount: float) -> None:
        self.add_trauma(amount)

    # --- Guncelleme ---------------------------------------------------------
    def update(self, dt: float, focus_x: float, focus_y: float,
               facing: int = 0, grounded: bool = True) -> None:
        if self._focus_timer > 0.0:
            self._focus_timer -= dt
            if self._focus:
                focus_x, focus_y = self._focus
                facing = 0
            if self._focus_timer <= 0.0:
                self._focus = None

        # Ileri bakis, yon degistirince aniden ziplamasin diye yumusatilir.
        want_look = self.lookahead * facing
        self._look_offset = damp(self._look_offset, want_look,
                                 self.lookahead_smoothing, dt)
        focus_x += self._look_offset

        # Olu bolge: hedef sadece dikdortgeni astigi kadar kamerayi ceker.
        cx = self.x + self.w * 0.5
        cy = self.y + self.h * 0.5
        dx = focus_x - cx
        dy = focus_y - cy
        half_w, half_h = self.deadzone_w * 0.5, self.deadzone_h * 0.5

        if dx > half_w:
            self.target_x = focus_x - half_w
        elif dx < -half_w:
            self.target_x = focus_x + half_w
        else:
            self.target_x = cx

        # Havadayken dikey olu bolge genisler: her ziplamada kamera zipramaz.
        v_half = half_h * (2.2 if not grounded else 1.0)
        if dy > v_half:
            self.target_y = focus_y - v_half
        elif dy < -v_half:
            self.target_y = focus_y + v_half
        else:
            self.target_y = cy

        self.x = damp(self.x, self.target_x - self.w * 0.5, self.smoothing, dt)
        self.y = damp(self.y, self.target_y - self.h * 0.5,
                      self.vertical_smoothing, dt)
        self._clamp_to_bounds()
        self._update_shake(dt)

    def _clamp_to_bounds(self) -> None:
        if self.bounds is None:
            return
        b = self.bounds
        # Seviye ekrandan darsa ortala; degilse kenarlara yapistir.
        if b.width <= self.w:
            self.x = b.centerx - self.w * 0.5
        else:
            self.x = clamp(self.x, b.left, b.right - self.w)
        if b.height <= self.h:
            self.y = b.centery - self.h * 0.5
        else:
            self.y = clamp(self.y, b.top, b.bottom - self.h)

    def _update_shake(self, dt: float) -> None:
        if self.trauma <= 0.0:
            self._shake_x = self._shake_y = 0.0
            return
        self.trauma = max(0.0, self.trauma - self.trauma_decay * dt)
        # Karesi alinmis travma: kucuk carpismalar zar zor, buyukleri sert.
        power = self.trauma * self.trauma * self.shake_scale
        self._shake_x = random.uniform(-1.0, 1.0) * self.max_shake * power
        self._shake_y = random.uniform(-1.0, 1.0) * self.max_shake * power

    # --- Donusumler ---------------------------------------------------------
    @property
    def offset(self) -> tuple[int, int]:
        """Dunya -> ekran cevrimi icin tam sayi kaydirma.

        Tam sayiya yuvarlamak sart: aksi halde pixel art alt-piksel konumlarda
        titrer ve kenarlarda hayalet cizgiler olusur.
        """
        return (int(self.x + self._shake_x), int(self.y + self._shake_y))

    def world_to_screen(self, x: float, y: float) -> tuple[int, int]:
        ox, oy = self.offset
        return int(x) - ox, int(y) - oy

    def screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        ox, oy = self.offset
        return x + ox, y + oy

    @property
    def view_rect(self) -> pygame.Rect:
        """Gorunur dunya dikdortgeni. Ekran disini cizmemek icin kullanilir."""
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def is_visible(self, rect: pygame.Rect, margin: int = 32) -> bool:
        return self.view_rect.inflate(margin * 2, margin * 2).colliderect(rect)
