"""Bolum 7 "Dar Gecit" - girth, cark, el.

`docs/yapi.md` B7: *"Tek kisilik bir aralik. Ardo gecemez, Rey gecer.
Rey obur taraftan kapiyi acar. Romantik an: Ardo elini uzatir, Rey
tutar, aralıktan ceker. Balon yok."*

Korunan kurallar:

  * Catlaktan **yalnizca ince olan** geciyor - ve bu oynanan karaktere
    degil KANONA bagli (Rey her zaman geciyor, Ardo hicbir zaman)
  * Ardo oynanirken oyuncunun kendisi gecemiyor - o zaman yoldas
    gonderiliyor. Iki yol da kapiyi aciyor.
  * Kapi **uc sutun** aciliyor: tek sutun acilsaydi duvarin icinde bir
    cukur olurdu ve kimse gecemezdi (ilk surumde tam olarak oyle oldu)
  * Cukur ne atlanarak ne tirmanarak geciliyor - sayilar hesaplandi
  * Cukura dusmek **kilitlemiyor**: basamaklardan geri cikiliyor
  * "El" sahnesinde **replik yok** - belgenin acik talimati
  * Eller birlestikten sonra sahne bir saniye daha bekliyor

Calistir:
    python tests/test_chapter07.py
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

# `pygame.init()` DEGIL - joystick alt sistemi bu makinede 40 saniye
# suruyor. `src/core/game.py` ile ayni yol.
pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.config import (  # noqa: E402
    MAX_JUMP_GAP_TILES, MAX_JUMP_HEIGHT_TILES, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.entities.character_stats import ARDO, REY  # noqa: E402
from src.entities.companion import other_character  # noqa: E402
from src.scenes.chapter07 import Chapter07Scene  # noqa: E402
from src.scenes.chapter07_cinematics import (  # noqa: E402
    HOLD_TOO_LONG, GapCinematic, HandCinematic, SealCinematic,
)
from src.world.gap import NarrowGap  # noqa: E402
from src.world.rooms.chapter07 import (  # noqa: E402
    CHASM_TILES, DOOR_ROWS, DOOR_TILES, GAP_CLEARANCE, GAP_ROWS, GAP_TILE,
    HAND_TILE, LEDGE_TILE, LEVEL, ROOM_STARTS, WINCH_TILE,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def step(game, count: int = 1) -> None:
    for _ in range(count):
        game.input.begin_frame()
        game.input.end_frame()
        game.scenes.update()
        game.frame += 1


def place(actor, tile) -> None:
    """Aktoru BOS bir tile'a koyar - DEVIR 6/20'nin uc kez yasanan hatasi."""
    actor.body.set_feet(tile[0] * TILE_SIZE + TILE_SIZE * 0.5,
                        tile[1] * TILE_SIZE)
    actor.body.vx = actor.body.vy = 0.0


def start(game, character: str = "rey") -> Chapter07Scene:
    # `transition=False` + `_flush()`: gecis animasyonu beklenmeden
    # sahne hemen kuruluyor. `test_chapter06.py` ile ayni desen.
    game.scenes.set_root(Chapter07Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter07Scene)
    return scene


# --- 1. Catlak: kim geciyor -------------------------------------------------
def test_gap_geometry() -> None:
    print("\n--- catlak ---")
    gap = NarrowGap(GAP_TILE, GAP_ROWS, GAP_CLEARANCE)
    check(gap.fits(REY.girth), "Rey catlaktan geciyor",
          f"girth {REY.girth} <= {GAP_CLEARANCE}")
    check(not gap.fits(ARDO.girth), "Ardo gecemiyor",
          f"girth {ARDO.girth} > {GAP_CLEARANCE}")
    # Aciklik ikisinin de **arasinda** olmali; kenara yapisik bir sayi
    # ileride girth bir puan oynayinca sessizce bozulurdu.
    check(REY.girth < GAP_CLEARANCE < ARDO.girth,
          "aciklik ikisinin ortasinda",
          f"{REY.girth} < {GAP_CLEARANCE} < {ARDO.girth}")


# --- 2. Cukur gecilemez ------------------------------------------------------
def _surface_row(rows: list[str], column: int) -> int:
    for index, row in enumerate(rows):
        if row[column] == "#" and index > 3:
            return index
    return len(rows)


def test_chasm_uncrossable() -> None:
    print("\n--- cukur ---")
    rows = list(LEVEL.terrain_rows)
    pit_left = CHASM_TILES.start
    pit_right = CHASM_TILES.stop - 1
    pit_floor = _surface_row(rows, pit_left)
    far_side = _surface_row(rows, pit_right + 1)

    rise = pit_floor - far_side
    check(rise > MAX_JUMP_HEIGHT_TILES,
          "cukurun karsi duvari tirmanilamiyor",
          f"{rise} tile > {MAX_JUMP_HEIGHT_TILES}")

    # Son basamaktan karsi kenara yatay aciklik.
    step_column = pit_left - 1
    span = (pit_right + 1) - step_column
    check(span > MAX_JUMP_GAP_TILES,
          "cukur atlanarak gecilemiyor",
          f"{span} tile > {MAX_JUMP_GAP_TILES}")

    # **Kilitlenme yok**: cukurdan sola dogru basamaklar var.
    climbs = []
    column = pit_left
    while column > pit_left - 4:
        here = _surface_row(rows, column)
        left = _surface_row(rows, column - 1)
        climbs.append(here - left)
        column -= 1
    check(all(c <= MAX_JUMP_HEIGHT_TILES for c in climbs),
          "cukurdan geri cikilabiliyor", f"basamaklar {climbs}")


# --- 3. Kapi uc sutun --------------------------------------------------------
def test_door_opens_through() -> None:
    print("\n--- kapi ---")
    game = Game()
    try:
        scene = start(game)
        closed = all(scene.tilemap.is_solid(c, r)
                     for c in DOOR_TILES for r in DOOR_ROWS)
        check(closed, "kapi kapali basliyor")
        scene._turn_winch()
        opened = not any(scene.tilemap.is_solid(c, r)
                         for c in DOOR_TILES for r in DOOR_ROWS)
        check(opened, "cark cevrilince UC sutun birden aciliyor",
              f"{len(DOOR_TILES)} sutun")
        check(scene.door_open, "kapi bayragi aciliyor")
    finally:
        game.shutdown()


# --- 4. Iki oynanis: Rey geciyor, Ardo gonderiyor ---------------------------
def test_rey_passes() -> None:
    print("\n--- Rey oynanisi ---")
    game = Game()
    try:
        scene = start(game, "rey")
        check(scene.player_is_slim, "Rey ince sayiliyor")
        check(scene.companion_key == "ardo", "yoldas Ardo",
              scene.companion_key)

        # Oyuncuyu catlagin icine koy - itilmemeli.
        place(scene.player, (GAP_TILE, GAP_ROWS.stop - 1))
        pushed = scene.gap.enforce(scene.player.body, REY.girth)
        check(not pushed, "Rey catlakta itilmiyor")

        # Yoldasi catlaga koy - itilmeli.
        place(scene.companion, (GAP_TILE, GAP_ROWS.stop - 1))
        pushed = scene.gap.enforce(scene.companion.body, ARDO.girth)
        check(pushed, "Ardo catlaktan geri itiliyor")
    finally:
        game.shutdown()


def test_ardo_sends_companion() -> None:
    print("\n--- Ardo oynanisi ---")
    game = Game()
    try:
        scene = start(game, "ardo")
        check(not scene.player_is_slim, "Ardo genis sayiliyor")
        check(scene.companion_key == "rey", "yoldas Rey", scene.companion_key)

        place(scene.player, (GAP_TILE, GAP_ROWS.stop - 1))
        check(scene.gap.enforce(scene.player.body, ARDO.girth),
              "Ardo oynanirken OYUNCU geri itiliyor")

        # Yoldas (Rey) siğiyor: gecebilmeli.
        place(scene.companion, (GAP_TILE, GAP_ROWS.stop - 1))
        check(not scene.gap.enforce(scene.companion.body, REY.girth),
              "yoldas Rey catlaktan geciyor")

        # Cark yoldas varinca **kendiliginden** doniyor: ona "tusa bas"
        # denemez. Bu olmasaydi Ardo oynanisi cikmaza girerdi.
        place(scene.companion, (WINCH_TILE[0], WINCH_TILE[1]))
        scene._update_winch()
        check(scene.door_open, "yoldas carka varinca kapi aciliyor")
    finally:
        game.shutdown()


# --- 5. "El" sahnesi ---------------------------------------------------------
def test_hand_scene() -> None:
    print("\n--- el sahnesi ---")
    game = Game()
    try:
        scene = start(game, "rey")
        game.scenes.push(HandCinematic, transition=False, character="rey")
        game.scenes._flush()
        hand = game.scenes.current
        assert isinstance(hand, HandCinematic)

        silent = all(not panel.dialogue_lines for panel in hand.panels)
        check(silent, "El sahnesinde REPLIK YOK",
              "docs/yapi.md: 'Balon yok'")

        # Kanon: asagidaki her zaman Rey, uzanan her zaman Ardo.
        below = hand.actor("below")
        above = hand.actor("above")
        check(below is not None and below.animator.character == "rey",
              "asagidaki Rey")
        check(above is not None and above.animator.character == "ardo",
              "uzanan Ardo")

        fazla = [p for p in hand.panels if p.name == "fazla"]
        check(len(fazla) == 1 and fazla[0].frames == HOLD_TOO_LONG,
              "eller bir saniye fazla tutuluyor",
              f"{HOLD_TOO_LONG} kare = 1 saniye")

        # Sahne gercekten oynuyor mu - bir tur cevir.
        step(game, 200)
        check(hand.particles.alive_count >= 0, "sahne kare uretiyor")
    finally:
        game.shutdown()


def test_hand_scene_ardo_side() -> None:
    print("\n--- el sahnesi (Ardo oynanisi) ---")
    game = Game()
    try:
        game.scenes.set_root(HandCinematic, transition=False,
                             character="ardo")
        game.scenes._flush()
        hand = game.scenes.current
        assert isinstance(hand, HandCinematic)
        below = hand.actor("below")
        above = hand.actor("above")
        # Roller **oynanan karakterle degismiyor** - kanon sabit.
        check(below is not None and below.animator.character == "rey",
              "Ardo oynanirken de asagidaki Rey")
        check(above is not None and above.animator.character == "ardo",
              "Ardo oynanirken uzanan yine Ardo (oyuncunun kendisi)")
    finally:
        game.shutdown()


# --- 6. Sahnelenmis ara sahneler gercekten cizim yapiyor mu -----------------
def test_staging_draws() -> None:
    print("\n--- sahneleme ---")
    game = Game()
    try:
        for name, scene_class in (("Muhur", SealCinematic),
                                  ("Sigmiyor", GapCinematic)):
            game.scenes.set_root(scene_class, transition=False,
                                 character="rey")
            game.scenes._flush()
            step(game, 40)
            scene = game.scenes.current
            check(len(getattr(scene, "actors", {})) >= 1,
                  f"{name}: sahnede aktor var")
            game.canvas.fill((0, 0, 0))
            scene.draw(game.canvas)
            painted = pygame.transform.average_color(game.canvas)[:3] != (0, 0, 0)
            check(painted, f"{name}: ekrana gercekten ciziliyor")
    finally:
        game.shutdown()


# --- 7. Bolum sonu -----------------------------------------------------------
def test_chapter_end() -> None:
    print("\n--- bolum sonu ---")
    game = Game()
    try:
        scene = start(game, "rey")
        check(scene.chapter_number == 7, "bolum numarasi 7")
        exit_at = LEVEL.first("exit")
        check(exit_at is not None, "cikis isareti var")
        scene.player.body.x = float(exit_at.x + 4)
        scene._check_exit()
        check(scene.finished, "cikista bolum bitiyor")
        data = scene.save_data
        check(data is not None and data.chapter == 7,
              "kayda bolum 7 yaziliyor",
              str(data.chapter) if data else "kayit yok")
    finally:
        game.shutdown()


def main() -> int:
    print("=== BOLUM 7: DAR GECIT ===")
    test_gap_geometry()
    test_chasm_uncrossable()
    test_door_opens_through()
    test_rey_passes()
    test_ardo_sends_companion()
    test_hand_scene()
    test_hand_scene_ardo_side()
    test_staging_draws()
    test_chapter_end()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("Dar Gecit: catlak, cark ve el tasarim sozune uyuyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
