"""Dusman cizimi - uc kip: sprite, siluet, kutu.

Davranis `enemy.py`'de, cizim burada (CLAUDE.md 11: dosya basina tek
sorumluluk).

**Can bari yok** (CLAUDE.md 7). Durum uc kanaldan birden okunur:
  renk    - tell'de tehlike rengi, sendelemede acilma, az canda koyulasma
  siluet  - tell'de kabarma (renk gormeyen oyuncu icin sart)
  hareket - sendeleyen durur, yaralanan yavaslar

Tek kanala guvenmek erisilebilirligi bitirir: renk korlugu olan oyuncu
tell'i kacirir ve olum haksiz hissettirir.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.entities.enemy import EnemyState

# Tell parlamasi nabiz atar - sabit renk "acik/kapali" gibi okunur,
# nabiz "yaklasiyor" gibi okunur.
TELL_PULSE_PERIOD = 6


def draw_enemy(enemy, surface: pygame.Surface,
               offset: tuple[int, int]) -> None:
    ox, oy = offset
    rect = enemy.body.rect.move(-ox, -oy)

    if enemy.scene.game.box_mode:
        _draw_box(enemy, surface, rect)
        _draw_tell_marker(enemy, surface, rect)
        return

    animator = getattr(enemy, "animator", None)
    if animator is None:
        _draw_box(enemy, surface, rect)
        return

    squash = _combined_squash(enemy)
    colour, strength = _tint(enemy)
    image = animator.render(
        enemy.facing,
        flash=enemy.flash.active,
        squash=squash,
        silhouette_mode=enemy.scene.game.silhouette_mode,
        tint_colour=colour,
        tint_strength=strength,
    )
    if image is None:
        _draw_box(enemy, surface, rect)
        return

    foot = enemy.sprite_foot_y * squash[1]
    surface.blit(image, (
        int(enemy.body.center_x - image.get_width() * 0.5) - ox,
        int(enemy.body.bottom - foot) - oy))

    _draw_tell_marker(enemy, surface, rect)


def _combined_squash(enemy) -> tuple[float, float]:
    """Vurus squash'i ile tell kabarmasini birlestirir.

    Ikisi carpilir, birbirinin yerine gecmez: tell sirasinda vurus yiyen
    dusman hem kabarmis hem ezilmis gorunur, ikisi de dogru bilgi.
    """
    hit_x, hit_y = enemy.squash.current
    tell_x, tell_y = enemy.silhouette_scale()
    return (hit_x * tell_x, hit_y * tell_y)


# Renk ne kadar bassin? Tam 1.0 sprite'i tek renge duzlestirir - kisa
# suren bir olay icin dogru, kalici bir durum icin degil.
TELL_TINT_STRENGTH = 0.85       # Tell kisa surer, guclu bassin
STAGGER_TINT_STRENGTH = 0.55    # Sendeleme birkac kare
LOW_HEALTH_TINT_STRENGTH = 0.55 # Olene kadar surer - siluet kaybolmasin.
                                # 0.30 denendi: saglam dusmandan ayirt
                                # edilemiyordu, yani hicbir bilgi vermiyordu.


def _tint(enemy) -> tuple[palette.RGB | None, float]:
    """(renk, siddet). Renk None ise sprite oldugu gibi cizilir."""
    if enemy.flash.active:
        return None, 1.0                 # Vurus flasi her seyi ezer
    if enemy.state is EnemyState.TELL:
        # Nabiz: tell ilerledikce hizlanmiyor ama parlaklik artiyor.
        phase = (enemy.state_frames // (TELL_PULSE_PERIOD // 2)) % 2
        if phase == 0 or enemy.tell_progress > 0.65:
            return enemy.tell_colour(), TELL_TINT_STRENGTH
        return None, 1.0
    if enemy.state is EnemyState.STAGGER:
        return palette.color("stone_light"), STAGGER_TINT_STRENGTH
    if enemy.health_ratio < 0.35:
        return palette.color("ink_soft"), LOW_HEALTH_TINT_STRENGTH
    return None, 1.0


def _draw_tell_marker(enemy, surface: pygame.Surface,
                      rect: pygame.Rect) -> None:
    """Basin ustunde buyuyen tehlike cizgisi.

    Siluet degisimi + renk zaten var; bu ucuncu kanal kalabalikta ise
    yariyor - alti dusmanin arasinda hangisinin saldirdigi bir bakista
    goruluyor.
    """
    if enemy.state is not EnemyState.TELL:
        return
    width = max(2, int(12 * enemy.tell_progress))
    x = rect.centerx - width // 2
    y = rect.top - 5
    surface.fill(enemy.tell_colour(), (x, y, width, 2))


def _draw_box(enemy, surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Kutu kipi: sanat yok, dovusun kendisi okunuyor mu diye bak."""
    scale_x, scale_y = _combined_squash(enemy)
    if scale_x != 1.0 or scale_y != 1.0:
        width = max(2, int(rect.width * scale_x))
        height = max(2, int(rect.height * scale_y))
        rect = pygame.Rect(rect.centerx - width // 2,
                           rect.bottom - height, width, height)
    surface.fill(_box_colour(enemy), rect)
    pygame.draw.rect(surface, palette.outline(), rect, 1)

    # Bakis yonu - kutuda yon okunabilmeli.
    marker_x = rect.right - 3 if enemy.facing > 0 else rect.left
    surface.fill(palette.color("ink"), (marker_x, rect.top + 2, 3, 3))


def _box_colour(enemy) -> palette.RGB:
    if enemy.flash.active:
        return palette.role("hit_flash")
    if enemy.state is EnemyState.TELL:
        return enemy.tell_colour()
    if enemy.state is EnemyState.STAGGER:
        return palette.color("stone_light")
    if enemy.state is EnemyState.ATTACK:
        return palette.color("danger_bright")
    # Can azaldikca koyulasir - bar olmadan da durum okunsun.
    base = palette.color(enemy.body_colour)
    if enemy.health_ratio < 0.35:
        return palette.color("ink_soft")
    return base
