"""Ziplama zarfini olcer.

Bolum tasarimindaki "su platforma erisilebiliyor mu" sorusunun cevabi burada.
Matematik yaklasik sonuc verir; sabit zaman adimi, apex hafifligi ve piksel
piksel carpisma cozumu bir araya gelince gercek deger kayar. Bu yuzden
olcuyoruz.

Cikti dogrudan `Level.MAX_JUMP_TILES` ve `Level.MAX_JUMP_HEIGHT_TILES`
degerlerini besler.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from lore.constants import FIXED_DT, TILE  # noqa: E402


def measure():
    from lore.core.app import App
    from lore.core.save import SaveData
    from lore.scenes.play import PlayScene

    app = App()
    save = SaveData()
    app.scenes.set_root(PlayScene, transition=False, level_id="act1_01",
                        save=save)
    for _ in range(4):
        app.scenes.update(FIXED_DT)
    scene = app.scenes.current
    p = scene.player
    tm = scene.tilemap

    # Duz, genis bir zemin bul (act1_01'in sag yarisi).
    floor_ty = next(ty for ty in range(tm.h) if tm.is_solid(60, ty))
    start_x = 60 * TILE + 8
    start_y = floor_ty * TILE

    results = {}
    for label, hold in (("tam basili", True), ("kisa dokunus", False)):
        p.body.set_feet(start_x, start_y)
        p.body.vx = p.body.vy = 0.0
        p.dead = False
        p.health = p.max_health
        app.input.clear()
        for _ in range(4):
            app.input.end_frame()
            scene.update(FIXED_DT)
            app.input.begin_frame(FIXED_DT)

        app.input.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        highest = p.body.y
        farthest = 0.0
        # Yatay menzili de olcmek icin sag tusu basili tut.
        app.input.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        for frame in range(120):
            if not hold and frame == 5:
                app.input.handle_event(
                    pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))
            app.input.end_frame()
            scene.update(FIXED_DT)
            app.input.begin_frame(FIXED_DT)
            highest = min(highest, p.body.y)
            farthest = max(farthest, p.body.x - (start_x - p.body.w * 0.5))
            if frame > 6 and p.body.grounded:
                break
        app.input.handle_event(
            pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT))
        app.input.handle_event(
            pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))

        rise = (start_y - p.body.h) - highest
        results[label] = (rise, farthest)

    app.shutdown()
    return results


res = measure()
print()
for label, (rise, run) in res.items():
    print(f"{label:14s} yukseklik {rise:6.1f} px = {rise / TILE:4.2f} tile   "
          f"menzil {run:6.1f} px = {run / TILE:4.2f} tile")

rise = res["tam basili"][0]
run = res["tam basili"][1]
print()
print("Guvenli tasarim siniri (marj payiyla):")
print(f"  MAX_JUMP_HEIGHT_TILES = {int(rise / TILE) - 0 if rise / TILE % 1 > 0.35 else int(rise / TILE) - 1}")
print(f"  MAX_JUMP_TILES        = {int(run / TILE) - 1}")
