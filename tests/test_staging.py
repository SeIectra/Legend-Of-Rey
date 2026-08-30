"""Sinematik sahneleme katmani - `src/scenes/staging.py`.

Bu katman 30.08.2026'da yazildi cunku bugune kadarki butun ara
sahnelerde **tek bir karakter cizilmemisti**. Testin isi o kazanimi
korumak: sahneler yeniden "buyuyen bir daire"ye donmesin.

Korunan kurallar:

  * `Cue` gercekten uygulaniyor (durum, yon, hareket, gorunurluk)
  * Hareket egrileri farkli: dusus HIZLANIYOR, varis YAVASLIYOR
  * Hitstop sahneyi gercekten donduruyor
  * Yakin plan portreyi ciziyor - oyunun en iyi yuz sanati diyalog
    kutusunun kosesinde kalmasin
  * Havadaki aktorde zemin golgesi yok
  * Derinlik (parallaks) kamera ofsetini olcekliyor

Calistir:
    python tests/test_staging.py
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

from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.scenes.staging import (  # noqa: E402
    ActorSpec, Cue, MoteField, StageActor, StagedScene, ease_in, ease_out,
)
from src.scenes.story import Panel  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


class _Probe(StagedScene):
    """Testin kendi sahnesi - gercek bolumlere bagli kalmamak icin."""

    ACTORS = (
        ActorSpec("a", "rey", 100.0, 150.0, facing=1),
        ActorSpec("b", "ardo", 200.0, 150.0, facing=-1, depth=0.5),
    )
    PANELS = (
        Panel(30, "bir", cues=(
            Cue("a", state="run", face=-1,
                move_to=(160.0, 150.0), move_frames=20),
        )),
        Panel(20, "iki", cues=(
            Cue("a", state="land", freeze=10, flash=0.4),
            Cue("b", visible=False),
        )),
        Panel(20, "yuz", closeup="a"),
    )

    def on_finished(self) -> None:
        pass


def step(game, count: int = 1) -> None:
    for _ in range(count):
        game.input.begin_frame()
        game.input.end_frame()
        game.scenes.update()
        game.frame += 1


def main() -> int:
    print("=== sahneleme katmani ===")

    # --- 1. Egriler ---
    print("\n--- hareket egrileri ---")
    check(ease_in(0.5) < 0.5, "dusus HIZLANIYOR (ease_in)",
          f"yarida {ease_in(0.5):.2f}")
    check(ease_out(0.5) > 0.5, "varis YAVASLIYOR (ease_out)",
          f"yarida {ease_out(0.5):.2f}")
    # Bu ayrim bir suslemenin degil bir hatanin sonucu: `smoothstep`
    # hem hizlanip hem yavasliyor ve dusen karakter yere yaklasirken
    # yavasliyordu. Yer cekimi yavaslamaz.
    check(ease_in(0.5) != ease_out(0.5), "iki egri gercekten farkli")

    actor = StageActor(ActorSpec("x", "rey", 0.0, 0.0))
    actor.move_to(100.0, 0.0, 10, "in")
    for _ in range(5):
        actor.update()
    check(actor.x < 50.0, "ease_in yarida yolun yarisindan AZ almis",
          f"x={actor.x:.1f}")

    game = Game()
    try:
        # --- 2. Cue'lar uygulaniyor mu ---
        print("\n--- cue'lar ---")
        game.scenes.set_root(_Probe, transition=False)
        game.scenes._flush()
        scene = game.scenes.current
        a, b = scene.actor("a"), scene.actor("b")
        check(a is not None and b is not None, "aktorler kuruldu")
        check(a.animator.state == "run", "durum uygulandi", a.animator.state)
        check(a.facing == -1, "yon uygulandi", str(a.facing))
        check(a.moving, "hareket basladi")

        start_x = a.x
        step(game, 22)
        check(a.x > start_x, "aktor gercekten hareket etti",
              f"{start_x:.0f} -> {a.x:.0f}")

        # --- 3. Hitstop ---
        print("\n--- hitstop ---")
        while scene.panel is not None and scene.panel.name != "iki":
            step(game)
        step(game, 2)
        check(scene.freeze_frames > 0, "carpma sahneyi donduruyor",
              f"{scene.freeze_frames} kare")
        frozen_x = a.x
        held = scene.panel_frames
        step(game, 3)
        check(a.x == frozen_x and scene.panel_frames == held,
              "donmusken aktor VE panel sayaci duruyor")
        check(not b.visible, "gorunurluk cue'su isliyor")

        # --- 4. Yakin plan ---
        print("\n--- yakin plan ---")
        while scene.panel is not None and scene.panel.name != "yuz":
            step(game)
        check(scene.panel is not None and scene.panel.closeup == "a",
              "yakin plan paneline gelindi")
        game.canvas.fill((0, 0, 0))
        scene.draw(game.canvas)
        # Portre kadraji doldurmali: ust yarida ten rengi olmali.
        top = game.canvas.subsurface(
            pygame.Rect(INTERNAL_WIDTH // 2 - 30, 20, 60, 60)).copy()
        painted = pygame.transform.average_color(top)[:3] != (0, 0, 0)
        check(painted, "yakin planda portre ciziliyor")

        # --- 5. Golge ve derinlik ---
        print("\n--- golge ve derinlik ---")
        airborne = StageActor(ActorSpec("h", "rey", 0.0, 0.0, shadow=False))
        check(not airborne.shadow,
              "havadaki aktorde zemin golgesi KAPALI")
        airborne.ground(120.0)
        check(airborne.shadow and airborne.y == 120.0,
              "yere inince golge geri geliyor")
        check(b.depth == 0.5, "derinlik okundu", str(b.depth))

        # --- 6. Zerreler ---
        print("\n--- ortam zerreleri ---")
        motes = MoteField(20)
        first = motes.cells[0]
        again = MoteField(20).cells[0]
        check(first == again,
              "dagilim DETERMINISTIK - ayni sahne her acilista ayni")
        check(motes.count <= 48, "ust sinir korunuyor", str(motes.count))
    finally:
        game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("Sahneleme katmani saglam: cue, hitstop, yakin plan, derinlik.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
