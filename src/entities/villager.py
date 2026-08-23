"""Koylu - Bolum 1'in koyunu yasayan bir yer yapan pasif NPC.

Arda'nin istegi (23.08.2026): *"ilk basta etrafta koyluler dolasabilir.
Olaylar patlak verdiginde koyluler evlerine kacsin."*

Bu bir dekor detayindan fazlasi. Prologun butun anlatimi "sakin koy →
yarik aciliyor → Cemo cekiliyor" uzerine kurulu; koy hic yasamiyorsa
kaybedilen sey de soyut kaliyor. Koyluler kacinca oyuncu **kaybi
cevresinde** goruyor, sadece Cemo'da degil.

## Uc durum, tek yon

    WANDER   iki nokta arasinda agir agir gider gelir, arada durur
    FLEE     en yakin evine kosar (panik - normalden hizli)
    INSIDE   eve girdi, artik cizilmiyor

Gecis **tek yonlu**: kacan koylu geri donmez. Yarik kapansa bile koy bir
daha dolmaz - kaybin kalici oldugunu mekanin kendisi soyluyor.

## `Actor`'dan turemiyor

`candle_keeper.py` ile ayni gerekce: can, hasar, durum makinesi
gereksiz. Vurus icinden gecer, hicbir sey olmaz - sahne onu hitbox hedefi
olarak hic eklemiyor. Yercekimi de yok; koyluler duz zeminde yuruyor ve
zeminin nerede oldugunu dogduklari yerden biliyorlar.

## `random` yok

Her koylunun ritmi kendi `seed`'inden turuyor (`cave_backdrop`'un
deterministik hash+sinus deseniyle ayni ruh). Ayni sahne her acilista
ayni sekilde yasiyor - kare kare degisen bir koy "gurultu" gibi okunur.
"""
from __future__ import annotations

import math

import pygame

from src.art.animator import Animator

WANDER = "wander"
FLEE = "flee"
INSIDE = "inside"

# Hizlar (piksel/kare). Kacis gezinmenin ~3 kati - panik okunur olmali.
WANDER_SPEED = 0.22
FLEE_SPEED = 0.72
# Gezinme yaricapi: dogdugu noktadan bu kadar uzaga gider.
WANDER_RANGE = 26.0
# Kapiya bu kadar yaklasinca iceri girmis sayilir.
DOOR_REACH = 6.0
# Kacmadan once bu kadar kare donup bakar - "ne oldu?" ani. Hepsi ayni
# karede donup kacsaydi bir suru gibi okunurdu; kademeli tepki panigi
# gercek yapiyor.
STARTLE_FRAMES = 18


class Villager:
    """Koyde dolasan, tehlike aninda evine kacan pasif NPC."""

    __slots__ = ("home_x", "x", "feet_y", "door_x", "state", "facing",
                 "frame", "seed", "animator", "sprite_foot_y", "startle")

    def __init__(self, x: float, feet_y: float, door_x: float,
                 seed: int = 0) -> None:
        from src.art.animation import CHARACTERS
        self.home_x = x
        self.x = x
        self.feet_y = feet_y
        self.door_x = door_x          # Kacinca gidecegi kapi
        self.state = WANDER
        self.facing = 1
        self.frame = 0
        self.seed = seed
        self.startle = 0
        self.animator = Animator("villager")
        self.animator.play("idle")
        self.sprite_foot_y = CHARACTERS["villager"].foot_y

    # --- Sorgular -----------------------------------------------------------
    @property
    def gone(self) -> bool:
        return self.state == INSIDE

    @property
    def _wander_phase(self) -> float:
        """Kendi ritmi. Her koylu farkli hizda gider gelir."""
        period = 260.0 + (self.seed % 7) * 40.0
        return (self.frame + self.seed * 37) / period * math.tau

    # --- Denetim ------------------------------------------------------------
    def flee(self) -> None:
        """Tehlike! Kisa bir irkilmeden sonra eve kosar."""
        if self.state == WANDER:
            self.state = FLEE
            # Irkilme suresi koyluye gore degisiyor - hepsi ayni karede
            # donmesin (bkz. STARTLE_FRAMES).
            self.startle = STARTLE_FRAMES + (self.seed % 5) * 6

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        if self.state == INSIDE:
            return
        self.frame += 1
        if self.state == WANDER:
            self._update_wander()
        else:
            self._update_flee()
        self.animator.update()

    def _update_wander(self) -> None:
        target = self.home_x + math.sin(self._wander_phase) * WANDER_RANGE
        delta = target - self.x
        if abs(delta) < 0.6:
            # Ucta bekliyor - surekli yurumek "devriye" gibi okunur,
            # duraklamalar "yasiyor" gibi.
            self.animator.play("idle")
            return
        step = math.copysign(min(WANDER_SPEED, abs(delta)), delta)
        self.x += step
        self.facing = 1 if step > 0 else -1
        self.animator.play("run" if abs(step) > 0.18 else "idle")

    def _update_flee(self) -> None:
        if self.startle > 0:
            # Donup bakiyor: hedefe yuzunu cevirir ama daha kosmaz.
            self.startle -= 1
            self.facing = 1 if self.door_x > self.x else -1
            self.animator.play("idle")
            return
        delta = self.door_x - self.x
        if abs(delta) <= DOOR_REACH:
            self.state = INSIDE
            return
        step = math.copysign(FLEE_SPEED, delta)
        self.x += step
        self.facing = 1 if step > 0 else -1
        self.animator.play("run")

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        if self.state == INSIDE:
            return
        image = self.animator.render(self.facing)
        if image is None:
            return
        ox, oy = offset
        surface.blit(image,
                     (int(self.x - image.get_width() * 0.5) - ox,
                      int(self.feet_y - self.sprite_foot_y) - oy))
