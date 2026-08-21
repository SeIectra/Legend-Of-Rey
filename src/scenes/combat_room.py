"""Dovus test odasi.

Duz zemin, birkac platform, uc antrenman kuklasi. Dovus degerleri ayarlanirken
hep gerekecek bir tezgah.

F4 ile kutu kipine gecip "kutularla eglenceli mi?" sorusunu sorabilirsin
(GOREVLER Gorev 1 ve 5).

Bu sahne ayni zamanda **game feel'in tek gecis noktasi**dir: `on_hit()` burada
hitstop, sarsinti ve parcacigi ayni karede tetikler.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.particles import ParticleField
from src.combat.hitbox import HitboxManager, Team
from src.config import (
    COMBO_THRESHOLD_HIGH, COMBO_THRESHOLD_MID, INTERNAL_HEIGHT, INTERNAL_WIDTH,
    TILE_SIZE,
)
from src.core.camera import Camera
from src.core.input import Action
from src.core.juice import ImpactEvent, ImpactWeight, Juice
from src.core.scene import Scene
from src.entities.dummy import TrainingDummy
from src.entities.character_stats import ARDO, REY
from src.entities.player import Player
from src.systems.save import read_save
from src.ui import text
from src.ui.hud import HUD
from src.world.tilemap import TileMap

# Test odasi: duz zemin + birkac platform. Icerik degil, tezgah.
ROOM_ROWS: list[str] = [
    "##############################################",
    "##..........................................##",
    "##..........................................##",
    "##..........................................##",
    "##........====................====..........##",
    "##..........................................##",
    "##..........................................##",
    "##..====..........................====......##",
    "##..........................................##",
    "##..........................................##",
    "##..........................................##",
    "##..........................................##",
    "##..........................................##",
    "##############################################",
    "##############################################",
]

SPAWN_TILE = (6, 12)
DUMMY_TILES = ((16, 12), (26, 12), (36, 12))
HUD_MARGIN = 6


class CombatRoomScene(Scene):
    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.tilemap = TileMap(ROOM_ROWS)
        self.camera = Camera()
        self.camera.set_bounds(self.tilemap.bounds)

        self.particles = ParticleField()
        self.juice = Juice(self.game, spawn_particles=self._emit_particles)
        # Ekran sarsintisi ayarlardan gelir - erisilebilirlik icin kapatilabilir.
        shake = float(self.game.settings.get("screen_shake", 1.0))
        self.juice.configure(shake_enabled=shake > 0.0, shake_scale=shake)
        self.hitboxes = HitboxManager(on_hit=self.on_hit)

        self.save_data, _ = read_save()
        self.hud = HUD(self.game)

        stats = ARDO if character == "ardo" else REY
        spawn_x = SPAWN_TILE[0] * TILE_SIZE + TILE_SIZE // 2
        spawn_y = (SPAWN_TILE[1] + 1) * TILE_SIZE
        self.player = Player(self, spawn_x, spawn_y, stats)

        self.enemies: list[TrainingDummy] = [
            TrainingDummy(self, tx * TILE_SIZE + TILE_SIZE // 2,
                          (ty + 1) * TILE_SIZE)
            for tx, ty in DUMMY_TILES
        ]

        self.camera.snap_to(self.player.body.center_x, self.player.body.center_y)
        self.toast = ""
        self.toast_frames = 0
        self.total_hits = 0

    # --- Dongu --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if self.game.input.pressed(Action.PAUSE):
            from src.ui.pause import PauseScene
            self.scenes.push(PauseScene, save_data=self.save_data)
        elif event.key == pygame.K_r:
            self.on_enter()          # Odayi sifirla

    def update(self) -> None:
        self.player.update()
        for enemy in self.enemies:
            enemy.update()

        self.hitboxes.update({
            Team.ENEMY: self.enemies,
            Team.PLAYER: [self.player],
        })

        self.particles.update()
        self.juice.update()
        self.camera.shake_offset = self.juice.shake.offset
        self.camera.update(self.player.body.center_x,
                           self.player.body.center_y - 6,
                           facing=self.player.facing,
                           grounded=self.player.body.grounded)

        gold = self.save_data.gold if self.save_data else 0
        echo = self.save_data.echo_tier if self.save_data else 2
        self.hud.update(self.player, gold, echo)

        if self.toast_frames > 0:
            self.toast_frames -= 1

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("abyss_dark"))
        offset = self.camera.offset

        self.tilemap.draw(surface, offset)
        for enemy in self.enemies:
            enemy.draw(surface, offset)
        self.player.draw(surface, offset)
        self.particles.draw(surface, offset)

        if self.game.debug_overlay:
            self._draw_hitboxes(surface, offset)
        self._draw_hud(surface)

    # --- Game feel kancalari ------------------------------------------------
    def on_hit(self, box, target, result, direction) -> None:
        """Bir vurus degdi. **Ucu birden tek cagridan** - kare kaymasi olmasin."""
        weight = ImpactWeight.NORMAL
        if result.killed:
            weight = ImpactWeight.KILL
        elif box.is_finisher:
            weight = ImpactWeight.FINISHER

        self.juice.on_hit(
            ImpactEvent(
                x=target.body.center_x,
                y=target.body.center_y,
                direction=direction,
                weight=weight,
                particle_path="violet" if box.is_counter else "blood",
                particle_count=10 if box.is_finisher else 6,
            ),
            target_flash=target.flash,
            target_squash=target.squash,
        )

        if box.owner is self.player:
            self.total_hits += 1
            self.player.register_hit()
            if box.is_counter:
                self.show_toast("KARŞI VURUŞ")
            if result.killed:
                # Kill cancel: recovery aninda kesilir, akis surer.
                self.player.notify_kill()

    def on_enemy_died(self, enemy) -> None:
        self.juice.explosion(enemy.body.center_x, enemy.body.center_y,
                             ImpactWeight.FINISHER)
        self.particles.burst(enemy.body.center_x, enemy.body.center_y, 16,
                             path="blood", speed=(1.0, 3.0))

    def on_combo_threshold(self, player, threshold: int) -> None:
        if threshold >= COMBO_THRESHOLD_HIGH:
            self.show_toast(f"{threshold} COMBO · Yankı iyileşir")
        elif threshold >= COMBO_THRESHOLD_MID:
            self.show_toast(f"{threshold} COMBO · can yenilenir")
        else:
            self.show_toast(f"{threshold} COMBO")

    def on_combo_reset(self) -> None: ...

    def on_player_attack(self, player, index: int) -> None: ...

    def on_attack_swing(self, player, box) -> None: ...

    def on_player_jump(self, player) -> None:
        self.particles.burst(player.body.feet[0], player.body.feet[1], 4,
                             direction=(0.0, -1.0), path="dust",
                             speed=(0.3, 0.9), life=(8, 16), gravity=0.04)

    def on_player_land(self, player, air_frames: int) -> None:
        self.particles.burst(player.body.feet[0], player.body.feet[1], 6,
                             direction=(0.0, -1.0), path="dust",
                             speed=(0.4, 1.2), life=(10, 20), gravity=0.05)

    def on_player_dodge(self, player) -> None:
        self.particles.burst(player.body.center_x, player.body.feet[1], 8,
                             direction=(-player.facing, 0.0), path="dust",
                             speed=(0.5, 1.6), life=(10, 22), gravity=0.03)

    def on_dodge_trail(self, player) -> None:
        if player.dodge.frames_left % 3 == 0:
            self.particles.burst(player.body.center_x, player.body.center_y, 1,
                                 direction=(-player.facing, 0.0), path="echo",
                                 speed=(0.1, 0.4), life=(8, 14), gravity=0.0)

    def on_player_hurt(self, player, result) -> None:
        self.show_toast("HASAR")

    def on_player_died(self, player) -> None:
        self.show_toast("ÖLDÜN · R ile sıfırla")

    def _emit_particles(self, event: ImpactEvent) -> None:
        self.particles.burst(event.x, event.y, event.particle_count,
                             direction=event.direction, path=event.particle_path)

    def show_toast(self, message: str, frames: int = 72) -> None:
        self.toast = message
        self.toast_frames = frames

    # --- Cizim yardimcilari -------------------------------------------------
    def _draw_hitboxes(self, surface: pygame.Surface,
                       offset: tuple[int, int]) -> None:
        ox, oy = offset
        for box in self.hitboxes.boxes:
            pygame.draw.rect(surface, palette.color("danger_bright"),
                             box.rect.move(-ox, -oy), 1)
        for actor in [self.player, *self.enemies]:
            pygame.draw.rect(surface, palette.color("echo"),
                             actor.hurtbox.move(-ox, -oy), 1)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        # Asamali aciga cikarma: bilgi yalnizca ilgili oldugunda gorunur.
        gold = self.save_data.gold if self.save_data else 0
        echo = self.save_data.echo_tier if self.save_data else 2
        self.hud.draw(surface, self.player, gold, echo)

        if self.toast_frames > 0:
            text.draw(surface, self.toast, INTERNAL_WIDTH // 2, 42,
                      color=palette.color("violet_bright"), align="center",
                      outline=True)

        text.draw(surface,
                  "Yön · Boşluk zıpla · J saldır · Shift kaçın · Esc menü",
                  INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 12,
                  color=palette.role("ui_text_dim"), align="center")

    def debug_lines(self) -> list[str]:
        return [
            *self.player.debug_lines(),
            f"hitbox {self.hitboxes.active_count}  "
            f"parçacık {self.particles.alive_count}  "
            f"sarsıntı {self.juice.shake.frames_left}",
            f"toplam vuruş {self.total_hits}",
        ]
