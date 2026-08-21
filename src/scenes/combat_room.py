"""Dovus test odasi - tezgah, bolum degil.

Duz zemin, uc kat platform, alti dusman. Dovus degerleri ayarlanirken hep
gerekecek. `F4` ile kutu kipine gecip "kutularla eglenceli mi?" sorusunu
sorabilirsin (GOREVLER Gorev 1 ve 5).

Butun game feel baglantisi `PlayScene`'de - burada yalnizca sahne kuruluyor.
"""
from __future__ import annotations

import pygame

from src.config import TILE_SIZE
from src.entities.dummy import TrainingDummy
from src.entities.enemies.bloated import Bloated
from src.entities.enemies.climber import Climber
from src.entities.enemies.shambler import Shambler
from src.scenes.play import PlayScene
from src.ui import text
from src.ui.i18n import t
from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.world.tilemap import TileMap

ROOM_ROWS: list[str] = [
    # Her basilabilir kat bir oncekinden **en fazla 3 tile** yukarida:
    # olculmus ziplama zarfi bu (MAX_JUMP_HEIGHT_TILES, tools/measure_jump.py).
    # Ilk halinde ust platformlar zeminden 6 tile yukaridaydi ve hicbir
    # sekilde cikilamiyordu; biri de tavanin dibindeydi, uzerinde
    # durulamiyordu bile. tools/reachability.py yakaladi.
    "##############################################",   # 0
    "##..........................................##",   # 1
    "##......##########..........................##",   # 2  tavan - tirmananlar
    "##..........................................##",   # 3
    "##..........................................##",   # 4
    "##..........................................##",   # 5
    "##..........................................##",   # 6
    "##................####......####............##",   # 7  ust kat  (10'dan +3)
    "##..........................................##",   # 8
    "##..........................................##",   # 9
    "##............####..............####........##",   # 10 orta kat (13'ten +3)
    "##..........................................##",   # 11
    "##..........................................##",   # 12
    "##############################################",   # 13 zemin
    "##############################################",   # 14
]

SPAWN_TILE = (6, 12)

# Antrenman kuklalari saginda, gercek dusmanlar solunda: ikisi de ayni odada
# denenebilsin. Kuklalar karsilik vermez, dusmanlar verir.
DUMMY_TILES = ((40, 12),)

# Alti dusman - "kalabalik okunabilir mi?" sinavi bu (GOREVLER Gorev 2).
# Hepsi gorus menzili icinde (ENEMY_SIGHT_RANGE = 170px ~ 10 tile). Once
# odaya yaymistim ve alti dusmanin ancak ikisi oyuncuyu goruyordu - yani
# "kalabalik okunabilir mi?" sorusu hic sorulmamis oluyordu. Tezgahin isi
# o soruyu sormak.
SHAMBLER_TILES = ((12, 12), (15, 12), (18, 12))
CLIMBER_TILES = ((7, 3), (10, 3), (13, 3))       # Tavan seridinin altinda
BLOATED_TILES = ((22, 12), (25, 12))
HUD_MARGIN = 6




class CombatRoomScene(PlayScene):
    def setup(self) -> None:
        self.tilemap = TileMap(ROOM_ROWS)
        self.player = self.make_player(
            SPAWN_TILE[0] * TILE_SIZE + TILE_SIZE // 2,
            (SPAWN_TILE[1] + 1) * TILE_SIZE)

        def place(cls, tiles):
            return [cls(self, tx * TILE_SIZE + TILE_SIZE // 2,
                        (ty + 1) * TILE_SIZE) for tx, ty in tiles]

        self.enemies = [
            *place(Shambler, SHAMBLER_TILES),
            *place(Climber, CLIMBER_TILES),
            *place(Bloated, BLOATED_TILES),
            *place(TrainingDummy, DUMMY_TILES),
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.on_enter(character=self.character)   # Odayi sifirla
            return
        super().handle_event(event)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        text.draw(surface, t("combat.controls"),
                  INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 12,
                  color=palette.role("ui_text_dim"), align="center")
