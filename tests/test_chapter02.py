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

# `pygame.init()` DEGIL. O, joystick alt sistemini de acar ve bu
# makinede 40 SANIYE surer (olculdu 30.08.2026 - bir surucu sorunu,
# kodla ilgisi yok). 21 test paketi bunu ayri ayri odedigi icin butun
# paket 14 dakikayi asiyordu.
#
# `src/core/game.py` de tam olarak bu yolu izliyor; test oyunla ayni
# sekilde acilsin. Ses gerekirse `synth.init_mixer()` cagrilir.
pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.config import (  # noqa: E402
    CLIMBER_PATIENCE_FRAMES, INTERNAL_HEIGHT, INTERNAL_WIDTH, TILE_SIZE,
)
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

    # --- Inis ara sahnesi (ilk gercek StoryScene kullanimi) -----------------
    # `src/scenes/story.py` yazilmisti ama hicbir yerden cagrilmiyordu.
    # DEVIR.md'nin kendi dersi: "yazilip hic calistirilmayan kod hatasiz
    # gorunur, hatasiz degildir" (tileset.py ve Boss.draw_health_bar ayni
    # tuzaga dusmustu). Bu test o altyapiyi bastan sona oynatiyor.
    print("\n--- inis ara sahnesi ---")
    from src.scenes.chapter02_cinematics import DescentCinematic
    from src.scenes.story import Panel

    check(all(isinstance(x, Panel) for x in DescentCinematic.PANELS),
          "ara sahne Panel listesiyle tanimli",
          str(len(DescentCinematic.PANELS)) + " panel")
    cine_game = Game()
    cine_game.scenes.set_root(DescentCinematic, transition=False,
                              character="rey")
    cine_game.scenes._flush()
    cine = cine_game.scenes.current
    # `duration_frames` StoryScene'de PROPERTY (panellerden hesaplaniyor) -
    # sinif uzerinden okunursa property nesnesi doner, ornek uzerinden
    # okunmali.
    check(cine.duration_frames > 0, "sure panellerden hesaplaniyor",
          str(cine.duration_frames) + " kare")
    surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))

    seen_panels = set()
    seen_line = False
    for _ in range(cine.duration_frames + 400):
        cine_game.input.begin_frame(); cine_game.input.end_frame()
        cine.update()
        if cine.panel is not None:
            seen_panels.add(cine.panel.name)
        if cine.dialogue.current is not None:
            seen_line = True
        cine.draw(surface)          # cizim de patlamamali
        if cine.finished:
            break

    check(len(seen_panels) == len(DescentCinematic.PANELS),
          "butun paneller sirayla oynadi",
          ", ".join(sorted(seen_panels)))
    check(seen_line, "sinematik icinde replik gosterildi (Arda'nin karari)")
    check(cine.finished, "ara sahne kendiliginden bitti - takilmiyor")
    cine_game.shutdown()

    # --- Boss atlanamaz: kilitli cikis + anahtar ----------------------------
    # Arda'nin bildirdigi kacak (24.08.2026): "birinci boss fight ile hic
    # kapismadan bolumu gecebiliyorsun, sadece ilerlemek yeterli." Arena
    # kapisi yalnizca GIRISI muhurluyordu; arka tarafta hicbir sey yoktu.
    print("\n--- boss atlanamaz (kilitli cikis + anahtar) ---")
    from src.world.rooms.chapter02 import ARENA_EXIT_COLUMN, ARENA_EXIT_ROWS

    skip_game = Game()
    skip_game.scenes.set_root(Chapter02Scene, transition=False, character="rey")
    skip_game.scenes._flush()
    skip = skip_game.scenes.current

    check(skip.exit_door.locked, "cikis kapisi bastan KILITLI")
    blocked = all(skip.tilemap.is_solid(ARENA_EXIT_COLUMN, r)
                  for r in ARENA_EXIT_ROWS)
    check(blocked, "kilitli kapinin butun satirlari kati - gecilemez")
    check(skip.boss_key is None, "anahtar boss olmeden ortada YOK")

    # Boss'u oldur: anahtar dusmeli, kapi HALA kilitli olmali.
    skip._open_arena()
    check(skip.boss_key is not None, "boss olunce anahtar dustu")
    check(skip.exit_door.locked,
          "anahtar dusunce kapi HENUZ acilmiyor - alinmasi gerek")

    # Anahtari al: kapi acilmali.
    skip.player.body.set_feet(skip.boss_key.x, skip.boss_key.feet_y)
    for _ in range(10):
        skip_game.input.begin_frame(); skip_game.input.end_frame()
        skip.update()
    check(skip.has_key, "anahtar alindi")
    check(not skip.exit_door.locked, "anahtarla kapi acildi")
    opened = all(not skip.tilemap.is_solid(ARENA_EXIT_COLUMN, r)
                 for r in ARENA_EXIT_ROWS)
    check(opened, "kapinin butun satirlari acildi - gecilebilir")
    skip_game.shutdown()

    # --- Tirmanan tavana GOMULU dogmuyor -----------------------------------
    # Arda: "mini boss'tan hemen once tepedeki asilanlar asagi dusemiyor."
    # Kok neden: govde tavan tile'inin ICINDE basliyordu, carpisma cozucu
    # cakismayi gorup `grounded` deyip dususu iptal ediyordu.
    print("\n--- Tirmanan tavana gomulu dogmuyor ---")
    from src.entities.enemies.climber import Climber

    climb_game = Game()
    climb_game.scenes.set_root(Chapter02Scene, transition=False,
                               character="rey")
    climb_game.scenes._flush()
    climb = climb_game.scenes.current
    climb.player.body.set_feet(110 * TILE_SIZE, 13 * TILE_SIZE)
    for _ in range(5):
        climb_game.input.begin_frame(); climb_game.input.end_frame()
        climb.update()
    hangers = [e for e in climb.enemies if isinstance(e, Climber)]
    check(bool(hangers), "odada Tirmanan var", str(len(hangers)))
    if hangers:
        hanger = hangers[0]
        head_row = int(hanger.body.y) // TILE_SIZE
        column = int(hanger.body.center_x) // TILE_SIZE
        check(not climb.tilemap.is_solid(column, head_row),
              "Tirmanan'in bulundugu satir KATI DEGIL (tavana gomulu degil)",
              "satir " + str(head_row))
        start_y = hanger.body.y
        for _ in range(CLIMBER_PATIENCE_FRAMES + 120):
            climb_game.input.begin_frame(); climb_game.input.end_frame()
            climb.update()
        check(not hanger.hanging, "sabir esiginde birakti")
        check(hanger.body.y > start_y + TILE_SIZE,
              "gercekten ASAGI DUSTU (birakma emri bosa gitmiyor)",
              "delta " + str(round(hanger.body.y - start_y, 1)) + "px")
    climb_game.shutdown()

    # --- Olumden sonra R gercekten sifirliyor (YUMUSAK KILIT) ---------------
    # Olum ekrani "OLDUN - R ile sifirla" yaziyordu ama R'yi YALNIZCA dovus
    # test odasi dinliyordu; bolumlerde tusun hicbir karsiligi yoktu.
    # Boss arenasinin cikisi anahtarla acilir hale gelince bu gercek bir
    # kilitlenmeye donustu: yenilen oyuncu ne sifirlayabiliyor ne
    # cikabiliyordu.
    print("\n--- olumden sonra R sifirliyor ---")
    dead_game = Game()
    dead_game.scenes.set_root(Chapter02Scene, transition=False, character="rey")
    dead_game.scenes._flush()
    dead = dead_game.scenes.current
    start_x = dead.player.body.center_x

    dead.player.body.set_feet(2600.0, 14 * TILE_SIZE)
    for _ in range(20):
        dead_game.input.begin_frame(); dead_game.input.end_frame()
        dead.update()
    dead.player.health = 0
    dead.player.dead = True

    # Diri oyuncuda R HICBIR SEY yapmamali - yanlislikla sifirlama olmasin.
    dead.player.dead = False
    reset_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
    moved_x = dead.player.body.center_x
    dead.handle_event(reset_event)
    check(abs(dead_game.scenes.current.player.body.center_x - moved_x) < 1.0,
          "DIRI oyuncuda R sifirlamiyor (kaza korumasi)")

    dead.player.dead = True
    dead.handle_event(reset_event)
    fresh = dead_game.scenes.current
    check(not fresh.player.dead, "R'den sonra oyuncu diri")
    check(fresh.player.health == fresh.player.max_health,
          "cani dolu", str(fresh.player.health))
    # **Davranis 29.08.2026'da bilerek degisti:** R artik bolumun degil
    # ODANIN basina donduruyor (kontrol noktasi - `tests/test_checkpoint.py`).
    # Bu kontrol eskiden "bolum basina dondu" diyordu; on dakikalik bir
    # bolumun sonunda olmek her seyi bastan oynamak demekti.
    check(fresh.player.body.center_x > start_x + TILE_SIZE * 10,
          "bolum basina DONMEDI - oldugu odadan devam ediyor",
          str(round(fresh.player.body.center_x, 1)))
    check(fresh.room == dead.checkpoint_room,
          "kontrol noktasi odasinda", fresh.room)
    check(fresh.exit_door.locked and not fresh.has_key,
          "kapi yeniden kilitli - olmek boss'u atlamanin yolu DEGIL")
    dead_game.shutdown()

    # --- Yanki Rey'e ozel, Bolum 2'de de -----------------------------------
    # Bolum 1'de duzeltilen hatanin aynisi burada da vardi: uc Yanki
    # repligi kapisizdi ve tirmik izi tepkisi sabit "rey" konusmacisiyla
    # yaziliydi. Bir bolume yazilan duzeltmenin otekine tasinmamasi bu
    # projenin en sik tekrarlanan hatasi.
    print("\n--- Bolum 2: Yanki Rey'e ozel ---")
    from src.world.rooms.chapter02 import ROOM_STARTS as _ROOMS

    def room_speakers(character: str):
        rs_game = Game()
        rs_game.scenes.set_root(Chapter02Scene, transition=False,
                                character=character)
        rs_game.scenes._flush()
        scene = rs_game.scenes.current
        found = []
        for _room, column in _ROOMS:
            scene.player.body.set_feet((column + 3) * TILE_SIZE, 13 * TILE_SIZE)
            for _ in range(4):
                rs_game.input.begin_frame(); rs_game.input.end_frame()
                scene.update()
            cur = scene.dialogue.current
            if cur is not None:
                found.append(cur.speaker)
        rs_game.shutdown()
        return found

    rey_speakers = room_speakers("rey")
    ardo_speakers = room_speakers("ardo")
    check("echo" in rey_speakers, "Rey Bolum 2'de Yanki'yi duyuyor",
          ", ".join(rey_speakers))
    check("echo" not in ardo_speakers,
          "Ardo Bolum 2'de Yanki'yi DUYMUYOR", ", ".join(ardo_speakers))
    check("rey" not in ardo_speakers,
          "Ardo oynarken REY etiketi cikmiyor", ", ".join(ardo_speakers))
    check("ardo" in ardo_speakers,
          "Ardo kendi gozlemiyle konusuyor - oda sessiz kalmiyor",
          ", ".join(ardo_speakers))

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Bolum 2 tasarim belgesine uyuyor.")
    return 0


raise SystemExit(main())
