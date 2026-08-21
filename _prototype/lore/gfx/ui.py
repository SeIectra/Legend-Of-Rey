"""Arayuz: HUD, paneller, menu bilesenleri.

Eski koddaki `draw_button` hem cizip hem tiklamayi isliyor, hem de
`pygame.time.delay(150)` ile ana dongusu donduruyordu. Burada cizim ve girdi
ayri: bilesenler durum tutar, sahne onlari surer.

HUD tasarim kurali: **bilgi ancak degistiginde dikkat cekmeli.** Kalpler
sabit durur, can azalinca titrer; Essence sayaci sadece degistiginde parlar.
"""
from __future__ import annotations

import math

import pygame

from lore.constants import VIRTUAL_H, VIRTUAL_W
from lore.core.input import Action
from lore.core.mathx import approach, clamp, ease_out_back, ease_out_cubic
from lore.gfx import text as gfx_text
from lore.gfx.palette import (
    ESSENCE, RAMPS, UI_BORDER, UI_PANEL, UI_TEXT, UI_TEXT_DIM, UI_TEXT_HILITE,
    mix,
)
from lore.gfx.tiles import build_heart


# --- Paneller ---------------------------------------------------------------
def panel(surface: pygame.Surface, rect: pygame.Rect, alpha: int = 215,
          border: bool = True, accent=UI_BORDER) -> None:
    """Yari saydam panel + ince cerceve + kose vurgulari."""
    body = pygame.Surface(rect.size, pygame.SRCALPHA)
    body.fill((*UI_PANEL, alpha))
    surface.blit(body, rect.topleft)
    if not border:
        return
    pygame.draw.rect(surface, accent, rect, 1)
    # Koselerde kucuk L isaretleri: cerceveye karakter katar.
    for cx, cy, dx, dy in (
        (rect.left, rect.top, 1, 1), (rect.right - 1, rect.top, -1, 1),
        (rect.left, rect.bottom - 1, 1, -1), (rect.right - 1, rect.bottom - 1, -1, -1),
    ):
        pygame.draw.line(surface, UI_TEXT_HILITE, (cx, cy), (cx + dx * 3, cy))
        pygame.draw.line(surface, UI_TEXT_HILITE, (cx, cy), (cx, cy + dy * 3))


def bar(surface: pygame.Surface, rect: pygame.Rect, ratio: float,
        color, background=None, ghost: float | None = None) -> None:
    """Deger cubugu. `ghost` verilirse gecikmeli "kaybedilen" kismi gosterir."""
    background = background or RAMPS["ink"][1]
    pygame.draw.rect(surface, background, rect)
    if ghost is not None and ghost > ratio:
        width = int(rect.width * clamp(ghost, 0.0, 1.0))
        pygame.draw.rect(surface, RAMPS["blood"][2],
                         (rect.x, rect.y, width, rect.height))
    width = int(rect.width * clamp(ratio, 0.0, 1.0))
    if width > 0:
        pygame.draw.rect(surface, color, (rect.x, rect.y, width, rect.height))
        # Ust kenarda acik cizgi: cubuga hacim verir.
        pygame.draw.line(surface, mix(color, (255, 255, 255), 0.35),
                         (rect.x, rect.y), (rect.x + width - 1, rect.y))
    pygame.draw.rect(surface, RAMPS["ink"][0], rect, 1)


# --- HUD --------------------------------------------------------------------
class HUD:
    def __init__(self, app) -> None:
        self.app = app
        self.heart_full = app.assets.generated("ui:heart_full",
                                               lambda: build_heart(True))
        self.heart_empty = app.assets.generated("ui:heart_empty",
                                                lambda: build_heart(False))
        self.essence_shown = 0.0
        self.essence_pop = 0.0
        self.health_shake = 0.0
        self.last_health = None
        self.toast = ""
        self.toast_timer = 0.0
        self.prompt = ""
        self.level_title = ""
        self.level_title_timer = 0.0

    def show_toast(self, message: str, duration: float = 2.4) -> None:
        self.toast = message
        self.toast_timer = duration

    def show_level_title(self, name: str, duration: float = 3.0) -> None:
        self.level_title = name
        self.level_title_timer = duration

    def update(self, dt: float, player) -> None:
        self.toast_timer = max(0.0, self.toast_timer - dt)
        self.level_title_timer = max(0.0, self.level_title_timer - dt)
        self.essence_pop = max(0.0, self.essence_pop - dt)
        self.health_shake = max(0.0, self.health_shake - dt)

        if player is None:
            return
        if self.last_health is not None and player.health < self.last_health:
            self.health_shake = 0.35
        self.last_health = player.health

        if abs(self.essence_shown - player.essence) > 0.5:
            self.essence_pop = 0.35
        # Sayac hedefe kayarak gider: artis gorunur, "hissedilir".
        self.essence_shown = approach(self.essence_shown, player.essence,
                                      max(24.0, abs(player.essence
                                                    - self.essence_shown) * 6.0) * dt)

    def draw(self, surface: pygame.Surface, player, scene=None) -> None:
        if player is not None:
            self._draw_hearts(surface, player)
            self._draw_essence(surface, player)
            self._draw_spell(surface, player)
        self._draw_boss(surface, scene)
        self._draw_prompt(surface)
        self._draw_toast(surface)
        self._draw_level_title(surface)

    def _draw_boss(self, surface: pygame.Surface, scene) -> None:
        boss = getattr(scene, "boss", None) if scene is not None else None
        if boss is None or boss.dead or boss.max_health <= 0:
            return
        width = 200
        rect = pygame.Rect(VIRTUAL_W // 2 - width // 2, 12, width, 8)
        panel(surface, pygame.Rect(rect.x - 4, rect.y - 13, width + 8, 25),
              alpha=190)
        gfx_text.draw_text(surface, boss.display_name, rect.centerx, rect.y - 11,
                           color=UI_TEXT_HILITE, align="center", shadow=True)
        ratio = clamp(boss.health / boss.max_health, 0.0, 1.0)
        bar(surface, rect, ratio, RAMPS["blood"][3])

    def _draw_hearts(self, surface: pygame.Surface, player) -> None:
        # Iki birim = bir kalp. Yarim kalp gostermek yerine kalbi soluklastir:
        # 5x11 fontla uyumlu, kucuk olcekte okunur kalir.
        hearts = (player.max_health + 1) // 2
        shake = 0
        if self.health_shake > 0.0:
            shake = int(math.sin(self.health_shake * 60.0) * 2)
        for i in range(hearts):
            filled = player.health - i * 2
            x = 6 + i * 13 + (shake if filled <= 0 else 0)
            image = self.heart_full if filled >= 2 else self.heart_empty
            surface.blit(image, (x, 6))
            if filled == 1:
                # Yarim kalp: sol yarisini dolu ciz.
                half = self.heart_full.subsurface((0, 0, 6, 11))
                surface.blit(half, (x, 6))

    def _draw_essence(self, surface: pygame.Surface, player) -> None:
        y = 20
        pop = ease_out_back(1.0 - self.essence_pop / 0.35) if self.essence_pop else 1.0
        color = UI_TEXT_HILITE if self.essence_pop > 0.0 else ESSENCE
        pygame.draw.circle(surface, ESSENCE, (10, y + 5), 3)
        pygame.draw.circle(surface, (200, 240, 255), (9, y + 4), 1)
        gfx_text.draw_text(surface, f"{int(self.essence_shown)}", 17,
                           y + int((1.0 - pop) * 2), color=color, shadow=True)

    def _draw_spell(self, surface: pygame.Surface, player) -> None:
        if not player.spells:
            return
        rect = pygame.Rect(VIRTUAL_W - 34, 6, 28, 28)
        panel(surface, rect, alpha=180)
        gfx_text.draw_text(surface, (player.active_spell or "")[:3].upper(),
                           rect.centerx, rect.centery - 5, color=UI_TEXT,
                           align="center")

    def _draw_prompt(self, surface: pygame.Surface) -> None:
        if not self.prompt:
            return
        w = gfx_text.text_width(self.prompt) + 16
        rect = pygame.Rect(VIRTUAL_W // 2 - w // 2, VIRTUAL_H - 46, w, 18)
        panel(surface, rect, alpha=200)
        gfx_text.draw_text(surface, self.prompt, rect.centerx, rect.y + 4,
                           color=UI_TEXT_HILITE, align="center")

    def _draw_toast(self, surface: pygame.Surface) -> None:
        if self.toast_timer <= 0.0:
            return
        alpha = int(255 * min(1.0, self.toast_timer * 2.5))
        w = gfx_text.text_width(self.toast) + 20
        rect = pygame.Rect(VIRTUAL_W // 2 - w // 2, VIRTUAL_H - 74, w, 18)
        panel(surface, rect, alpha=min(200, alpha))
        gfx_text.draw_text(surface, self.toast, rect.centerx, rect.y + 4,
                           color=UI_TEXT, align="center", alpha=alpha)

    def _draw_level_title(self, surface: pygame.Surface) -> None:
        if self.level_title_timer <= 0.0:
            return
        t = self.level_title_timer
        alpha = int(255 * min(1.0, t * 1.4))
        slide = int((1.0 - ease_out_cubic(min(1.0, (3.0 - t) * 3.0))) * 20)
        gfx_text.draw_text(surface, self.level_title, VIRTUAL_W // 2,
                           46 - slide, color=UI_TEXT_HILITE, align="center",
                           outline=True, alpha=alpha)


# --- Menu -------------------------------------------------------------------
class MenuItem:
    def __init__(self, label: str, action=None, enabled: bool = True,
                 hint: str = "") -> None:
        self.label = label
        self.action = action
        self.enabled = enabled
        self.hint = hint


class Menu:
    """Klavye/gamepad ile gezilen dikey menu. Fare de calisir."""

    def __init__(self, items: list[MenuItem], x: int, y: int, spacing: int = 18,
                 width: int = 150, centered: bool = True) -> None:
        self.items = items
        self.x = x
        self.y = y
        self.spacing = spacing
        self.width = width
        self.centered = centered
        self.index = 0
        self._anim = 0.0
        self._ensure_selectable(1)

    def _ensure_selectable(self, direction: int) -> None:
        for _ in range(len(self.items)):
            if self.items[self.index].enabled:
                return
            self.index = (self.index + direction) % len(self.items)

    def item_rect(self, i: int) -> pygame.Rect:
        x = self.x - self.width // 2 if self.centered else self.x
        return pygame.Rect(x, self.y + i * self.spacing, self.width, self.spacing - 3)

    def move(self, direction: int, audio=None) -> None:
        start = self.index
        for _ in range(len(self.items)):
            self.index = (self.index + direction) % len(self.items)
            if self.items[self.index].enabled:
                break
        if self.index != start:
            self._anim = 1.0
            if audio:
                audio.play("ui_move")

    def activate(self, audio=None) -> None:
        item = self.items[self.index]
        if not item.enabled:
            if audio:
                audio.play("ui_back")
            return
        if audio:
            audio.play("ui_select")
        if item.action:
            item.action()

    def handle_input(self, inp, audio=None) -> None:
        if inp.pressed(Action.UP):
            self.move(-1, audio)
        elif inp.pressed(Action.DOWN):
            self.move(1, audio)
        if inp.pressed(Action.CONFIRM):
            self.activate(audio)

    def handle_mouse(self, app, audio=None) -> None:
        """Fare konumunu sanal cozunurluge cevirip secimle eslestirir."""
        mx, my = pygame.mouse.get_pos()
        view = app.viewport
        if not view.collidepoint(mx, my) or app.scale <= 0:
            return
        vx = (mx - view.x) / app.scale
        vy = (my - view.y) / app.scale
        for i, item in enumerate(self.items):
            if item.enabled and self.item_rect(i).collidepoint(vx, vy):
                if i != self.index:
                    self.index = i
                    self._anim = 1.0
                    if audio:
                        audio.play("ui_move")
                break

    def click(self, app, audio=None) -> bool:
        mx, my = pygame.mouse.get_pos()
        view = app.viewport
        if not view.collidepoint(mx, my) or app.scale <= 0:
            return False
        vx = (mx - view.x) / app.scale
        vy = (my - view.y) / app.scale
        for i, item in enumerate(self.items):
            if item.enabled and self.item_rect(i).collidepoint(vx, vy):
                self.index = i
                self.activate(audio)
                return True
        return False

    def update(self, dt: float) -> None:
        self._anim = max(0.0, self._anim - dt * 4.0)

    def draw(self, surface: pygame.Surface) -> None:
        for i, item in enumerate(self.items):
            rect = self.item_rect(i)
            selected = i == self.index
            if not item.enabled:
                color = RAMPS["stone"][1]
            elif selected:
                color = UI_TEXT_HILITE
            else:
                color = UI_TEXT_DIM

            offset = 0
            if selected:
                # Secili satir hafifce one cikar ve nefes alir.
                offset = int(3 + math.sin(pygame.time.get_ticks() * 0.005) * 1.5)
                marker_x = rect.centerx - gfx_text.text_width(item.label) // 2 - 10
                gfx_text.draw_text(surface, ">", marker_x + offset, rect.y,
                                   color=UI_TEXT_HILITE, shadow=True)

            gfx_text.draw_text(surface, item.label, rect.centerx + offset, rect.y,
                               color=color, align="center", shadow=True)
            if selected and item.hint:
                gfx_text.draw_text(surface, item.hint, VIRTUAL_W // 2,
                                   VIRTUAL_H - 22, color=UI_TEXT_DIM,
                                   align="center")


class Slider:
    """Yatay deger kaydirici (ses seviyeleri icin)."""

    def __init__(self, label: str, value: float, on_change=None,
                 step: float = 0.05) -> None:
        self.label = label
        self.value = clamp(value, 0.0, 1.0)
        self.on_change = on_change
        self.step = step

    def adjust(self, direction: int, audio=None) -> None:
        new = clamp(self.value + direction * self.step, 0.0, 1.0)
        if abs(new - self.value) > 1e-6:
            self.value = new
            if self.on_change:
                self.on_change(self.value)
            if audio:
                audio.play("ui_move")

    def draw(self, surface: pygame.Surface, rect: pygame.Rect,
             selected: bool) -> None:
        color = UI_TEXT_HILITE if selected else UI_TEXT_DIM
        gfx_text.draw_text(surface, self.label, rect.x, rect.y, color=color,
                           shadow=True)
        track = pygame.Rect(rect.x + 108, rect.y + 3, 92, 6)
        bar(surface, track, self.value, ESSENCE)
        gfx_text.draw_text(surface, f"{int(self.value * 100):3d}%",
                           track.right + 6, rect.y, color=color)
