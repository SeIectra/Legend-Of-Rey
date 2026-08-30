"""Bolunen - Katman 3'un ucuncu ve son uyesi.

`docs/gdd.md` 7: *"Bolunen - vurunca ikiye ayrilir; **combo sana karsi
calisir**."*

## Ucuncu ihanet: kendi becerin

    Sessiz       Yanki gostermiyor     -> arac eksik
    Yankilayan   Yanki yaniltiyor      -> arac kirli
    Bolunen      COMBO cogaltiyor      -> **beceri** aleyhine

Ilk ikisi yardimci sisteme saldiriyordu. Bu, oyuncunun on iki bolumdur
ogrendigi seye saldiriyor: zincir kurmak. Her vurus bir dusman daha
yapiyor, yani "daha iyi oynamak" daha kotu sonuc veriyor.

Katman 1 combo kurmayi ogretti, Katman 2 combo'nun kirilabilecegini,
Katman 3 combo'nun **yanlis olabilecegini**.

## Cozum: bitirici vurus

Bolunme **her** vurusta degil; son bolunmeden sonra parca artik
bolunmuyor (`SPLITTER_GENERATIONS`). Ve bitirici vurus
(`is_finisher`) bolunmeyi atlıyor - yani zinciri **tamamlamak**
cozum, yarida birakmak degil.

Bu ayrim dersi tersine ceviriyor: "combo yapma" degil, "combo'yu
bitir". Aksi halde oyuncu dovusmekten kacinirdi ve bir dusman
oyuncuyu oynamamaya itmemeli.

## Nesil ve boyut

Her nesil yariya iniyor: can, boyut, hasar. Ucuncu nesil (dort kucuk
parca) tek vurusla oluyor, yani kalabalık bir temizlik islemi degil
kisa bir final.
"""
from __future__ import annotations

import pygame

from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.config import (
    SPLITTER_ACTIVE_FRAMES, SPLITTER_DAMAGE, SPLITTER_GENERATIONS,
    SPLITTER_HEALTH, SPLITTER_POISE, SPLITTER_REACH, SPLITTER_RECOVER_FRAMES,
    SPLITTER_SPEED, SPLITTER_SPLIT_PUSH, SPLITTER_TELL_FRAMES,
)
from src.entities.enemies.shambler import Shambler


class Splitter(Shambler):
    """Vurdukca cogalan sey."""

    sprite_name = "splitter"
    max_health = SPLITTER_HEALTH
    poise = SPLITTER_POISE
    move_speed = SPLITTER_SPEED
    contact_range = SPLITTER_REACH
    tell_frames = SPLITTER_TELL_FRAMES
    active_frames = SPLITTER_ACTIVE_FRAMES
    recover_frames = SPLITTER_RECOVER_FRAMES
    damage = SPLITTER_DAMAGE
    body_colour = "bile"
    silhouette_scale = 1.0

    def __init__(self, scene, x: float, y: float,
                 generation: int = 0) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.generation = generation
        # Her nesil yariya iniyor.
        scale = 0.5 ** generation
        self.max_health = max(6, int(SPLITTER_HEALTH * scale))
        self.health = self.max_health
        self.damage = max(3, int(SPLITTER_DAMAGE * scale))
        self.silhouette_scale = max(0.55, 1.0 - generation * 0.2)

    @property
    def can_split(self) -> bool:
        return self.generation < SPLITTER_GENERATIONS

    def take_damage(self, box, direction):
        result = super().take_damage(box, direction)
        if not result.hit or not self.can_split:
            return result
        # **Bitirici bolmuyor.** Ders "combo yapma" degil "combo'yu
        # bitir" - gerekce modul basliginda.
        if getattr(box, "is_finisher", False):
            return result
        if result.killed:
            return result
        self._split(direction)
        return result

    def _split(self, direction) -> None:
        """Iki parcaya ayriliyor - biri saga, biri sola.

        Yeni parcalar **uyanik** doguyor: bolunmenin bedeli aninda
        hissedilmeli, yoksa oyuncu farki bir sonraki odada anlar.
        """
        scene = self.scene
        if scene is None or len(scene.enemies) > 24:
            # Ust sinir: bir oyuncu bir dusmani sonsuza kadar
            # vurabiliyor ve ekranda yuzlerce parca birikmemeli.
            return
        dx = 1.0 if direction[0] >= 0 else -1.0
        for side in (dx, -dx):
            child = Splitter(scene, self.body.center_x + side * 10,
                             self.body.feet[1],
                             generation=self.generation + 1)
            child.aware = True
            child.body.vx = side * SPLITTER_SPLIT_PUSH
            child.body.vy = -1.4
            scene.enemies.append(child)
        # Ana govde yok oluyor - iki parca onun yerine geciyor.
        self.health = 0
        self.die()
        scene.particles.burst(self.body.center_x, self.body.center_y, 12,
                              # "blood" bir parcacik YOLU; "rot" bir golge
                              # zinciri ve `PARTICLE_PATHS`te yok.
                              path="blood",
                              speed=(0.6, 2.0))
        on_split = getattr(scene, "on_splitter_split", None)
        if on_split:
            on_split(self)
