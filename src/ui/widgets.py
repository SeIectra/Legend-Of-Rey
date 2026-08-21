"""Menu bilesenleri: panel, buton listesi, sekme, deger secici.

**Uc girdi yontemi ayni anda calisir** (docs/menu-ui.md 8.4): klavye, gamepad
ve fare. Mod degistirme gerekmez. Fare hareket edince imlec gorunur, klavye
kullanilinca kaybolur - kucuk ama profesyonel detay.

Gorsel dil (docs/menu-ui.md 3):
  * Secili olmayan : soluk gri metin, ikon yok
  * Secili         : beyaz metin + solda isaret + mor parilti
  * Secim degisimi : 4 karelik yumusak gecis
  * Onay           : 6 karelik flas

**Hicbir menu gecisi 12 kareyi asmaz.** Menu hizli hissetmeli; Hades'te
menuler simsek hizindadir ve oyuncu arayuze degil aksiyona odaklanir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import pygame

from src.art import palette
from src.config import MENU_TRANSITION_MAX_FRAMES
from src.core.input import Action
from src.ui import text
from src.ui.font_data import GLYPH_HEIGHT

SELECT_ANIM_FRAMES = 4
CONFIRM_FLASH_FRAMES = 6

# Hicbir menu gecisi 12 kareyi asmaz (CLAUDE.md 9). Bir gun biri bu sayilari
# "daha yumusak olsun" diye buyutmeye kalkarsa burada durur.
assert SELECT_ANIM_FRAMES <= MENU_TRANSITION_MAX_FRAMES
assert CONFIRM_FLASH_FRAMES <= MENU_TRANSITION_MAX_FRAMES
MARKER = "▸"
MARKER_GAP = 8
ROW_HEIGHT = 18


def panel(surface: pygame.Surface, rect: pygame.Rect, alpha: int = 215,
          border: bool = True) -> None:
    """Yari saydam panel + ince cerceve + kose vurgulari."""
    body = pygame.Surface(rect.size, pygame.SRCALPHA)
    body.fill((*palette.role("ui_panel"), alpha))
    surface.blit(body, rect.topleft)
    if not border:
        return
    pygame.draw.rect(surface, palette.role("ui_border"), rect, 1)
    for cx, cy, dx, dy in (
        (rect.left, rect.top, 1, 1), (rect.right - 1, rect.top, -1, 1),
        (rect.left, rect.bottom - 1, 1, -1),
        (rect.right - 1, rect.bottom - 1, -1, -1),
    ):
        pygame.draw.line(surface, palette.role("ui_text_bright"),
                         (cx, cy), (cx + dx * 3, cy))
        pygame.draw.line(surface, palette.role("ui_text_bright"),
                         (cx, cy), (cx, cy + dy * 3))


def value_bar(surface: pygame.Surface, rect: pygame.Rect, ratio: float,
              colour: palette.RGB | None = None) -> None:
    colour = colour or palette.color("echo")
    surface.fill(palette.color("ink"), rect)
    filled = int(rect.width * max(0.0, min(1.0, ratio)))
    if filled > 0:
        surface.fill(colour, (rect.x, rect.y, filled, rect.height))
    pygame.draw.rect(surface, palette.outline(), rect, 1)


def blur(surface: pygame.Surface, factor: int = 4) -> pygame.Surface:
    """Ucuz bulaniklik: kucult, buyut. Gaussian gerekmez.

    Duraklatma menusunun arka plani icin. Bu, oyun ici piksel art'a degil
    yalnizca arka plan katmanina uygulanir.
    """
    width, height = surface.get_size()
    small = pygame.transform.smoothscale(
        surface, (max(1, width // factor), max(1, height // factor)))
    return pygame.transform.smoothscale(small, (width, height))


@dataclass
class MenuItem:
    label: str
    action: Callable[[], None] | None = None
    enabled: bool = True
    visible: bool = True            # Gorunmez oge gezinmede atlanir
    hint: str = ""
    gap_before: bool = False        # CIKIS bir boslukla ayrilir
    danger: bool = False            # Yikici eylem - farkli renk


class Menu:
    """Dikey buton listesi. Klavye, gamepad ve fare ayni anda calisir."""

    def __init__(self, items: list[MenuItem], x: int, y: int,
                 width: int = 150, centered: bool = False,
                 on_sound: Callable[[str], None] | None = None) -> None:
        self.items = items
        self.x = x
        self.y = y
        self.width = width
        self.centered = centered
        # Ses sistemi Gorev 10'da gelecek; dikis simdiden hazir.
        self.on_sound = on_sound

        self.index = 0
        self.select_anim = 0
        self.confirm_flash = 0
        self.mouse_visible = False
        self._ensure_selectable(1)

    # --- Gezinme ------------------------------------------------------------
    def _selectable(self, index: int) -> bool:
        item = self.items[index]
        return item.visible and item.enabled

    def _ensure_selectable(self, direction: int) -> None:
        for _ in range(len(self.items)):
            if self._selectable(self.index):
                return
            self.index = (self.index + direction) % len(self.items)

    def move(self, direction: int) -> None:
        start = self.index
        for _ in range(len(self.items)):
            self.index = (self.index + direction) % len(self.items)
            if self._selectable(self.index):
                break
        if self.index != start:
            self.select_anim = SELECT_ANIM_FRAMES
            self._play("tick")

    def activate(self) -> None:
        item = self.items[self.index]
        if not (item.visible and item.enabled):
            self._play("deny")
            return
        self.confirm_flash = CONFIRM_FLASH_FRAMES
        self._play("confirm")
        if item.action:
            item.action()

    def _play(self, name: str) -> None:
        if self.on_sound:
            self.on_sound(name)

    # --- Kare dongusu -------------------------------------------------------
    def update(self, game) -> None:
        self.select_anim = max(0, self.select_anim - 1)
        self.confirm_flash = max(0, self.confirm_flash - 1)

        inp = game.input
        if inp.pressed(Action.UP):
            self.move(-1)
        elif inp.pressed(Action.DOWN):
            self.move(1)
        if inp.pressed(Action.CONFIRM):
            self.activate()

        # Fare hareket edince imlec gorunur, klavye kullanilinca kaybolur.
        if inp.mouse_moved:
            self.mouse_visible = True
        elif inp.last_device == "keyboard":
            self.mouse_visible = False

        if self.mouse_visible:
            self._hover(game)

    def _virtual_mouse(self, game) -> tuple[float, float] | None:
        """Fare konumunu sanal cozunurluge cevirir."""
        mx, my = pygame.mouse.get_pos()
        view = game.viewport
        if not view.collidepoint(mx, my) or game.scale <= 0:
            return None
        return ((mx - view.x) / game.scale, (my - view.y) / game.scale)

    def _hover(self, game) -> None:
        position = self._virtual_mouse(game)
        if position is None:
            return
        for index in range(len(self.items)):
            if not self._selectable(index):
                continue
            if self.item_rect(index).collidepoint(position):
                if index != self.index:
                    self.index = index
                    self.select_anim = SELECT_ANIM_FRAMES
                    self._play("tick")
                return

    def click(self, game) -> bool:
        """Fare tiklamasi - True donerse bir oge etkinlestirildi."""
        position = self._virtual_mouse(game)
        if position is None:
            return False
        for index in range(len(self.items)):
            if not self._selectable(index):
                continue
            if self.item_rect(index).collidepoint(position):
                self.index = index
                self.activate()
                return True
        return False

    # --- Yerlesim -----------------------------------------------------------
    def item_rect(self, index: int) -> pygame.Rect:
        y = self.y
        for i in range(index):
            if not self.items[i].visible:
                continue
            y += ROW_HEIGHT + (6 if self.items[i].gap_before else 0)
        if self.items[index].gap_before:
            y += 6
        x = self.x - self.width // 2 if self.centered else self.x
        return pygame.Rect(x, y, self.width, ROW_HEIGHT - 3)

    @property
    def selected(self) -> MenuItem:
        return self.items[self.index]

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        for index, item in enumerate(self.items):
            if not item.visible:
                continue          # Gri degil, YOK (docs/menu-ui.md 3)
            self._draw_item(surface, index, item)

    def _draw_item(self, surface: pygame.Surface, index: int,
                   item: MenuItem) -> None:
        rect = self.item_rect(index)
        selected = index == self.index

        if not item.enabled:
            colour = palette.color("stone_dark")
        elif item.danger and selected:
            colour = palette.color("danger_bright")
        elif selected:
            colour = palette.role("ui_text")
        else:
            colour = palette.role("ui_text_dim")

        offset = 0
        if selected:
            # Secim degisiminde 4 karelik yumusak kayma.
            slide = self.select_anim / max(1, SELECT_ANIM_FRAMES)
            offset = int(3 - slide * 3)
            self._draw_glow(surface, rect)
            text.draw(surface, MARKER, rect.x - MARKER_GAP + offset, rect.y,
                      color=palette.color("violet_bright"))

        if self.confirm_flash > 0 and selected:
            colour = palette.role("hit_flash")

        text.draw(surface, item.label, rect.x + offset, rect.y, color=colour,
                  shadow=True)

    def _draw_glow(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Mor alevden geliyormus gibi hafif parilti."""
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.004)
        alpha = int(26 + pulse * 22)
        glow = pygame.Surface((rect.width + 12, rect.height + 4),
                              pygame.SRCALPHA)
        glow.fill((*palette.color("violet"), alpha))
        surface.blit(glow, (rect.x - 6, rect.y - 2))

    def draw_hint(self, surface: pygame.Surface, x: int, y: int) -> None:
        item = self.selected
        if item.hint:
            text.draw(surface, item.hint, x, y,
                      color=palette.role("ui_text_dim"), align="center")

    def draw_cursor(self, surface: pygame.Surface, game) -> None:
        """Fare imleci - yalnizca fare kullanilirken."""
        if not self.mouse_visible:
            return
        position = self._virtual_mouse(game)
        if position is None:
            return
        x, y = int(position[0]), int(position[1])
        colour = palette.role("ui_text")
        pygame.draw.line(surface, colour, (x, y), (x, y + 5))
        pygame.draw.line(surface, colour, (x, y), (x + 4, y + 4))
        surface.set_at((x, y), palette.role("ui_text_bright"))


class TabBar:
    """Ayarlar ekraninin sekmeleri."""

    def __init__(self, labels: list[str], x: int, y: int, width: int) -> None:
        self.labels = labels
        self.x = x
        self.y = y
        self.width = width
        self.index = 0

    def move(self, direction: int) -> None:
        self.index = (self.index + direction) % len(self.labels)

    def tab_rect(self, index: int) -> pygame.Rect:
        span = self.width // len(self.labels)
        return pygame.Rect(self.x + index * span, self.y, span, GLYPH_HEIGHT + 6)

    def draw(self, surface: pygame.Surface) -> None:
        for index, label in enumerate(self.labels):
            rect = self.tab_rect(index)
            active = index == self.index
            if active:
                surface.fill(palette.color("ink_soft"), rect)
                pygame.draw.line(surface, palette.color("violet_bright"),
                                 (rect.left + 2, rect.bottom - 1),
                                 (rect.right - 3, rect.bottom - 1))
            text.draw(surface, label, rect.centerx, rect.y + 3,
                      color=(palette.role("ui_text") if active
                             else palette.role("ui_text_dim")),
                      align="center")
