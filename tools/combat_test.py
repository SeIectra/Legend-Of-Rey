"""Savas dogrulama testi.

Duman testi "cokmuyor" der; bu test "gercekten calisiyor" der. Oyuncuyu
dusmanin yanina koyup saldirtiyor ve hasarin, olumun, Essence dusmesinin ve
dusman yapay zekasinin isledigini olcuyor.
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
    from lore.core.save import SaveData
    from lore.scenes.play import PlayScene

    app = App()
    save = SaveData()
    save.level_id = "act1_02"
    app.scenes.set_root(PlayScene, transition=False, level_id="act1_02",
                        save=save)

    errors = []
    shots = []

    def step(n, label=None):
        for _ in range(n):
            app.input.end_frame()
            app.scenes.update(1 / 60)
            app.input.begin_frame(1 / 60)
        app.canvas.fill((0, 0, 0, 255))
        app.scenes.draw(app.canvas)
        if label:
            pygame.image.save(app.canvas, os.path.join(OUT, f"cmb_{label}.png"))
            shots.append(label)

    step(4)
    scene = app.scenes.current
    p = scene.player
    print(f"bolum={scene.level.id} dusman={len(scene.enemies)}")
    if not scene.enemies:
        errors.append("bolumde dusman yok")
        return shots, errors

    enemy = scene.enemies[0]
    print(f"dusman: {type(enemy).__name__} can={enemy.health} "
          f"durum={enemy.state} bakis={enemy.facing}")

    # --- 1) Sirttan vurus -------------------------------------------------
    # Dusmanin tam arkasina konumlan ve o bizden uzaga baksin.
    enemy.facing = 1
    enemy.aggro = False
    enemy.state = "patrol"
    p.body.set_feet(enemy.body.centerx - 14, enemy.body.y + enemy.body.h)
    p.facing = 1
    p.body.vx = p.body.vy = 0.0
    before = enemy.health
    app.input.handle_event(key(pygame.K_j))
    step(2)
    app.input.handle_event(key(pygame.K_j, False))
    step(14, "01_backstab")
    print(f"sirttan vurus: {before} -> {enemy.health} "
          f"(hitbox {len(scene.combat.hitboxes)})")
    if enemy.health >= before:
        errors.append(f"sirttan vurus hasar vermedi ({before} -> {enemy.health})")

    # --- 2) Dusmani oldur --------------------------------------------------
    guard = 0
    while not enemy.dead and guard < 40:
        guard += 1
        p.body.set_feet(enemy.body.centerx - 14, enemy.body.y + enemy.body.h)
        p.facing = 1
        p.iframes = 5.0                 # Test icin: karsi saldiri olcumu bozmasin
        enemy.iframes = 0.0
        app.input.handle_event(key(pygame.K_j))
        step(2)
        app.input.handle_event(key(pygame.K_j, False))
        step(16)
    print(f"{guard} saldiri sonrasi dusman olu={enemy.dead} can={enemy.health}")
    if not enemy.dead:
        errors.append(f"dusman {guard} saldiriya ragmen olmedi (can={enemy.health})")

    # --- 3) Essence dustu mu ----------------------------------------------
    step(10, "02_death")
    print(f"toplanabilir: {len(scene.pickups)}")
    if not scene.pickups:
        errors.append("olen dusmandan Essence dusmedi")

    p.iframes = 0.0
    before_essence = p.essence
    for pickup in scene.pickups:
        pickup.body.set_feet(p.body.centerx, p.body.y + p.body.h)
    step(40, "03_collect")
    print(f"essence: {before_essence} -> {p.essence}")
    if p.essence <= before_essence:
        errors.append("Essence toplanmadi")

    # --- 4) Dusman AI: gorup kovalar mi -----------------------------------
    if len(scene.enemies) > 1:
        other = scene.enemies[1]
    else:
        from lore.entities.enemies import spawn_enemy
        other = spawn_enemy(scene, "grunt", p.body.centerx + 60,
                            p.body.y + p.body.h)
        scene.enemies.append(other)
    other.aggro = False
    other.state = "patrol"
    other.body.set_feet(p.body.centerx + 60, p.body.y + p.body.h)
    other.facing = -1
    p.iframes = 99.0
    step(40)
    print(f"AI: durum={other.state} aggro={other.aggro} "
          f"mesafe={abs(other.body.centerx - p.body.centerx):.0f}")
    if other.state == "patrol" and not other.aggro:
        errors.append("dusman goz onundeki oyuncuyu fark etmedi")

    # --- 5) Oyuncu hasar alir ---------------------------------------------
    p.iframes = 0.0
    before_hp = p.health
    other.body.set_feet(p.body.centerx + 12, p.body.y + p.body.h)
    other.state = "windup"
    other.state_timer = 0.01
    step(30, "04_player_hurt")
    print(f"oyuncu cani: {before_hp} -> {p.health}")
    if p.health >= before_hp:
        errors.append("dusman saldirisi oyuncuya hasar vermedi")

    # --- 6) Dikene basmak --------------------------------------------------
    scene.load_level("act1_03")
    step(4)
    p = scene.player
    tm = scene.tilemap
    spike = None
    for ty in range(tm.h):
        for tx in range(tm.w):
            if tm.is_hazard(tx, ty):
                spike = (tx, ty)
                break
        if spike:
            break
    if spike is None:
        errors.append("act1_03 icinde diken bulunamadi")
    else:
        p.iframes = 0.0
        before_hp = p.health
        p.body.set_feet(spike[0] * 16 + 8, spike[1] * 16 + 16)
        step(4, "05_spike")
        print(f"diken {spike}: can {before_hp} -> {p.health}")
        if p.health >= before_hp:
            errors.append("diken hasar vermedi")

    app.shutdown()
    return shots, errors


try:
    shots, errors = main()
    print("\n--- SONUC ---")
    if errors:
        print(f"HATA ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("savas sistemleri calisiyor")
except Exception:
    traceback.print_exc()
    sys.exit(2)
