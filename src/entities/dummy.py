"""Antrenman kuklasi - Faz 1 dovus testi icin.

Hareketsiz, saldirmayan hedef. Tek isi vurus geri bildirimini gostermek:
sendeleme, flas, geri itme, olum ve **kill cancel**.

Bu kukla gecici degil - dovus degerleri ayarlanirken hep gerekecek. Ama gercek
dusman AI'si Gorev 2'de yazilacak; burada davranis yok, bilerek.

Kuklada can bari **var** (nisan tahtasi oldugu icin); gercek dusmanlarda
olmayacak - durum sendeleme, renk ve hizla okunur (docs/derinlestirme.md 4.4).
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import Team
from src.entities.actor import Actor

RESPAWN_FRAMES = 90         # Olduktan sonra kendini toparlar - test akmasin
BAR_WIDTH = 20
BAR_HEIGHT = 3


class TrainingDummy(Actor):
    team = Team.ENEMY
    body_width = 14
    body_height = 24
    max_health = 60
    poise = 3
    iframes_on_hit = 0          # Combo kesilmesin

    sprite_name = "shambler"

    def __init__(self, scene, x: float, y: float,
                 max_health: int | None = None) -> None:
        if max_health is not None:
            self.max_health = max_health
        super().__init__(scene, x, y)
        self.respawn_frames = 0
        self.home_x = self.body.x
        self.hits_taken = 0

        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y

    def take_damage(self, box, direction):
        result = super().take_damage(box, direction)
        if result.hit:
            self.hits_taken += 1
        return result

    def die(self) -> None:
        super().die()
        self.respawn_frames = RESPAWN_FRAMES
        self.scene.on_enemy_died(self)

    def update(self) -> None:
        if self.dead:
            self._update_dead()
            return

        if self.iframes > 0:
            self.iframes -= 1
        if self.stagger_frames > 0:
            self.stagger_frames -= 1
        self.flash.update()
        self.squash.update()

        # Sendelerken surtunme dusuk - geri itme okunur kalsin.
        friction = 0.08 if self.stagger_frames > 0 else 0.35
        self.body.approach_vx(0.0, friction)
        self.body.apply_gravity()
        self.body.move(self.scene.tilemap)
        self._update_animation()

    def _update_dead(self) -> None:
        self.flash.update()
        self.squash.update()
        self.body.approach_vx(0.0, 0.25)
        self.body.apply_gravity()
        self.body.move(self.scene.tilemap)
        self._update_animation()

        self.respawn_frames -= 1
        if self.respawn_frames <= 0:
            self._respawn()

    def _respawn(self) -> None:
        self.dead = False
        self.health = self.max_health
        self.poise_left = self.poise
        self.stagger_frames = 0
        self.hits_taken = 0
        self.body.x = self.home_x
        self.body.vx = self.body.vy = 0.0

    # --- Cizim --------------------------------------------------------------
    def _update_animation(self) -> None:
        if self.dead:
            self.animator.play("death")
        elif self.stagger_frames > 0:
            self.animator.play("hurt")
        else:
            self.animator.play("idle")
        self.animator.update()

    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        ox, oy = offset
        rect = self.body.rect.move(-ox, -oy)

        if self.scene.game.box_mode:
            self._draw_box(surface, rect)
        else:
            image = self.animator.render(
                self.facing,
                flash=self.flash.active,
                squash=self.squash.current,
                silhouette_mode=self.scene.game.silhouette_mode,
                # Sendeleyen dusman tehlike rengiyle parlar: durum renkle
                # ve siluetle birlikte okunur (renk korlugu icin sart).
                tint_colour=(palette.role("enemy_tell")
                             if self.stagger_frames > 0 and not self.flash.active
                             else None),
            )
            if image is None:
                self._draw_box(surface, rect)
            else:
                foot = self.sprite_foot_y * self.squash.current[1]
                surface.blit(image, (
                    int(self.body.center_x - image.get_width() * 0.5) - ox,
                    int(self.body.bottom - foot) - oy))

        if not self.dead:
            self._draw_health_bar(surface, rect)

    def _draw_box(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        scale_x, scale_y = self.squash.current
        if scale_x != 1.0 or scale_y != 1.0:
            width = max(2, int(rect.width * scale_x))
            height = max(2, int(rect.height * scale_y))
            rect = pygame.Rect(rect.centerx - width // 2,
                               rect.bottom - height, width, height)
        surface.fill(self._colour(), rect)
        pygame.draw.rect(surface, palette.outline(), rect, 1)

    def _colour(self):
        if self.dead:
            return palette.color("ink_soft")
        if self.flash.active:
            return palette.role("hit_flash")
        if self.stagger_frames > 0:
            return palette.color("danger")
        # Can azaldikca koyulasir - bar olmadan da durum okunabilsin diye.
        return (palette.color("blood") if self.health_ratio < 0.4
                else palette.color("blood_bright"))

    def _draw_health_bar(self, surface: pygame.Surface,
                         rect: pygame.Rect) -> None:
        x = rect.centerx - BAR_WIDTH // 2
        y = rect.top - 6
        surface.fill(palette.color("ink"), (x, y, BAR_WIDTH, BAR_HEIGHT))
        filled = int(BAR_WIDTH * self.health_ratio)
        if filled > 0:
            surface.fill(palette.color("blood_bright"),
                         (x, y, filled, BAR_HEIGHT))
        pygame.draw.rect(surface, palette.outline(),
                         (x, y, BAR_WIDTH, BAR_HEIGHT), 1)
