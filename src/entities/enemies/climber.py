"""Tirmanan - dikey farkindalik ogretir.

*Soru: yukariya da bak* (docs/gdd.md 7)

Tavanda asili bekler. Oyuncu **altindan gecerken** birakir. Ritim imzasi:
**ani tek vurus, uzun bekleme** - dustukten sonra 30 kare toparlanir, o
pencere oyuncunun odulu.

**Telegraf sart.** Birakmadan once sallanir, toz doker ve tehlike rengiyle
parlar (`TELL_FRAMES_CLIMBER` = 16 kare, alt sinir 14). Habersiz dusen bir
dusman "yukari bakmayi ogret" degil, "ezberle ve tekrar oyna" olur - oyuncu
ilk seferinde adaletsizce olur ve bunun ogretici hicbir yani yoktur.

Poise 1: tek vurusta sendeler. Havadan gelen tehdit kirilgan olmali, yoksa
konumlanma imkansizlasir.
"""
from __future__ import annotations

from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.config import (
    CLIMBER_ACTIVE_FRAMES, CLIMBER_DAMAGE, CLIMBER_DROP_SPEED,
    CLIMBER_FLEE_SPEED, CLIMBER_HEALTH, CLIMBER_POISE, CLIMBER_REACH,
    CLIMBER_RECOVER_FRAMES, CLIMBER_SPEED, CLIMBER_TRIGGER_X,
    TELL_FRAMES_CLIMBER,
)
from src.entities.enemy import Enemy, EnemyState


class Climber(Enemy):
    body_width = 11
    body_height = 18
    max_health = CLIMBER_HEALTH
    poise = CLIMBER_POISE

    tell_frames = TELL_FRAMES_CLIMBER
    active_frames = CLIMBER_ACTIVE_FRAMES
    recover_frames = CLIMBER_RECOVER_FRAMES
    attack_damage = CLIMBER_DAMAGE
    attack_reach = CLIMBER_REACH
    attack_height = 14
    attack_knockback = 1.2
    move_speed = CLIMBER_SPEED
    contact_range = 18.0

    sprite_name = "climber"
    body_colour = "echo"

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.hanging = True
        self.anchor_x = self.body.center_x
        self.anchor_y = self.body.y

    # --- Asili durum --------------------------------------------------------
    @property
    def overhead_player(self) -> bool:
        """Oyuncu tam altindan geciyor mu?"""
        player = self.player
        if player is None or player.dead:
            return False
        return (abs(player.body.center_x - self.body.center_x) <= CLIMBER_TRIGGER_X
                and player.body.center_y > self.body.center_y)

    def _think(self) -> None:
        if self.hanging:
            self._think_hanging()
            return
        super()._think()

    @property
    def _fleeing_light(self) -> bool:
        """Isik yaklasinca kacar (docs/bolum-03.md Oda 3 - "isik silahtir").

        `scene.light` yalnizca Bolum 3'te var; baska bolumlerde `None` ve
        bu davranis hicbir zaman tetiklenmez - Climber'a dokunmak diger
        bolumleri bozmuyor.
        """
        light = getattr(self.scene, "light", None)
        if light is None:
            return False
        return light.in_light(self.body.center_x, self.body.center_y)

    def _think_hanging(self) -> None:
        # Asiliyken yercekimi yok; tavana tutunuyor.
        self.body.vy = 0.0
        self.body.vx = 0.0
        self.body.y = self.anchor_y

        if self._fleeing_light:
            # Devrilme planini birakir, tavan boyunca isiktan uzaklasir.
            player = self.player
            if player is not None:
                away = -1.0 if player.body.center_x >= self.body.center_x else 1.0
                self.anchor_x += away * CLIMBER_FLEE_SPEED
                self.body.x = self.anchor_x - self.body.width * 0.5
            return

        if self.state is EnemyState.TELL:
            self._face_player()
            if self.state_frames >= self.tell_frames:
                self._drop()
            return

        if self.state is EnemyState.STAGGER:
            # Asiliyken vurulursa duser - yukarida kalip sikismasin.
            self._drop()
            return

        if self.overhead_player and self.scene.tokens.request(self):
            self._begin_tell()

    def _drop(self) -> None:
        self.hanging = False
        self.body.vy = CLIMBER_DROP_SPEED
        self._set_state(EnemyState.APPROACH)
        on_drop = getattr(self.scene, "on_climber_drop", None)
        if on_drop:
            on_drop(self)

    def update(self) -> None:
        if self.hanging and not self.dead:
            # Asiliyken Actor.update'in yercekimi cagrisini atliyoruz ama
            # geri kalan her seyi (iframe, flash, squash) calistiriyoruz.
            self.state_frames += 1
            self._update_awareness()
            self._think()
            if self.iframes > 0:
                self.iframes -= 1
            if self.stagger_frames > 0:
                self.stagger_frames -= 1
            self.flash.update()
            self.squash.update()
            self._update_animation()
            return
        super().update()
        self._update_animation()

    def silhouette_scale(self) -> tuple[float, float]:
        """Asiliyken tell sallanma gibi okunur, kabarma gibi degil."""
        if self.state is EnemyState.TELL and self.hanging:
            # Yatayda genisleyip dikeyde kisalir - "kopmak uzere" hissi.
            grow = 0.22 * self.tell_progress
            return (1.0 + grow, 1.0 - grow * 0.5)
        return super().silhouette_scale()

    def _update_animation(self) -> None:
        if self.dead:
            self.animator.play("death")
        elif self.state is EnemyState.STAGGER:
            self.animator.play("hurt")
        elif self.hanging:
            self.animator.play("idle")
        elif not self.body.grounded:
            self.animator.play("fall")
        elif self.state in (EnemyState.TELL, EnemyState.ATTACK):
            self.animator.play("attack1")
        elif abs(self.body.vx) > 0.08:
            self.animator.play("run")
        else:
            self.animator.play("idle")
        self.animator.update()

    def draw(self, surface, offset) -> None:
        from src.entities.enemy_render import draw_enemy
        draw_enemy(self, surface, offset)
