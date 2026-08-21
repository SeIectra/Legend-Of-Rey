"""Oyuncu: hareket, ziplama, uclu zincir, kacinma, karsi vurus.

Rey ve Ardo ayni sinifi paylasir; sayisal farklar `character_stats.py`'de
(docs/dovus-sistemi.md 8). Rey bilgiyle ve akisla kazanir, Ardo zamanlamayla
ve dayaniklilikla.

Cizim uc kipte calisir (F4): sprite, siluet ve kutu. Kutu kipi "kutularla
eglenceli mi?" sorusunu sprite'lari atmadan sormaya yarar.
"""
from __future__ import annotations

import pygame

from src.combat.combo import (
    AttackPhase, ChainState, ComboCounter, DodgeState, counter_damage,
)
from src.combat.hitbox import Hitbox, Team, melee_rect
from src.config import (
    APEX_GRAVITY_SCALE, APEX_SPEED_THRESHOLD, COYOTE_FRAMES, DODGE_SPEED,
    DODGE_TOTAL_FRAMES, JUMP_CUT_MULTIPLIER, PLAYER_AIR_ACCEL,
    PLAYER_AIR_FRICTION, PLAYER_GROUND_ACCEL, PLAYER_GROUND_FRICTION,
    PLAYER_JUMP_SPEED, PLAYER_RUN_SPEED,
)
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.core.input import Action
from src.entities.actor import Actor
from src.entities.character_stats import CharacterStats, REY
from src.entities.player_render import draw_player

ATTACK_REACH = 22
ATTACK_HEIGHT = 18
FINISHER_REACH = 28
FINISHER_HEIGHT = 22
# Saldiri sirasinda one atilma - saldiri hem hareket hem hasardir.
LUNGE_BY_INDEX = (0.9, 1.1, 2.0)
PLAYER_IFRAMES_ON_HIT = 45
HURT_ANIMATION_FRAMES = 14


class Player(Actor):
    team = Team.PLAYER
    body_width = 10
    body_height = 22
    iframes_on_hit = PLAYER_IFRAMES_ON_HIT

    def __init__(self, scene, x: float, y: float,
                 stats: CharacterStats = REY) -> None:
        self.stats = stats
        self.max_health = stats.max_health
        super().__init__(scene, x, y)

        self.animator = Animator(stats.sprite_name)
        # Sprite hucresi karakterden buyuk; ayak cizgisini govdenin altina
        # hizalamak icin gerekli. Bilinmezse karakter havada durur.
        self.sprite_foot_y = CHARACTERS[stats.sprite_name].foot_y

        self.chain = ChainState(window_frames=stats.chain_window)
        self.dodge = DodgeState(charges=stats.dodge_charges,
                                max_charges=stats.dodge_charges)
        self.combo = ComboCounter()

        self.coyote_frames = 0
        self.jump_held = False
        self.air_frames = 0
        self.hurt_frames = 0        # Hasar animasyonu suresi
        self.last_hit_was_counter = False

    # --- Durum sorgulari ----------------------------------------------------
    @property
    def invulnerable(self) -> bool:
        return self.iframes > 0 or self.dodge.invulnerable

    @property
    def busy(self) -> bool:
        return self.chain.busy or self.dodge.active or self.dead

    @property
    def state_name(self) -> str:
        if self.dead:
            return "olu"
        if self.dodge.active:
            return "kacinma"
        if self.chain.busy:
            return f"vurus{self.chain.index + 1}:{self.chain.phase.name.lower()}"
        if not self.body.grounded:
            return "havada"
        if abs(self.body.vx) > 0.2:
            return "kosu"
        return "bosta"

    # --- Ana guncelleme -----------------------------------------------------
    def update(self) -> None:
        if self.dead:
            self._update_dead()
            return

        inp = self.scene.game.input
        if self.iframes > 0:
            self.iframes -= 1
        if self.hurt_frames > 0:
            self.hurt_frames -= 1
        self.flash.update()
        self.squash.update()

        self.dodge.update(self.body.grounded)
        if self.combo.update():
            self.scene.on_combo_reset()

        if self.dodge.active:
            self._update_dodge()
        else:
            self._update_chain(inp)
            if not self.chain.busy or self.chain.phase is AttackPhase.RECOVERY:
                self._update_movement(inp)
            self._handle_actions(inp)

        self._apply_physics()
        self._update_ground_state()
        self._update_animation()

    def _update_animation(self) -> None:
        """Animasyon durumu oynanistan turer, tersi degil.

        Saldirilar **ilerlemeyle** surulur: kare, saldirinin kendi kare
        butcesindeki konumdan secilir. Boylece animasyon dovus zamanlamasini
        asla kaydiramaz.
        """
        if self.dead:
            self.animator.play("death")
            self.animator.update()
            return

        if self.chain.busy:
            state = f"attack{min(self.chain.index + 1, 3)}"
            self.animator.play(state)
            self.animator.set_progress(self._attack_progress())
            return

        if self.hurt_frames > 0:
            self.animator.play("hurt")
        elif self.dodge.active:
            self.animator.play("dodge")
            self.animator.set_progress(
                1.0 - self.dodge.frames_left / max(1, DODGE_TOTAL_FRAMES))
            return
        elif not self.body.grounded:
            self.animator.play("jump" if self.body.vy < -0.3 else "fall")
        elif abs(self.body.vx) > 0.25:
            self.animator.play("run")
        else:
            self.animator.play("idle")
        self.animator.update()

    def _attack_progress(self) -> float:
        """Su anki saldirinin 0..1 arasi ilerlemesi."""
        spec = self.chain.spec
        total = spec.total
        if total <= 0:
            return 1.0
        if self.chain.phase is AttackPhase.WINDUP:
            done = spec.windup - self.chain.phase_frames_left
        elif self.chain.phase is AttackPhase.ACTIVE:
            done = spec.windup + (spec.active - self.chain.phase_frames_left)
        else:
            done = (spec.windup + spec.active
                    + (spec.recovery - self.chain.phase_frames_left))
        return max(0.0, min(1.0, done / total))

    # --- Hareket ------------------------------------------------------------
    def _update_movement(self, inp) -> None:
        move = inp.axis_x
        if abs(move) < 0.2:
            move = 0.0

        # Saldiri sirasinda yon kontrolu kisitli - tamamen kilitlemek kotu
        # hissettirir, serbest birakmak vurusu anlamsizlastirir.
        authority = 1.0
        if self.chain.busy:
            authority = 0.45 if self.chain.phase is AttackPhase.RECOVERY else 0.0

        if move != 0.0 and authority > 0.0:
            self.facing = 1 if move > 0 else -1

        speed = PLAYER_RUN_SPEED * self.stats.move_multiplier
        accel = PLAYER_GROUND_ACCEL if self.body.grounded else PLAYER_AIR_ACCEL
        friction = (PLAYER_GROUND_FRICTION if self.body.grounded
                    else PLAYER_AIR_FRICTION)

        if move != 0.0 and authority > 0.0:
            self.body.approach_vx(move * speed * authority, accel)
        else:
            self.body.approach_vx(0.0, friction)

    def _handle_actions(self, inp) -> None:
        # Kacinma once bakilir: saldiriyi iptal edebilir, akiciligin kalbi bu.
        if inp.buffered(Action.DODGE) and self._can_dodge():
            inp.consume(Action.DODGE)
            self._start_dodge(inp)
            return

        if inp.buffered(Action.JUMP) and self._can_jump():
            inp.consume(Action.JUMP)
            self._jump()

        # Degisken ziplama yuksekligi
        if not inp.held(Action.JUMP) and self.body.vy < 0.0 and self.jump_held:
            self.body.vy *= JUMP_CUT_MULTIPLIER
            self.jump_held = False

        if inp.buffered(Action.ATTACK):
            inp.consume(Action.ATTACK)
            self._request_attack()

    def _can_jump(self) -> bool:
        return (self.coyote_frames > 0 and not self.chain.busy
                and not self.dodge.active)

    def _can_dodge(self) -> bool:
        if not self.dodge.can_dodge:
            return False
        # Vurus 1 ve 2'nin recovery'si iptal edilebilir; bitiricininki edilemez.
        if self.chain.busy and not self.chain.cancelable:
            return False
        return True

    def _jump(self) -> None:
        self.body.vy = -PLAYER_JUMP_SPEED
        self.coyote_frames = 0
        self.jump_held = True
        self.air_frames = 1
        self.squash.jump()
        self.scene.on_player_jump(self)

    def _update_ground_state(self) -> None:
        if self.body.grounded:
            self.coyote_frames = COYOTE_FRAMES
            if not self.body.was_grounded and self.air_frames > 10:
                self.squash.land()
                self.scene.on_player_land(self, self.air_frames)
            self.air_frames = 0
        else:
            self.coyote_frames = max(0, self.coyote_frames - 1)
            self.air_frames += 1

    def _apply_physics(self) -> None:
        if not self.dodge.active:
            # Apex hafifligi: ziplamanin tepesinde yercekimi azalir, havadaki
            # kontrol suresi uzar.
            scale = (APEX_GRAVITY_SCALE
                     if abs(self.body.vy) < APEX_SPEED_THRESHOLD else 1.0)
            self.body.apply_gravity(scale)
        self.body.move(self.scene.tilemap)
        self.body.drop_through = False

    # --- Kacinma ------------------------------------------------------------
    def _start_dodge(self, inp) -> None:
        direction = self.facing
        if abs(inp.axis_x) > 0.3:
            direction = 1 if inp.axis_x > 0 else -1
        self.facing = direction
        self.chain.cancel()
        self.dodge.start(direction)
        self.scene.on_player_dodge(self)

    def _update_dodge(self) -> None:
        # Kacinma boyunca yercekimi yok: mesafe tahmin edilebilir kalir.
        self.body.vx = self.dodge.direction * DODGE_SPEED
        self.body.vy = 0.0
        self.scene.on_dodge_trail(self)

    # --- Saldiri ------------------------------------------------------------
    def _request_attack(self) -> None:
        if self.chain.busy:
            self.chain.request_next()
            return
        self.chain.start(self.chain.next_index())
        self._apply_lunge()
        self.scene.on_player_attack(self, self.chain.index)

    def _apply_lunge(self) -> None:
        lunge = LUNGE_BY_INDEX[min(self.chain.index, len(LUNGE_BY_INDEX) - 1)]
        if not self.body.grounded:
            lunge *= 0.55
        self.body.vx = self.facing * lunge

    def _update_chain(self, inp) -> None:
        event = self.chain.update()
        if event == "spawn_hitbox":
            self._spawn_attack_hitbox()
        elif event == "chain":
            self._apply_lunge()
            self.scene.on_player_attack(self, self.chain.index)

    def _spawn_attack_hitbox(self) -> None:
        spec = self.chain.spec
        finisher = self.chain.is_finisher
        reach = FINISHER_REACH if finisher else ATTACK_REACH
        height = FINISHER_HEIGHT if finisher else ATTACK_HEIGHT

        damage = spec.damage
        is_counter = self.dodge.consume_counter()
        if is_counter:
            damage = counter_damage(damage, self.stats.counter_bonus)
        self.last_hit_was_counter = is_counter

        box = Hitbox(
            rect=melee_rect(self.body, self.facing, reach, height),
            damage=damage,
            owner=self,
            targets=Team.ENEMY | Team.BREAKABLE,
            knockback=spec.knockback,
            knockback_up=1.4 if finisher else 0.6,
            active_frames=spec.active,
            poise_damage=2 if finisher else 1,
            is_finisher=finisher,
            is_counter=is_counter,
            pierce=finisher,
        )
        self.scene.hitboxes.spawn(box)
        self.scene.on_attack_swing(self, box)

    def notify_kill(self) -> None:
        """Bir dusman oldu: recovery iptal olur (kill cancel).

        Kalabalik dovusun "bicip gecme" hissi tek basina bundan gelir.
        """
        self.chain.kill_cancel()

    def register_hit(self) -> None:
        """Vurus degdi: combo sayacini ilerlet."""
        for threshold in self.combo.register_hit():
            self.scene.on_combo_threshold(self, threshold)

    # --- Hasar --------------------------------------------------------------
    def take_damage(self, box, direction):
        result = super().take_damage(box, direction)
        if result.hit:
            self.chain.cancel()
            self.combo.reset()
            self.hurt_frames = HURT_ANIMATION_FRAMES
            self.scene.on_player_hurt(self, result)
        return result

    def die(self) -> None:
        super().die()
        self.scene.on_player_died(self)

    def _update_dead(self) -> None:
        self.body.approach_vx(0.0, PLAYER_GROUND_FRICTION)
        self.body.apply_gravity()
        self.body.move(self.scene.tilemap)
        self.flash.update()

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        draw_player(self, surface, offset)

    def debug_lines(self) -> list[str]:
        return [
            f"{self.stats.name}  {self.state_name}",
            f"can {self.health}/{self.max_health}  combo {self.combo.count}"
            f" (en iyi {self.combo.best})",
            f"kacinma sarj {self.dodge.charges}  "
            f"karsi {self.dodge.counter_window_left}  "
            f"coyote {self.coyote_frames}",
        ]
