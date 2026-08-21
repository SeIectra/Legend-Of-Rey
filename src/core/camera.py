"""Kamera: takip, olu bolge, ileri bakis, sarsinti birlesimi.

Yumusatma katsayisi 0.12, ileri bakis 12 piksel (docs/dovus-sistemi.md 5).

**Ofset daima tam sayiya yuvarlanir.** Ondalik ofset piksel art dokusunu
titretir - en yaygin ve en fark edilir hata budur (docs/menu-ui.md 0.6).

Sarsinti burada uretilmez; `juice.ScreenShake` uretir, kamera yalnizca son
ofsete ekler. Boylece "vurus geri bildirimi tek yerden" kurali korunur.
"""
from __future__ import annotations

import pygame

from src.config import (
    CAMERA_DEADZONE_HEIGHT, CAMERA_DEADZONE_WIDTH, CAMERA_LOOKAHEAD_PIXELS,
    CAMERA_SMOOTHING, INTERNAL_HEIGHT, INTERNAL_WIDTH,
)

# Havadayken dikey olu bolge bu kadar genisler - her ziplamada kamera ziplamaz.
AIRBORNE_DEADZONE_SCALE = 2.2
LOOKAHEAD_SMOOTHING = 0.06


class Camera:
    def __init__(self, width: int = INTERNAL_WIDTH,
                 height: int = INTERNAL_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.x = 0.0
        self.y = 0.0

        self.bounds: pygame.Rect | None = None
        self.shake_offset = (0, 0)
        self._lookahead = 0.0

    def set_bounds(self, rect: pygame.Rect | None) -> None:
        self.bounds = rect

    def snap_to(self, x: float, y: float) -> None:
        """Yumusatma olmadan aninda konumlan. Bolum baslangicinda kullanilir."""
        self.x = x - self.width * 0.5
        self.y = y - self.height * 0.5
        self._lookahead = 0.0
        self._clamp()

    def update(self, focus_x: float, focus_y: float, facing: int = 0,
               grounded: bool = True) -> None:
        # Ileri bakis yon degisince aniden ziplamasin diye yumusatilir.
        target_look = CAMERA_LOOKAHEAD_PIXELS * facing
        self._lookahead += (target_look - self._lookahead) * LOOKAHEAD_SMOOTHING
        focus_x += self._lookahead

        center_x = self.x + self.width * 0.5
        center_y = self.y + self.height * 0.5
        half_w = CAMERA_DEADZONE_WIDTH * 0.5
        half_h = CAMERA_DEADZONE_HEIGHT * 0.5
        if not grounded:
            half_h *= AIRBORNE_DEADZONE_SCALE

        target_x = center_x
        if focus_x - center_x > half_w:
            target_x = focus_x - half_w
        elif center_x - focus_x > half_w:
            target_x = focus_x + half_w

        target_y = center_y
        if focus_y - center_y > half_h:
            target_y = focus_y - half_h
        elif center_y - focus_y > half_h:
            target_y = focus_y + half_h

        self.x += (target_x - self.width * 0.5 - self.x) * CAMERA_SMOOTHING
        self.y += (target_y - self.height * 0.5 - self.y) * CAMERA_SMOOTHING
        self._clamp()

    def _clamp(self) -> None:
        if self.bounds is None:
            return
        area = self.bounds
        if area.width <= self.width:
            self.x = area.centerx - self.width * 0.5
        else:
            self.x = max(area.left, min(self.x, area.right - self.width))
        if area.height <= self.height:
            self.y = area.centery - self.height * 0.5
        else:
            self.y = max(area.top, min(self.y, area.bottom - self.height))

    @property
    def offset(self) -> tuple[int, int]:
        """Dunya -> ekran kaydirmasi. Tam sayi: piksel art titremesin."""
        return (round(self.x) + self.shake_offset[0],
                round(self.y) + self.shake_offset[1])

    @property
    def view_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def is_visible(self, rect: pygame.Rect, margin: int = 32) -> bool:
        return self.view_rect.inflate(margin * 2, margin * 2).colliderect(rect)
