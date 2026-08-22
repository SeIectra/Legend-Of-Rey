"""Sonmus Olan - Bolum 3 mini-boss (Oda 7).

`docs/bolum-03.md`: *"Eskiden Mum Bekcisi gibi bir varlikmis. Ama mumlari
sonmus, kendisi bozulmus."* Uc hamlesi var, sabit donguyle gelir (ayni
`BloatedOne` felsefesi - rastgele boss ogrenilemez, sadece sinir bozar):

    Karanlik Dalgasi   20 kare tell, arenadaki tum isiklari 2 sn sondurur
    Surukleme          hizli tek vurus - kacinmayla gecilir
    Mum Cagrisi        uc sonmus mum belirir, Golge Suruklenen dogurur

**Arena uc katmanli:** boss'a vur, ortadaki mangali yak, mangali koru.
Mangal (`Brazier`) yanarken boss sersemler (combo penceresi) ve Karanlik
Dalgasi'ni kullanamaz - bu yuzden mangal ayni zamanda bir savunma aracidir.
Boss'un `drag` hamlesi mangala yeterince yakin biterse onu sondurur
(`_maybe_snuff_brazier`) - "boss mangali sondurmeye calisiyor" hissi
boylece AI'yi yeniden yazmadan, mevcut hamlenin bir yan etkisi olarak
geliyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import Hitbox, Team, melee_rect
from src.config import (
    BRAZIER_BURN_FRAMES, BRAZIER_LIGHT_RADIUS, BRAZIER_STAGGER_FRAMES,
    CANDLE_CALL_TELL_FRAMES, DARK_WAVE_TELL_FRAMES, DRAG_SNUFF_RANGE,
    DRAG_TELL_FRAMES, EXTINGUISHED_ONE_HEALTH, EXTINGUISHED_ONE_POISE,
    TILE_SIZE,
)
from src.entities.boss import Boss
from src.entities.enemy import EnemyState

MOVES = ("dark_wave", "drag", "candle_call", "drag")

DARK_WAVE_ACTIVE = 4
DARK_WAVE_RECOVER = 40
DRAG_ACTIVE = 6
DRAG_RECOVER = 24
DRAG_REACH = 26
DRAG_DAMAGE = 16
DRAG_SPEED = 3.4
CANDLE_CALL_ACTIVE = 2
CANDLE_CALL_RECOVER = 30
CANDLE_CALL_COUNT = 3


class Brazier:
    """Arenanin ortasindaki mangal. Sahne tarafindan yakilir/soner."""

    __slots__ = ("x", "y", "lit", "burn_frames", "just_lit")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.lit = False
        self.burn_frames = 0
        self.just_lit = False

    @property
    def radius(self) -> float:
        return BRAZIER_LIGHT_RADIUS if self.lit else 0.0

    def light(self) -> bool:
        if self.lit:
            return False
        self.lit = True
        self.burn_frames = BRAZIER_BURN_FRAMES
        self.just_lit = True
        return True

    def extinguish(self) -> None:
        self.lit = False
        self.burn_frames = 0

    def update(self) -> None:
        self.just_lit = False
        if self.lit:
            self.burn_frames -= 1
            if self.burn_frames <= 0:
                self.extinguish()

    def draw(self, surface: pygame.Surface, offset: tuple[int, int],
             frame: int = 0) -> None:
        ox, oy = offset
        x = int(self.x) - ox
        y = int(self.y) - oy
        surface.fill(palette.color("stone_dark"), (x - 7, y - 2, 14, 6))
        surface.fill(palette.color("stone"), (x - 7, y - 2, 14, 1))
        if not self.lit:
            surface.fill(palette.color("ink"), (x - 4, y - 6, 8, 4))
            return
        flicker = (frame // 5) % 3
        surface.fill(palette.color("ember"), (x - 4, y - 10 + flicker, 8, 6 - flicker))
        surface.fill(palette.color("gold"), (x - 2, y - 6, 4, 3))
        from src.art.glow import radial_glow
        glow = radial_glow(int(BRAZIER_LIGHT_RADIUS),
                           palette.color("ember"),
                           peak=0.4 + 0.06 * math.sin(frame * 0.1))
        surface.blit(glow, (x - glow.get_width() // 2, y - glow.get_height() // 2),
                     special_flags=pygame.BLEND_RGB_ADD)


class ExtinguishedOne(Boss):
    """Sonmus Olan - Bolum 3 mini-boss."""

    body_width = 14
    body_height = 26
    max_health = EXTINGUISHED_ONE_HEALTH
    poise = EXTINGUISHED_ONE_POISE

    tell_frames = DARK_WAVE_TELL_FRAMES
    active_frames = DARK_WAVE_ACTIVE
    recover_frames = DARK_WAVE_RECOVER
    attack_damage = DRAG_DAMAGE
    attack_reach = DRAG_REACH
    attack_height = 22
    attack_knockback = 2.4
    move_speed = 0.4
    contact_range = 40.0

    phases = (0.5,)
    sprite_name = "climber"
    body_colour = "violet_dark"
    boss_name_key = "boss.extinguished_one"

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.move_index = 0
        self.move = "drag"
        self.summoned = 0

    # --- Hamle secimi ---------------------------------------------------------
    def _next_move(self) -> str:
        brazier = getattr(self.scene, "brazier", None)
        guard = 0
        while guard < len(MOVES):
            guard += 1
            move = MOVES[self.move_index % len(MOVES)]
            self.move_index += 1
            if move == "dark_wave" and brazier is not None and brazier.lit:
                # Mangal yanarken Karanlik Dalgasi iptal - bu yuzden mangal
                # bir savunma araci.
                continue
            return move
        return "drag"

    def _begin_tell(self) -> None:
        self.move = self._next_move()
        self.tell_frames = {
            "dark_wave": DARK_WAVE_TELL_FRAMES,
            "drag": DRAG_TELL_FRAMES,
            "candle_call": CANDLE_CALL_TELL_FRAMES,
        }[self.move]
        super()._begin_tell()

    def _begin_attack(self) -> None:
        self.active_frames = {
            "dark_wave": DARK_WAVE_ACTIVE,
            "drag": DRAG_ACTIVE,
            "candle_call": CANDLE_CALL_ACTIVE,
        }[self.move]
        self.recover_frames = {
            "dark_wave": DARK_WAVE_RECOVER,
            "drag": DRAG_RECOVER,
            "candle_call": CANDLE_CALL_RECOVER,
        }[self.move]
        if self.move == "drag":
            self.body.vx = self.facing * DRAG_SPEED
        super()._begin_attack()

    # --- Hamleler ---------------------------------------------------------------
    def _spawn_attack(self) -> None:
        if self.move == "dark_wave":
            self._do_dark_wave()
        elif self.move == "drag":
            self._do_drag()
        else:
            self._do_candle_call()

    def _do_dark_wave(self) -> None:
        """Arenadaki tum isiklari 2 saniyeligine sondurur."""
        self._notify("dark_wave")

    def _do_drag(self) -> None:
        rect = melee_rect(self.body, self.facing, DRAG_REACH, self.attack_height)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=DRAG_DAMAGE, active_frames=DRAG_ACTIVE,
            knockback=3.2, poise_damage=2,
        ))
        self._maybe_snuff_brazier()
        self._notify("drag")

    def _maybe_snuff_brazier(self) -> None:
        """Surukleme mangala yeterince yakin bitti mi - oyleyse sondurur."""
        brazier = getattr(self.scene, "brazier", None)
        if brazier is None or not brazier.lit:
            return
        if abs(self.body.center_x - brazier.x) <= DRAG_SNUFF_RANGE:
            brazier.extinguish()
            self._notify("snuff")

    def _do_candle_call(self) -> None:
        """Uc sonmus mum - Golge Suruklenen dogurur."""
        from src.entities.enemies.shadow_shambler import ShadowShambler
        for i in range(CANDLE_CALL_COUNT):
            side = (-1, 0, 1)[i % 3]
            x = self.body.center_x + side * TILE_SIZE * 4
            self.scene.enemies.append(
                ShadowShambler(self.scene, x, self.body.bottom))
            self.summoned += 1
        self._notify("candle_call")

    def _notify(self, move: str) -> None:
        hook = getattr(self.scene, "on_boss_move", None)
        if hook:
            hook(self, move)

    def on_brazier_lit(self) -> None:
        """Mangal yandi - boss sersemler, combo penceresi acilir."""
        self._set_state(EnemyState.STAGGER)
        self.stagger_frames = BRAZIER_STAGGER_FRAMES
        self.scene.tokens.force_release(self)
        self.on_attack_cancelled()

    # --- Dongu --------------------------------------------------------------
    def _think(self) -> None:
        if self.state is EnemyState.ATTACK and self.move == "drag":
            # Surukleme boyunca hiz sabit tutulur - _think normalde vx'i
            # yaklastirirdi, dash'in gucunu yerdi.
            return
        super()._think()

    def silhouette_scale(self) -> tuple[float, float]:
        if self.state is not EnemyState.TELL:
            return (1.0, 1.0)
        t_value = self.tell_progress
        if self.move == "dark_wave":
            pulse = 0.16 * math.sin(t_value * math.pi * 3)
            return (1.0 + pulse, 1.0 + pulse)
        if self.move == "drag":
            return (1.0 - 0.14 * t_value, 1.0 + 0.22 * t_value)
        return (1.0 + 0.10 * t_value, 1.0 - 0.06 * t_value)

    def _update_animation(self) -> None:
        if self.dead:
            self.animator.play("death")
        elif self.state is EnemyState.STAGGER:
            self.animator.play("hurt")
        elif self.state in (EnemyState.TELL, EnemyState.ATTACK):
            self.animator.play("attack1")
        elif abs(self.body.vx) > 0.08:
            self.animator.play("run")
        else:
            self.animator.play("idle")
        self.animator.update()

    def update(self) -> None:
        super().update()
        if not self.remove:
            self._update_animation()

    def draw(self, surface: pygame.Surface, offset) -> None:
        from src.entities.enemy_render import draw_enemy
        draw_enemy(self, surface, offset)

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"hamle {self.move}  sira {self.move_index}  "
            f"cagrilan {self.summoned}"]
