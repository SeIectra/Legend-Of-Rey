"""Ziplama zarfini olcer - bolum tasariminin siniri.

"Su platforma erisilebiliyor mu?" sorusunun cevabi burada. Matematik yaklasik
sonuc verir; sabit kare adimi, apex hafifligi ve piksel piksel carpisma cozumu
bir araya gelince gercek deger kayar. Bu yuzden **olcuyoruz, tahmin etmiyoruz.**

Cikti dogrudan `src/config.py` icindeki iki degeri besler:
    MAX_JUMP_GAP_TILES      azami ucurum genisligi
    MAX_JUMP_HEIGHT_TILES   basilabilir satirlar arasi azami dikey adim

`PLAYER_JUMP_SPEED` ya da `PLAYER_RUN_SPEED` degistiginde **once burayi
calistir**, sonra o sabitleri guncelle, sonra bolumleri yeniden dogrula.
Prototipte bu adim atlandigi icin bir bolumun cikis kapisina ulasilamiyordu.

Kullanim:
    python tools/measure_jump.py
"""
from __future__ import annotations

import os

# Depo kokunu import yoluna ekle - arac dogrudan calistirilabilsin.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from src.config import (  # noqa: E402
    MAX_JUMP_GAP_TILES, MAX_JUMP_HEIGHT_TILES, PLAYER_JUMP_SPEED,
    PLAYER_RUN_SPEED, TILE_SIZE,
)

KEY_JUMP = pygame.K_SPACE
KEY_RIGHT = pygame.K_RIGHT
MAX_AIR_FRAMES = 180


def measure() -> dict[str, tuple[float, float, int]]:
    """(yukseklik, menzil, havada kalinan kare) olcumleri."""
    from src.core.game import Game
    from src.scenes.combat_room import CombatRoomScene

    game = Game()
    game.scenes.set_root(CombatRoomScene, transition=False)
    game.scenes._flush()
    scene = game.scenes.current
    player = scene.player

    def step(press=(), release=()) -> None:
        game.input.begin_frame()
        for key in press:
            game.input.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
        for key in release:
            game.input.handle_event(pygame.event.Event(pygame.KEYUP, key=key))
        game.input.end_frame()
        scene.update()

    results: dict[str, tuple[float, float, int]] = {}
    start_x, start_y = player.body.x, player.body.y

    for label, hold_jump in (("tam basılı", True), ("kısa dokunuş", False)):
        # Zemine oturt ve dinlendir.
        player.body.x, player.body.y = start_x, start_y
        player.body.vx = player.body.vy = 0.0
        game.input.clear()
        for _ in range(10):
            step()

        ground_top = player.body.bottom
        highest = player.body.bottom
        farthest = 0.0
        origin_x = player.body.x

        step(press=(KEY_JUMP, KEY_RIGHT))
        air_frames = 0
        for frame in range(MAX_AIR_FRAMES):
            if not hold_jump and frame == 4:
                step(release=(KEY_JUMP,))
            else:
                step()
            air_frames += 1
            highest = min(highest, player.body.bottom)
            farthest = max(farthest, player.body.x - origin_x)
            if frame > 6 and player.body.grounded:
                break
        step(release=(KEY_JUMP, KEY_RIGHT))

        results[label] = (ground_top - highest, farthest, air_frames)

    game.shutdown()
    return results


def main() -> int:
    results = measure()
    print(f"\nJUMP_SPEED {PLAYER_JUMP_SPEED}  RUN_SPEED {PLAYER_RUN_SPEED}"
          f"  (piksel/kare)\n")
    for label, (height, distance, frames) in results.items():
        print(f"{label:14s} yükseklik {height:6.1f} px = {height / TILE_SIZE:4.2f} tile"
              f"   menzil {distance:6.1f} px = {distance / TILE_SIZE:4.2f} tile"
              f"   havada {frames:3d} kare")

    height, distance, _ = results["tam basılı"]

    # Dikey: yarim tile pay birak. Kenardan kenara tam zamanlama istemek adil
    # bir bolum tasarimi degildir.
    safe_height = max(1, int((height - TILE_SIZE * 0.5) // TILE_SIZE))

    # Yatay: iki donusum var, ikisini karistirmak kolay.
    #   1) Bir tam tile guvenlik payi dus
    #   2) N tile genisligindeki bosluk, kenardaki basilabilir tile'lar
    #      arasinda N+1 tile yol demektir -> bir eksilt
    safe_gap = max(1, int((distance - TILE_SIZE) // TILE_SIZE) - 1)

    print("\nÖnerilen tasarım sınırları (marj payıyla):")
    print(f"  MAX_JUMP_HEIGHT_TILES = {safe_height}   (config: {MAX_JUMP_HEIGHT_TILES})")
    print(f"  MAX_JUMP_GAP_TILES    = {safe_gap}   (config: {MAX_JUMP_GAP_TILES})")

    drift = (safe_height != MAX_JUMP_HEIGHT_TILES
             or safe_gap != MAX_JUMP_GAP_TILES)
    if drift:
        print("\n!! config.py'deki değerler ölçümle uyuşmuyor.")
        print("   Güncelle, sonra bölümleri yeniden doğrula.")
        return 1
    print("\nconfig.py ölçümle uyumlu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
