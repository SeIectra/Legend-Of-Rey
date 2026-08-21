"""Basssiz duman testi: oyunu gercekten calistirir, kare kare surer.

Gorunur pencere olmadan (SDL dummy surucu) tum sistemleri isletir ve belirli
karelerde ekran goruntusu alir. Boylece hem cokme hem gorsel hata yakalanir.
"""
import os
import sys
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "build", "testshots")
os.makedirs(OUT, exist_ok=True)

import pygame  # noqa: E402


def key(k, down=True):
    return pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=k)


def main():
    from lore.core.app import App
    from lore.scenes.boot import BootScene
    from lore.scenes.play import PlayScene
    from lore.scenes.title import TitleScene

    app = App()
    app.scenes.set_root(BootScene, transition=False)
    app.scenes.transition.duration = 0.02        # Testte perde beklemeyelim

    shots = []
    errors = []

    def step(n, label=None, events=()):
        for i in range(n):
            for ev in (events if i == 0 else ()):
                app.input.handle_event(ev)
                app.scenes.handle_event(ev)
            app.input.end_frame()
            app.scenes.update(1 / 60)
            app.input.begin_frame(1 / 60)
        app.canvas.fill((0, 0, 0, 255))
        app.scenes.draw(app.canvas)
        if label:
            path = os.path.join(OUT, f"shot_{label}.png")
            pygame.image.save(app.canvas, path)
            shots.append(label)

    # 1) Boot -> Title
    step(30, "01_boot")
    step(150, "02_title")
    scene = app.scenes.current
    print(f"boot sonrasi sahne: {type(scene).__name__}")
    if not isinstance(scene, TitleScene):
        errors.append(f"TitleScene bekleniyordu, {type(scene).__name__} geldi")
        return shots, errors

    # 2) Yeni oyun: menude ilgili satiri sec, sonra gercek girdi akisini kullan
    labels = [i.label for i in scene.menu.items]
    print(f"menu: {labels} secili={scene.menu.index}")
    scene.menu.index = labels.index("Yeni Oyun")
    step(2, None, [key(pygame.K_RETURN)])
    step(2, None, [key(pygame.K_RETURN, False)])
    step(4, "03_slots")
    print(f"menu modu: {scene.mode}")
    step(2, None, [key(pygame.K_RETURN)])
    step(2, None, [key(pygame.K_RETURN, False)])
    step(20, "04_play")

    scene = app.scenes.current
    print(f"menu sonrasi sahne: {type(scene).__name__}")
    if not isinstance(scene, PlayScene):
        errors.append(f"PlayScene bekleniyordu, {type(scene).__name__} geldi")
        return shots, errors

    print(f"bolum: {scene.level.id}  harita {scene.tilemap.w}x{scene.tilemap.h}")
    print(f"oyuncu: {scene.player.body.x:.1f},{scene.player.body.y:.1f} "
          f"zemin={scene.player.body.grounded}")

    # 3) Sag yurur
    app.input.handle_event(key(pygame.K_RIGHT))
    step(60, "05_run")
    p = scene.player
    print(f"kosu sonrasi: x={p.body.x:.1f} vx={p.body.vx:.1f} "
          f"durum={p.anim.state} zemin={p.body.grounded}")
    if p.body.vx < 40:
        errors.append(f"kosu hizi dusuk: vx={p.body.vx:.1f}")

    # 4) Dikey zipla testi: yatay girdiyi birak ve bilinen duz zemine koy,
    # yoksa kor bot ziplarken yan cukura kayiyor ve olcum anlamsizlasiyor.
    app.input.handle_event(key(pygame.K_RIGHT, False))
    p.body.set_feet(8 * 16 + 8, 16 * 16)
    p.body.vx = p.body.vy = 0.0
    step(4)
    app.input.handle_event(key(pygame.K_SPACE))
    step(6)
    print(f"zipla: vy={p.body.vy:.1f} durum={p.anim.state}")
    if p.body.vy > -100:
        errors.append(f"ziplama calismadi: vy={p.body.vy:.1f}")
    step(18, "06_jump")
    app.input.handle_event(key(pygame.K_SPACE, False))
    step(50, "07_landed")
    print(f"inis: y={p.body.y:.1f} zemin={p.body.grounded}")
    if not p.body.grounded:
        errors.append("inisden sonra zeminde degil")

    # 5) Saldirir
    app.input.handle_event(key(pygame.K_j))
    step(3)
    print(f"saldiri: durum={p.anim.state} timer={p.attack_timer:.2f} "
          f"hitbox={len(scene.combat.hitboxes)}")
    step(10, "08_attack")
    app.input.handle_event(key(pygame.K_j, False))

    # 6) Uzun kosu: dusmanlarla karsilasma
    app.input.handle_event(key(pygame.K_RIGHT))
    step(320, "09_far")
    print(f"uzun kosu sonrasi: x={p.body.x:.1f} can={p.health} "
          f"oz={p.essence} dusman={len(scene.enemies)}")
    app.input.handle_event(key(pygame.K_RIGHT, False))

    # 7) Duraklat
    app.input.handle_event(key(pygame.K_ESCAPE))
    app.scenes.handle_event(key(pygame.K_ESCAPE))
    step(10, "10_pause")
    print(f"duraklatma sahnesi: {type(app.scenes.current).__name__} "
          f"yigin={len(app.scenes.stack)}")

    # 8) Ayarlar
    app.input.handle_event(key(pygame.K_ESCAPE, False))
    step(2, None, [key(pygame.K_DOWN)])
    step(2, None, [key(pygame.K_DOWN, False)])
    step(2, None, [key(pygame.K_RETURN)])
    step(2, None, [key(pygame.K_RETURN, False)])
    step(8, "11_settings")
    print(f"ayarlar sahnesi: {type(app.scenes.current).__name__}")

    # 9) Her bolumu yukle
    from lore.world.level import LevelIndex
    index = LevelIndex()
    for level_id in index.all_ids():
        try:
            scene.load_level(level_id)
        except Exception as exc:
            errors.append(f"{level_id} yuklenemedi: {exc}")
            traceback.print_exc()
    print(f"tum bolumler yuklendi: {index.all_ids()}")

    app.shutdown()
    return shots, errors


try:
    shots, errors = main()
    print("\n--- SONUC ---")
    print(f"ekran goruntusu: {len(shots)}")
    if errors:
        print(f"HATA ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("hata yok")
except Exception:
    traceback.print_exc()
    sys.exit(2)
