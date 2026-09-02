"""Bolum 17 "Ikili Kule" - ikili kontrol, tutulan kapilar.

`docs/yapi.md` B17: *"Ayri yollardan tirmanis, karakter arasi gecis.
Bulmaca: Biri kolu tutar, digeri gecer. **Sonra tersi.** Camdan/
parmakliktan birbirini gorursunuz ama dokunamazsiniz."*

Korunan kurallar:

  * **Iki oynanabilir karakter, tek girdi.** Yalnizca aktif olan komut
    aliyor; pasif olan yasamaya devam ediyor (yer cekimi, animasyon).
    Ikisi birden hareket ederse bolum cozulemez hale gelir.
  * **Pasif olan plakada DURUYOR.** Bulmacanin temeli bu: onu
    dondursaydik "birini plakada birak" diye bir sey olmazdi.
  * **Kapilar latch'lenmiyor** - plakadan inince kapaniyor. Arda'nin
    karari (02.09.2026); latch'li olsaydi mekanik bir dizi tek
    seferlik dugmeye donerdi.
  * **Kapi kimseyi tasin icinde birakmiyor** - sutunda biri dururken
    kapanmiyor.
  * **B6 bozulmadi**: `PlateGate` varsayilani hala latch'li, yoksa
    orada oyuncu arenaya hapsolabilirdi.
  * **Bulmaca gercekten cozulebiliyor ve gercekten zorunlu**: her
    katta kapali kapi gecisi engelliyor, dogru plaka onu aciyor.
  * **Zirvede biri kapiyi tutuyor** - cikis ancak oyle aciliyor.
  * Ara sahne iki karakterde de **cizim dahil** calisiyor.

Calistir:
    python tests/test_chapter17.py
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

from src.config import SWITCH_COOLDOWN, TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.core.input import NEUTRAL_INPUT, Action  # noqa: E402
from src.scenes.chapter17 import Chapter17Scene  # noqa: E402
from src.scenes.chapter17_cinematics import HeldDoorCinematic  # noqa: E402
from src.systems.save import SaveData, write_save  # noqa: E402
from src.ui.chapter_end import ChapterEndScene, ChapterResult  # noqa: E402
from src.world.plate import PlateGate  # noqa: E402
from src.world.rooms.chapter17 import (  # noqa: E402
    ALL_STAGES, LEFT_MAX, LEFT_MIN, LEVEL, RIGHT_MAX, RIGHT_MIN, SPAWN_RIGHT,
    TIDY_BONUS, open_terrain,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def start(game, character: str = "rey") -> Chapter17Scene:
    write_save(SaveData(
        chapter=17, character=character,
        abilities=["sword", "dodge", "echo_sight", "echo_ask"], flags={}))
    game.scenes.set_root(Chapter17Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter17Scene)
    return scene


def stand_on(player, tile_x: int, tile_y: int) -> None:
    """Karakteri bir tile'in **ustune** koyar (plaka hizasi)."""
    player.body.set_feet(tile_x * TILE_SIZE + TILE_SIZE * 0.5,
                         tile_y * TILE_SIZE)


def run(scene, frames: int) -> None:
    game = scene.game
    for _ in range(frames):
        game.input.begin_frame()
        game.input.end_frame()
        scene.update()
        game.frame += 1


def in_left(tile_x: int) -> bool:
    return LEFT_MIN <= tile_x <= LEFT_MAX


# --- 1. Ikili kontrol ★ -------------------------------------------------------
def test_only_one_is_controlled() -> None:
    """Iki `Player`, tek girdi. Ikisi birden hareket ederse bolum biter."""
    print("\n--- yalnizca biri kontrol ediliyor ---")
    game = Game()
    try:
        scene = start(game)
        check(scene.left is not scene.right, "iki AYRI karakter var")
        check(scene.player is scene.left, "basta soldaki oynaniyor")
        check(scene.left.controlled and not scene.right.controlled,
              "yalnizca aktif olan komut aliyor")

        scene.duo.switch()
        scene.player = scene.duo.active
        check(scene.player is scene.right, "gecisten sonra sagdaki oynaniyor")
        check(scene.right.controlled and not scene.left.controlled,
              "kontrol tam olarak yer degistirdi")
        check(sum(p.controlled for p in scene.duo.players) == 1,
              "her zaman TAM BIR tane kontrol ediliyor")
    finally:
        game.quit()


def test_passive_keeps_living() -> None:
    """Pasif olan durmuyor - yer cekimi ve animasyon isliyor.

    Bulmacanin temeli: plakada birakilan karakter orada **durmaya
    devam ediyor**. Dondurulsaydi plaka mantigi ("ustunde biri var mi")
    calismazdi.
    """
    print("\n--- pasif olan yasiyor ---")
    game = Game()
    try:
        scene = start(game)
        passive = scene.duo.other
        passive.body.set_feet(passive.body.center_x,
                              passive.body.feet[1] - TILE_SIZE * 3)
        passive.body.grounded = False
        before = passive.body.feet[1]
        run(scene, 30)
        check(passive.body.feet[1] > before,
              "pasif karaktere yer cekimi isliyor",
              f"{before:.0f} -> {passive.body.feet[1]:.0f}")
        check(passive.body.grounded, "ve yere indi")
        check(NEUTRAL_INPUT.held(Action.RIGHT) is False,
              "notr girdi hicbir seye evet demiyor")
    finally:
        game.quit()


def test_switch_has_a_cooldown() -> None:
    print("\n--- gecis beklemesi ---")
    game = Game()
    try:
        scene = start(game)
        check(scene.duo.switch(), "ilk gecis oldu")
        check(not scene.duo.switch(), "hemen ardindan ikincisi OLMADI")
        for _ in range(SWITCH_COOLDOWN):
            scene.duo.update()
        check(scene.duo.switch(), "bekleme bitince yeniden gecilebiliyor")
        check(scene.duo.switches == 2, "sayac yalnizca gercek gecisleri sayiyor",
              str(scene.duo.switches))
    finally:
        game.quit()


# --- 2. Kapilar ★ -------------------------------------------------------------
def test_gates_are_not_latching() -> None:
    """*"Biri kolu TUTAR."* Birakinca kapanmali."""
    print("\n--- kapi basili tutuldugu surece acik ---")
    check(PlateGate(0, (0,), ()).latching,
          "varsayilan hala LATCH'LI - Bolum 6 bozulmadi")
    game = Game()
    try:
        scene = start(game)
        stage = ALL_STAGES[0]
        gate = scene.gates[0]
        plate_x, plate_y = stage["plates"][0]
        holder = scene.left if in_left(plate_x) else scene.right

        check(not gate.latching, "bu bolumun kapilari latch'siz")
        check(not gate.open, "basta kapali")
        row = stage["gate_rows"][0]
        check(scene.tilemap.is_solid(gate.column, row),
              "ve haritada gercekten TAS")

        stand_on(holder, plate_x, plate_y)
        run(scene, 6)
        check(gate.open, "plakaya basilinca acildi")
        check(not scene.tilemap.is_solid(gate.column, row),
              "harita da acildi - carpisma gercek")

        stand_on(holder, plate_x + 5, plate_y)
        run(scene, 40)
        check(not gate.open, "plakadan inince KAPANDI")
        check(scene.tilemap.is_solid(gate.column, row), "harita da kapandi")
    finally:
        game.quit()


def test_gate_never_closes_on_someone() -> None:
    """Kapanan kapi kimseyi tasin icinde birakmiyor."""
    print("\n--- kapi kimseyi ezmiyor ---")
    game = Game()
    try:
        scene = start(game)
        stage = ALL_STAGES[0]
        gate = scene.gates[0]
        plate_x, plate_y = stage["plates"][0]
        holder = scene.left if in_left(plate_x) else scene.right
        passer = scene.right if holder is scene.left else scene.left

        stand_on(holder, plate_x, plate_y)
        run(scene, 6)
        check(gate.open, "kapi acildi")

        # Gecen karakteri tam kapinin icine koy, sonra plakadan in.
        stand_on(passer, gate.column, max(stage["gate_rows"]) + 1)
        stand_on(holder, plate_x + 5, plate_y)
        run(scene, 40)
        check(gate.open,
              "sutunda biri dururken kapi KAPANMADI - bekliyor")

        # Cekilince kapaniyor.
        stand_on(passer, gate.column + 3, max(stage["gate_rows"]) + 1)
        run(scene, 10)
        check(not gate.open, "temizlenince kapandi")
    finally:
        game.quit()


# --- 3. Bulmaca gercek mi ★ ---------------------------------------------------
def test_every_stage_is_gated_and_solvable() -> None:
    """Her katta kapi gecisi ENGELLIYOR ve dogru plaka onu ACIYOR.

    Iki iddia birden: kapi olmasaydi bulmaca sus olurdu, plaka
    acmasaydi bolum gecilemezdi. Ikisi de her kat icin olculuyor.
    """
    print("\n--- her kat hem kapali hem cozulebilir ---")
    game = Game()
    try:
        scene = start(game)
        for index, stage in enumerate(ALL_STAGES):
            gate = scene.gates[index]
            name = "zirve" if index == len(ALL_STAGES) - 1 else f"kat {index}"
            rows = stage["gate_rows"]
            check(all(scene.tilemap.is_solid(gate.column, r) for r in rows),
                  f"{name}: kapi basta gecisi engelliyor",
                  f"sutun {gate.column}")

            # Plakayi tutan karakter kapinin OTEKI saftinda olmali -
            # bulmacanin tanimi bu.
            plate_x, plate_y = stage["plates"][0]
            check(in_left(plate_x) is not in_left(gate.column),
                  f"{name}: plaka kapinin OTEKI saftinda")

            holder = scene.left if in_left(plate_x) else scene.right
            stand_on(holder, plate_x, plate_y)
            run(scene, 6)
            check(all(not scene.tilemap.is_solid(gate.column, r)
                      for r in rows),
                  f"{name}: dogru plaka kapiyi aciyor")
            # Temizle - sonraki kat kendi basina olculsun.
            stand_on(holder, plate_x + 5, plate_y)
            run(scene, 40)
    finally:
        game.quit()


def test_exit_needs_the_other_one() -> None:
    """Zirve: cikis ancak oteki kapiyi tutarken aciliyor.

    `docs/gdd.md` 11 B17: *"Biri olmadan gecilmiyor."* Bolumun son
    hareketi bunun goruntusu.
    """
    print("\n--- cikis otekine bagli ---")
    game = Game()
    try:
        scene = start(game)
        exit_at = LEVEL.first("exit")
        summit = ALL_STAGES[-1]
        gate = scene.gates[-1]
        check(in_left(exit_at.tile_x), "cikis SOL safta", str(exit_at.tile_x))
        check(in_left(gate.column), "onundeki kapi da solda")
        plate_x, _ = summit["plates"][0]
        check(not in_left(plate_x),
              "ama kapiyi acan plaka SAG safta - tutan oteki",
              str(plate_x))
        check(exit_at.tile_x < gate.column,
              "cikis kapinin OTESINDE - kapi acilmadan varilamaz",
              f"cikis {exit_at.tile_x} < kapi {gate.column}")
    finally:
        game.quit()


def test_both_shafts_climb_alone() -> None:
    """Kapilar acikken **her saft kendi basina** tirmanilabiliyor.

    Bu, bulmacanin cozulebilir oldugunun geometrik kaniti: kapi
    acildiktan sonra karakterin ziplayarak cikamamasi bolumun
    kilitlenmesi demek olurdu. Ayni kontrolu `tools/reachability.py`
    da yapiyor; burada **sartin varligi** korunuyor.
    """
    print("\n--- kapilar acikken saftlar tirmanilabiliyor ---")
    rows = open_terrain()
    for stage in ALL_STAGES:
        column = stage["gate_column"]
        check(all(rows[r][column] != "#" for r in stage["gate_rows"]),
              f"sutun {column}: dogrulama haritasinda kapi acik")
    check(len(rows) == len(LEVEL.terrain_rows),
          "dogrulama haritasi ayni olculerde")
    left_spawn = LEVEL.first("player")
    check(in_left(left_spawn.tile_x), "sol dogum sol safta")
    check(RIGHT_MIN <= SPAWN_RIGHT[0] <= RIGHT_MAX, "sag dogum sag safta")


# --- 4. Ara sahne ★ -----------------------------------------------------------
def test_cinematic_plays_for_both() -> None:
    """Ikisi de, **cizim dahil** - projedeki en pahali kor nokta."""
    print("\n--- kapanis (iki karakter, cizim dahil) ---")
    for character in ("rey", "ardo"):
        game = Game()
        try:
            game.scenes.set_root(HeldDoorCinematic, transition=False,
                                 character=character)
            game.scenes._flush()
            for _ in range(260):
                game.input.begin_frame()
                game.input.end_frame()
                game.scenes.update()
                game.canvas.fill((0, 0, 0, 255))
                game.scenes.draw(game.canvas)
                game.frame += 1
            check(True, f"kapanis ({character}) cokmeden oynuyor")
        except Exception as exc:       # noqa: BLE001 - test raporluyor
            check(False, f"kapanis ({character})",
                  f"{type(exc).__name__}: {exc}")
        finally:
            game.quit()


def test_scene_draws_both_players() -> None:
    """Sahne pasif karakteri de ciziyor - `PlayScene` yalnizca aktifi biliyor.

    Bolum 16'da tam bu satir unutulmustu ve yoldas gorunmez kalmisti.
    """
    print("\n--- iki karakter de ciziliyor ---")
    game = Game()
    try:
        scene = start(game)
        for _ in range(30):
            game.input.begin_frame()
            game.input.end_frame()
            game.scenes.update()
            game.canvas.fill((0, 0, 0, 255))
            game.scenes.draw(game.canvas)
            game.frame += 1
        check(True, "30 kare cizimle gecti (cokme yok)")
        import inspect
        source = inspect.getsource(Chapter17Scene)
        check("self.duo.other.draw" in source, "pasif karakter ciziliyor")
        check("self.duo.other.update" in source, "pasif karakter guncelleniyor")
    finally:
        game.quit()


# --- 5. Bolum sonu ------------------------------------------------------------
def test_tidy_reward_is_visible() -> None:
    print("\n--- verimlilik odulu gorunuyor ---")
    game = Game()
    try:
        def ghost_row(tidy: bool):
            result = ChapterResult(
                chapter_key="chapter.twintower", frames=60, best_combo=0,
                gold=100, secrets_found=1, secrets_total=1,
                ghost=tidy, ghost_bonus=TIDY_BONUS)
            end = ChapterEndScene(game)
            end.on_enter(result=result)
            for label, value, role in end._rows():
                if label == "chapter_end.ghost":
                    return value, role
            return None, None

        kept, kept_role = ghost_row(True)
        missed, missed_role = ghost_row(False)
        check(kept is not None and missed is not None,
              "satir iki durumda da var")
        check(str(TIDY_BONUS) in missed,
              "kaciran da odulun buyuklugunu goruyor", missed)
        check(kept_role == "reward" and missed_role != "danger",
              "kazanan altin, kaciran kirmizi DEGIL",
              f"{kept_role} / {missed_role}")
    finally:
        game.quit()


def test_chapter_shape() -> None:
    print("\n--- bolum sekli ---")
    check(len(ALL_STAGES) == 6, "bes kat + zirve", str(len(ALL_STAGES)))
    sides = [in_left(s["plates"][0][0]) for s in ALL_STAGES]
    check(all(sides[i] != sides[i + 1] for i in range(len(sides) - 1)),
          "plakalar DEGISIMLI - 'sonra tersi'", str(sides))
    kinds = {p.kind for p in LEVEL.placements}
    check("chest" in kinds and "exit" in kinds, "sandik ve cikis var")
    check(len(LEVEL.of("trigger")) == 1, "tek ara sahne tetikleyicisi")
    check(len(LEVEL.of("player")) == 1,
          "haritada tek isaretli dogum - oteki sabit (SPAWN_RIGHT)")
    # Dusman yok: `docs/gdd.md` 11 B17'yi dovus dongusunu kiran dort
    # bolumden biri sayiyor.
    enemies = [p for p in LEVEL.placements
               if p.kind not in ("player", "chest", "exit", "trigger")]
    check(not enemies, "dusman YOK - bulmaca bolumu", str(len(enemies)))


def main() -> int:
    test_only_one_is_controlled()
    test_passive_keeps_living()
    test_switch_has_a_cooldown()
    test_gates_are_not_latching()
    test_gate_never_closes_on_someone()
    test_every_stage_is_gated_and_solvable()
    test_exit_needs_the_other_one()
    test_both_shafts_climb_alone()
    test_cinematic_plays_for_both()
    test_scene_draws_both_players()
    test_tidy_reward_is_visible()
    test_chapter_shape()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("Bolum 17 tutarli - biri tutuyor, digeri geciyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
