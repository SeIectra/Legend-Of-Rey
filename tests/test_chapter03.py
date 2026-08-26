"""Bolum 3 dogrulamasi - "Mesale Mahzeni" bassiz oynanir.

`docs/bolum-03.md`'nin uc yeni mekanigini (mesale ekonomisi, ses haritasi,
Mor Alev karari) + yeni dusman (Golge Suruklenen) + Mum Bekcisi ticareti +
mini-boss'u (mangal mekanigi) test eder. `tests/test_chapter02.py` ile ayni
desen: bolum bassiz **oynaniyor**, elle gezmek yerine.

Calistir:
    python tests/test_chapter03.py
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

from src.config import TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.scenes.chapter03 import Chapter03Scene, TRADE_OFFERS  # noqa: E402
from src.systems import charms, economy  # noqa: E402
from src.ui import i18n  # noqa: E402
from src.ui.chapter_end import ChapterResult  # noqa: E402
from src.world.rooms.chapter03 import (  # noqa: E402
    ARENA_DOOR_COLUMN, LEVEL, ROOM3_SOCKET_INDICES, ROOM_STARTS, WIND_ZONES,
)
from src.world.torch import HELD, LANDED  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def make_scene(game: Game) -> Chapter03Scene:
    game.scenes.set_root(Chapter03Scene, transition=False, character="rey")
    game.scenes._flush()
    return game.scenes.current


def idle(game: Game, scene, frames: int) -> None:
    for _ in range(frames):
        game.input.begin_frame()
        game.input.end_frame()
        scene.update()


def press(game: Game, scene, action) -> None:
    """Bir tusa taze basar - `pressed()` yalnizca bu karede true doner.

    `InputManager._activate()` gercek tus olayinin yaptigi seyi yapar:
    `_held`de degilse `_pressed`e ekler. Hemen ardindan `_deactivate()`
    cagirmak onemli: aksi halde tus `_held`de sonsuza dek kalir (test
    ortaminda hicbir KEYUP olayi gelmiyor) ve **ikinci** `press()` cagrisi
    "zaten basili" sayilip sessizce yok sayilir.
    """
    game.input.begin_frame()
    game.input._activate(action)
    game.input._deactivate(action)
    game.input.end_frame()
    scene.update()


def teleport(scene, tile_x: int, tile_y: int = 13) -> None:
    scene.player.body.set_feet(tile_x * TILE_SIZE + TILE_SIZE * 0.5,
                               (tile_y + 1) * TILE_SIZE)
    scene.player.body.vx = 0.0
    scene.player.body.vy = 0.0


def room_start(name: str) -> int:
    return dict(ROOM_STARTS)[name]


def main() -> int:
    i18n.set_language("tr")
    game = Game()
    from src.core.input import Action

    # --- 1. Harita ------------------------------------------------------------
    print("--- harita ---")
    scene = make_scene(game)
    idle(game, scene, 1)          # `_update_light()`/kisitlar ilk karede kurulur
    check(len(ROOM_STARTS) == 7, "yedi oda", str(len(ROOM_STARTS)))
    counts: dict[str, int] = {}
    for placement in LEVEL.placements:
        counts[placement.kind] = counts.get(placement.kind, 0) + 1
    check(counts.get("shadow_shambler") == 4, "4 Golge Suruklenen",
          str(counts.get("shadow_shambler")))
    check(counts.get("candle_keeper") == 1, "1 Mum Bekcisi")
    check(counts.get("miniboss") == 1, "1 mini-boss")
    check(counts.get("chest") == 2, "2 sandik (Oda 2 + gizli)")

    # --- 2. Oyuncu B2'den kalan mesaleyle basliyor -----------------------------
    print("\n--- mesale ---")
    check(scene.torch is not None and scene.torch.state == HELD,
          "oyuncu elinde yanan bir mesaleyle basliyor")
    check(scene.light.in_light(scene.player.body.center_x,
                              scene.player.body.center_y),
          "tasinan mesale oyuncuyu aydinlatiyor")
    check(scene.player.chain.max_index == 1,
          "mesale elde iken zincir 2'li (bitirici yok)",
          str(scene.player.chain.max_index))

    # Uzak bir noktada karanlik olmali.
    check(not scene.light.in_light(scene.player.body.center_x + 500,
                                  scene.player.body.center_y),
          "mesale yaricapi disinda karanlik")

    # --- 3. Firlatma ve yeniden alma -------------------------------------------
    print("\n--- mesale firlatma ---")
    scene.player.facing = 1
    press(game, scene, Action.INTERACT)
    check(scene.torch is not None and scene.torch.state != HELD,
          "INTERACT ile mesale firlatildi/birakildi", scene.torch.state)
    idle(game, scene, 40)
    check(scene.torch is None or scene.torch.state == LANDED,
          "mesale bir yerde durdu (havada kalmadi)")
    check(scene.player.chain.max_index is None,
          "mesale elde degilken zincir kisitlamasi kalkiyor")

    # --- 4. Ses haritasi (sonar) ------------------------------------------------
    print("\n--- sonar ---")
    scene2 = make_scene(game)
    check(scene2.echo is not None, "Rey'in Yankisi var")
    before_cd = scene2.echo.sonar_cooldown
    press(game, scene2, Action.ECHO)
    check(scene2.echo.sonar_active, "ECHO basinca sonar tetiklendi")
    check(scene2.echo.sonar_cooldown > before_cd, "cooldown baslad")
    press(game, scene2, Action.ECHO)
    check(scene2.echo.sonar_frames < scene2.echo._sonar_total,
          "cooldown bitmeden ikinci basim yeni darbe baslatmiyor")

    # --- 5. Golge Suruklenen: karanlikta dokunulmaz, isikta vurulabilir --------
    print("\n--- Golge Suruklenen ---")
    scene3 = make_scene(game)
    dark_start = room_start("surunen_karanlik")
    teleport(scene3, dark_start + 2)
    idle(game, scene3, 2)
    check(scene3.room == "surunen_karanlik", "Oda 4'e girildi", scene3.room)
    shadow = next(e for e in scene3.enemies
                  if type(e).__name__ == "ShadowShambler")
    # Oyuncunun kendi mesalesi yakinsa golgeyi de aydinlatir - bu testte
    # "karanlikta" durumunu izole etmek icin mesaleyi (test amacli) sondur.
    scene3.torch = None
    idle(game, scene3, 2)
    check(not scene3.light.in_light(shadow.body.center_x, shadow.body.center_y),
          "Golge Suruklenen baslangicta karanlikta")

    from src.combat.hitbox import Hitbox, Team
    box = Hitbox(rect=shadow.hurtbox.copy(), damage=999, owner=scene3.player,
                 targets=Team.ENEMY, active_frames=5)
    result = shadow.take_damage(box, (1.0, 0.0))
    check(not result.hit, "karanlikta vurus islemiyor (dokunulmaz)")

    scene3.light.set_static("test_torch", shadow.body.center_x,
                            shadow.body.center_y, TILE_SIZE * 3.0)
    result2 = shadow.take_damage(box, (1.0, 0.0))
    check(result2.hit and result2.killed, "isikta vurulabiliyor",
          f"can {shadow.health}")

    # --- 6. Yuvalar bulmacasi ---------------------------------------------------
    print("\n--- Oda 3 bulmacasi ---")
    scene4 = make_scene(game)
    teleport(scene4, room_start("yuvalar_bulmacasi") + 2)
    idle(game, scene4, 2)
    check(not scene4.puzzle_solved, "bulmaca basta cozulmemis")
    for i in ROOM3_SOCKET_INDICES:
        scene4.sconces[i][2] = True
    idle(game, scene4, 2)
    check(scene4.puzzle_solved, "bes yuva da yaninca bulmaca cozuluyor")

    # --- 7. Mum Bekcisi ticareti -------------------------------------------------
    print("\n--- Mum Bekcisi ---")
    scene5 = make_scene(game)
    keeper = scene5.candle_keeper
    check(keeper is not None, "Mum Bekcisi haritada var")
    scene5.save_data.gold = 500
    teleport(scene5, int(keeper.x) // TILE_SIZE, tile_y=10)
    idle(game, scene5, 2)
    press(game, scene5, Action.INTERACT)
    check(scene5.trading, "yakinda INTERACT ticareti aciyor")

    offer = TRADE_OFFERS[0]
    gold_before = scene5.save_data.gold
    scene5._buy(offer)
    check(scene5.save_data.gold == gold_before - offer.cost,
          "satin alinca altin dusuyor")
    check(economy.already_bought(scene5.save_data, offer),
          "tekil satin alim isaretlendi")
    gold_after_first = scene5.save_data.gold
    scene5.trading = True
    scene5._buy(offer)
    check(scene5.save_data.gold == gold_after_first,
          "ikinci kez alinamiyor - altin tekrar dusmuyor")

    scene6 = make_scene(game)
    scene6.save_data.gold = 0
    scene6._buy(TRADE_OFFERS[1])
    check(scene6.save_data.gold == 0, "yetersiz altinda hicbir sey dusmuyor")

    # --- 8. Ruzgar mesaleyi sonduruyor -------------------------------------------
    print("\n--- Oda 6 ruzgar ---")
    scene7 = make_scene(game)
    wind_lo, _wind_hi = WIND_ZONES[0]
    teleport(scene7, wind_lo + 2)
    idle(game, scene7, 2)
    check(scene7.room == "alev_sinavi", "Oda 6'ya girildi", scene7.room)
    check(scene7.torch is not None, "mesale hala elde")
    check(scene7._in_wind_zone(scene7.player.body.center_x),
          "oyuncu ruzgar bolgesinde")
    idle(game, scene7, 2)
    check(scene7.light.radius_at(scene7.player.body.center_x,
                                scene7.player.body.center_y) == 0.0
          or scene7.light.in_light(scene7.player.body.center_x,
                                   scene7.player.body.center_y) is False,
          "ruzgar bolgesinde sıradan mesale ısık vermiyor")

    # --- 9. Mor Alev secimi -------------------------------------------------------
    print("\n--- Mor Alev ---")
    scene8 = make_scene(game)
    teleport(scene8, room_start("mor_alev") + 13)
    idle(game, scene8, 2)
    check(not scene8.has_purple_flame, "basta Mor Alev alinmamis")
    tier_before = scene8.echo.tier
    press(game, scene8, Action.INTERACT)
    check(scene8.has_purple_flame, "yakinda INTERACT ile Mor Alev alindi")
    check(scene8.torch is None, "Mor Alev alinca sıradan mesale birakiliyor")
    check(scene8.echo.tier >= tier_before, "Yanki kademesi yukseldi/sabit kaldi")
    check(scene8.player.chain.max_index is None,
          "Mor Alev tasirken zincir kisitlamasi yok")

    # --- 10. Mangal + boss sersemlemesi -------------------------------------------
    print("\n--- mangal ve mini-boss ---")
    scene9 = make_scene(game)
    boss_start = room_start("sonmus_olan")
    # Arda'nin bildirdigi hata (Bolum 2'de zaten bir kez cikmisti): kapi
    # oda sinirina girer girmez kapanirsa oyuncunun yuzune kapaniyor gibi
    # hissettiriyor. Once esigin GERISINE teleport edip kapinin henuz
    # kapanmadigini, sonra esigi gecince kapandigini ayri ayri dogrula.
    teleport(scene9, boss_start + 1)
    idle(game, scene9, 2)
    check(scene9.boss is not None, "oda sinirinda mini-boss zaten dogdu")
    check(not scene9.arena_sealed,
          "kapi oda sinirinda HENUZ kapanmiyor (esige kadar tampon var)")
    teleport(scene9, ARENA_DOOR_COLUMN + 2)
    idle(game, scene9, 2)
    check(scene9.arena_sealed, "esigi gecince kapi kapaniyor")
    check(not scene9.brazier.lit, "mangal basta sonuk")

    scene9.has_purple_flame = True       # Test icin - yakma kosulunu saglar
    teleport(scene9, int(scene9.brazier.x) // TILE_SIZE, tile_y=13)
    idle(game, scene9, 2)
    press(game, scene9, Action.INTERACT)
    check(scene9.brazier.lit, "yakinda INTERACT ile mangal yanıyor")
    check(scene9.boss.stagger_frames > 0, "mangal yaninca boss sersemledi")

    scene9.boss.health = 0
    scene9.boss.dead = True
    idle(game, scene9, 4)
    check(scene9.boss_defeated, "boss olunce arena acildi")
    check(charms.FENER in scene9.player.charms, "Fener tilsimi verildi")

    # --- 11. Bolum sonu ekraninda Mor Alev satiri ---------------------------------
    print("\n--- bolum sonu ---")
    taken = ChapterResult("chapter.torch_crypt", 100, 5, 50, 1, 1,
                          purple_flame_taken=True)
    none_case = ChapterResult("chapter.first_descent", 100, 5, 50, 1, 1)

    from src.ui.chapter_end import ChapterEndScene
    game.scenes.push(ChapterEndScene, result=taken)
    game.scenes._flush()
    end = game.scenes.current
    rows_taken = end._rows()
    check(any(r[0] == "chapter_end.purple_flame" for r in rows_taken),
          "Mor Alev satiri Bolum 3 sonucunda gorunuyor")
    game.scenes.pop()
    game.scenes._flush()

    game.scenes.push(ChapterEndScene, result=none_case)
    game.scenes._flush()
    end2 = game.scenes.current
    rows_none = end2._rows()
    check(not any(r[0] == "chapter_end.purple_flame" for r in rows_none),
          "Bolum 2 sonucunda Mor Alev satiri YOK (purple_flame_taken=None)")
    game.scenes.pop()
    game.scenes._flush()

    game.shutdown()

    # --- Boss atlanamaz: Bolum 3'un de kilitli cikisi var -------------------
    # Bolum 2'deki kacagin aynisi buradaydi: giris muhurlense de arka taraf
    # acikti. `_seal_arena`'nin Bolum 3'e hic tasinmamis olmasiyla ayni
    # sinif hata - bir bolume yazilan seyin otekine tasinmasi unutuluyor.
    print("\n--- Bolum 3: kilitli cikis + anahtar ---")
    from src.world.rooms.chapter03 import ARENA_EXIT_COLUMN, ARENA_EXIT_ROWS

    gate_game = Game()
    gate_game.scenes.set_root(Chapter03Scene, transition=False, character="rey")
    gate_game.scenes._flush()
    gate = gate_game.scenes.current

    check(gate.exit_door.locked, "Bolum 3 cikis kapisi bastan KILITLI")
    check(all(gate.tilemap.is_solid(ARENA_EXIT_COLUMN, r)
              for r in ARENA_EXIT_ROWS),
          "kapinin butun satirlari kati")
    exit_spot = LEVEL.first("exit")
    check(exit_spot is not None and ARENA_EXIT_COLUMN < exit_spot.tile_x,
          "kapi CIKISTAN ONCE - atlanamiyor",
          f"kapi {ARENA_EXIT_COLUMN} < cikis {exit_spot.tile_x if exit_spot else -1}")

    gate._open_arena()
    check(gate.boss_key is not None, "boss olunce anahtar dustu")
    check(gate.exit_door.locked, "anahtar dusunce kapi HENUZ acik degil")
    gate.player.body.set_feet(gate.boss_key.x, gate.boss_key.feet_y)
    for _ in range(10):
        gate_game.input.begin_frame(); gate_game.input.end_frame()
        gate.update()
    check(gate.has_key and not gate.exit_door.locked,
          "anahtarla kapi acildi")
    gate_game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Bolum 3 tasarim belgesine uyuyor.")
    return 0


raise SystemExit(main())
