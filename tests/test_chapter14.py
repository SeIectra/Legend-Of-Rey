"""Bolum 14 "Yanki'nin Kaynagi" - twist, ihanet ve BOSS 3.

`docs/yapi.md` B14: *"Rey anlar: Yanki lanet degil, asagidaki seyin
sesi."* *Mekanik:* **Yanki tersine doner - actiginda dusmanlar da seni
gorur.**

Korunan kurallar:

  * **Ihanet gercek.** Bayrak aciksa duyuyu acmak menzildeki
    dusmanlari uyandiriyor; kapaliyken uyandirmiyor. Olculuyor.
  * **Gecikme var.** Bir an bakmak ile acik tutmak ayni sey degil -
    yoksa yanlislikla dokunan oyuncu cezalandirilir.
  * **Kalici ve MERKEZI.** Bayrak kayda yaziliyor, mekanizma
    `PlayScene`de: B15-B18 hicbir sey yazmadan devraliyor. Bir
    bolume ozel yazilsaydi bu test kirilsin.
  * **Ardo da kapsam disinda degil**: Iz Surme'yi acmak da ele
    veriyor. Ayni kural, baska kurgu.
  * **Bolumun tezi**: `Source.echo_visible is False` ve
    `Mimic.echo_visible is True`. Yanki gercegini gizliyor, yalanini
    gosteriyor. Ikisi ters donerse bolumun anlami kayboluyor.
  * **Katman 3 burada basliyor** - ucu de haritada, her biri kendi
    odasinda.
  * Boss olmeden cikis acilmiyor; olunce **olmedi** deniyor.

Calistir:
    python tests/test_chapter14.py
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

from src.config import (  # noqa: E402
    SENSE_BETRAYAL_DELAY, SENSE_BETRAYAL_RANGE, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.entities.bosses.source import MOVES, TELL, Mimic, Source  # noqa: E402
from src.scenes.chapter14 import Chapter14Scene  # noqa: E402
from src.scenes.chapter14_cinematics import (  # noqa: E402
    AfterCinematic, ArenaCinematic, SourceCinematic,
)
from src.systems.save import SaveData, read_save, write_save  # noqa: E402
from src.world.rooms.chapter14 import (  # noqa: E402
    FLOOR_TOP, LEVEL, ROOM_STARTS,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def start(game, character: str = "rey", betrayed: bool = False):
    write_save(SaveData(chapter=14, character=character,
                        abilities=["sword", "dodge", "echo_sight",
                                   "echo_ask"],
                        flags={"sense_betrayed": True} if betrayed else {}))
    game.scenes.set_root(Chapter14Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter14Scene)
    return scene


def open_sense(scene, frames: int) -> None:
    """Duyuyu `frames` kare acik tutar ve sahneyi ilerletir."""
    for _ in range(frames):
        if scene.echo is not None:
            scene.echo.update(True)
        if scene.tracking is not None:
            scene.tracking.update(True)
        scene._update_betrayal()


def awake(scene) -> int:
    return sum(1 for e in scene.enemies if e.aware and not e.dead)


# --- 1. Ihanet ★ --------------------------------------------------------------
def test_betrayal() -> None:
    """Bolumun tek mekanigi: **duyuyu acmak seni ele veriyor.**"""
    print("\n--- ihanet ---")
    game = Game()
    try:
        # Bayrak KAPALI: eski sozlesme, acmak bedava.
        before = start(game, betrayed=False)
        before._spawn_room("ters")
        for enemy in before.enemies:
            enemy.aware = False
            enemy.body.set_feet(before.player.body.center_x + 60,
                                FLOOR_TOP * TILE_SIZE)
        open_sense(before, SENSE_BETRAYAL_DELAY + 30)
        check(awake(before) == 0,
              "bayrak kapaliyken duyu acmak kimseyi uyandirmiyor",
              f"{awake(before)} uyanik")

        # Bayrak ACIK: ayni tus odayi uyandiriyor.
        after = start(game, betrayed=True)
        after._spawn_room("ters")
        for enemy in after.enemies:
            enemy.aware = False
            enemy.body.set_feet(after.player.body.center_x + 60,
                                FLOOR_TOP * TILE_SIZE)
        total = len(after.enemies)
        check(after.sense_betrayed, "bayrak kayittan okunuyor")
        open_sense(after, SENSE_BETRAYAL_DELAY + 30)
        check(awake(after) == total,
              "bayrak acikken duyu acmak MENZILDEKI HERKESI uyandiriyor",
              f"{awake(after)}/{total}")
        check(after.betrayal_wakes == total, "sahne kancasi her uyanmada tetikleniyor",
              str(after.betrayal_wakes))
    finally:
        game.quit()


def test_betrayal_has_grace() -> None:
    """Bir an bakmak ile acik tutmak ayni sey DEGIL."""
    print("\n--- gecikme ---")
    game = Game()
    try:
        scene = start(game, betrayed=True)
        scene._spawn_room("ters")
        for enemy in scene.enemies:
            enemy.aware = False
            enemy.body.set_feet(scene.player.body.center_x + 60,
                                FLOOR_TOP * TILE_SIZE)
        open_sense(scene, SENSE_BETRAYAL_DELAY - 4)
        check(awake(scene) == 0,
              "gecikme dolmadan kimse uyanmiyor - kisa bakis cezasiz",
              f"{SENSE_BETRAYAL_DELAY - 4} kare")
        open_sense(scene, 8)
        check(awake(scene) > 0, "gecikme dolunca uyaniyorlar")
    finally:
        game.quit()


def test_betrayal_respects_range() -> None:
    print("\n--- menzil ---")
    game = Game()
    try:
        scene = start(game, betrayed=True)
        scene._spawn_room("ters")
        far = scene.enemies[0]
        for enemy in scene.enemies:
            enemy.aware = False
        far.body.set_feet(scene.player.body.center_x
                          + SENSE_BETRAYAL_RANGE + 80, FLOOR_TOP * TILE_SIZE)
        for enemy in scene.enemies[1:]:
            enemy.body.set_feet(scene.player.body.center_x + 40,
                                FLOOR_TOP * TILE_SIZE)
        open_sense(scene, SENSE_BETRAYAL_DELAY + 20)
        check(not far.aware, "menzil disindaki uyanmiyor")
        check(all(e.aware for e in scene.enemies[1:]),
              "menzil icindekiler uyaniyor")
    finally:
        game.quit()


def test_betrayal_is_central_and_persistent() -> None:
    """**B15-B18 hicbir sey yazmadan devralmali.**

    Mekanizma `PlayScene`de, bayrak kayitta. Biri bunu bolume ozel
    hale getirirse bu test kirilsin: projede "her bolum bir satir
    eklemek zorunda" uc kez hatanin sekli oldu.
    """
    print("\n--- merkezi ve kalici ---")
    from src.scenes.play import PlayScene
    check(hasattr(PlayScene, "_update_betrayal"),
          "mekanizma PlayScene'de - bolume ozel degil")
    check(hasattr(PlayScene, "sense_open"),
          "duyu sorusu tek yerde (Yanki/Iz Surme ayrimi cagirana sizmiyor)")

    game = Game()
    try:
        scene = start(game, betrayed=False)
        check(not scene.sense_betrayed, "bolum ihanetsiz basliyor")
        scene._begin_betrayal()
        check(scene.sense_betrayed, "donus noktasi bayragi aciyor")
        check(scene.save_data.flags.get("sense_betrayed"),
              "bayrak KAYDA yazildi - sonraki bolumler devralacak")

        from src.systems.save import write_save as _w
        _w(scene.save_data)
        stored, _ = read_save()
        check(stored.flags.get("sense_betrayed"),
              "bayrak diske de gitti")
    finally:
        game.quit()


def test_betrayal_covers_ardo() -> None:
    """Ardo'nun Yankisi yok - **Iz Surme'yi acmak da ele veriyor.**"""
    print("\n--- Ardo da kapsamda ---")
    game = Game()
    try:
        scene = start(game, character="ardo", betrayed=True)
        check(scene.echo is None and scene.tracking is not None,
              "Ardo'da Yanki yok, Iz Surme var")
        scene._spawn_room("ters")
        for enemy in scene.enemies:
            enemy.aware = False
            enemy.body.set_feet(scene.player.body.center_x + 50,
                                FLOOR_TOP * TILE_SIZE)
        open_sense(scene, SENSE_BETRAYAL_DELAY + 20)
        check(awake(scene) == len(scene.enemies),
              "Iz Surme acmak da uyandiriyor - ayni kural, baska kurgu",
              f"{awake(scene)}/{len(scene.enemies)}")
    finally:
        game.quit()


# --- 2. Bolumun tezi ★ --------------------------------------------------------
def test_echo_lies() -> None:
    """**Yanki gercegini gizliyor, yalanini gosteriyor.**

    Iki satir, ve bolumun butun anlami onlarda. Ters donerlerse
    Bolum 14 sradan bir boss dovusune iner.
    """
    print("\n--- Yanki yalan soyluyor ---")
    check(Source.echo_visible is False,
          "KAYNAK Yanki'da GORUNMUYOR (Sessiz'in dersi, boss olcusunde)")
    check(Mimic.echo_visible is True,
          "SAHTE SURET Yanki'da GORUNUYOR - tez bu terslikte")

    game = Game()
    try:
        scene = start(game, betrayed=True)
        scene._spawn_room("arena")
        boss = scene.boss
        check(boss is not None, "arenada boss var")

        boss.phase = 1
        before = len(scene.enemies)
        boss._do_mimic()
        made = [e for e in scene.enemies[before:] if isinstance(e, Mimic)]
        check(len(made) == 2, "iki sahte suret cikti", str(len(made)))
        check(all(m.echo_visible for m in made),
              "suretlerin hepsi Yanki'da gorunuyor")
        check(all(m.damage == 0 for m in made),
              "sahte suret HASAR VERMIYOR - yalan bir tuzak degil bir soru")
        check(all(m.max_health == 1 for m in made),
              "tek vurusla dagiliyor - ceza hasar degil ZAMAN")
    finally:
        game.quit()


def test_mimic_expires() -> None:
    """Suret kendiliginden soluyor - hepsini oldurmek zorunlu degil."""
    print("\n--- suret soluyor ---")
    game = Game()
    try:
        scene = start(game)
        scene._spawn_room("arena")
        mimic = Mimic(scene, 400.0, FLOOR_TOP * TILE_SIZE)
        scene.enemies.append(mimic)
        mimic.life = 3
        for _ in range(8):
            mimic.update()
        check(mimic.dead, "omru dolan suret kendiliginden dagiliyor")
    finally:
        game.quit()


# --- 3. BOSS 3 ----------------------------------------------------------------
def test_source_phases() -> None:
    print("\n--- Kaynak: Katman 3'un atasi ---")
    check(len(MOVES) == 3, "uc faz", str(len(MOVES)))
    check("mimic" in MOVES[1], "faz 1 sahte suret (Yankilayan'in dersi)")
    check("split" in MOVES[2], "faz 2 gercekten boluniyor (Bolunen'in dersi)")
    short = {n: f for n, f in TELL.items() if f < 14}
    check(not short, "her hamlenin tell'i >= 14 kare (CLAUDE.md 7)",
          str(short) or "hepsi")

    game = Game()
    try:
        scene = start(game)
        scene._spawn_room("arena")
        boss = scene.boss
        # Suzuluyor: yercekimi yok, ve yeri degisiyor.
        check(boss.body.gravity_scale == 0.0, "yere basmiyor - suzuluyor")
        heights = []
        for _ in range(120):
            boss.update()
            heights.append(boss.body.feet[1])
        check(max(heights) > min(heights), "suzulme gercekten oynuyor",
              f"{min(heights):.1f}..{max(heights):.1f}")

        # Faz 2: gercek bolunme, ve ust sinir.
        boss.phase = 2
        before = len(scene.enemies)
        for _ in range(20):
            boss._do_split()
        from src.config import SOURCE_SPLIT_LIMIT
        check(boss.split_count <= SOURCE_SPLIT_LIMIT,
              "bolunme ust siniri tutuyor",
              f"{boss.split_count} <= {SOURCE_SPLIT_LIMIT}")
        check(len(scene.enemies) > before, "bolunme gercekten dusman ekliyor")

        # Bos tell yok: sinir dolunca sira atlaniyor.
        boss.move_index = list(MOVES[2]).index("split")
        check(boss._next_move() != "split",
              "bolunme siniri dolunca sira ATLANIYOR - bos tell yok")
    finally:
        game.quit()


# --- 4. Katman 3 burada basliyor ---------------------------------------------
def test_layer3_debuts() -> None:
    print("\n--- Katman 3 acilisi ---")
    kinds = {p.kind for p in LEVEL.placements}
    for name in ("silent", "echoing", "splitter"):
        check(name in kinds, f"{name} ILK KEZ bir bolume yerlestirildi")
    check("source" in kinds, "BOSS 3 haritada")

    # Her biri kendi odasinda taniticiyor - ayni desen B7'de de var.
    def room_of(tile_x: int) -> str:
        name = ROOM_STARTS[0][0]
        for room_name, start in ROOM_STARTS:
            if tile_x >= start:
                name = room_name
        return name

    first_silent = min(p.tile_x for p in LEVEL.of("silent"))
    first_echoing = min(p.tile_x for p in LEVEL.of("echoing"))
    first_splitter = min(p.tile_x for p in LEVEL.of("splitter"))
    check(room_of(first_silent) == "sessiz", "Sessiz kendi odasinda taniticiyor",
          room_of(first_silent))
    check(first_silent < first_echoing < first_splitter,
          "sira: once aracin EKSIGI, sonra YALANI, en sonda BECERI")


def test_first_rooms_use_old_contract() -> None:
    """Ihanet **odanin ortasinda** basliyor - once refleks tazelensin."""
    print("\n--- donus noktasinin yeri ---")
    from src.world.rooms.chapter14 import BETRAYAL_ROOM
    names = [n for n, _ in ROOM_STARTS]
    index = names.index(BETRAYAL_ROOM)
    check(index >= 2,
          "ilk iki oda ESKI sozlesmeyle oynaniyor - kirilacak refleks taze",
          f"{BETRAYAL_ROOM} {index}. oda")

    trigger_rooms = set()
    for spot in LEVEL.of("trigger"):
        name = names[0]
        for room_name, start in ROOM_STARTS:
            if spot.tile_x >= start:
                name = room_name
        trigger_rooms.add(name)
    check("sessiz" in trigger_rooms,
          "donus ara sahnesi ihanet odasindan ONCE tetikleniyor",
          str(sorted(trigger_rooms)))


# --- 5. Arena ve cikis --------------------------------------------------------
def test_arena_and_exit() -> None:
    print("\n--- arena ---")
    game = Game()
    try:
        scene = start(game)
        check(not scene.exit_open, "cikis basta kapali")
        start_tile, _ = scene._room_span("arena")
        scene.player.body.set_feet((start_tile + 8) * TILE_SIZE,
                                   FLOOR_TOP * TILE_SIZE)
        scene._enter_room("arena")
        scene._update_arena()
        check(scene.arena_sealed, "arenaya girince muhurleniyor")

        exit_at = LEVEL.first("exit")
        scene.player.body.set_feet(exit_at.x + 4, FLOOR_TOP * TILE_SIZE)
        scene._check_exit()
        check(not scene.finished, "boss olmeden cikis calismiyor")

        scene.boss.health = 0
        scene.boss.die()
        scene._update_arena()
        check(scene.boss_defeated and scene.exit_open,
              "boss dusunce cikis acildi")
    finally:
        game.quit()


def test_after_restart() -> None:
    print("\n--- olumden sonra arena ---")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("arena")
        check(scene.boss is not None, "boss dogdu")
        scene.setup()
        check(scene.boss is None, "setup sifirladi")
        scene.after_restart("arena")
        check(scene.boss is not None and not scene.boss.dead,
              "after_restart boss'u geri getiriyor")
        check(scene.arena_sealed, "muhur de geri geldi")
    finally:
        game.quit()


# --- 6. Ara sahneler ----------------------------------------------------------
def test_cinematics() -> None:
    print("\n--- ara sahneler ---")
    check(SourceCinematic.skippable is False,
          "KAYNAK sahnesi ATLANAMAZ - on uc bolumluk iliski yeniden taniniyor")

    game = Game()
    try:
        surface = pygame.Surface((480, 270))
        for scene_cls, name in ((SourceCinematic, "kaynak"),
                                (ArenaCinematic, "arena"),
                                (AfterCinematic, "olmedi")):
            for character in ("rey", "ardo"):
                game.scenes.set_root(scene_cls, transition=False,
                                     character=character)
                game.scenes._flush()
                scene = game.scenes.current
                for _ in range(120):
                    scene.update()
                    scene.draw(surface)
                check(True, f"{name} ({character}) 120 kare cokmeden oynuyor")
    finally:
        game.quit()


def test_cinematic_callback() -> None:
    """Donus noktasini sahne degil **bolum** tetikliyor."""
    print("\n--- geri cagirma ---")
    game = Game()
    try:
        fired = []
        game.scenes.set_root(SourceCinematic, transition=False,
                             character="rey", on_done=lambda: fired.append(1))
        game.scenes._flush()
        scene = game.scenes.current
        scene.on_finished()
        check(fired, "sahne bitince bolumun kancasi cagriliyor")
    finally:
        game.quit()


def main() -> int:
    test_betrayal()
    test_betrayal_has_grace()
    test_betrayal_respects_range()
    test_betrayal_is_central_and_persistent()
    test_betrayal_covers_ardo()
    test_echo_lies()
    test_mimic_expires()
    test_source_phases()
    test_layer3_debuts()
    test_first_rooms_use_old_contract()
    test_arena_and_exit()
    test_after_restart()
    test_cinematics()
    test_cinematic_callback()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("Bolum 14 tutarli - Yanki tersine dondu, tez korunuyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
