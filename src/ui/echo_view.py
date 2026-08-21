"""Yanki'nin gorsel dili - yardim ve bedel ayni anda.

Gorevin bitis olcutu: *"Yanki'yi actigimda hem yardim aldigimi hem bir sey
kaybettigimi AYNI ANDA hissetmeliyim."* O yuzden acildigi anda ekranda iki
sey birden oluyor:

    **kazanc**  duvar ardindaki dusmanlar beliriyor, gizli gecitler parliyor
    **bedel**   ekran kenari kararıyor, renkler kayiyor, savunma dusuyor

Ikisi ayni egriden besleniyor (`EchoState.strength`), yani biri olmadan
digeri gorunemiyor. Ayri degiskenlere baglansaydi bir gun biri "vinyeti
biraz azaltalim" der ve mekanigin kalbi sessizce olurdu.

## Kademe HUD cubugu degil

Kademe **vinyetin yogunluguyla** okunuyor (CLAUDE.md 9: diegetik tercih
et). BERRAK'ta kenar hafif kararir ve uzagi gorursun; BULANIK'ta daha cok
kararir ama az gorursun - kotu takas gozle hissedilir. Sol ustte kucuk bir
gosterge yalnizca kademe **degistiginde** beliriyor (asamali aciga
cikarma).
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import (
    ECHO_TIER_CLEAR, ECHO_TIER_MURKY, ECHO_TIER_SILENT, INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
)
from src.systems.echo import Answer

# Kademeye gore vinyet rengi. BULANIK daha bogucu - takas gozle okunsun.
TIER_TINT = {
    ECHO_TIER_CLEAR: "violet_dark",
    ECHO_TIER_MURKY: "abyss_dark",
    ECHO_TIER_SILENT: "void",
}

# Kromatik kayma: kanallar birer piksel ayrilir. Bir piksel yeter -
# fazlasi "bozuk ekran" gibi okunur, "baska bir sey duyuyorum" gibi degil.
CHROMA_SHIFT = 1

_vignette_cache: dict[tuple, pygame.Surface] = {}


def draw_reveal(surface: pygame.Surface, offset: tuple[int, int],
                echo, player, enemies, walls=()) -> None:
    """Kazanc tarafi: duvar ardindaki dusmanlar ve gizli gecitler.

    Menzil disindakiler **hic** cizilmez - Yanki her seyi gostermiyor,
    yakini gosteriyor. BULANIK'ta menzil 96 piksel: bir odanin yarisi.
    """
    if not echo.active or echo.sight_range <= 0.0:
        return
    ox, oy = offset
    px, py = player.body.center_x, player.body.center_y
    reach = echo.sight_range

    for enemy in enemies:
        distance = math.hypot(enemy.body.center_x - px,
                              enemy.body.center_y - py)
        if distance > reach:
            continue
        # Uzaktakiler daha silik: menzilin kenarinda kayboluyor.
        fade = 1.0 - (distance / reach) ** 2
        _draw_silhouette(surface, enemy, ox, oy, fade, echo)

    for wall in walls:
        if math.hypot(wall.rect.centerx - px, wall.rect.centery - py) > reach:
            continue
        _draw_crack(surface, wall, ox, oy, echo)


def _draw_silhouette(surface, enemy, ox: int, oy: int, fade: float,
                     echo) -> None:
    """Dusmanin siluetı - duvar ardindan gorunur."""
    rect = enemy.body.rect.move(-ox, -oy)
    colour = palette.color("echo_bright" if echo.tier == ECHO_TIER_CLEAR
                           else "echo")
    ghost = pygame.Surface(rect.size, pygame.SRCALPHA)
    ghost.fill((*colour, int(150 * fade * echo.strength)))
    surface.blit(ghost, rect.topleft)
    pygame.draw.rect(surface, colour, rect, 1)


def _draw_crack(surface, wall, ox: int, oy: int, echo) -> None:
    """Kirilabilir duvarin catlagi - yalnizca Yanki ile gorunur."""
    rect = wall.rect.move(-ox, -oy)
    glow = radial_glow(max(6, rect.width // 2),
                       palette.color("echo_bright"),
                       peak=0.35 * echo.strength)
    surface.blit(glow, (rect.centerx - glow.get_width() // 2,
                        rect.centery - glow.get_height() // 2),
                 special_flags=pygame.BLEND_RGB_ADD)
    pygame.draw.rect(surface, palette.color("echo_bright"), rect, 1)


def draw_cost(surface: pygame.Surface, echo) -> None:
    """Bedel tarafi: vinyet ve kromatik kayma.

    **Tek karartma yuzeyi** (CLAUDE.md 4): Yanki vinyeti ayri bir gecis
    acmiyor, ayni yuzeyi kullaniyor.
    """
    if not echo.active:
        return
    _draw_chroma(surface, echo)

    strength = echo.vignette
    if strength <= 0.0:
        return
    key = (round(strength, 2), echo.tier)
    veil = _vignette_cache.get(key)
    if veil is None:
        veil = _build_vignette(strength, echo.tier)
        if len(_vignette_cache) > 48:
            _vignette_cache.clear()
        _vignette_cache[key] = veil
    surface.blit(veil, (0, 0))


def _build_vignette(strength: float, tier: int) -> pygame.Surface:
    veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
    colour = palette.color(TIER_TINT.get(tier, "void"))
    # Kenardan merkeze dogru zayiflayan cerceveler - ucuz gradyan.
    steps = 34
    for i in range(steps):
        alpha = int(255 * strength * (1.0 - i / steps) ** 2 * 0.55)
        if alpha <= 0:
            continue
        pygame.draw.rect(veil, (*colour, alpha),
                         pygame.Rect(i, i, INTERNAL_WIDTH - i * 2,
                                     INTERNAL_HEIGHT - i * 2), 1)
    return veil.convert_alpha()


def _draw_chroma(surface: pygame.Surface, echo) -> None:
    """Kanallari bir piksel ayirir - "baska bir sey duyuyorum" hissi."""
    if echo.strength < 0.4:
        return
    shift = CHROMA_SHIFT
    ghost = surface.copy()
    ghost.set_alpha(int(46 * echo.strength))
    surface.blit(ghost, (shift, 0), special_flags=pygame.BLEND_RGB_ADD)
    surface.blit(ghost, (-shift, 0), special_flags=pygame.BLEND_RGB_ADD)


def draw_answer(surface: pygame.Surface, offset: tuple[int, int],
                echo, player) -> None:
    """Yanki'nin cevabi - kelimesiz.

    Dogru cevap net bir ok; eksik cevap titrek bir ok; **yalan da net bir
    ok** cizer. Yalanin yalan oldugu ekranda yazmaz - oyuncu kademesini
    bilir ve riski kendi hesaplar. Yazsaydi mekanik anlamsizlasirdi.
    """
    if echo.answer_frames <= 0 or echo.last_answer is Answer.NONE:
        return
    ox, oy = offset
    x = int(player.body.center_x) - ox
    y = int(player.body.top) - oy - 16

    if echo.last_answer is Answer.PARTIAL:
        # Eksik cevap titrer - guvenilmezligi hareketiyle belli eder.
        x += int(math.sin(echo.answer_frames * 0.4) * 2)

    colour = palette.color("echo_bright")
    direction = echo.answer_direction if hasattr(echo, "answer_direction") else 1
    for i in range(7):
        width = 7 - i
        surface.fill(colour, (x + direction * i - width // 2, y - i, width, 1))
