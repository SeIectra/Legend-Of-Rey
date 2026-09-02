"""Yankilayan - Katman 3'un ikinci uyesi.

`docs/gdd.md` 7: *"Yankilayan - **sesini taklit eder, sahte ipucu
verir**."*

## Ikinci ihanet: kirlilik

Sessiz bir **eksiklik**ti (Yanki gostermiyor). Yankilayan bir
**kirlilik**: Yanki gosteriyor ama gosterdigi sey yalan.

Bolum 10 ve 11'de yalan soyleyen Yanki'nin kendisiydi. Burada yalani
soyleyen **baska bir sey** ve Rey'in sesiyle konusuyor. Twist'ten
(B14: *"Yanki lanet degil, asagidaki seyin sesi"*) sonra bu geriye
donuk anlam kazaniyor: bunlar o sesin cocuklari.

## Sahte ipucu bir HITBOX degil

Yankilayan hasar vermek icin yalan soylemiyor; **yanlis yere
baktirmak** icin soyluyor. Sahte isaret bos bir noktayi ya da bir
tuzagi gosteriyor, oyuncu oraya gidiyor, o sirada gercek tehdit
arkasindan geliyor.

Sahne kancasi (`on_false_hint`) isaretin nereye konuldugunu
bildiriyor; bolum onu kendi diliyle ciziyor. Dusmanin arayuze
dogrudan yazmasi katmanlari karistirirdi.

## Isareti **susturmak** mumkun

Yankilayan olunce sahte isaretleri de siliniyor. Yani cozum yine
"once onu sustur" - Okcu'nun ogrettigi hedef secme dersi burada bir
kez daha, ama bu sefer bilgi icin.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.config import (
    ECHOING_ACTIVE_FRAMES, ECHOING_DAMAGE, ECHOING_HEALTH, ECHOING_HINT_LIFE,
    ECHOING_HINT_RANGE, ECHOING_POISE, ECHOING_REACH, ECHOING_RECOVER_FRAMES,
    ECHOING_SPEED, ECHOING_TELL_FRAMES,
)
from src.entities.enemy import Enemy, EnemyState
from src.entities.enemies.shambler import Shambler


class Echoing(Shambler):
    """Rey'in sesiyle konusan sey."""

    sprite_name = "echoing"
    max_health = ECHOING_HEALTH
    poise = ECHOING_POISE
    move_speed = ECHOING_SPEED
    contact_range = ECHOING_REACH
    tell_frames = ECHOING_TELL_FRAMES
    active_frames = ECHOING_ACTIVE_FRAMES
    recover_frames = ECHOING_RECOVER_FRAMES
    damage = ECHOING_DAMAGE
    body_colour = "echo_dark"
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
        # Su an ekranda duran sahte isaret: (x, y, kalan_kare).
        self.false_hint: tuple[float, float, int] | None = None
        self.hint_cooldown = 0

    # --- Sahte ipucu ---------------------------------------------------------
    def update(self) -> None:
        super().update()
        if self.dead:
            # **Oldu, yalani da olsun.** "Once onu sustur" cozumunun
            # gorunur karsiligi bu: isaret kaybolunca oyuncu neyin
            # sahte oldugunu anliyor.
            self.false_hint = None
            return
        if self.hint_cooldown > 0:
            self.hint_cooldown -= 1
        if self.false_hint is not None:
            x, y, life = self.false_hint
            self.false_hint = (x, y, life - 1) if life > 1 else None
        elif self.aware and self.hint_cooldown <= 0:
            self._plant_hint()

    def _plant_hint(self) -> None:
        """Sahte isareti **kendi arkasina** koyuyor.

        Yon onemli: isaret oyuncuyu Yankilayan'in otesine cagirmali,
        yani oyuncu ona giderken yaninden gecmek zorunda. Onune
        konsaydi isaret bir uyari islevi gorurdu - tam tersi.
        """
        player = self.player
        if player is None:
            return
        away = 1 if self.body.center_x > player.body.center_x else -1
        self.false_hint = (self.body.center_x + away * ECHOING_HINT_RANGE,
                           self.body.center_y, ECHOING_HINT_LIFE)
        self.hint_cooldown = ECHOING_HINT_LIFE * 2
        on_hint = getattr(self.scene, "on_false_hint", None)
        if on_hint:
            on_hint(self, self.false_hint[0], self.false_hint[1])

    # --- Cizim ---------------------------------------------------------------
    def draw_extra(self, surface: pygame.Surface, offset) -> None:
        """Sahte isaret - **Yanki'nin isaretiyle ayni gorunuyor.**

        Bir bolumdur kirilabilir duvarlari gosteren camgobegi parilti.
        Ayni renk, ayni nabiz. Farkli cizseydik oyuncu ilk bakista
        ayirt eder ve yalan hicbir sey ifade etmezdi.

        Ayirt etmenin tek yolu **kaynagi**: bu parilti bir duvarda
        degil boslukta duruyor, ve yakininda bir Yankilayan var.
        """
        if self.false_hint is None:
            return
        ox, oy = offset
        x, y, life = self.false_hint
        # **Taban genligi asmamali.** `0.45 + 0.55*sin` araligi
        # -0.10..1.00 - yani nabzin dibinde carpan NEGATIF oluyor ve
        # `surface.fill` "invalid color" diye patliyor. Parlaklik bir
        # carpan oldugu icin taban >= genlik olmak zorunda.
        pulse = 0.55 + 0.45 * math.sin(self.frames * 0.09)
        fade = min(1.0, life / 30.0)
        colour = tuple(int(c * pulse * fade)
                       for c in palette.color("echo_bright"))
        px, py = int(x) - ox, int(y) - oy
        for index in range(4):
            surface.fill(colour, (px + index * 4 - 6, py + 6 - index, 2, 2))
        surface.fill(colour, (px - 7, py - 4, 14, 1))
