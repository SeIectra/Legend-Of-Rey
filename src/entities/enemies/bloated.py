"""Sismek - konumlandirmayi ogretir.

*Soru: nerede durdugun onemli* (docs/gdd.md 7)

Yaklasir, siser, patlar. Ritim imzasi: **yaklas-sis-patla, sabit sure.**
Fitil bir kez yandi mi durmaz - sendeleme bile durdurmaz, sadece geciktirmez.
Oyuncu "kacacak zamanim var mi?" diye hesap yapar ve bu hesap her seferinde
ayni tutar (`BLOATED_FUSE_FRAMES` = 30 kare).

**Ekoloji: patlama diger dusmanlara da hasar verir.** Bu bir yan etki degil,
tasarim. Oyuncu Sismek'i kalabaligin ortasina cekip kacmayi kesfedebilmeli -
kesfedince oyun ona "akilli oynadin" demis olur. Dost ates oyuncuya da isler;
tek tarafli olsaydi risk kalmaz, numara ucuzlardi.

Olurken de patlar: oyuncunun onu erken oldurmesi bedava kurtulus degil,
konumlanma sorusu.
"""
from __future__ import annotations

from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import Hitbox, Team
from src.config import (
    BLOATED_BLAST_DAMAGE, BLOATED_BLAST_RADIUS, BLOATED_FUSE_FRAMES,
    BLOATED_HEALTH, BLOATED_POISE, BLOATED_SELF_DESTRUCT, BLOATED_SPEED,
    BLOATED_TRIGGER_RANGE, TELL_FRAMES_BLOATED,
)
from src.entities.enemy import Enemy, EnemyState

import pygame


class Bloated(Enemy):
    body_width = 14
    body_height = 18
    max_health = BLOATED_HEALTH
    poise = BLOATED_POISE

    tell_frames = TELL_FRAMES_BLOATED
    active_frames = 2
    recover_frames = 1
    attack_damage = BLOATED_BLAST_DAMAGE
    move_speed = BLOATED_SPEED
    contact_range = BLOATED_TRIGGER_RANGE

    sprite_name = "bloated"
    body_colour = "ember_dark"
    tell_sound = "bloated_fuse"
    # Bos: `die()` zaten `_explode()` uzerinden "bloated_explode" caliyor -
    # genel olum sesi ustune binerse ikilenir.
    death_sound = ""

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.fuse_lit = False
        self.exploded = False

    # --- Fitil --------------------------------------------------------------
    def _begin_tell(self) -> None:
        super()._begin_tell()
        self.fuse_lit = True

    def on_attack_cancelled(self) -> None:
        """Fitil yanan Sismek sendelemez - yanmaya devam eder.

        Bu bilincli: aksi halde oyuncu Sismek'i sonsuza kadar vurup
        patlamasini engelleyebilirdi ve tehdit olmaktan cikardi.
        """
        if self.fuse_lit:
            self._set_state(EnemyState.TELL)
            # Sendeleme sayaci geriye kalan fitili yemesin.
            self.stagger_frames = 0

    def _think(self) -> None:
        if self.fuse_lit and self.state is not EnemyState.TELL and not self.exploded:
            # Hangi durumda olursa olsun fitil yaniyorsa TELL'e don.
            self._set_state(EnemyState.TELL)
        if self.fuse_lit and self.state is EnemyState.TELL:
            self._face_player()
            self.body.approach_vx(0.0, 0.25)
            if self.state_frames >= BLOATED_FUSE_FRAMES:
                self._explode()
            return
        super()._think()

    def die(self) -> None:
        # Olurken de patlar - erken oldurmek bedava kurtulus degil.
        if BLOATED_SELF_DESTRUCT and not self.exploded:
            self._explode()
        super().die()

    def _explode(self) -> None:
        if self.exploded:
            return
        self.exploded = True

        radius = int(BLOATED_BLAST_RADIUS)
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = (int(self.body.center_x), int(self.body.center_y))

        # **Hem oyuncuya hem dusmanlara.** Tek tarafli dost ates riski
        # ortadan kaldirir, numarayi ucuzlatir.
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER | Team.ENEMY,
            damage=BLOATED_BLAST_DAMAGE, active_frames=self.active_frames,
            knockback=3.4, knockback_up=1.8, poise_damage=3,
            # Patlama **deler**: yaricap icindeki herkesi vurur. Varsayilan
            # davranis ilk hedefte tukenmek - yakin dovus icin dogru, patlama
            # icin degil.
            pierce=True,
        ))

        on_blast = getattr(self.scene, "on_bloated_explode", None)
        if on_blast:
            on_blast(self)
        self.remove = True

    def _can_attack(self) -> bool:
        return True

    def silhouette_scale(self) -> tuple[float, float]:
        """Fitil yandikca **sisiyor** - siluetten okunur, renkten degil."""
        if self.state is EnemyState.TELL:
            grow = 0.45 * self.tell_progress
            return (1.0 + grow, 1.0 + grow * 0.7)
        return (1.0, 1.0)

    def _update_animation(self) -> None:
        if self.dead:
            self.animator.play("death")
        elif self.state is EnemyState.TELL:
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

    def draw(self, surface, offset) -> None:
        from src.entities.enemy_render import draw_enemy
        draw_enemy(self, surface, offset)
