"""Bolum 5 "Sular" dogrulamasi - su bulmacasi GERCEKTEN cozulebiliyor mu.

`tools/reachability.py` bu bolumun yalnizca **kuru** halini dogrulayabilir:
BFS suyu bilmiyor ve ust kata yuzerek cikiliyor. Yuzme yolunu bir BFS
modeline zorlamak denendi ve yaniltici cikti (yuzmek "yuzeyde yurumek"
degil, su hacminde yukselmek). O yuzden su yolu burada **gercek fizikle**
sinaniyor: oyuncu vanaya basiyor, su yukseliyor, yuzuyor, ust kata
cikiyor.

Korunan kurallar:

  * Bulmaca **cozulebilir**: dort adim gercekten calisiyor
  * Bulmaca **atlanamaz**: su yuksekken savak kapali, cikisa gidilemiyor
  * Su fizigi: batinca kaldirma var, cikinca kendiliginden geri donuyor
  * Suda dusman YOK (bolumun sorusu dovus degil)

Calistir:
    python tests/test_chapter05.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((64, 64))

from src.config import TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.scenes.chapter05 import Chapter05Scene  # noqa: E402
from src.world.rooms.chapter05 import (  # noqa: E402
    LEVEL, SLUICE_ROWS, SLUICE_TILE_COLUMN, UPPER_FLOOR_ROW, VALVE_HIGH_TILE,
    VALVE_LOW_TILE, WATER_HIGH, WATER_LOW,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def step(game, scene, count: int = 1, keys=()) -> None:
    for _ in range(count):
        game.input.begin_frame()
        for key in keys:
            game.input.handle_event(
                pygame.event.Event(pygame.KEYDOWN, key=key))
        game.input.end_frame()
        scene.update()
        for key in keys:
            game.input.begin_frame()
            game.input.handle_event(
                pygame.event.Event(pygame.KEYUP, key=key))
            game.input.end_frame()


def stand_at_valve(scene, tile) -> None:
    """Oyuncuyu vananin yanina koyar - govdesi bos tile'da olmali.

    DEVIR 6/20: govdesi kati tile ile cakisan aktor tamamen donuyor.
    Bu proje ayni sinif hataya uc kez dustu, biri de bir TESTIN kendi
    yerlesimiydi.
    """
    scene.player.body.set_feet(tile[0] * TILE_SIZE + TILE_SIZE * 0.5,
                               (tile[1] + 1) * TILE_SIZE)
    scene.player.body.vx = scene.player.body.vy = 0.0


def main() -> int:
    game = Game()
    game.scenes.set_root(Chapter05Scene, transition=False, character="rey")
    game.scenes._flush()
    scene = game.scenes.current

    # --- 1. Baslangic durumu ------------------------------------------------
    print("--- baslangic ---")
    check(abs(scene.water.level - WATER_LOW) < 1.0,
          "su bastan ALCAK - oyuncu once kuru hali goruyor",
          f"{scene.water.level:.0f}")
    check(scene.sluice_open, "savak bastan ACIK (su alcak)")
    check(scene.player.water_ratio == 0.0, "oyuncu suda degil")

    # --- 2. Dusman suyun ulasmadigi yerde -----------------------------------
    # Su bir BULMACA, dovus alani degil. Suda dovusmek hem okunmaz
    # (kaldirma kuvveti kacinmayi bozar) hem bolumun sorusunu bogar.
    print("\n--- dusman sudan uzak ---")
    enemy_columns = [spot.tile_x for spot in LEVEL.of("shambler")]
    check(bool(enemy_columns), "bolumde dusman var", str(len(enemy_columns)))
    check(all(column < SLUICE_TILE_COLUMN for column in enemy_columns),
          "dusmanlarin hepsi su odasindan ONCE", str(enemy_columns))

    # --- 3. Vana suyu YUKSELTIYOR -------------------------------------------
    print("\n--- vana 1: su yukseliyor ---")
    stand_at_valve(scene, VALVE_LOW_TILE)
    step(game, scene, 6)
    check(scene._valve_near() >= 0, "oyuncu vananin menzilinde",
          str(scene._valve_near()))
    step(game, scene, 4, keys=(pygame.K_e,))
    check(scene.valves_turned >= 1, "vana cevrildi",
          str(scene.valves_turned))
    check(scene.water.rising or scene.water.target < WATER_LOW,
          "su YUKSELMEYE basladi",
          f"hedef {scene.water.target:.0f} < {WATER_LOW}")

    for _ in range(600):
        step(game, scene)
        if not scene.water.moving:
            break
    check(abs(scene.water.level - WATER_HIGH) < 2.0,
          "su en yuksek seviyeye ulasti",
          f"{scene.water.level:.0f} ~ {WATER_HIGH}")

    # --- 4. Su yuksekken savak KAPALI - bulmaca atlanamaz -------------------
    print("\n--- su yuksek: savak kapali ---")
    check(not scene.sluice_open, "savak kapandi")
    check(all(scene.tilemap.is_solid(SLUICE_TILE_COLUMN, row)
              for row in SLUICE_ROWS),
          "savagin butun satirlari kati - cikisa gidilemiyor")

    # --- 5. Oyuncu YUZEREK ust kata cikiyor ---------------------------------
    # Bulmacanin can alici adimi. `reachability.py` bunu dogrulayamaz.
    print("\n--- yuzerek ust kata ---")
    # **Rota onemli**: platformun TAM ALTINDAN duz yukari yuzulemez -
    # oyuncu alt yuzeye carpar. Gercek yol aciklikta yukselip sonra saga
    # gecmek. Ilk surumde test oyuncuyu vananin altina koymustu ve
    # "bulmaca cozulemiyor" diyordu; hata bulmacada degil TESTTEYDI.
    open_column = SLUICE_TILE_COLUMN + 2      # platformun solunda, acik su
    scene.player.body.set_feet(open_column * TILE_SIZE, 13 * TILE_SIZE)
    step(game, scene, 5)
    start_y = scene.player.body.y
    check(scene.player.water_ratio > 0.5, "oyuncu suyun icinde",
          f"{scene.player.water_ratio:.2f}")

    # Once yuzeye kadar yuz, sonra saga dogru platforma yuru.
    upper_y = (UPPER_FLOOR_ROW + 1) * TILE_SIZE
    for _ in range(600):
        step(game, scene, keys=(pygame.K_SPACE,))
        if scene.player.body.bottom <= upper_y:
            break
    surfaced_y = scene.player.body.y
    check(surfaced_y < start_y - TILE_SIZE * 3,
          "yuzerek belirgin sekilde yukseldi",
          f"y {start_y:.0f} -> {surfaced_y:.0f}")

    reached = False
    for _ in range(600):
        step(game, scene, keys=(pygame.K_SPACE, pygame.K_RIGHT))
        if (scene.player.body.bottom <= upper_y + 2
                and scene.player.body.center_x
                > VALVE_HIGH_TILE[0] * TILE_SIZE - TILE_SIZE * 4):
            reached = True
            break
    check(reached, "YUZEREK ust kata cikildi - bulmaca cozulebilir",
          f"y {start_y:.0f} -> {scene.player.body.y:.0f}")

    # --- 6. Vana 2 suyu INDIRIYOR -------------------------------------------
    print("\n--- vana 2: su iniyor ---")
    stand_at_valve(scene, VALVE_HIGH_TILE)
    step(game, scene, 60)          # bekleme suresi dolsun
    step(game, scene, 4, keys=(pygame.K_e,))
    check(scene.water.target > WATER_HIGH,
          "su INMEYE basladi", f"hedef {scene.water.target:.0f}")
    for _ in range(900):
        step(game, scene)
        if not scene.water.moving:
            break
    check(abs(scene.water.level - WATER_LOW) < 2.0,
          "su en alt seviyeye indi", f"{scene.water.level:.0f}")

    # --- 7. Savak acildi - cikis yolu var -----------------------------------
    print("\n--- su alcak: savak acildi ---")
    check(scene.sluice_open, "savak yeniden acildi")
    check(all(not scene.tilemap.is_solid(SLUICE_TILE_COLUMN, row)
              for row in SLUICE_ROWS),
          "savagin butun satirlari acik - cikisa gidilebilir")

    # --- 8. Su fizigi kendiliginden geri donuyor ----------------------------
    # Sudan cikan govde ayri bir "cikti" yolu olmadan eski davranisina
    # donmeli - yoksa bir kez suya giren oyuncu sonsuza dek hafif kalirdi.
    print("\n--- sudan cikinca fizik geri donuyor ---")
    scene.player.body.set_feet(VALVE_LOW_TILE[0] * TILE_SIZE, 13 * TILE_SIZE)
    step(game, scene, 5)
    in_water_scale = scene.player.body.gravity_scale
    scene.water.set_target(WATER_LOW)
    scene.water.level = WATER_LOW
    scene.player.body.set_feet(VALVE_LOW_TILE[0] * TILE_SIZE, 8 * TILE_SIZE)
    step(game, scene, 3)
    check(scene.player.body.gravity_scale == 1.0,
          "sudan cikinca yercekimi normale dondu",
          f"{in_water_scale:.2f} -> {scene.player.body.gravity_scale:.2f}")

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Bolum 5 su bulmacasi cozulebilir ve atlanamaz.")
    return 0


raise SystemExit(main())
