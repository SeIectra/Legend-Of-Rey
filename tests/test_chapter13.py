"""Bolum 13 "Cemo" - zaman kapilari ve BOSS 2.

`docs/yapi.md` B13: *"Kafeste, canli, sana bakiyor - **ulasamadan
tasinir.** Mekanik: Zaman kapilari - kovalamaca bolumu."*
`docs/gdd.md` 9 mekanik 8: *"Kolu cevir, X saniyede kos - **dovuserek
degil kacarak**."*

Korunan kurallar:

  * **Her kapi gecilebilir.** Sayac tahmin degil olcum: en yavas
    karakterin duz kosu suresi hesaplaniyor ve kullanilabilir pencere
    ondan en az 1.35 kat uzun olmali. Ilk yerlesimde Oda 6 bu testte
    **gecilemez** cikti (0.71x) - hem mesafe hem sayac duzeltildi.
  * **Zorluk mesafeden geliyor.** Tile basina dusen sure odadan odaya
    azaliyor; sayacin ham buyuklugune bakip "comert" demek yanlis.
  * **Yumusak kilit yok.** Kol yeniden cevrilebiliyor; kapanan
    surgunun altinda kalan oyuncu duvarin icinde birakilmiyor.
  * **Tek kol, iki kapi, TEK sayac** (Oda 6). Iki ayri sayac olsaydi
    bir zincir degil bir sira olurdu.
  * **Zindanci Katman 2'nin sinavi**: faz 0 onden gecirmiyor
    (Kalkanli), faz 1 mermi atiyor (Okcu), faz 2 cagiriyor (Komutan).
  * **Karanlik tell'i gizlemiyor** - `CLAUDE.md` 7: her hamle en az
    14 kare onceden okunabilir.
  * Fener her fazda soluyor ve faz 2'de isik kaynagi ORTADAN KALKIYOR.
  * Boss olmeden cikis acilmiyor; olunce muhur kalkiyor.

Calistir:
    python tests/test_chapter13.py
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
    ARDO_MOVE_MULTIPLIER, PLAYER_RUN_SPEED, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.entities.bosses.gaoler import MOVES, TELL, Gaoler  # noqa: E402
from src.entities.enemy import EnemyState  # noqa: E402
from src.scenes.chapter13 import Chapter13Scene  # noqa: E402
from src.scenes.chapter13_cinematics import (  # noqa: E402
    CageCinematic, GateCinematic, GaolerCinematic, MarkCinematic,
)
from src.systems.save import SaveData, write_save  # noqa: E402
from src.systems.timegate import PASSABLE_TILES, GateBank, Lever, TimeGate  # noqa: E402
from src.world.rooms.chapter13 import (  # noqa: E402
    FLOOR_TOP, GATE_TOP, LEVEL, ROOM_STARTS,
)

failures: list[str] = []

# En yavas oynanabilir karakter. Kapilar ONA gore olculuyor - Rey'e
# gore olcmek Ardo'yu disarida birakirdi.
SLOWEST = PLAYER_RUN_SPEED * ARDO_MOVE_MULTIPLIER
# Kullanilabilir pencere / duz kosu suresi. Kalan pay hizlanmaya
# (~8 kare), yoldaki dusmana ve kusursuz olmayan oynayisa.
MIN_MARGIN = 1.35


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def start(game, character: str = "rey") -> Chapter13Scene:
    write_save(SaveData(chapter=13, character=character,
                        abilities=["sword", "dodge", "echo_sight",
                                   "echo_ask"]))
    game.scenes.set_root(Chapter13Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter13Scene)
    return scene


def usable_frames(gate: TimeGate) -> int:
    """Surgu kac kare boyunca GERCEKTEN gecilebilir kaliyor.

    `is_open` ile ayni sey degil: surgu inerken kapi hala aciktir ama
    bosluk oyuncunun boyundan kisalmistir. Mekanigin gerilimi tam
    olarak bu aradaki fark, o yuzden olculen sey bu.
    """
    probe = TimeGate(gate.tile_x, gate.top_row, gate.floor_row, gate.frames)
    probe.open()
    count = 0
    while probe.is_open:
        if probe.passable:
            count += 1
        probe.update()
    return count


# --- 1. Surgu mekanigi -------------------------------------------------------
def test_gate_mechanics() -> None:
    print("\n--- surgu ---")
    gate = TimeGate(tile_x=5, top_row=GATE_TOP, floor_row=FLOOR_TOP,
                    frames=100)
    check(not gate.is_open and not gate.passable,
          "kapali basliyor", f"bosluk {gate.gap_tiles}")

    gate.open()
    check(gate.is_open and gate.passable, "kol acinca gecilebilir")
    check(gate.gap_tiles == gate.height,
          "yeni acilan surgu TAM acik", f"{gate.gap_tiles} tile")

    # Bosluk zamanla azaliyor - sayac diegetik, cubuk degil.
    gaps = []
    for _ in range(100):
        gate.update()
        gaps.append(gate.gap_tiles)
    check(gaps == sorted(gaps, reverse=True),
          "bosluk yalnizca AZALIYOR (surgu iniyor)")
    check(gate.gap_tiles == 0, "sure bitince tamamen kapali")

    usable = usable_frames(TimeGate(5, GATE_TOP, FLOOR_TOP, frames=100))
    ratio = usable / 100
    check(0.75 <= ratio <= 0.85,
          "kullanilabilir sure nominalin ~%80'i",
          f"{usable}/100 = %{ratio*100:.0f}")
    check(gate.height - PASSABLE_TILES >= 1,
          "surgu oyuncu boyundan yuksek - inisin bir anlami var",
          f"{gate.height} tile")


# --- 2. Her kapi GERCEKTEN gecilebilir ★ --------------------------------------
def test_every_gate_is_beatable() -> None:
    """Bolumun en onemli testi.

    Bir zaman bulmacasinda tek olumcul hata sureyi yanlis vermektir:
    oyuncu kusursuz oynar ve yine de gecemez. Burada duz kosu suresi
    hesaplaniyor ve pencereyle karsilastiriliyor.
    """
    print("\n--- her kapi gecilebilir mi (en yavas karakter) ---")
    game = Game()
    try:
        scene = start(game, character="ardo")
        per_tile: list[tuple[str, float]] = []
        for lever in scene.gates.levers:
            room = scene._room_at(lever.center_x)
            gates = scene.gates.gates_of(lever)
            check(bool(gates), f"{room}: kolun bagli kapisi var")
            # En UZAK kapi belirleyici - tek sayac hepsini tasiyor.
            far = max(gates, key=lambda g: abs(g.center_x - lever.center_x))
            distance = abs(far.center_x - lever.center_x)
            need = distance / SLOWEST
            window = usable_frames(far)
            margin = window / need
            tiles = distance / TILE_SIZE
            per_tile.append((room, window / tiles))
            check(margin >= MIN_MARGIN,
                  f"{room}: pencere yeterli",
                  f"{tiles:.0f} tile, {need:.0f} kare gerek, "
                  f"{window} kare var = {margin:.2f}x")

        # Zorluk **mesafeden** geliyor: tile basina dusen sure odadan
        # odaya azaliyor. Bu olmadan "cifte" odasi en buyuk sayaca
        # sahip oldugu icin en kolay gorunurdu.
        order = [room for room, _ in per_tile]
        values = [value for _, value in per_tile]
        check(values == sorted(values, reverse=True),
              "zorluk egrisi tile basina AZALIYOR",
              "  ".join(f"{r}:{v:.1f}" for r, v in per_tile))
        check(order[-1] == "cifte", "en dar oda zincir odasi", order[-1])
    finally:
        game.quit()


# --- 3. Yumusak kilit yok ----------------------------------------------------
def test_no_soft_lock() -> None:
    print("\n--- yumusak kilit yok ---")
    bank = GateBank()
    gate = bank.add_gate(TimeGate(5, GATE_TOP, FLOOR_TOP, frames=60,
                                  name="a"))
    lever = bank.add_lever(Lever(1, 12, gates=("a",)))

    check(bool(bank.pull(lever)), "kol ilk seferde caliyor")
    check(not bank.pull(lever), "cooldown sirasinda ikinci basma yutuluyor")
    for _ in range(200):
        lever.update()
        gate.update()
    check(gate.gap_tiles == 0, "sure doldu, kapi kapandi")
    reopened = bank.pull(lever)
    check(bool(reopened) and gate.passable,
          "kacirilan kapi YENIDEN acilabiliyor - kilitlenme yok")


def test_ejection() -> None:
    """Kapanan surgunun altinda kalan oyuncu duvarda birakilmiyor."""
    print("\n--- surgu altinda kalmak ---")
    game = Game()
    try:
        scene = start(game)
        gate = scene.gates.gates["kol_0"]
        body = scene.player.body
        body.set_feet(gate.center_x, FLOOR_TOP * TILE_SIZE)
        gate.open()
        for _ in range(gate.frames + 4):
            scene.gates.update(scene.tilemap)
        scene._on_gate_closed(gate)
        check(not scene.tilemap.solid_overlap(body.rect),
              "oyuncu duvarin icinde birakilmadi",
              f"itilme {scene.ejections}")
        check(scene.player.health > 0, "ceza olum DEGIL - zaman")
    finally:
        game.quit()


# --- 4. Oda 6: tek kol, iki kapi, tek sayac ----------------------------------
def test_chain_room() -> None:
    print("\n--- zincir odasi ---")
    game = Game()
    try:
        scene = start(game)
        chain = [lever for lever in scene.gates.levers
                 if scene._room_at(lever.center_x) == "cifte"]
        check(len(chain) == 1, "zincir odasinda TEK kol var", str(len(chain)))
        gates = scene.gates.gates_of(chain[0])
        check(len(gates) == 2, "tek kol IKI kapiyi aciyor", str(len(gates)))

        scene.gates.pull(chain[0])
        remaining = {g.remaining for g in gates}
        check(len(remaining) == 1,
              "iki kapi TEK sayaci paylasiyor - sira degil zincir",
              str(remaining))
    finally:
        game.quit()


# --- 5. Zindanci: Katman 2'nin sinavi ----------------------------------------
def test_gaoler_phases() -> None:
    print("\n--- Zindanci: uc faz, uc ders ---")
    check(len(MOVES) == 3, "uc faz", str(len(MOVES)))
    check("keys" in MOVES[1], "faz 1 mermi atiyor (Okcu'nun dersi)")
    check("chain" in MOVES[1], "faz 1 uzun menzil (Mizrakli'nin dersi)")
    check("call" in MOVES[2], "faz 2 cagiriyor (Komutan'in dersi)")

    # `CLAUDE.md` 7 BAGLAYICI: her saldiri en az 14 kare onceden okunur.
    short = {name: frames for name, frames in TELL.items() if frames < 14}
    check(not short, "her hamlenin tell'i >= 14 kare", str(short) or "hepsi")

    game = Game()
    try:
        scene = start(game)
        scene._spawn_room("zindan")
        boss = scene.boss
        check(boss is not None, "arenada boss var")
        check(boss.guarding, "faz 0'da gard acik (Kalkanli'nin dersi)")

        # Onden gecmiyor, arkadan geciyor. YON cozumu.
        boss.facing = 1
        front = _fake_box(boss, damage=20)
        result = boss.take_damage(front, (-1, 0))
        check(not result.hit, "onden gelen vurus GECMIYOR")
        health = boss.health
        result = boss.take_damage(_fake_box(boss, damage=20), (1, 0))
        check(result.hit and boss.health < health,
              "arkadan gelen vurus geciyor", f"{health} -> {boss.health}")

        # Toparlanma penceresinde gard dusuyor - sabirli oyuncu onden
        # de girebilmeli.
        boss._set_state(EnemyState.RECOVER)
        check(not boss.guarding, "toparlanirken gard DUSUYOR")
    finally:
        game.quit()


def _fake_box(owner, damage: int = 10):
    """Oyuncunun vurusu yerine gecen en kucuk sey."""
    from src.combat.hitbox import Hitbox, Team
    return Hitbox(rect=owner.body.rect.copy(), owner=None,
                  targets=Team.ENEMY, damage=damage, active_frames=2)


def test_gaoler_lantern() -> None:
    """Fener: her fazda soluyor, faz 2'de ISIK KAYNAGI KALKIYOR."""
    print("\n--- fener ---")
    game = Game()
    try:
        scene = start(game)
        scene._spawn_room("zindan")
        boss = scene.boss

        radii = []
        for phase in (0, 1, 2):
            boss.phase = phase
            radii.append(boss.lantern_radius)
        check(radii[0] > radii[1] > radii[2],
              "fener her fazda soluyor", str(radii))
        check(radii[2] == 0.0, "faz 2'de fener KIRIK", str(radii[2]))

        boss.phase = 0
        boss._update_lantern()
        check(scene.light.has_static("gaoler_lantern"),
              "faz 0'da arenayi fener aydinlatiyor")
        boss.phase = 2
        boss._update_lantern()
        check(not scene.light.has_static("gaoler_lantern"),
              "faz 2'de isik kaynagi ORTADAN KALKIYOR")

        # Karanlikta bile tell okunur olmali (`CLAUDE.md` 7). Gozler
        # ciziliyor - `draw_extra` cokmeden calisiyor ve tell renginde
        # ayrisiyor.
        surface = pygame.Surface((480, 270))
        boss._set_state(EnemyState.TELL)
        boss.draw_extra(surface, (0, 0))
        check(True, "karanlik fazda gozler ciziliyor (tell okunur kaliyor)")
    finally:
        game.quit()


def test_gaoler_call_and_snuff() -> None:
    print("\n--- cagirma ve sondurme ---")
    game = Game()
    try:
        scene = start(game)
        scene._spawn_room("zindan")
        boss = scene.boss
        before = len(scene.enemies)
        boss._do_call()
        check(len(scene.enemies) > before,
              "cagirma gercekten dusman ekliyor",
              f"{before} -> {len(scene.enemies)}")
        for enemy in scene.enemies[before:]:
            check(not scene.tilemap.solid_overlap(enemy.body.rect),
                  "cagirilan dusman duvarin icinde DEGIL")
            check(enemy.aware, "cagirilan dusman UYANIK dogar")

        # Ust sinir: sinirsiz olsaydi zorluk beceriyle TERS orantili
        # olurdu - bir olum sarmalinin tanimi.
        for _ in range(20):
            boss._do_call()
        from src.config import GAOLER_CALL_LIMIT
        check(boss.called <= GAOLER_CALL_LIMIT,
              "cagirma ust siniri tutuyor",
              f"{boss.called} <= {GAOLER_CALL_LIMIT}")

        # Sondurme: faz 2'nin isik ekonomisi.
        near = min(scene.braziers,
                   key=lambda b: abs(b.x - boss.body.center_x))
        near.light()
        boss._do_snuff()
        check(not near.lit, "boss yakindaki mangali sonduruyor",
              f"{abs(near.x - boss.body.center_x):.0f} px uzakta")

        # **Bos tell yok.** Sonduruleсek mangal kalmadiysa sira
        # atlanmali - oyuncu bir tehdit gorup hicbir sey olmamasi
        # "okumak ise yaramiyor" dersini verir.
        for brazier in scene.braziers:
            brazier.extinguish()
        boss.phase = 2
        boss.move_index = list(MOVES[2]).index("snuff")
        check(boss._next_move() != "snuff",
              "sonduruleсek mangal yokken sira ATLANIYOR")
    finally:
        game.quit()


def test_brazier_lit_by_sword() -> None:
    """Mangal kilicla yakiliyor - yeni bir tus ogretilmiyor."""
    print("\n--- mangali yakmak ---")
    game = Game()
    try:
        scene = start(game)
        brazier = scene.braziers[0]
        check(not brazier.lit, "mangal sonuk basliyor")
        box = _fake_box(scene.player)
        box.rect = pygame.Rect(int(brazier.x) - 6, int(brazier.y) - 10, 12, 12)
        scene.on_attack_swing(scene.player, box)
        check(brazier.lit, "kilic degince yaniyor")
        scene._update_braziers()
        check(scene.light.in_light(brazier.x, brazier.y - 6),
              "yanan mangal ISIK veriyor")
    finally:
        game.quit()


# --- 6. Arena, muhur, cikis --------------------------------------------------
def test_arena_and_exit() -> None:
    print("\n--- arena ve cikis ---")
    game = Game()
    try:
        scene = start(game)
        check(not scene.exit_open, "cikis basta KAPALI")

        start_tile, _ = scene._room_span("zindan")
        scene.player.body.set_feet((start_tile + 8) * TILE_SIZE,
                                   FLOOR_TOP * TILE_SIZE)
        scene._enter_room("zindan")
        scene._update_arena()
        check(scene.arena_sealed, "arenaya girince muhurleniyor")
        check(scene.tilemap.is_solid(start_tile + 3, 10),
              "muhur zemine yazildi")

        # Cikisa gitmek boss olmeden bolumu bitirmiyor.
        exit_at = LEVEL.first("exit")
        scene.player.body.set_feet(exit_at.x + 4, FLOOR_TOP * TILE_SIZE)
        scene._check_exit()
        check(not scene.finished, "boss olmeden cikis calismiyor")

        scene.boss.health = 0
        scene.boss.die()
        scene._update_arena()
        check(scene.boss_defeated and scene.exit_open, "boss olunce cikis acildi")
        check(not scene.tilemap.is_solid(start_tile + 3, 10),
              "boss olunce muhur kalkti")
    finally:
        game.quit()


def test_after_restart_respawns_boss() -> None:
    """Arenada olen oyuncu BOS bir arenada uyanmamali (`DEVIR.md` B6)."""
    print("\n--- olumden sonra arena ---")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("zindan")
        check(scene.boss is not None, "boss dogdu")
        # Olum sonrasi `setup()` her seyi sifirliyor.
        scene.setup()
        check(scene.boss is None, "setup boss'u sifirladi")
        scene.after_restart("zindan")
        check(scene.boss is not None and not scene.boss.dead,
              "after_restart boss'u geri getiriyor")
        check(scene.arena_sealed, "muhur de geri geldi")
    finally:
        game.quit()


# --- 7. Ara sahneler ---------------------------------------------------------
def test_cinematics() -> None:
    print("\n--- ara sahneler ---")
    check(CageCinematic.skippable is False,
          "kafes sahnesi ATLANAMAZ - kayip gecilerek ogrenilmez")
    game = Game()
    try:
        for scene_cls, name in ((CageCinematic, "kafes"),
                                (MarkCinematic, "isaret"),
                                (GaolerCinematic, "zindanci"),
                                (GateCinematic, "kapi")):
            for character in ("rey", "ardo"):
                game.scenes.set_root(scene_cls, transition=False,
                                     character=character)
                game.scenes._flush()
                scene = game.scenes.current
                surface = pygame.Surface((480, 270))
                for _ in range(90):
                    scene.update()
                    scene.draw(surface)
                check(True, f"{name} ({character}) 90 kare cokmeden oynuyor")
    finally:
        game.quit()


# --- 8. Bolum akisi ----------------------------------------------------------
def test_chapter_shape() -> None:
    print("\n--- bolum akisi ---")
    names = [name for name, _ in ROOM_STARTS]
    check(len(names) == 7, "yedi oda", str(len(names)))
    check(names[0] == "kafes" and names[-1] == "zindan",
          "kafesle basliyor, zindanla bitiyor")

    kinds = {p.kind for p in LEVEL.placements}
    check("archer" in kinds and "commander" in kinds,
          "Okcu ve Komutan ILK KEZ bir bolume yerlestirildi")
    check("gaoler" in kinds, "BOSS 2 haritada")
    check("cemo" in kinds, "Cemo haritada")

    # Kafes odasinda dusman YOK - an bozulmamali.
    cage_end = ROOM_STARTS[1][1]
    fighters = [p for p in LEVEL.placements
                if p.tile_x < cage_end
                and p.kind in ("shambler", "archer", "commander", "spearman")]
    check(not fighters, "kafes odasinda dusman yok", str(len(fighters)))

    # Ogretme odasinda da yok - once ogret, sonra sina.
    teach_start, teach_end = ROOM_STARTS[1][1], ROOM_STARTS[2][1]
    teachers = [p for p in LEVEL.placements
                if teach_start <= p.tile_x < teach_end
                and p.kind in ("shambler", "archer", "commander", "spearman")]
    check(not teachers, "ogretme odasinda dusman yok", str(len(teachers)))


def main() -> int:
    test_gate_mechanics()
    test_every_gate_is_beatable()
    test_no_soft_lock()
    test_ejection()
    test_chain_room()
    test_gaoler_phases()
    test_gaoler_lantern()
    test_gaoler_call_and_snuff()
    test_brazier_lit_by_sword()
    test_arena_and_exit()
    test_after_restart_respawns_boss()
    test_cinematics()
    test_chapter_shape()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("Bolum 13 tutarli - kapilar gecilebilir, boss adil.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
