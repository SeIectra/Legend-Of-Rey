"""Karakterin ayaklarinin zemine degip degmedigini buyutulmus olarak gosterir.

Isik ve post-fx kapatilir; sadece tile ve sprite kalir ki hizalama net gorunsun.
Kirmizi cizgi govdenin alt kenari, yani "zemin" cizgisidir.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = r"c:\Users\arda\Desktop\projects\Legend-Of-Rey"
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "build", "testshots")
os.makedirs(OUT, exist_ok=True)

import pygame  # noqa: E402

from lore.constants import FIXED_DT, TILE  # noqa: E402


def main():
    from lore.core.app import App
    from lore.core.save import SaveData
    from lore.scenes.play import PlayScene

    app = App()
    app.scenes.set_root(PlayScene, transition=False, level_id="act1_02",
                        save=SaveData())
    for _ in range(4):
        app.scenes.update(FIXED_DT)
    scene = app.scenes.current

    # Hizalamayi gizleyen her seyi kapat.
    scene.lights.enabled = False
    scene.postfx.grade = dict(scene.postfx.grade, tint_strength=0.0, vignette=0.0)
    scene.hud.toast_timer = 0.0
    scene.hud.level_title_timer = 0.0

    p = scene.player
    tm = scene.tilemap
    floor_ty = next(ty for ty in range(tm.h) if tm.is_solid(30, ty))
    p.body.set_feet(30 * TILE + 8, floor_ty * TILE)
    p.body.vx = p.body.vy = 0.0

    enemy = scene.enemies[0]
    enemy.body.set_feet(34 * TILE + 8, floor_ty * TILE)
    enemy.body.vx = 0.0
    enemy.state = "patrol"

    for _ in range(10):
        scene.update(FIXED_DT)
        p.body.set_feet(30 * TILE + 8, floor_ty * TILE)
        enemy.body.set_feet(34 * TILE + 8, floor_ty * TILE)

    app.canvas.fill((0, 0, 0, 255))
    scene.draw(app.canvas)

    # Govde alt kenarini (zemin cizgisi) isaretle.
    ox, oy = scene.camera.offset
    ground_y = int(p.body.y + p.body.h) - oy
    pygame.draw.line(app.canvas, (255, 60, 60),
                     (0, ground_y), (app.canvas.get_width(), ground_y))

    # Oyuncunun etrafini kirp ve 6x buyut.
    cx = int(p.body.centerx) - ox
    crop = pygame.Rect(max(0, cx - 46), max(0, ground_y - 44), 100, 60)
    sub = app.canvas.subsurface(crop).copy()
    big = pygame.transform.scale(sub, (crop.w * 6, crop.h * 6))
    path = os.path.join(OUT, "footcheck.png")
    pygame.image.save(big, path)
    print(f"{path}  (kirmizi cizgi = zemin, {crop.w}x{crop.h} -> 6x)")
    app.shutdown()


main()
