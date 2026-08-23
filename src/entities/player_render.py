"""Oyuncunun cizimi - uc kip: sprite, siluet, kutu.

Davranis `player.py`'de, cizim burada. Ayirmanin iki sebebi var: dosya basina
tek sorumluluk (CLAUDE.md 11) ve kutu kipinin oynanis kodunu kirletmemesi.

**Kutu kipi (F4)** gecici bir sey degil, kalici bir arac: "kutularla eglenceli
mi?" sorusunu sprite'lari atmadan sormanin yolu (DEVIR gorev 1 ve 5).
Bir gun dovus hissi bozuldugunda ilk bakilacak yer orasi.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.combat.combo import AttackPhase
from src.combat.hitbox import melee_rect

IFRAME_BLINK_ALPHA = 140
IFRAME_BLINK_PERIOD = 3


def draw_player(player, surface: pygame.Surface,
                offset: tuple[int, int]) -> None:
    """Oyuncuyu gecerli cizim kipinde cizer."""
    if player.scene.game.box_mode:
        _draw_box(player, surface, offset)
        _draw_attack_arc(player, surface, offset)
        return

    image = player.animator.render(
        player.facing,
        flash=player.flash.active,
        squash=player.squash.current,
        silhouette_mode=player.scene.game.silhouette_mode,
        alpha=_alpha(player),
    )
    if image is None:
        _draw_box(player, surface, offset)
        return

    ox, oy = offset
    # Sprite hucresi govdeden buyuk: yatayda merkezle, dikeyde sprite'in
    # **taban cizgisini** govdenin altina hizala. Hucrenin altini hizalamak
    # karakteri havada birakir. Squash yuksekligi degistirdigi icin taban
    # cizgisi de olceklenir.
    foot = player.sprite_foot_y * player.squash.current[1]
    x = int(player.body.center_x - image.get_width() * 0.5) - ox
    y = int(player.body.bottom - foot) - oy
    surface.blit(image, (x, y))

    if player.dodge.counter_ready:
        _draw_counter_hint(player, surface, offset)


def _alpha(player) -> int:
    """Dokunulmazlik boyunca yanip sonme - durumu gizlemeden bildirir."""
    if player.iframes > 0 and (player.iframes // IFRAME_BLINK_PERIOD) % 2 == 0:
        return IFRAME_BLINK_ALPHA
    return 255


def _draw_counter_hint(player, surface: pygame.Surface,
                       offset: tuple[int, int]) -> None:
    """Karsi vurus penceresi acik - oyuncu firsatini gormeli."""
    ox, oy = offset
    rect = player.body.rect.move(-ox, -oy)
    surface.fill(palette.color("violet_bright"),
                 (rect.centerx - 3, rect.top - 5, 6, 2))


def _squashed_rect(player, offset: tuple[int, int]) -> pygame.Rect:
    ox, oy = offset
    rect = player.body.rect.move(-ox, -oy)
    scale_x, scale_y = player.squash.current
    if scale_x == 1.0 and scale_y == 1.0:
        return rect
    width = max(2, int(rect.width * scale_x))
    height = max(2, int(rect.height * scale_y))
    return pygame.Rect(rect.centerx - width // 2, rect.bottom - height,
                       width, height)


def _draw_box(player, surface: pygame.Surface,
              offset: tuple[int, int]) -> None:
    """Kutu kipi: sanat yok, dovusun kendisi eglenceli mi diye bak."""
    rect = _squashed_rect(player, offset)
    surface.fill(_body_colour(player), rect)
    pygame.draw.rect(surface, palette.outline(), rect, 1)
    _draw_facing_marker(player, surface, rect)


def _body_colour(player) -> palette.RGB:
    """Kutu rengi durumu anlatir - sprite olmadan da okunabilsin."""
    if player.flash.active:
        return palette.role("hit_flash")
    if player.dodge.invulnerable:
        return palette.color("echo_bright")
    if player.iframes > 0 and (player.iframes // IFRAME_BLINK_PERIOD) % 2 == 0:
        return palette.color("stone_light")
    if player.chain.phase is AttackPhase.WINDUP:
        return palette.color("gold")
    if player.dodge.counter_ready:
        return palette.color("violet_bright")
    return palette.color(player.stats.body_color)


def _draw_facing_marker(player, surface: pygame.Surface,
                        rect: pygame.Rect) -> None:
    """Bakis yonu isareti - kutuda yon okunabilmeli."""
    marker_x = rect.right - 3 if player.facing > 0 else rect.left
    surface.fill(palette.color(player.stats.accent_color),
                 (marker_x, rect.top + 3, 3, 3))


def _draw_attack_arc(player, surface: pygame.Surface,
                     offset: tuple[int, int]) -> None:
    """Aktif karelerde vurus yayi - hitbox'in nerede oldugu gorunsun.

    Yalnizca kutu kipinde: sprite kipinde kilicin kendisi bu isi yapiyor.
    """
    if player.chain.phase is not AttackPhase.ACTIVE:
        return
    from src.entities.player import (
        ATTACK_HEIGHT, ATTACK_REACH, FINISHER_HEIGHT, FINISHER_REACH,
    )
    ox, oy = offset
    finisher = player.chain.is_finisher
    reach = FINISHER_REACH if finisher else ATTACK_REACH
    height = FINISHER_HEIGHT if finisher else ATTACK_HEIGHT
    arc = melee_rect(player.body, player.facing, reach, height).move(-ox, -oy)
    colour = (palette.color("violet_bright") if player.last_hit_was_counter
              else palette.color("bone"))
    surface.fill(colour, arc)
    pygame.draw.rect(surface, palette.outline(), arc, 1)
