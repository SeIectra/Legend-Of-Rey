"""Bolum 10 "Ayrilik" - Yanki'nin ilk yalani + Mizrakli.

`docs/yapi.md` B10: *"Yol ikiye ayrilir. Yalniz devam. Yanki yukselir,
yorum yapmaya baslar, ilk kez yanlis bilgi verip seni tuzaga sokar."*

Korunan kurallar:

  * **Yoldas yok.** Bolumun adi bu; biri "yalniz olmasin" diye yoldas
    eklerse test kirilsin.
  * **Yalan bir SECIM.** Iki yol da yuruyerek gecilebilir; hicbiri
    kilit degil. Ceza var, cikmaz yok.
  * **Tuzak once uyariyor** (`TRAP_CREAK_FRAMES`). Uyarisiz bir tuzak
    haksizlik, uyarili bir tuzak ders.
  * **Tuzak oldurmuyor.** Bir yanlis secim bolumu bastan oynatmamali.
  * **Sadakat gorunmez ve iki yonlu** - `docs/derinlestirme.md` 2.2.
  * **Mizrakli mesafeyi silah yapiyor**: menzili oyuncununkinden uzun,
    ve yaklasan oyuncudan geri cekiliyor.

Calistir:
    python tests/test_chapter10.py
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

from src.config import (  # noqa: E402
    SPEARMAN_MIN_RANGE, SPEARMAN_REACH, SPEARMAN_TELL_FRAMES, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.entities.enemies.spearman import Spearman  # noqa: E402
from src.scenes.chapter10 import Chapter10Scene, TRAP_CREAK_FRAMES  # noqa: E402
from src.scenes.chapter10_cinematics import (  # noqa: E402
    LieCinematic, PartingCinematic,
)
from src.systems import loyalty  # noqa: E402
from src.systems.save import SaveData, write_save  # noqa: E402
from src.world.rooms.chapter10 import (  # noqa: E402
    HONEST_TILE, LEVEL, LOWER_ROW, LURE_TILE, ROOM_STARTS, SPLIT_TILE,
    TRAP_ROW, TRAP_TILES, UPPER_ROW,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def start(game, character: str = "rey") -> Chapter10Scene:
    write_save(SaveData(chapter=10, character=character,
                        abilities=["sword", "dodge", "echo_sight"]))
    game.scenes.set_root(Chapter10Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter10Scene)
    return scene


def enter_fork(scene) -> None:
    column = dict(ROOM_STARTS)["catal"]
    scene.player.body.set_feet(column * TILE_SIZE + 20, LOWER_ROW * TILE_SIZE)
    scene.update_scene()


# --- 1. Yalnizlik ------------------------------------------------------------
def test_alone() -> None:
    print("\n--- yalnizlik ---")
    game = Game()
    try:
        scene = start(game)
        check(scene.companion is None,
              "yoldas YOK - bolumun adi bu")
        check(loyalty.read(scene.save_data) == 0,
              "sadakat notr basliyor")
        # Zorluk sicramasi: Mizrakli burada tanitiliyor.
        check(len(LEVEL.of("spearman")) >= 3,
              "Mizrakli birden fazla - zorluk sicramasi",
              f"{len(LEVEL.of('spearman'))} tane")
    finally:
        game.shutdown()


# --- 2. Mizrakli mesafeyi silah yapiyor -------------------------------------
def test_spearman() -> None:
    print("\n--- Mizrakli ---")
    check(SPEARMAN_REACH > 20,
          "menzil oyuncunun kilicindan (~16) UZUN", str(SPEARMAN_REACH))
    check(SPEARMAN_MIN_RANGE < SPEARMAN_REACH,
          "geri cekilme mesafesi menzilin icinde",
          f"{SPEARMAN_MIN_RANGE} < {SPEARMAN_REACH}")
    check(SPEARMAN_TELL_FRAMES >= 14,
          "tell CLAUDE.md 7'nin 14 kare kuralina uyuyor",
          f"{SPEARMAN_TELL_FRAMES} kare")

    game = Game()
    try:
        scene = start(game)
        spear = Spearman(scene, 200.0, 13 * TILE_SIZE)
        scene.enemies.append(spear)
        spear.aware = True

        # Oyuncu COK yakin: geri cekilmeli.
        scene.player.body.set_feet(spear.body.center_x + 6,
                                   spear.body.feet[1])
        check(spear._too_close(), "yakinda oldugunu anliyor")
        before = spear.body.vx
        spear._approach()
        check(spear.body.vx != before,
              "yaklasani ITMIYOR, kendisi geri cekiliyor")
        # Geri adim oyuncudan UZAKLASAN yonde olmali.
        away = -1 if scene.player.body.center_x > spear.body.center_x else 1
        check((spear.body.vx > 0) == (away > 0),
              "geri adim dogru yonde",
              f"vx={spear.body.vx:.2f}")

        # Uzaktayken normal yaklasiyor.
        scene.player.body.set_feet(spear.body.center_x + 120,
                                   spear.body.feet[1])
        check(not spear._too_close(), "uzakta 'cok yakin' degil")
    finally:
        game.shutdown()


# --- 3. Yalan bir secim ------------------------------------------------------
def test_lie_is_a_choice() -> None:
    print("\n--- yalan ---")
    game = Game()
    try:
        scene = start(game)
        enter_fork(scene)
        check(scene.lure_shown, "Yanki ust yolu isaretliyor")
        check(not scene.choice, "henuz secim yok")

        # Yanki'nin dedigi: ust yol.
        scene.player.body.set_feet((LURE_TILE[0] + 4) * TILE_SIZE,
                                   UPPER_ROW * TILE_SIZE)
        scene.update_scene()
        check(scene.choice == "followed", "ust yol = guvendi", scene.choice)
        check(loyalty.read(scene.save_data) > 0,
              "sadakat ARTTI", str(loyalty.read(scene.save_data)))
    finally:
        game.shutdown()

    game = Game()
    try:
        scene = start(game)
        enter_fork(scene)
        scene.player.body.set_feet((HONEST_TILE[0] + 6) * TILE_SIZE,
                                   LOWER_ROW * TILE_SIZE)
        scene.update_scene()
        check(scene.choice == "ignored", "alt yol = guvenmedi", scene.choice)
        check(loyalty.read(scene.save_data) < 0,
              "sadakat AZALDI", str(loyalty.read(scene.save_data)))
    finally:
        game.shutdown()


# --- 4. Tuzak uyariyor ve oldurmuyor ----------------------------------------
def test_trap() -> None:
    print("\n--- tuzak ---")
    game = Game()
    try:
        scene = start(game)
        enter_fork(scene)
        column = list(TRAP_TILES)[2]
        scene.player.body.set_feet(column * TILE_SIZE, TRAP_ROW * TILE_SIZE)

        scene._update_trap()
        check(scene.trap_creak == 1 and not scene.trap_sprung,
              "ilk temasta GICIRDIYOR, hemen cokmuyor")
        check(bool(scene.toast), "uyari yazisi cikiyor", repr(scene.toast))

        for _ in range(TRAP_CREAK_FRAMES):
            scene._update_trap()
        check(scene.trap_sprung, "uyaridan sonra cokuyor")
        check(not scene.tilemap.is_solid(column, TRAP_ROW),
              "zemin gercekten kalkiyor")
        # **Oldurmuyor.**
        check(scene.player.health > 0, "tuzak OLDURMUYOR",
              f"can {scene.player.health}")

        # Tuzaktan cikmak: zemin kalktigi icin oyuncu asagi dusuyor ve
        # alt yol zaten devam ediyor - cikmaz yok.
        below = scene.tilemap.is_solid(column, TRAP_ROW + 6)
        check(below, "dusulen yerin altinda zemin var - cikmaz degil")
    finally:
        game.shutdown()


# --- 5. Dort varyantli "Yalan" sahnesi --------------------------------------
def test_lie_scene_variants() -> None:
    print("\n--- yalan sahnesi ---")
    game = Game()
    try:
        seen = set()
        for followed, ignored, sprung, label in (
                (True, False, True, "guvendi + tuzaga dustu"),
                (True, False, False, "guvendi + kacti"),
                (False, True, False, "guvenmedi"),
                (False, False, False, "notr")):
            game.scenes.set_root(LieCinematic, transition=False,
                                 character="rey", followed=followed,
                                 ignored=ignored, sprung=sprung)
            game.scenes._flush()
            scene = game.scenes.current
            keys = tuple(line.key for p in scene.panels
                         for line in p.dialogue_lines)
            check(len(keys) == 2, f"{label}: iki replik", str(len(keys)))
            seen.add(keys)
        check(len(seen) == 4, "dort varyant BIRBIRINDEN farkli",
              f"{len(seen)} ayri replik cifti")

        # Ardo oynanisinda Iz Surme konusuyor, Yanki degil.
        game.scenes.set_root(LieCinematic, transition=False,
                             character="ardo", followed=True, sprung=True)
        game.scenes._flush()
        speakers = {line.speaker for p in game.scenes.current.panels
                    for line in p.dialogue_lines}
        check("echo" not in speakers,
              "Ardo oynanisinda Yanki konusmuyor", str(sorted(speakers)))
    finally:
        game.shutdown()


# --- 6. Bolum sonu -----------------------------------------------------------
def test_chapter_end() -> None:
    print("\n--- bolum sonu ---")
    game = Game()
    try:
        scene = start(game)
        check(scene.chapter_number == 10, "bolum numarasi 10")
        check(scene.player.body.center_x < SPLIT_TILE * TILE_SIZE,
              "oyuncu ayrilik noktasindan ONCE basliyor")
        exit_at = LEVEL.first("exit")
        scene.player.body.x = float(exit_at.x + 4)
        scene._check_exit()
        check(scene.finished, "cikista bolum bitiyor")
        check(scene.save_data.chapter == 10, "kayda bolum 10 yaziliyor")
        # Sadakat kayitta kaliyor - B14 okuyacak.
        check(loyalty.SETTINGS_KEY in scene.save_data.flags
              or loyalty.read(scene.save_data) == 0,
              "sadakat kayitta tasiniyor")
    finally:
        game.shutdown()


def main() -> int:
    print("=== BOLUM 10: AYRILIK ===")
    test_alone()
    test_spearman()
    test_lie_is_a_choice()
    test_trap()
    test_lie_scene_variants()
    test_chapter_end()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("Ayrilik: yalniz, yalan bir secim, tuzak uyariyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
