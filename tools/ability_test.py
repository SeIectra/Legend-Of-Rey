"""Yetenek kilidi acilis akisini dogrular.

Sandigi ac -> yetenek kazanilsin -> tus gercekten calissin -> dokunulmazlik
penceresi islesin. "Atilma ogrenildi" yazip tusun bir sey yapmamasi, bu testin
var olma sebebi.
"""
import os
import sys
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

from lore.constants import FIXED_DT  # noqa: E402


def key(k, down=True):
    return pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=k)


def main():
    from lore.core.app import App
    from lore.core.input import Action
    from lore.core.save import SaveData
    from lore.scenes.play import PlayScene

    app = App()
    app.scenes.set_root(PlayScene, transition=False, level_id="act1_05",
                        save=SaveData())
    errors = []

    def step(n):
        for _ in range(n):
            app.input.end_frame()
            app.scenes.update(FIXED_DT)
            app.input.begin_frame(FIXED_DT)

    step(4)
    scene = app.scenes.current
    p = scene.player

    # --- 1) Kilitliyken tus geri bildirim vermeli --------------------------
    print(f"baslangic yetenekleri: {sorted(p.abilities) or 'yok'}")
    scene.hud.toast = ""
    app.input.handle_event(key(pygame.K_LSHIFT))
    step(2)
    app.input.handle_event(key(pygame.K_LSHIFT, False))
    print(f"kilitliyken mesaj: {scene.hud.toast!r}")
    if not scene.hud.toast:
        errors.append("kilitli yetenege basinca hicbir geri bildirim yok")
    if p.dash_timer > 0.0:
        errors.append("kilitli oldugu halde atilma calisti")

    # --- 2) Sandiktan yetenegi al -----------------------------------------
    chest = next((pr for pr in scene.props
                  if getattr(pr, "contents", None) == "dash"), None)
    if chest is None:
        errors.append("act1_05 icinde atilma sandigi yok")
        return errors
    chest.interact(p)
    step(2)
    print(f"sandik sonrasi yetenekler: {sorted(p.abilities)}")
    print(f"acilis mesaji: {scene.hud.toast!r}")
    if "dash" not in p.abilities:
        errors.append("sandik atilma yetenegini vermedi")
    label = app.input.binding_label(Action.DASH)
    if label not in scene.hud.toast:
        errors.append(f"acilis mesaji tusu ({label}) icermiyor: {scene.hud.toast!r}")

    # --- 3) Atilma gercekten calissin --------------------------------------
    p.body.vx = p.body.vy = 0.0
    p.facing = 1
    start_x = p.body.x
    app.input.handle_event(key(pygame.K_LSHIFT))
    step(2)
    app.input.handle_event(key(pygame.K_LSHIFT, False))
    print(f"atilma: timer={p.dash_timer:.3f} vx={p.body.vx:.1f} "
          f"durum={p.anim.state}")
    if p.dash_timer <= 0.0:
        errors.append("atilma tetiklenmedi")
    if abs(p.body.vx) < 200:
        errors.append(f"atilma hizi dusuk: vx={p.body.vx:.1f}")

    # --- 4) Atilma sirasinda dokunulmazlik ---------------------------------
    if not p.invulnerable:
        errors.append("atilma sirasinda dokunulmazlik yok")
    else:
        print("atilma sirasinda dokunulmazlik: var")

    step(12)
    moved = p.body.x - start_x
    print(f"atilma mesafesi: {moved:.1f} px = {moved / 16:.2f} tile")
    if moved < 24:
        errors.append(f"atilma neredeyse hic ilerletmedi: {moved:.1f} px")

    # --- 5) Bekleme suresi --------------------------------------------------
    p.body.vx = 0.0
    app.input.handle_event(key(pygame.K_LSHIFT))
    step(2)
    app.input.handle_event(key(pygame.K_LSHIFT, False))
    if p.dash_timer > 0.0:
        errors.append("bekleme suresi yokmus gibi ard arda atildi")
    else:
        print(f"bekleme suresi calisiyor (kalan {p.dash_cooldown:.2f} sn)")

    app.shutdown()
    return errors


try:
    errors = main()
    print("\n--- SONUC ---")
    if errors:
        print(f"HATA ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("yetenek kilidi ve atilma calisiyor")
except Exception:
    traceback.print_exc()
    sys.exit(2)
