"""IZ SURME - Ardo artik bir EKSIKLIKLE tanimli degil.

`docs/derinlestirme.md` 2.4, belgenin en net tespiti:

    "Su an Ardo'nun oynanisi 'Yanki yok' - yani bir EKSIKLIKLE tanimli.
    Bu zayif tasarim. Ona kendi guclu mekanigini ver."
    "Rey GELECEGI/GIZLIYI duyar, Ardo GECMISI gorur. Ayni zindani iki
    farkli boyuttan okur."

Korunan kurallar:

  * Ardo'da Iz Surme VAR, Rey'de yok - ve tersi (tam simetri)
  * Ayni tus ikisini de aciyor, egri de ayni (girdi ortak, duyu farkli)
  * Dunya gercekten iz birakiyor (yuruyen aktor, olum, patlama)
  * Iz **yasiyor**: taze/eski ayirt ediliyor
  * Havadaki aktor iz birakmiyor
  * **Bedeli var**: Iz Surme acikken yasayan dusmanlar soluyor
  * **Esitlik yapisal**: kirilabilir duvarlari ikisi de bulabiliyor -
    yoksa Ardo gizli odalari hic bulamazdi ve bolum verisine icerik
    eklemek `CLAUDE.md` 3'e takilirdi

Calistir:
    python tests/test_tracking.py
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

from src.config import (  # noqa: E402
    TRACE_FADE_FRAMES, TRACE_MAX, TRACKING_ENEMY_FADE, TRACKING_FALL_FRAMES,
    TRACKING_RANGE, TRACKING_RISE_FRAMES, TRACKING_STEP_FRAMES,
)
from src.core.game import Game  # noqa: E402
from src.core.input import Action  # noqa: E402
from src.scenes.chapter02 import Chapter02Scene  # noqa: E402
from src.systems import echo as echo_mod  # noqa: E402
from src.systems.tracking import (  # noqa: E402
    BLOOD, FOOT, TraceField, TrackingState,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def step(game, count: int = 1, keys=()) -> None:
    for _ in range(count):
        game.input.begin_frame()
        for key in keys:
            game.input.handle_event(
                pygame.event.Event(pygame.KEYDOWN, key=key))
        game.input.end_frame()
        game.scenes.update()
        game.frame += 1


def main() -> int:
    game = Game()

    # --- 1. Tam simetri -----------------------------------------------------
    print("--- Rey / Ardo simetrisi ---")
    game.scenes.set_root(Chapter02Scene, transition=False, character="rey")
    game.scenes._flush()
    rey = game.scenes.current
    check(rey.echo is not None and rey.tracking is None,
          "Rey: Yanki VAR, Iz Surme YOK")
    check(rey.enemy_fade == 0.0,
          "Rey Ardo'nun bedelini odemiyor", str(rey.enemy_fade))

    game.scenes.set_root(Chapter02Scene, transition=False, character="ardo")
    game.scenes._flush()
    ardo = game.scenes.current
    check(ardo.echo is None and ardo.tracking is not None,
          "Ardo: Yanki YOK, Iz Surme VAR")

    # --- 2. Ayni egri -------------------------------------------------------
    # Iki karakterin GIRDISI ayni hissetmeli; ayrilan sey duyu, tempo degil.
    print("\n--- ayni egri ---")
    check(TRACKING_RISE_FRAMES == echo_mod.RISE_FRAMES,
          "acilma egrisi Yanki ile ayni",
          f"{TRACKING_RISE_FRAMES} == {echo_mod.RISE_FRAMES}")
    check(TRACKING_FALL_FRAMES == echo_mod.FALL_FRAMES,
          "kapanma egrisi Yanki ile ayni",
          f"{TRACKING_FALL_FRAMES} == {echo_mod.FALL_FRAMES}")
    # Menzil ise BILEREK farkli - asimetrinin kendisi tasarim.
    clear = echo_mod.SIGHT_RANGE[max(echo_mod.SIGHT_RANGE)]
    murky = echo_mod.SIGHT_RANGE[1]
    check(murky < TRACKING_RANGE < clear,
          "menzil berrak Yanki ile bulanik Yanki ARASINDA - "
          "Iz Surme zayiflamaz ama hic o kadar da gormez",
          f"{murky} < {TRACKING_RANGE} < {clear}")

    # --- 3. Egri gercekten yuruyor ------------------------------------------
    print("\n--- egri yuruyor ---")
    state = TrackingState()
    check(not state.active, "bastan kapali")
    for _ in range(TRACKING_RISE_FRAMES + 1):
        state.update(True)
    check(state.strength >= 0.999, "tam acildi", f"{state.strength:.2f}")
    check(abs(state.range - TRACKING_RANGE) < 1.0,
          "menzil tam", f"{state.range:.0f}")
    check(abs(state.enemy_fade - TRACKING_ENEMY_FADE) < 0.01,
          "bedel tam", f"{state.enemy_fade:.2f}")
    for _ in range(TRACKING_FALL_FRAMES + 1):
        state.update(False)
    check(not state.active, "birakinca sondu", f"{state.strength:.2f}")

    # --- 4. Dunya iz birakiyor ----------------------------------------------
    print("\n--- dunya iz birakiyor ---")
    before = len(ardo.traces.traces)
    step(game, TRACKING_STEP_FRAMES * 4, keys=(pygame.K_RIGHT,))
    after = len(ardo.traces.traces)
    check(after > before, "yuruyen oyuncu ayak izi birakti",
          f"{before} -> {after}")
    check(all(t.kind == FOOT for t in ardo.traces.traces),
          "hepsi ayak izi (henuz dovus olmadi)")

    # --- 5. Havada iz YOK ---------------------------------------------------
    # Ucan/dusen bir aktorun ayak izi olmaz; olsaydi bosluklar iz
    # cizgileriyle dolardi ve iz "iz" olmaktan cikardi.
    print("\n--- havada iz birakmiyor ---")
    field = TraceField()
    ardo.player.body.grounded = False
    ardo.player.body.vx = 2.0
    count = len(field.traces)
    for _ in range(TRACKING_STEP_FRAMES * 3):
        field.update()
        field.record_step(ardo.player)
    check(len(field.traces) == count,
          "havadaki aktor iz birakmadi", str(len(field.traces)))

    # --- 6. Iz yasiyor ------------------------------------------------------
    print("\n--- iz yasiyor ---")
    field = TraceField()
    field.add(10.0, 10.0, FOOT)
    fresh = field.traces[-1]
    check(fresh.age(field.frame) == 0.0, "yeni iz taze")
    check(fresh.age(field.frame + TRACE_FADE_FRAMES) >= 1.0,
          "sure dolunca tamamen soluk")
    check(0.4 < fresh.age(field.frame + TRACE_FADE_FRAMES // 2) < 0.6,
          "yarida yari soluk - yas SUREKLI, esik degil",
          f"{fresh.age(field.frame + TRACE_FADE_FRAMES // 2):.2f}")

    # --- 7. Ust sinir -------------------------------------------------------
    print("\n--- ust sinir ---")
    field = TraceField()
    for index in range(TRACE_MAX + 50):
        field.add(float(index), 0.0, FOOT)
    check(len(field.traces) == TRACE_MAX,
          "iz sayisi tavani asmiyor", str(len(field.traces)))
    check(field.traces[0].x >= 50,
          "tavana varinca EN ESKISI dusuyor",
          f"ilk iz x={field.traces[0].x:.0f}")

    # --- 8. Menzil sorgusu --------------------------------------------------
    print("\n--- menzil ---")
    field = TraceField()
    field.add(0.0, 0.0, FOOT)
    field.add(500.0, 0.0, FOOT)
    near = field.near(0.0, 0.0, 100.0)
    check(len(near) == 1, "yalnizca menzildeki iz donuyor", str(len(near)))

    # --- 9. Bedel gercekten uygulaniyor -------------------------------------
    print("\n--- bedel: dusmanlar soluyor ---")
    ardo.tracking.strength = 1.0
    check(ardo.enemy_fade > 0.5,
          "Iz Surme acikken dusmanlar soluyor", f"{ardo.enemy_fade:.2f}")
    ardo.tracking.strength = 0.0
    check(ardo.enemy_fade == 0.0, "kapaliyken solma yok")

    # --- 10. Esitlik: gizli duvarlari ikisi de buluyor ----------------------
    # Bu **yapisal** olmali: bolum verisine "Ardo icin ipucu" eklemek
    # `CLAUDE.md` 3'e (sirasi gelmemis icerik) takilirdi. Cozum: Yanki ne
    # gosteriyorsa Iz Surme de gosteriyor, gerekce farkli - Rey duvarin
    # ARKASINI duyuyor, Ardo duvardan birinin GECTIGINI goruyor.
    print("\n--- gizli duvarlar: ikisi de bulabiliyor ---")
    from src.ui import tracking_view
    check(hasattr(tracking_view, "draw_cracks"),
          "Iz Surme'nin de catlak cizimi var")
    step(game, 3)
    check(len(ardo.breakables) > 0,
          "Bolum 2'de kirilabilir duvar var - kontrol bos degil",
          str(len(ardo.breakables)))
    # Gercekten cizildigini kanitla: bos bir yuzeye ciz, degisti mi bak.
    ardo.tracking.strength = 1.0
    wall = ardo.breakables[0]
    ardo.player.body.set_feet(wall.rect.centerx, wall.rect.bottom)
    canvas = pygame.Surface((480, 270))
    canvas.fill((0, 0, 0))
    tracking_view.draw_cracks(canvas, (int(wall.rect.centerx) - 240,
                                       int(wall.rect.centery) - 135),
                              ardo.tracking, ardo.player, ardo.breakables)
    lit = pygame.transform.average_color(canvas)[:3]
    check(sum(lit) > 0,
          "catlak GERCEKTEN cizildi - bos yuzey artik bos degil",
          str(lit))

    # --- 11. Kan izi dovusten geliyor ---------------------------------------
    # Ilk oda ("inis") bos - dusmani KENDIMIZ kuruyoruz. Ilk surum
    # `ardo.enemies[0]` aliyordu ve liste bostu, yani test kendi
    # kurulumu yuzunden kaliyordu.
    print("\n--- dovus iz birakiyor ---")
    from src.entities.enemies.shambler import Shambler
    victim = Shambler(ardo, ardo.player.body.center_x + 40.0,
                      ardo.player.body.bottom)
    before = sum(1 for t in ardo.traces.traces if t.kind == BLOOD)
    ardo.on_enemy_died(victim)
    after = sum(1 for t in ardo.traces.traces if t.kind == BLOOD)
    check(after > before, "olum bir KAN izi birakti", f"{before} -> {after}")
    blood = [t for t in ardo.traces.traces if t.kind == BLOOD][-1]
    check(abs(blood.x - victim.body.center_x) < 2.0,
          "kan izi dusmanin OLDUGU yerde", f"{blood.x:.0f}")

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Iz Surme: Ardo'nun kendi duyusu var, bedeli var, esitlik yapisal.")
    return 0


raise SystemExit(main())
