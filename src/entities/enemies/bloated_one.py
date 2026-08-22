"""Sismis Olan - Bolum 2 mini-boss.

`docs/bolum-02.md` Oda 7. Buyutulmus Suruklenen (1.6x), uc hamlesi var:

    Savurma   genis yatay, 18 kare tell   -> kacinmayla gecilir
    Cokus     havaya ziplar, iner, sok dalgasi -> ziplayarak gecilir
    Cagri     iki Suruklenen dogurur (can %50 altina inince)

**Yeni mekanik ogretmiyor - sinav.** Oyuncunun ogrendigi her seyi
birlestirmesini istiyor: zincir, kacinma, ziplama, konumlanma.

## Hamleler farkli **cozum** istiyor

Ucu de kacinmayla gecilseydi dovus tek tuslu olurdu. Savurma yatay geliyor
(kacin), Cokus dikey geliyor (zipla). Oyuncu hangi tell'in hangi cozumu
istedigini **ogrenmek** zorunda - ezber degil, okuma.

## Ritim yine sabit

Hamle sirasi rastgele degil, sabit bir donguyle geliyor. Rastgele bir boss
ogrenilemez, sadece sinir bozar (docs/derinlestirme.md 4.2). Sabit sirada
oyuncu ikinci-ucuncu denemede gecebilir - basari olcutu tam olarak bu
(docs/bolum-02.md: "ilk denemede zor, ikinci-ucuncude gecilebilir").
"""
from __future__ import annotations

import math

import pygame

from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import Hitbox, Team, melee_rect
from src.config import TILE_SIZE
from src.entities.boss import Boss
from src.entities.enemy import EnemyState

SCALE = 1.6                      # Buyutulmus Suruklenen

# Hamle siralari - **sabit**, ogrenilebilir.
MOVES_PHASE_0 = ("sweep", "slam", "sweep")
MOVES_PHASE_1 = ("sweep", "slam", "summon", "sweep", "slam")

SWEEP_TELL = 18                  # docs/bolum-02.md: 18 kare
SWEEP_ACTIVE = 6
SWEEP_RECOVER = 26
SWEEP_REACH = 34
SWEEP_DAMAGE = 14

SLAM_TELL = 22
SLAM_RISE = 14                   # Havada gecirdigi kare
SLAM_ACTIVE = 5
SLAM_RECOVER = 30
SLAM_DAMAGE = 16
SHOCKWAVE_REACH = 58
SHOCKWAVE_HEIGHT = 10            # Alcak: **ziplayarak** gecilir

SUMMON_TELL = 26
SUMMON_COUNT = 2


class BloatedOne(Boss):
    """Sismis Olan - Bolum 2 mini-boss."""

    body_width = int(12 * SCALE)
    body_height = int(22 * SCALE)
    max_health = 240
    poise = 6                    # Combo'yu kolayca kirdirmiyor

    tell_frames = SWEEP_TELL
    active_frames = SWEEP_ACTIVE
    recover_frames = SWEEP_RECOVER
    attack_damage = SWEEP_DAMAGE
    attack_reach = SWEEP_REACH
    attack_height = 20
    attack_knockback = 3.0
    move_speed = 0.34
    contact_range = 46.0

    phases = (0.5,)              # %50'de Cagri acilir
    sprite_name = "shambler"
    body_colour = "blood"
    boss_name_key = "boss.bloated_one"
    tell_sound = "shambler_tell"  # Ayni iskelet/sprite - ayni tell sesi

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.move_index = 0
        self.move = "sweep"
        self.airborne_frames = 0
        self.summoned = 0

    # --- Hamle secimi -------------------------------------------------------
    @property
    def rotation(self) -> tuple[str, ...]:
        return MOVES_PHASE_1 if self.phase >= 1 else MOVES_PHASE_0

    def _next_move(self) -> str:
        order = self.rotation
        move = order[self.move_index % len(order)]
        self.move_index += 1
        return move

    def _begin_tell(self) -> None:
        self.move = self._next_move()
        # Her hamlenin kendi tell suresi var; alt sinir 14 kare (BAGLAYICI).
        self.tell_frames = {
            "sweep": SWEEP_TELL,
            "slam": SLAM_TELL,
            "summon": SUMMON_TELL,
        }[self.move]
        super()._begin_tell()

    def _begin_attack(self) -> None:
        self.airborne_frames = SLAM_RISE if self.move == "slam" else 0
        self.active_frames = {
            "sweep": SWEEP_ACTIVE,
            "slam": SLAM_ACTIVE,
            "summon": 2,
        }[self.move]
        self.recover_frames = {
            "sweep": SWEEP_RECOVER,
            "slam": SLAM_RECOVER,
            "summon": 24,
        }[self.move]
        super()._begin_attack()

    # --- Hamleler -----------------------------------------------------------
    def _spawn_attack(self) -> None:
        if self.move == "sweep":
            self._do_sweep()
        elif self.move == "slam":
            self._do_slam()
        else:
            self._do_summon()

    def _do_sweep(self) -> None:
        """Genis yatay savurma - **kacinmayla** gecilir."""
        rect = melee_rect(self.body, self.facing, SWEEP_REACH,
                          self.attack_height)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=SWEEP_DAMAGE, active_frames=SWEEP_ACTIVE,
            knockback=3.0, poise_damage=2,
        ))
        self._notify("sweep")

    def _do_slam(self) -> None:
        """Yere inis + sok dalgasi - **ziplayarak** gecilir.

        Dalga alcak (10 piksel): kacinma kurtarmiyor, ziplamak kurtariyor.
        Iki hamlenin farkli cozum istemesi dovusun tek tuslu olmasini
        engelliyor.
        """
        wave = pygame.Rect(int(self.body.center_x - SHOCKWAVE_REACH),
                           int(self.body.bottom - SHOCKWAVE_HEIGHT),
                           SHOCKWAVE_REACH * 2, SHOCKWAVE_HEIGHT)
        self.scene.hitboxes.spawn(Hitbox(
            rect=wave, owner=self, targets=Team.PLAYER,
            damage=SLAM_DAMAGE, active_frames=SLAM_ACTIVE,
            knockback=3.6, knockback_up=1.4, poise_damage=3, pierce=True,
        ))
        from src.core.juice import ImpactWeight
        self.scene.juice.explosion(self.body.center_x, self.body.bottom,
                                   ImpactWeight.FINISHER)
        self._notify("slam")

    def _do_summon(self) -> None:
        """Iki Suruklenen cagirir. Yalnizca ikinci fazda."""
        from src.entities.enemies.shambler import Shambler
        for side in (-1, 1):
            x = self.body.center_x + side * TILE_SIZE * 3
            self.scene.enemies.append(
                Shambler(self.scene, x, self.body.bottom))
            self.summoned += 1
        self._notify("summon")

    def _notify(self, move: str) -> None:
        hook = getattr(self.scene, "on_boss_move", None)
        if hook:
            hook(self, move)

    # --- Dongu --------------------------------------------------------------
    def _think(self) -> None:
        if self.state is EnemyState.ATTACK and self.airborne_frames > 0:
            # Cokus: havada asili kaliyor, sonra iniyor.
            self.airborne_frames -= 1
            self.body.vy = -1.4 if self.airborne_frames > SLAM_RISE // 2 else 3.2
            return
        super()._think()

    def silhouette_scale(self) -> tuple[float, float]:
        """Tell sirasinda hamleye gore **farkli** deformasyon.

        Savurma yatayda genisliyor, Cokus dikeyde toplaniyor. Oyuncu
        hangi hamlenin geldigini renkten degil **siluetten** okuyabilsin -
        renk korlugu icin de sart.
        """
        if self.state is not EnemyState.TELL:
            return (1.0, 1.0)
        t_value = self.tell_progress
        if self.move == "slam":
            return (1.0 - 0.18 * t_value, 1.0 + 0.28 * t_value)
        if self.move == "summon":
            pulse = 0.12 * math.sin(t_value * math.pi * 4)
            return (1.0 + pulse, 1.0 + pulse)
        return (1.0 + 0.30 * t_value, 1.0 - 0.12 * t_value)

    def _update_animation(self) -> None:
        if self.dead:
            self.animator.play("death")
        elif self.state is EnemyState.STAGGER:
            self.animator.play("hurt")
        elif self.state in (EnemyState.TELL, EnemyState.ATTACK):
            self.animator.play("attack3" if self.move == "slam" else "attack1")
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
        """Buyutulmus ciziliyor - 1.6x."""
        from src.entities.enemy_render import draw_enemy
        ox, oy = offset
        if self.scene.game.box_mode:
            draw_enemy(self, surface, offset)
            return

        squash_x, squash_y = self.squash.current
        tell_x, tell_y = self.silhouette_scale()
        image = self.animator.render(
            self.facing,
            flash=self.flash.active,
            silhouette_mode=self.scene.game.silhouette_mode,
        )
        if image is None:
            draw_enemy(self, surface, offset)
            return
        width = max(2, int(image.get_width() * SCALE * squash_x * tell_x))
        height = max(2, int(image.get_height() * SCALE * squash_y * tell_y))
        big = pygame.transform.scale(image, (width, height))
        foot = self.sprite_foot_y * SCALE * squash_y * tell_y
        surface.blit(big, (int(self.body.center_x - width * 0.5) - ox,
                           int(self.body.bottom - foot) - oy))

        if self.state is EnemyState.TELL:
            self._draw_tell_bar(surface, ox, oy)

    def _draw_tell_bar(self, surface: pygame.Surface, ox: int, oy: int) -> None:
        rect = self.body.rect.move(-ox, -oy)
        width = max(3, int(20 * self.tell_progress))
        surface.fill(self.tell_colour(),
                     (rect.centerx - width // 2, rect.top - 7, width, 2))

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"hamle {self.move}  sira {self.move_index}  "
            f"cagrilan {self.summoned}"]
