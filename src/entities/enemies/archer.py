"""Okcu - Katman 2'nin ucuncu uyesi.

`docs/gdd.md` 7: *"Okcu - uzaktan bozar, **once susturulmali**."*

## Katman 2'nin ucuncu dilbilgisi

    Kalkanli   yonle sordu    - arkaya gec
    Mizrakli   mesafeyle      - menzilinin disindan vuruyor
    Okcu       **zamanla**    - sen baskasiyla dovusurken vuruyor

Ucu de "combo'yu kir" diyor. Okcu'nun ozelligi tek basina neredeyse
zararsiz olmasi: tehdit **oldugu yer degil, oldugu an**. Yakin
dovusun ortasinda gelen bir ok zinciri kiriyor.

"Once susturulmali" cumlesi buradan geliyor: oyuncu once ona
kosmali, sonra otekilerle ugrasmali - yani **hedef secme** ogretiliyor.

## Ok bir hitbox

Ayri bir `Projectile` sinifi yazilmadi: bir ok zaten "belirli
karelerde aktif bir hasar hacmi", yani tam olarak bir hitbox. Tek
eksigi hareketti ve `Hitbox.velocity` onu ekledi (`combat/hitbox.py`).

Kazanc: carpisma, `already_hit`, `pierce`, `on_hit` kancasi ve game
feel'in tamami bedavaya geliyor.

## Yakinda **kacar**, dovusmez

Okcu bir yakin dovusucu degil. Oyuncu yaklasinca geri cekiliyor ve
menzile giremezse ok atamiyor - yani "ona kos" cozumu gercekten
calisiyor. Kosede sikisirsa carpisiyor ama zayif.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import Hitbox, Team
from src.config import (
    ARCHER_ACTIVE_FRAMES, ARCHER_ARROW_DAMAGE, ARCHER_ARROW_LIFE,
    ARCHER_ARROW_SPEED, ARCHER_DAMAGE, ARCHER_FLEE_RANGE, ARCHER_FLEE_SPEED,
    ARCHER_HEALTH, ARCHER_POISE, ARCHER_REACH, ARCHER_RECOVER_FRAMES,
    ARCHER_SHOT_RANGE, ARCHER_SPEED, ARCHER_TELL_FRAMES,
)
from src.entities.enemy import Enemy, EnemyState


class Archer(Enemy):
    """Uzaktan atar, yaklasani birakip kacar."""

    sprite_name = "archer"
    max_health = ARCHER_HEALTH
    poise = ARCHER_POISE
    move_speed = ARCHER_SPEED
    contact_range = ARCHER_SHOT_RANGE       # "temas" = atis menzili
    tell_frames = ARCHER_TELL_FRAMES
    active_frames = ARCHER_ACTIVE_FRAMES
    recover_frames = ARCHER_RECOVER_FRAMES
    damage = ARCHER_DAMAGE
    body_colour = "moss"
    silhouette_scale = 1.0

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        # Yay gerginligi (0..1) - cizim bunu okuyor.
        self.draw_tension = 0.0

    # --- Mesafe --------------------------------------------------------------
    def _too_close(self) -> bool:
        player = self.player
        if player is None:
            return False
        return self.distance_to(player) < ARCHER_FLEE_RANGE

    def _approach(self) -> None:
        """Yaklasandan **kaciyor** - `Enemy._approach` eziliyor.

        Taban sinif temas menziline girene kadar yaklasiyor. Okcu oyle
        davransaydi "once susturulmali" cumlesi anlamsiz olurdu: oyuncu
        zaten ona kosmaya calisiyor, o da kosarsa bir yakin dovus
        dusmani olurdu.
        """
        player = self.player
        if player is None:
            return
        if self._too_close():
            self._face_player()
            self.body.approach_vx(-self.facing * ARCHER_FLEE_SPEED, 0.3)
            return
        super()._approach()

    def _think(self) -> None:
        # Yay gerginligi tell ilerlemesinden turuyor - ayri sayac
        # tutmak iki kaynak demekti.
        if self.state is EnemyState.TELL:
            self.draw_tension = self.tell_progress
        elif self.state is EnemyState.ATTACK:
            self.draw_tension = 0.0
        else:
            self.draw_tension *= 0.85
        super()._think()

    def _spawn_attack(self) -> None:
        """Ok firlatiyor - **hareketli** hitbox.

        Dikey nisan yok: ok duz gidiyor. Bir yay parabolu daha "gercek"
        olurdu ve daha kotu - oyuncunun okun nereye gidecegini bir
        bakista bilmesi gerekiyor, yoksa kacinma bir tahmine doner.
        """
        vx = ARCHER_ARROW_SPEED * self.facing
        rect = pygame.Rect(0, 0, 10, 4)
        rect.center = (int(self.body.center_x + self.facing * 10),
                       int(self.body.center_y))
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, targets=Team.PLAYER, damage=ARCHER_ARROW_DAMAGE,
            owner=self, active_frames=ARCHER_ARROW_LIFE,
            velocity=(vx, 0.0), stop_on_solid=True,
            knockback=1.2, knockback_up=0.4))
        self.scene.game.play_sound("swing_light")

    # --- Cizim ---------------------------------------------------------------
    def draw_extra(self, surface: pygame.Surface, offset) -> None:
        """Yay - gerginligi **gorunur**.

        Tell suresi uzun (`CLAUDE.md` 7: en az 14 kare) ama bir sure
        tek basina okunmaz; yayin gerilmesi o sureyi goze cevirıyor.
        """
        ox, oy = offset
        x = int(self.body.center_x) - ox + self.facing * 6
        y = int(self.body.center_y) - oy
        pull = int(self.draw_tension * 4)
        surface.fill(palette.color("earth_dark"), (x, y - 6, 2, 12))
        # Kiris geriye cekiliyor.
        string_x = x - self.facing * pull
        for step in range(-5, 6):
            offset_x = int(abs(step) * 0.4 * self.facing)
            surface.fill(palette.color("stone_light"),
                         (string_x + offset_x, y + step, 1, 1))
        if self.draw_tension > 0.55:
            # Ok gorunuyor - "birazdan atacak" bilgisi.
            surface.fill(palette.color("danger_bright"),
                         (string_x, y - 1, self.facing * 8, 2))
