"""Suruklenen - Katman 1'in combo hedef tahtasi.

*Soru: combo kurmayi ogren* (docs/gdd.md 7)

**Ritim imzasi: yavas 3'luk - bekle, bekle, vur.** Sabit, ogrenilebilir.
Ic sayac her `SHAMBLER_BEAT_FRAMES` karede bir ilerler; ucuncu vurusta
saldirir. Oyuncu iki bosluk sayip ucuncude hazir olmayi ogrenir - ve
ogrendiginde kendini akilli hisseder. Rastgele olsaydi ayni oyuncu sadece
sinirlenirdi.

Poise 2: iki vurusta sendeler. Yavas oldugu icin cezasi da hafif olmali,
yoksa combo hedefi degil engel olur.
"""
from __future__ import annotations

from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.config import (
    SHAMBLER_ACTIVE_FRAMES, SHAMBLER_BEAT_FRAMES, SHAMBLER_DAMAGE,
    SHAMBLER_HEALTH, SHAMBLER_POISE, SHAMBLER_REACH, SHAMBLER_RECOVER_FRAMES,
    SHAMBLER_SPEED, TELL_FRAMES_SHAMBLER,
)
from src.entities.enemy import Enemy, EnemyState

BEATS_BEFORE_ATTACK = 3          # bekle - bekle - vur


class Shambler(Enemy):
    body_width = 12
    body_height = 22
    max_health = SHAMBLER_HEALTH
    poise = SHAMBLER_POISE

    tell_frames = TELL_FRAMES_SHAMBLER
    active_frames = SHAMBLER_ACTIVE_FRAMES
    recover_frames = SHAMBLER_RECOVER_FRAMES
    attack_damage = SHAMBLER_DAMAGE
    attack_reach = SHAMBLER_REACH
    attack_height = 16
    attack_knockback = 1.5
    move_speed = SHAMBLER_SPEED
    contact_range = 20.0

    sprite_name = "shambler"
    body_colour = "echo_dark"
    tell_sound = "shambler_tell"
    death_sound = "shambler_death"

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.beat = 0
        self.beat_frames = 0

    def _can_attack(self) -> bool:
        """Ritim ucuncu vurusa gelmediyse saldirmaz - sadece bekler."""
        return self.beat >= BEATS_BEFORE_ATTACK - 1

    def _think(self) -> None:
        # Ritim sayaci yalnizca oyuncuyu gorurken ve saldiri disinda isler.
        # Saldiri sirasinda islerse ritim kayar ve ogrenilemez hale gelir.
        if self.aware and self.state in (EnemyState.APPROACH, EnemyState.ORBIT):
            self.beat_frames += 1
            if self.beat_frames >= SHAMBLER_BEAT_FRAMES:
                self.beat_frames = 0
                self.beat = (self.beat + 1) % BEATS_BEFORE_ATTACK
        super()._think()

    def _begin_tell(self) -> None:
        super()._begin_tell()
        self.beat = 0
        self.beat_frames = 0

    def on_attack_cancelled(self) -> None:
        # Sendeleyen dusman ritmi bastan sayar - oyuncu nefes alsin.
        self.beat = 0
        self.beat_frames = 0

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
        self._update_animation()

    def draw(self, surface, offset) -> None:
        from src.entities.enemy_render import draw_enemy
        draw_enemy(self, surface, offset)
