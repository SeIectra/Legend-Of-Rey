"""Mizrakli - Katman 2'nin ikinci uyesi, Bolum 10'da geliyor.

`docs/gdd.md` 7 Katman 2'nin sorusu: **combo'yu KIRMAYI ogren.**

Kalkanli o soruyu **yonle** soruyordu: onden vurma, arkaya gec.
Mizrakli **mesafeyle** soruyor: senin menzilinin disindan vuruyor.

## Kalkanli'nin tersi ve bu bilincli

    Kalkanli   yaklas ve DOGRU YERE vur
    Mizrakli   yaklasmadan vuramazsin ama yaklasirsan vurulursun

Ayni ders (zincir bedava degil), iki farkli fizik sorusu. Ucuncusu
(Okcu) menzili tamamen kapatacak, dordunculeyse (Komutan) otekileri
yonetecek - Katman 2'nin dort uyesi ayni cumleyi dort ayri dilbilgisiyle
soyluyor.

## Iki gecerli cevap

1. **Kacinmayla iceri gir.** Mizrak uzun ama **dar**: saldiri
   penceresi disinda govdesi savunmasiz. `SPEARMAN_RECOVER_FRAMES`
   (34) tam olarak iceri girip iki vurus yapacak kadar uzun.
2. **Geri cekilip mizragi bosa harcat.** Saldiri baslarken oyuncu
   menzilden cikarsa mizrak havayi doverek toparlanma penceresine
   giriyor - "yemleme" cozumu, Kalkanli'daki gibi.

## Neden geri cekiliyor

`Enemy._approach` temas menziline girene kadar yaklasiyor. Mizrakli
onu **ezmek zorunda**: oyuncuya yapisirsa uzun menzili anlamsizlasir ve
sıradan bir dusman olur. `_keep_distance()` oyuncu cok yaklasinca geri
adim attiriyor - ve bu geri adim onun tek zayifligi, cunku geri
giderken saldiramiyor.

## Mizrak vurusu **iterek** geliyor

`SPEARMAN_PUSHBACK` oyuncuyu geri savuruyor. Hasarin kendisi orta
(`SPEARMAN_DAMAGE`); asil ceza konumun kaybi - kapatmak icin
harcadigin mesafeyi geri veriyorsun. Ceza can degil **mesafe**, tipki
Kalkanli'nin cezasinin can degil ritim olmasi gibi.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.animator import Animator
from src.art.animation import CHARACTERS
from src.combat.hitbox import Hitbox, Team
from src.config import (
    SPEARMAN_ACTIVE_FRAMES, SPEARMAN_BACKSTEP_SPEED, SPEARMAN_DAMAGE,
    SPEARMAN_HEALTH, SPEARMAN_MIN_RANGE, SPEARMAN_POISE, SPEARMAN_PUSHBACK,
    SPEARMAN_REACH, SPEARMAN_RECOVER_FRAMES, SPEARMAN_SPEED,
    SPEARMAN_TELL_FRAMES,
)
from src.entities.enemy import Enemy, EnemyState


class Spearman(Enemy):
    """Uzun menzil, kisa sabir. Yaklasani iter."""

    sprite_name = "spearman"
    max_health = SPEARMAN_HEALTH
    poise = SPEARMAN_POISE
    move_speed = SPEARMAN_SPEED
    contact_range = SPEARMAN_REACH
    tell_frames = SPEARMAN_TELL_FRAMES
    active_frames = SPEARMAN_ACTIVE_FRAMES
    recover_frames = SPEARMAN_RECOVER_FRAMES
    damage = SPEARMAN_DAMAGE
    body_colour = "stone"
    # NOT: burada bir `silhouette_scale = 1.0` alani vardi ve
    # `Enemy.silhouette_scale()` **metodunu** goelgeliyordu. Sonuc:
    # `enemy_render` onu cagirinca `TypeError`, yani dusman ekrana
    # girdigi an oyun cokuyordu - ve cokmeseydi bile tell sirasindaki
    # siluet sismesi olurdu, ki o `CLAUDE.md` 10'un renk korlugu
    # garantisi: *"tehlike asla sadece renkle anlatilmaz"*.

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        # Mizragin uzanma orani (0..1) - cizim bunu okuyor.
        self.thrust = 0.0

    # --- Mesafe --------------------------------------------------------------
    def _too_close(self) -> bool:
        player = self.player
        if player is None:
            return False
        return self.distance_to(player) < SPEARMAN_MIN_RANGE

    def _keep_distance(self) -> None:
        """Oyuncu cok yaklasti - geri adim.

        **Saldiramadan** geri gidiyor: uzun menzilin bedeli bu.
        Oyuncunun kazanma yolu tam olarak burasi.
        """
        self._face_player()
        self.body.approach_vx(-self.facing * SPEARMAN_BACKSTEP_SPEED, 0.3)

    def _approach(self) -> None:
        """`Enemy._approach` **eziliyor**: yapismak yerine mesafe tutuyor.

        Taban sinif temas menziline girene kadar yaklasiyor; Mizrakli
        oyle davransaydi uzun menzili hicbir sey ifade etmezdi.
        """
        player = self.player
        if player is None:
            return
        if self._too_close():
            self._keep_distance()
            return
        super()._approach()

    def _think(self) -> None:
        # Mizragin uzanmasi saldiri ilerlemesinden turuyor - ayri bir
        # sayac tutmak iki kaynak demekti ve biri kayardi.
        if self.state is EnemyState.TELL:
            self.thrust = -0.25 * self.tell_progress          # geri cekilis
        elif self.state is EnemyState.ATTACK:
            self.thrust = 1.0
        elif self.state is EnemyState.RECOVER:
            left = max(0.0, 1.0 - self.state_frames / max(1, self.recover_frames))
            self.thrust = left
        else:
            self.thrust *= 0.8
        super()._think()

    def _spawn_attack(self) -> None:
        """Mizrak vurusu - uzun ve **dar**.

        Yuksekligi bilerek kisa (10 piksel): ziplayarak ustunden
        gecilebiliyor. Uzun menzilin bir de dikey cevabi olmali, yoksa
        tek cozum kacinma olurdu.
        """
        reach = SPEARMAN_REACH + 14
        rect = pygame.Rect(0, 0, reach, 10)
        if self.facing > 0:
            rect.midleft = (int(self.body.center_x), int(self.body.center_y))
        else:
            rect.midright = (int(self.body.center_x), int(self.body.center_y))
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, team=Team.ENEMY, damage=self.damage,
            owner=self, frames=self.active_frames,
            knockback=SPEARMAN_PUSHBACK))

    # --- Cizim ---------------------------------------------------------------
    def draw_extra(self, surface: pygame.Surface, offset) -> None:
        """Mizragin kendisi.

        Sprite'ta yok (`spearman` genel bir insansi govde) - silah
        burada, uzanma oranina gore ciziliyor. Ayni yol Bolum 3'un
        tasinan mesalesinde de kullanildi: az piksel, dogru bilgi.
        """
        ox, oy = offset
        base_x = int(self.body.center_x) - ox
        y = int(self.body.center_y) - oy
        length = int((SPEARMAN_REACH + 12) * max(0.0, self.thrust))
        if length <= 0:
            return
        x0 = base_x + (2 if self.facing > 0 else -2 - length)
        surface.fill(palette.color("earth_dark"), (x0, y, length, 2))
        # Ucu: tehlike rengi. `CLAUDE.md` 10 - tehlike yalnizca renkle
        # degil sekille de: uc, sapdan daha kalin.
        tip_x = x0 + length - 3 if self.facing > 0 else x0
        tone = ("danger_bright" if self.state is EnemyState.ATTACK
                else "stone_light")
        surface.fill(palette.color(tone), (tip_x, y - 1, 3, 4))
