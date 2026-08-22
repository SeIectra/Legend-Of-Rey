"""Bolum 2 dogrulamasi - dikey dilimin sinavi.

Bu bolum `docs/bolum-02.md`'ye gore *"oyunun normal dokusunu tam kalitede
kanitlamak"* zorunda. Bir bolumu elle oynayarak dogrulamak yavas ve
guvenilmez: her degisiklikten sonra dokuz odayi bastan gezmek gerekir.
Burada bolum bassiz olarak **oynaniyor**.

Kontrol edilenler:

  * Sekiz oda + gizli oda haritada var ve dusmanlar odaya girilince doguyor
  * Yanki odasinda ses **kendiliginden** yukseliyor (belge: "ogretim zirvesi")
  * Iki catlagin anlami farkli: biri yolu aciyor, digeri gizli odayi
  * Sandiklar dokununca aciliyor ve odulu **bir kez** veriyor
  * Tilsim carpani yalnizca kosul saglaninca biniyor
  * Mini-boss arenasi muhurleniyor ve boss olunce **aciliyor**
  * Bolum sonu ekrani "0/1 gizli alan" ayrimini yapiyor

Calistir:
    python tests/test_chapter02.py
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

from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH, TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.core.input import Action  # noqa: E402
from src.scenes.chapter02 import Chapter02Scene  # noqa: E402
from src.systems import abilities, charms  # noqa: E402
from src.ui import i18n  # noqa: E402
from src.ui.chapter_end import ChapterResult, format_time  # noqa: E402
from src.world.rooms.chapter02 import (  # noqa: E402
    ARENA_DOOR_COLUMN, ARENA_DOOR_ROWS, CHEST_GOLD_MAIN, CHEST_GOLD_SECRET,
    ECHO_RISE_DELAY, LEVEL, ROOM_STARTS, SECRET_WALL_MIN_COLUMN,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def make_scene(game: Game, character: str = "rey") -> Chapter02Scene:
    game.scenes.set_root(Chapter02Scene, transition=False, character=character)
    game.scenes._flush()
    return game.scenes.current


def idle(game: Game, scene, frames: int) -> None:
    """Girdisiz kare ilerlet."""
    for _ in range(frames):
        game.input.begin_frame()
        game.input.end_frame()
        scene.update()


def teleport(scene, tile_x: int, tile_y: int = 13) -> None:
    """Oyuncuyu bir tile'a tasi. Odalar arasi gezinmek icin.

    Gercekten yuruterek gecmek 3200 piksellik bir haritada binlerce kare
    surer ve testi yavaslatir; burada olculen sey yuruyus degil, odaya
    girisin **tetikledigi** seyler.
    """
    scene.player.body.set_feet(tile_x * TILE_SIZE + TILE_SIZE * 0.5,
                               (tile_y + 1) * TILE_SIZE)
    scene.player.body.vx = 0.0
    scene.player.body.vy = 0.0


def main() -> int:
    i18n.set_language("tr")
    game = Game()

    # --- 1. Harita ve odalar ------------------------------------------------
    print("--- harita ---")
    scene = make_scene(game)
    check(scene.tilemap.width == 200 and scene.tilemap.height == 16,
          "harita 200x16 tile",
          f"{scene.tilemap.width}x{scene.tilemap.height}")
    check(len(ROOM_STARTS) == 9, "dokuz oda (sekiz + gizli)",
          str(len(ROOM_STARTS)))

    counts: dict[str, int] = {}
    for placement in LEVEL.placements:
        counts[placement.kind] = counts.get(placement.kind, 0) + 1
    check(counts.get("shambler") == 10, "10 Suruklenen (+2 boss cagirir = 12)",
          str(counts.get("shambler")))
    check(counts.get("climber") == 3, "3 Tirmanan", str(counts.get("climber")))
    check(counts.get("bloated") == 2, "2 Sismek", str(counts.get("bloated")))
    check(counts.get("miniboss") == 1, "1 mini-boss")
    check(counts.get("chest") == 2, "2 sandik (ana yol + gizli)")

    # --- 2. Dusmanlar odaya girilince doguyor -------------------------------
    print("\n--- odaya girisle dogus ---")
    check(len(scene.enemies) == 0, "ilk odada dusman yok - belge: nefes",
          f"{len(scene.enemies)} dusman")

    teleport(scene, 20)
    idle(game, scene, 2)
    check(scene.room == "ilk_kan", "ikinci odaya girildi", scene.room)
    check(len(scene.enemies) == 3, "Oda 2'nin uc Suruklenen'i dogdu",
          f"{len(scene.enemies)} dusman")

    before = len(scene.enemies)
    teleport(scene, 18)
    idle(game, scene, 2)
    teleport(scene, 20)
    idle(game, scene, 2)
    check(len(scene.enemies) == before,
          "odaya ikinci giriste tekrar dogmuyor", f"{len(scene.enemies)}")

    # --- 3. Sandik ----------------------------------------------------------
    print("\n--- sandik ---")
    main_chest = next(c for c in scene.chests if not c.secret)
    check(main_chest.gold == CHEST_GOLD_MAIN, "ana yol sandigi 30 altin",
          str(main_chest.gold))
    gold_before = scene.earned_gold
    scene.player.body.set_feet(main_chest.x, main_chest.feet_y)
    idle(game, scene, 2)
    check(main_chest.opened, "dokununca acildi")
    check(scene.earned_gold == gold_before + CHEST_GOLD_MAIN,
          "altin bir kez eklendi", f"+{scene.earned_gold - gold_before}")
    idle(game, scene, 20)
    check(scene.earned_gold == gold_before + CHEST_GOLD_MAIN,
          "acik sandik tekrar odul vermiyor", str(scene.earned_gold))

    # --- 4. Yanki odasi - ses kendiliginden yukseliyor ----------------------
    print("\n--- Yanki odasi ---")
    yanki_start = dict(ROOM_STARTS)["yanki_odasi"]
    teleport(scene, yanki_start + 4)
    idle(game, scene, 2)
    check(scene.room == "yanki_odasi", "Yanki odasina girildi", scene.room)
    check(not scene.player.has(abilities.ECHO_SIGHT),
          "Yanki Gorusu **henuz** yok")

    idle(game, scene, ECHO_RISE_DELAY - 10)
    check(scene.echo_forced == 0, "gecikme dolmadan ses yukselmiyor")
    idle(game, scene, 20)
    check(scene.echo_forced > 0, "ses **kendiliginden** yukseldi",
          f"{scene.echo_forced} kare")
    check(scene.player.has(abilities.ECHO_SIGHT), "Yanki Gorusu verildi")
    check(scene.echo is not None and scene.echo.active,
          "tusa basilmadan Yanki acik")

    # Bedel: ekran **kararmali**. Bu tuzaga uc kez dusuldu, artik olculuyor.
    canvas = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))

    def brightness() -> float:
        import numpy as np
        canvas.fill((0, 0, 0))
        scene.draw(canvas)
        return float(np.mean(pygame.surfarray.array3d(canvas)))

    dimmed = brightness()
    scene.echo_forced = 0
    idle(game, scene, 40)
    lit = brightness()
    check(dimmed < lit, "Yanki acikken ekran KARARIYOR (parlamiyor)",
          f"acik {dimmed:.1f} < kapali {lit:.1f}")

    # --- 5. Iki catlagin anlami farkli --------------------------------------
    print("\n--- iki catlak ---")
    walls = scene.tilemap.breakable_rects()
    columns = sorted({rect.x // TILE_SIZE for rect in walls})
    check(len(columns) == 2, "haritada iki ayri kirilabilir sutun",
          str(columns))
    check(columns[0] < SECRET_WALL_MIN_COLUMN <= columns[1],
          "biri ogretici (ana yol), digeri gizli oda", str(columns))

    teach_rects = [r for r in walls if r.x // TILE_SIZE == columns[0]]
    scene.on_wall_broken(teach_rects)
    check(not scene.secret_found,
          "ogretici duvari kirmak gizli alan saymiyor")

    secret_rects = [r for r in walls if r.x // TILE_SIZE == columns[1]]
    scene.on_wall_broken(secret_rects)
    check(scene.secret_found, "gizli oda duvari gizli alani isaretliyor")

    # --- 6. Gizli oda: sessizlik --------------------------------------------
    print("\n--- gizli oda ---")
    secret_start = dict(ROOM_STARTS)["gizli_oda"]
    # Odacigin zemini yalnizca sag yarida (yerel 7..15); sol yari bosluk.
    # Sol yariya birakilan oyuncu ana koridora dusuyordu ve "gizli odaya
    # girdim" sanmasina ragmen sessizlik hic baslamiyordu.
    chamber_tile = int(next(c for c in scene.chests if c.secret).x) // TILE_SIZE
    teleport(scene, chamber_tile, tile_y=7)
    idle(game, scene, 60)
    check(scene.room == "gizli_oda", "gizli odaya girildi", scene.room)
    check(scene.hush > 0.5, "dunya susuyor", f"hush {scene.hush:.2f}")
    check(game.music_hush == scene.hush,
          "muzik kisilma orani oyuna aktarildi (Gorev 10 okuyacak)")

    secret_chest = next(c for c in scene.chests if c.secret)
    check(secret_chest.gold == CHEST_GOLD_SECRET, "gizli sandik 80 altin",
          str(secret_chest.gold))
    scene.player.body.set_feet(secret_chest.x, secret_chest.feet_y)
    idle(game, scene, 2)
    check(secret_chest.opened, "gizli sandik acildi")
    check(charms.BLOODY_WHET in scene.player.charms,
          "ilk tilsim takildi (Kanli Bileme)")

    # Ana koridora in: ayni sutunlar, farkli yukseklik. Sessizlik bitmeli.
    teleport(scene, secret_start + 6)
    idle(game, scene, 40)
    check(scene.hush < 0.5,
          "odacigin altindaki ana koridorda sessizlik yok",
          f"hush {scene.hush:.2f}")

    # --- 7. Tilsim kosullu -------------------------------------------------
    print("\n--- tilsim kosullu ---")
    player = scene.player
    player.combo.count = 0
    idle_scale = charms.damage_scale(player.charms, player)
    player.combo.count = charms.WHET_COMBO
    hot_scale = charms.damage_scale(player.charms, player)
    check(idle_scale == 1.0, "dusuk combo'da carpan yok", str(idle_scale))
    check(abs(hot_scale - 1.15) < 1e-9, "5+ combo'da %15",
          f"{hot_scale:.3f}")
    player.combo.count = 0

    # --- 7b. Kapi kapanirken oyuncu govdesi icinde kalmiyor -----------------
    # Arda'nin ekran goruntusuyle bildirdigi hata: gercekten YURUYEREK
    # girince (teleport degil) kapi bazen govdenin sol yarisi hala
    # sutunu kaplarken kapaniyordu - oyuncu yeni kati tile'in icinde
    # kalip cikamiyordu. `center_x` esigi govde genisligi kadar bir
    # pencere birakiyordu; `body.x` (sol kenar) o pencereyi kapatir.
    print("\n--- kapiya yururken gomulme ---")
    scene_walk = make_scene(game)
    boss_start_walk = dict(ROOM_STARTS)["miniboss"]
    teleport(scene_walk, boss_start_walk - 6)
    scene_walk.player.body.vx = 0.0
    game.input._activate(Action.RIGHT)
    embedded = False
    sealed_frame = None
    # Sadece kapinin GERCEKTEN katilastirdigi satirlar (ARENA_DOOR_ROWS) -
    # tavan/zemin (0-3, 14-15) her sutunda zaten kati, oyuncu normalde
    # yururken zeminde onlara da deger; bu **gomulme degil**, sadece
    # yer cekimi. Yalniz kapinin kendi araligini kontrol etmek gerekiyor.
    door_row_top = min(ARENA_DOOR_ROWS) * TILE_SIZE
    door_row_height = (max(ARENA_DOOR_ROWS) + 1 - min(ARENA_DOOR_ROWS)) * TILE_SIZE
    for frame in range(400):
        game.input.begin_frame()
        game.input.end_frame()
        scene_walk.update()
        door_solid = any(scene_walk.tilemap.is_solid(ARENA_DOOR_COLUMN, r)
                         for r in ARENA_DOOR_ROWS)
        if door_solid and scene_walk.player.body.rect.colliderect(
                pygame.Rect(ARENA_DOOR_COLUMN * TILE_SIZE, door_row_top,
                           TILE_SIZE, door_row_height)):
            embedded = True
        if scene_walk.arena_sealed and sealed_frame is None:
            sealed_frame = frame
        if sealed_frame is not None and frame > sealed_frame + 20:
            break
    game.input._deactivate(Action.RIGHT)
    check(sealed_frame is not None, "yururken de kapi sonunda kapaniyor")
    check(not embedded,
          "kapi kapanirken oyuncunun govdesi kati tile ile CAKISMIYOR")

    # --- 8. Arena muhurlenip aciliyor ---------------------------------------
    print("\n--- mini-boss arenasi ---")
    boss_start = dict(ROOM_STARTS)["miniboss"]
    teleport(scene, boss_start + 6)
    idle(game, scene, 2)
    check(scene.arena_sealed, "arenaya girince kapi indi")
    check(scene.tilemap.is_solid(ARENA_DOOR_COLUMN, 10),
          "kapi sutunu kati oldu")
    check(scene.boss is not None, "mini-boss dogdu")

    scene.boss.health = 0
    scene.boss.dead = True
    idle(game, scene, 4)
    check(not scene.arena_sealed, "boss olunce kapi kalkti")
    check(not scene.tilemap.is_solid(ARENA_DOOR_COLUMN, 10),
          "kapi sutunu tekrar bos")
    # Oyuncu hala kapi sutununun otesinde duruyor (yurumedi) - kapi
    # **yeniden kilitlenmemeli**. Ilk fix denemesi tam bunu yapiyordu:
    # acildiktan hemen sonraki karede "hala esik otesindeyim" mantigi
    # onu tekrar kapatiyordu.
    idle(game, scene, 10)
    check(not scene.arena_sealed,
          "kapi acildiktan sonra kendini yeniden kilitlemiyor")

    # Oyuncu olurse de kilitli kalmamali.
    scene2 = make_scene(game)
    teleport(scene2, boss_start + 6)
    idle(game, scene2, 2)
    check(scene2.arena_sealed, "ikinci kosuda kapi indi")
    scene2.on_player_died(scene2.player)
    check(not scene2.arena_sealed, "oyuncu olunce de kapi aciliyor")

    # --- 9. Bolum sonu ekrani -----------------------------------------------
    print("\n--- bolum sonu ---")
    check(format_time(0) == "00:00", "sure bicimi 00:00", format_time(0))
    check(format_time(60 * 95) == "01:35", "95 saniye -> 01:35",
          format_time(60 * 95))

    missed = ChapterResult("chapter.first_descent", 100, 7, 30, 0, 1)
    found = ChapterResult("chapter.first_descent", 100, 7, 110, 1, 1)
    check(missed.missed_secret, "0/1 kacirilmis sayiliyor")
    check(not found.missed_secret, "1/1 kacirilmis degil")

    exit_at = LEVEL.first("exit")
    teleport(scene, exit_at.tile_x)
    idle(game, scene, 2)
    check(scene.finished, "cikisa varinca bolum bitti")
    game.scenes._flush()
    from src.ui.chapter_end import ChapterEndScene
    end = game.scenes.current
    check(isinstance(end, ChapterEndScene), "bolum sonu ekrani acildi",
          type(end).__name__)

    # Satirlar sirayla acilmali - hepsi birden gelirse tablo gibi okunur.
    check(end.visible_rows() == 0, "ilk karede hicbir satir acik degil")
    for _ in range(120):
        end.update()
    check(end.visible_rows() == 4, "dort satirin hepsi acildi",
          str(end.visible_rows()))
    canvas.fill((0, 0, 0))
    end.draw(canvas)
    import numpy as np
    check(int(np.count_nonzero(pygame.surfarray.array3d(canvas))) > 0,
          "bolum sonu ekrani ciziliyor")

    # --- 10. Ardo icin cikmaz yok -------------------------------------------
    print("\n--- Ardo (Yanki yok) ---")
    ardo = make_scene(game, character="ardo")
    check(ardo.echo is None, "Ardo'nun Yanki'si yok")
    teleport(ardo, yanki_start + 4)
    idle(game, ardo, ECHO_RISE_DELAY + 10)
    check(ardo.crack_revealed,
          "Ardo catlagi iz surerek buluyor - oda cikmaz degil")

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Bolum 2 tasarim belgesine uyuyor.")
    return 0


raise SystemExit(main())
