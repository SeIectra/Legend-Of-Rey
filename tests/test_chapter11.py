"""Bolum 11 "Ayna Salonu" - isin, ayna, ve Yanki'nin surekli yalani.

`docs/yapi.md` B11: *"Golge yaratiklar sadece isikta olur. Aynalari
cevirerek isini yaratiklara yonlendir. Yanki sana yalan soyluyor
olabilir - hangi aynanin dogru oldugunu kendin bulmalisin."*

Korunan kurallar:

  * **Isin isiktan yapiliyor.** `LightState`'e kaynak yaziyor, yani
    `ShadowShambler` (Bolum 3) hicbir degisiklik olmadan calisiyor.
    Biri ayri bir "isin" tipi yazmaya kalkarsa bu test kirilsin.
  * **Ayna cevirmek yolu degistiriyor** ve isin duvarda duruyor.
  * **Baslangic cozum DEGIL**, dogru yapilandirma cozum.
  * **Yanki zaten dogru olan aynayi isaretliyor** - yalanin bicimi bu.
  * **Dongu cokmuyor**: iki ayna karsi karsiya gelebilir.
  * Golge yaratigi karanlikta dokunulmaz, isikta degil.

Calistir:
    python tests/test_chapter11.py
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

pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.config import TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.scenes.chapter11 import Chapter11Scene  # noqa: E402
from src.systems import beam, loyalty  # noqa: E402
from src.systems.beam import BACKSLASH, RIGHT, SLASH, Mirror  # noqa: E402
from src.systems.save import SaveData, write_save  # noqa: E402
from src.world.rooms.chapter11 import (  # noqa: E402
    HALL_DOOR_ROWS, HALL_DOOR_TILE, HALL_EMITTER_TILE, HALL_MIRROR_TILES,
    HALL_RECEIVER_TILE, LEVEL, LIE_INDEX, ROOM_STARTS,
)
from src.world.tilemap import TileMap  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def start(game, character: str = "rey", flags=None) -> Chapter11Scene:
    write_save(SaveData(chapter=11, character=character,
                        abilities=["sword", "dodge", "echo_sight"],
                        flags=flags or {}))
    game.scenes.set_root(Chapter11Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter11Scene)
    return scene


# --- 1. Isin izleme ----------------------------------------------------------
def test_trace() -> None:
    print("\n--- isin ---")
    rows = ["############"] + ["#..........#"] * 6 + ["############"]
    tilemap = TileMap(rows)

    straight = beam.trace(tilemap, [], (1, 3), RIGHT)
    check(straight.tiles[-1] == (10, 3),
          "isin duvara kadar gidiyor ve DURUYOR", str(straight.tiles[-1]))
    check(not straight.bounces, "aynasiz yansima yok")

    mirror = Mirror(6, 3, SLASH)
    turned = beam.trace(tilemap, [mirror], (1, 3), RIGHT)
    after = [t for t in turned.tiles if t[0] == 6 and t[1] != 3]
    check(all(y < 3 for _x, y in after), "'/' sagdan geleni YUKARI ceviriyor",
          str(after))
    mirror.rotate()
    flipped = beam.trace(tilemap, [mirror], (1, 3), RIGHT)
    after = [t for t in flipped.tiles if t[0] == 6 and t[1] != 3]
    check(all(y > 3 for _x, y in after), "cevrilince ASAGI", str(after))

    # Dongu: iki ayna karsi karsiya. Cokmemeli.
    loop = beam.trace(tilemap, [Mirror(4, 3, SLASH), Mirror(8, 3, BACKSLASH)],
                      (1, 3), RIGHT)
    check(len(loop.tiles) < beam.MAX_STEPS + 5,
          "dongu cokmuyor, kesiliyor", f"{len(loop.tiles)} adim")


# --- 2. Isin ISIK yaziyor ----------------------------------------------------
def test_beam_is_light() -> None:
    print("\n--- isin = isik ---")
    game = Game()
    try:
        scene = start(game)
        hall = scene.paths[1]
        check(hall.tiles, "salon isini var")
        x, y = hall.tiles[len(hall.tiles) // 2]
        check(scene.light.in_light(x * TILE_SIZE + 8, y * TILE_SIZE + 8),
              "isinin uzerindeki nokta ISIKLI - `in_light` degismedi")
        # Isin disinda karanlik.
        check(not scene.light.in_light(x * TILE_SIZE + 8,
                                       (y + 5) * TILE_SIZE + 8),
              "isinin disi karanlik")

        # Ayna cevrilince ESKI yol karanliga donmeli.
        old = hall.tiles[-1]
        scene.hall_mirrors[0].rotate()
        scene._trace_beams()
        moved = old not in scene.paths[1].tiles
        if moved:
            check(not scene.light.in_light(old[0] * TILE_SIZE + 8,
                                           old[1] * TILE_SIZE + 8),
                  "eski yol karanliga donuyor - bayat kaynak kalmiyor")
        else:
            check(True, "eski yol karanliga donuyor", "yol degismedi, atlandi")
    finally:
        game.shutdown()


# --- 3. Bulmaca ---------------------------------------------------------------
def test_puzzle() -> None:
    print("\n--- bulmaca ---")
    game = Game()
    try:
        scene = start(game)
        check(not scene.solved, "baslangic COZUM DEGIL")
        check(scene.tilemap.is_solid(HALL_DOOR_TILE, HALL_DOOR_ROWS.start),
              "kapi kapali")

        for mirror, (_x, _y, _start, correct) in zip(scene.hall_mirrors,
                                                     HALL_MIRROR_TILES):
            mirror.kind = correct
        scene._trace_beams()
        check(scene.solved, "dogru yapilandirma cozuyor")
        check(HALL_RECEIVER_TILE in scene.paths[1].tiles,
              "isin aliciya variyor")
        check(not scene.tilemap.is_solid(HALL_DOOR_TILE, HALL_DOOR_ROWS.start),
              "kapi aciliyor")
    finally:
        game.shutdown()


# --- 4. Yalan ----------------------------------------------------------------
def test_lie() -> None:
    print("\n--- yalan ---")
    # Yanki'nin isaretledigi ayna ZATEN dogru olmali: yalanin bicimi
    # "dogru olani boz" - en zarif bicim, cunku sonrasinda oyuncu butun
    # zinciri yeniden dusunmek zorunda kaliyor.
    _x, _y, start_kind, correct = HALL_MIRROR_TILES[LIE_INDEX]
    check(start_kind == correct,
          "Yanki ZATEN DOGRU olan aynayi isaretliyor",
          f"baslangic {start_kind!r} == dogru {correct!r}")

    others = [(s, c) for i, (_a, _b, s, c) in enumerate(HALL_MIRROR_TILES)
              if i != LIE_INDEX]
    check(all(s != c for s, c in others),
          "oteki aynalar gercekten cevrilmeli", str(others))

    game = Game()
    try:
        # Bolum 10'da Yanki'yi dinlememis oyuncu supheli.
        scene = start(game, flags={loyalty.SETTINGS_KEY: -2})
        column = dict(ROOM_STARTS)["salon"]
        scene.player.body.set_feet(column * TILE_SIZE + 20, 13 * TILE_SIZE)
        scene.update_scene()
        check(scene.lie_told, "salonda Yanki konusuyor")
        check(scene.doubt_told,
              "guvenmeyen oyuncu kendi supheyle uyariliyor")
    finally:
        game.shutdown()

    game = Game()
    try:
        scene = start(game, flags={loyalty.SETTINGS_KEY: 3})
        column = dict(ROOM_STARTS)["salon"]
        scene.player.body.set_feet(column * TILE_SIZE + 20, 13 * TILE_SIZE)
        scene.update_scene()
        check(scene.lie_told and not scene.doubt_told,
              "GUVENEN oyuncuya suphe replikleri gelmiyor")
    finally:
        game.shutdown()


# --- 5. Golge yaratigi -------------------------------------------------------
def test_shadow() -> None:
    print("\n--- golge yaratigi ---")
    game = Game()
    try:
        scene = start(game)
        from src.combat.hitbox import Hitbox, Team
        from src.entities.enemies.shadow_shambler import ShadowShambler
        # Karanlikta bir yaratik.
        creature = ShadowShambler(scene, 40.0, 13 * TILE_SIZE)
        box = Hitbox(rect=pygame.Rect(0, 0, 20, 20), damage=10,
                     owner=scene.player, targets=Team.ENEMY)
        box.rect.center = (int(creature.body.center_x),
                           int(creature.body.center_y))
        before = creature.health
        result = creature.take_damage(box, (1.0, 0.0))
        check(not result.hit and creature.health == before,
              "karanlikta DOKUNULMAZ")
        check(creature.shrugged_off == 1,
              "bosa vurus isaretleniyor - sahne kurali soyleyebilsin")

        # Isiga sok.
        scene.light.set_static("test", creature.body.center_x,
                               creature.body.center_y, 30.0)
        result = creature.take_damage(box, (1.0, 0.0))
        check(result.hit and creature.health < before,
              "isikta hasar aliyor", f"{before} -> {creature.health}")
    finally:
        game.shutdown()


# --- 6. Bolum sonu -----------------------------------------------------------
def test_chapter_end() -> None:
    print("\n--- bolum sonu ---")
    game = Game()
    try:
        scene = start(game)
        check(scene.chapter_number == 11, "bolum numarasi 11")
        check(scene.companion is None, "hala yalniz - Bolum 10'dan beri")
        exit_at = LEVEL.first("exit")
        scene.player.body.x = float(exit_at.x + 4)
        scene._check_exit()
        check(scene.finished, "cikista bolum bitiyor")
        check(scene.save_data.chapter == 11, "kayda bolum 11 yaziliyor")
    finally:
        game.shutdown()


def main() -> int:
    print("=== BOLUM 11: AYNA SALONU ===")
    test_trace()
    test_beam_is_light()
    test_puzzle()
    test_lie()
    test_shadow()
    test_chapter_end()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("Ayna Salonu: isin isiktan, yalan dogruyu bozmaya davet ediyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
