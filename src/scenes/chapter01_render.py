"""Bolum 1'in sahne parcalarinin cizimi - kilic, kolye, yarik, Cemo, ogreti.

`enemy_render.py` deseniyle ayni: ilk parametre `scene`, metot degil
serbest fonksiyon. Ayrildi cunku `chapter01.py` 578 satira cikmisti -
CLAUDE.md 11'in 400 satir siniri. Sahne MANTIGI orada kaldi; burasi
yalnizca o durumun nasil gorundugunu biliyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import INTERNAL_WIDTH, TILE_SIZE
from src.core.input import Action
from src.ui import balloon, text
from src.ui.i18n import t
from src.world.rooms.chapter01 import (
    TUTORIAL_ATTACK_AFTER, TUTORIAL_MOVE_AFTER,
)

HINT_Y = 244          # INTERNAL_HEIGHT - 26


def draw_sword(scene, surface: pygame.Surface, offset) -> None:
    """Yerde duran kilic - hafif suzulur ve parildar.

    Toplanabilir bir seyin **toplanabilir gorunmesi** gerekiyor: durgun
    bir sprite dekor sanilir.
    """
    if scene.sword_pos is None:
        return
    ox, oy = offset
    bob = int(round(math.sin(scene.game.frame * 0.06) * 2))
    x = int(scene.sword_pos[0]) - ox
    y = int(scene.sword_pos[1]) - oy + bob

    glow = radial_glow(14, palette.color("gold"), peak=0.30)
    surface.blit(glow, (x - 14, y - 14),
                 special_flags=pygame.BLEND_RGB_ADD)
    # Kilic: dikey namlu + capraz balcak.
    surface.fill(palette.color("stone_light"), (x, y - 9, 1, 14))
    surface.fill(palette.color("bone"), (x, y - 9, 1, 3))
    surface.fill(palette.color("brass" if False else "gold"),
                 (x - 3, y + 2, 7, 1))
    surface.fill(palette.color("earth_dark"), (x, y + 3, 1, 3))


def draw_necklace(scene, surface: pygame.Surface, offset) -> None:
    """Kolye: once havada (verilirken), sonra oyuncunun boynunda.

    Boyundaki hali **diegetik gosterge** (CLAUDE.md 9): Yanki kademesi
    ve kolye pusulasi bir HUD cubugu ile degil, bu sprite'in
    parildamasiyla anlatiliyor. Bu yuzden aldiktan sonra da cizilmeye
    devam ediyor - bir kez gorunup kaybolan bir efekt degil.
    """
    if not (scene.gift_flying or scene.necklace):
        return
    ox, oy = offset
    if scene.gift_flying:
        wx, wy = scene.gift_position()
        # Ucarken donuyor: sabit bir nesne "kaydiriliyor" gibi okunur.
        spin = math.sin(scene.gift_progress * math.pi * 3.0)
        glow_peak = 0.45
    else:
        wx, wy = scene._necklace_target()
        spin = 0.0
        # Boyundayken nabiz atiyor - kolye pusulasinin gorsel dili.
        glow_peak = 0.16 + 0.06 * math.sin(scene.game.frame * 0.07)

    x = int(round(wx)) - ox
    y = int(round(wy)) - oy

    glow = radial_glow(9, palette.color("gold"), peak=glow_peak)
    surface.blit(glow, (x - 9, y - 9), special_flags=pygame.BLEND_RGB_ADD)
    # Zincir: iki yana acilan kisa kollar. Donusu genislikle veriyoruz -
    # bu olcekte gercek rotasyon bulanik piksel demek.
    span = max(1, int(round(2 + abs(spin) * 2)))
    surface.fill(palette.color("brass" if False else "gold"),
                 (x - span, y - 2, span * 2 + 1, 1))
    # Tas: tek piksel, paletin en parlak altini.
    surface.fill(palette.color("gold"), (x, y - 1, 1, 2))
    surface.fill(palette.color("white_flash"), (x, y - 1, 1, 1))


def draw_rift(scene, surface: pygame.Surface, offset) -> None:
    if scene.rift <= 0.0:
        return
    ox, oy = offset
    x = int(scene.rift_x) - ox
    y = int(scene.rift_y) - oy
    width = int(26 * scene.rift)
    height = int(40 * scene.rift)

    glow = radial_glow(max(4, height), palette.color("violet"),
                       peak=0.5 * scene.rift)
    surface.blit(glow, (x - height, y - height),
                 special_flags=pygame.BLEND_RGB_ADD)
    # Yarik: zeminde acilan dikey bir gedik.
    for i in range(height):
        t_value = i / max(1, height)
        span = max(1, int(width * (1.0 - t_value) * 0.5))
        surface.fill(palette.color("void"), (x - span, y - i, span * 2, 1))
        if t_value < 0.5:
            surface.fill(palette.color("violet_dark"),
                         (x - span // 2, y - i, max(1, span), 1))


def draw_cemo(scene, surface: pygame.Surface, offset) -> None:
    ox, oy = offset
    facing = 1 if scene.beat in ("taken", "chase") else -1
    image = scene.cemo.render(facing)
    if image is None:
        return
    foot = 27          # CEMO_SPEC.foot_y
    # Gomuldukce sprite'in alti kirpilir: yarigin icinde kaybolur.
    visible = max(1, image.get_height() - int(scene.cemo_sink))
    image = image.subsurface((0, 0, image.get_width(), visible))
    surface.blit(image, (int(scene.cemo_x - image.get_width() * 0.5) - ox,
                         int(scene.cemo_y - foot) - oy))

    icon = _cemo_balloon(scene)
    if icon:
        balloon.draw(surface, icon,
                     int(scene.cemo_x) - ox,
                     int(scene.cemo_y - foot) - oy,
                     frame=scene.game.frame,
                     colour=palette.color("violet_bright")
                     if icon == "alert" else palette.role("ui_text"))

def _cemo_balloon(scene) -> str:
    return {
        "wake": "necklace",
        "gift": "necklace",
        "taken": "alert",
        "chase": "alert",
    }.get(scene.beat, "")


def draw_tutorial(scene, surface: pygame.Surface) -> None:
    """Ogreti metni **son care**. Once oyuncuya deneme sansi verilir."""
    hint = ""
    if scene.beat != "play":
        return
    if not scene.moved and scene.game.frame > TUTORIAL_MOVE_AFTER:
        hint = t("chapter01.hint_move",
                 left=scene.game.input.binding_label(Action.LEFT),
                 right=scene.game.input.binding_label(Action.RIGHT))
    elif (scene.moved and not scene.attacked and scene.enemies
            # Yumrukla bile saldirilabiliyor artik - ipucu kilica
            # bakmiyor, sadece dusman gorunur olunca tetikleniyor.
            and scene.game.frame > TUTORIAL_ATTACK_AFTER):
        hint = t("chapter01.hint_attack",
                 key=scene.game.input.binding_label(Action.ATTACK))
    if not hint:
        return
    text.draw(surface, hint, INTERNAL_WIDTH // 2, HINT_Y,
              color=palette.role("ui_text_dim"), align="center")
