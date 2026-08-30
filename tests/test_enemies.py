"""Katman 2 ve 3'un dusmanlari - **davranis** testleri.

`docs/gdd.md` 7 her dusmani tek bir cumleyle tanimliyor. Bu test o
cumlelerin kodda gercekten karsiligi olup olmadigini soruyor; sinifin
yuklendigini degil.

    Kalkanli    onden vurulmaz, arkaya gec          (B5'te yazildi)
    Mizrakli    uzun menzil, yaklasmayi engeller    (B10)
    Okcu        uzaktan bozar, once susturulmali
    Komutan     takviye cagirir, kalabalik yonetimi
    Sessiz      Yanki onu gostermez
    Yankilayan  sesini taklit eder, sahte ipucu
    Bolunen     vurunca ikiye ayrilir

Katman 3'un ucu de **yardimci sistemin kendisine** saldiriyor: biri
eksiltiyor, biri kirletiyor, biri oyuncunun becerisini aleyhine
ceviriyor. Test o uc farkin gercekten farkli oldugunu koruyor.

Calistir:
    python tests/test_enemies.py
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

from src.combat.hitbox import Hitbox, Team  # noqa: E402
from src.config import (  # noqa: E402
    ARCHER_ARROW_SPEED, ARCHER_FLEE_RANGE, ARCHER_SHOT_RANGE,
    COMMANDER_SUMMON_LIMIT, SILENT_AMBUSH_RANGE, SPEARMAN_REACH,
    SPLITTER_GENERATIONS, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.entities.enemies.archer import Archer  # noqa: E402
from src.entities.enemies.commander import Commander  # noqa: E402
from src.entities.enemies.echoing import Echoing  # noqa: E402
from src.entities.enemies.silent import Silent  # noqa: E402
from src.entities.enemies.splitter import Splitter  # noqa: E402
from src.entities.enemy import EnemyState  # noqa: E402
from src.scenes.chapter10 import Chapter10Scene  # noqa: E402
from src.systems.save import SaveData, write_save  # noqa: E402

# Zemin satiri 14 (`rooms/chapter10.py` FLOOR_TOP), yani ayaklar
# **onun ustunde**: 14 * 16. Ilk surumde 13 * 16 verilmisti ve
# dusmanlar bir tile havada duruyordu - Komutan'in "altimda zemin var
# mi" kontrolu hakli olarak reddediyordu ve test kodu suclamisti.
FEET_Y = 14 * TILE_SIZE

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def arena(game):
    """Gercek bir bolum sahnesi - tilemap, zemin, hitbox yoneticisi.

    Sahte bir sahne yazmak daha hizli olurdu ve daha az sey sinardi:
    mermi duvarda olsun diye `hitboxes.tilemap` gerek, cagirilan
    dusmanin altinda zemin gerek. Gercek sahne bunlari zaten kuruyor.
    """
    write_save(SaveData(chapter=10, character="rey",
                        abilities=["sword", "dodge"]))
    game.scenes.set_root(Chapter10Scene, transition=False, character="rey")
    game.scenes._flush()
    scene = game.scenes.current
    scene.enemies.clear()
    return scene


def player_hitbox(scene, finisher: bool = False) -> Hitbox:
    box = Hitbox(rect=pygame.Rect(0, 0, 20, 20), damage=12,
                 owner=scene.player, targets=Team.ENEMY,
                 is_finisher=finisher)
    return box


# --- Okcu --------------------------------------------------------------------
def test_archer() -> None:
    print("\n--- Okcu: uzaktan bozar, once susturulmali ---")
    check(ARCHER_SHOT_RANGE > SPEARMAN_REACH * 3,
          "atis menzili Mizrakli'dan cok daha uzun",
          f"{ARCHER_SHOT_RANGE} vs {SPEARMAN_REACH}")
    check(ARCHER_FLEE_RANGE < ARCHER_SHOT_RANGE,
          "kacma mesafesi atis menzilinin icinde")

    game = Game()
    try:
        scene = arena(game)
        archer = Archer(scene, 300.0, FEET_Y)
        scene.enemies.append(archer)
        archer.aware = True

        # Oyuncu YAKIN: kacmali, saldirmamali.
        scene.player.body.set_feet(archer.body.center_x + 10,
                                   archer.body.feet[1])
        archer._approach()
        away = -1 if scene.player.body.center_x > archer.body.center_x else 1
        check((archer.body.vx > 0) == (away > 0) and archer.body.vx != 0,
              "yaklasandan KACIYOR - 'once susturulmali' bunu gerektiriyor",
              f"vx={archer.body.vx:.2f}")

        # Ok gercekten bir mermi: hareket ediyor.
        scene.player.body.set_feet(archer.body.center_x - 120,
                                   archer.body.feet[1])
        archer.facing = -1
        before = len(scene.hitboxes.boxes)
        archer._spawn_attack()
        check(len(scene.hitboxes.boxes) == before + 1, "ok firlatildi")
        arrow = scene.hitboxes.boxes[-1]
        check(arrow.velocity[0] < 0, "ok bakilan yone gidiyor",
              str(arrow.velocity))
        start_x = arrow.rect.x
        for _ in range(5):
            arrow.update()
        check(arrow.rect.x < start_x, "ok gercekten ILERLIYOR",
              f"{start_x} -> {arrow.rect.x}")
        check(arrow.stop_on_solid, "ok duvarda oluyor")
    finally:
        game.shutdown()


# --- Komutan -----------------------------------------------------------------
def test_commander() -> None:
    print("\n--- Komutan: takviye cagirir ---")
    game = Game()
    try:
        scene = arena(game)
        commander = Commander(scene, 300.0, FEET_Y)
        scene.enemies.append(commander)
        commander.aware = True
        scene.player.body.set_feet(360.0, commander.body.feet[1])

        before = len(scene.enemies)
        commander._spawn_attack()
        check(len(scene.enemies) == before + 1, "takviye geldi",
              f"{before} -> {len(scene.enemies)}")
        summoned = next((e for e in scene.enemies if e is not commander),
                        None)
        check(summoned is not None and summoned.aware,
              "cagirilan UYANIK doguyor")
        check(summoned is not None
              and not scene.tilemap.solid_overlap(summoned.body.rect),
              "duvarin icine cagirmiyor")

        # **Ust sinir.** Sinirsiz olsaydi zorluk beceriyle ters
        # orantili olurdu - bir olum sarmalinin tanimi.
        for _ in range(10):
            commander._spawn_attack()
        check(commander.summoned == COMMANDER_SUMMON_LIMIT,
              "ust sinir korunuyor", str(commander.summoned))
        check(not commander.can_summon, "sinir dolunca cagiramiyor")

        # Kesilebilir olmali: "komutani sustur" bir mekanik.
        fresh = Commander(scene, 500.0, FEET_Y)
        fresh._set_state(EnemyState.TELL)
        fresh.banner = 0.8
        fresh.on_attack_cancelled()
        check(fresh.banner == 0.0,
              "sendeleyince cagirma IPTAL - susturmak ise yariyor")
    finally:
        game.shutdown()


# --- Sessiz ------------------------------------------------------------------
def test_silent() -> None:
    print("\n--- Sessiz: Yanki onu gostermez ---")
    check(Silent.echo_visible is False,
          "Yanki'nin siluetinde YOK - Katman 3'un ilk ihaneti")

    game = Game()
    try:
        scene = arena(game)
        silent = Silent(scene, 400.0, FEET_Y)
        scene.enemies.append(silent)

        # Uzaktan uyanmiyor - pusu.
        scene.player.body.set_feet(silent.body.center_x + 200,
                                   silent.body.feet[1])
        silent._update_awareness()
        check(not silent.roused and not silent.aware,
              "uzaktan uyanmiyor - pusu gercek")

        scene.player.body.set_feet(
            silent.body.center_x + SILENT_AMBUSH_RANGE - 6,
            silent.body.feet[1])
        silent._update_awareness()
        check(silent.roused and silent.aware, "yaklasinca kalkiyor")

        # Bir kez kalkinca bir daha yatmiyor.
        scene.player.body.set_feet(silent.body.center_x + 300,
                                   silent.body.feet[1])
        silent._update_awareness()
        check(silent.roused, "kalkan bir daha yatmiyor - sinir bozmasin")

        # Gorunmezlik bir SIR degil: sprite ciziliyor.
        check(silent.animator is not None,
              "ekranda ciziliyor - gozle bulunabilir")
    finally:
        game.shutdown()


# --- Yankilayan --------------------------------------------------------------
def test_echoing() -> None:
    print("\n--- Yankilayan: sahte ipucu ---")
    game = Game()
    try:
        scene = arena(game)
        echoing = Echoing(scene, 400.0, FEET_Y)
        scene.enemies.append(echoing)
        echoing.aware = True
        scene.player.body.set_feet(300.0, echoing.body.feet[1])

        seen: list[tuple[float, float]] = []
        scene.on_false_hint = lambda e, x, y: seen.append((x, y))
        echoing._plant_hint()
        check(echoing.false_hint is not None, "sahte isaret kondu")
        check(seen, "sahne haberdar ediliyor - cizimi bolum yapiyor")

        # **Kendi arkasina** koyuyor: oyuncu ona giderken yanindan
        # gecmek zorunda. Onune konsaydi bir uyari islevi gorurdu.
        hint_x = echoing.false_hint[0]
        player_x = scene.player.body.center_x
        check(abs(hint_x - player_x) > abs(echoing.body.center_x - player_x),
              "isaret Yankilayan'in ARKASINDA",
              f"oyuncu {player_x:.0f}, dusman {echoing.body.center_x:.0f},"
              f" isaret {hint_x:.0f}")

        # Olunce yalani da oluyor - "once onu sustur".
        echoing.health = 0
        echoing.die()
        echoing.update()
        check(echoing.false_hint is None,
              "olunce sahte isaret kayboluyor")
    finally:
        game.shutdown()


# --- Bolunen -----------------------------------------------------------------
def test_splitter() -> None:
    print("\n--- Bolunen: vurunca ikiye ayrilir ---")
    game = Game()
    try:
        scene = arena(game)
        splitter = Splitter(scene, 400.0, FEET_Y)
        scene.enemies.append(splitter)

        box = player_hitbox(scene)
        box.rect.center = (int(splitter.body.center_x),
                           int(splitter.body.center_y))
        before = len(scene.enemies)
        splitter.take_damage(box, (1.0, 0.0))
        children = [e for e in scene.enemies if isinstance(e, Splitter)
                    and e is not splitter]
        check(len(scene.enemies) > before, "vurunca cogaldi",
              f"{before} -> {len(scene.enemies)}")
        check(len(children) == 2, "IKIYE ayrildi", str(len(children)))
        check(all(c.generation == 1 for c in children), "nesil arttı")
        check(all(c.max_health < splitter.max_health for c in children),
              "parcalar daha zayif",
              f"{splitter.max_health} -> {children[0].max_health}")
        check(children[0].body.vx * children[1].body.vx < 0,
              "iki parca ZIT yone savruluyor")

        # **Bitirici bolmuyor** - ders "combo yapma" degil "combo'yu bitir".
        clean = Splitter(scene, 600.0, FEET_Y)
        scene.enemies.append(clean)
        finisher = player_hitbox(scene, finisher=True)
        finisher.rect.center = (int(clean.body.center_x),
                                int(clean.body.center_y))
        count = len(scene.enemies)
        clean.take_damage(finisher, (1.0, 0.0))
        check(len(scene.enemies) == count,
              "BITIRICI vurus bolmuyor - zinciri tamamlamak cozum")

        # Nesil siniri: sonsuza bolunmuyor.
        deep = Splitter(scene, 700.0, FEET_Y,
                        generation=SPLITTER_GENERATIONS)
        check(not deep.can_split, "son nesil artik bolunmuyor")
    finally:
        game.shutdown()


# --- Katman 3'un ucu birbirinden farkli --------------------------------------
def test_layer3_distinct() -> None:
    print("\n--- Katman 3: uc ayri ihanet ---")
    check(Silent.echo_visible is False and Echoing.echo_visible is True,
          "Sessiz gizleniyor, Yankilayan GORUNUYOR - biri eksiltiyor,"
          " oteki kirletiyor")
    check(hasattr(Echoing, "_plant_hint") and not hasattr(Silent,
                                                          "_plant_hint"),
          "sahte ipucu yalnizca Yankilayan'da")
    check(hasattr(Splitter, "can_split")
          and not hasattr(Echoing, "can_split"),
          "bolunme yalnizca Bolunen'de")


# --- 7. Cizim gercekten calisiyor mu -----------------------------------------
def test_draw_extra_runs() -> None:
    """Her dusmanin `draw_extra`si cagrilabiliyor mu.

    Bu test bir hatadan dogdu. `Echoing.draw_extra` `self.frames`
    okuyordu ama `Enemy`de oyle bir alan **yoktu** - yani sahte isaret
    ekrana gelir gelmez oyun cokerdi. Butun davranis testleri yesildi
    cunku hicbiri CIZIM cagirmiyordu.

    Ders: bir dusmanin sozlesmesi yalnizca ne yaptigi degil, ekranda
    gorunebildigi de. Ozel cizimi olan her dusman buraya girer.
    """
    print("\n--- cizim ---")
    game = Game()
    try:
        scene = arena(game)
        surface = pygame.Surface((480, 270))
        specimens = (
            ("Okcu", Archer), ("Komutan", Commander), ("Sessiz", Silent),
            ("Yankilayan", Echoing), ("Bolunen", Splitter),
        )
        for name, cls in specimens:
            enemy = cls(scene, 200.0, FEET_Y)
            scene.enemies.append(enemy)
            enemy.aware = True
            # Ozel cizimlerin cogu bir durum bekliyor (sancak, sahte
            # isaret, yay gerilimi) - once birkac kare yasat.
            for _ in range(90):
                enemy.update()
                enemy.draw(surface, (0, 0))
                enemy.draw_extra(surface, (0, 0))
            check(True, f"{name}: 90 kare cizim cokmeden calisiyor")
            # Tell sirasinda da: gorsellerin cogu tam orada devreye
            # giriyor ve tam orada patlar.
            enemy._set_state(EnemyState.TELL)
            for _ in range(20):
                enemy.update()
                enemy.draw_extra(surface, (0, 0))
            check(True, f"{name}: tell sirasinda cizim calisiyor")

            # **Renk korlugu sozlesmesi** (`CLAUDE.md` 10): tehlike
            # asla yalnizca renkle anlatilmaz - tell sirasinda siluet
            # de degisir. Alti dusman bu metodu bir `float` alaniyla
            # gölgelemişti, yani sekil kanali sessizce olmustu.
            check(callable(type(enemy).silhouette_scale),
                  f"{name}: silhouette_scale bir METOD (float degil)")
            enemy._set_state(EnemyState.TELL)
            enemy.state_frames = max(1, enemy.tell_frames - 2)
            wide, tall = enemy.silhouette_scale()
            check(tall > 1.0,
                  f"{name}: tell'de siluet SISIYOR - sekil kanali canli",
                  f"{wide:.2f}x{tall:.2f}")
    finally:
        game.quit()


def main() -> int:
    print("=== KATMAN 2 ve 3 DUSMANLARI ===")
    test_archer()
    test_commander()
    test_silent()
    test_echoing()
    test_splitter()
    test_layer3_distinct()
    test_draw_extra_runs()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("Bes dusman da belgedeki cumlesini gercekten yapiyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
