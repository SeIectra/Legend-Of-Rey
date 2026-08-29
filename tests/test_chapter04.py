"""Bolum 4 dogrulamasi - "Kayit Odasi" bassiz oynanir.

`docs/yapi.md` B4: *"Dovus yok. Onceki maceracinin kampi: iskelet, gunluk
(resimli, kelimesiz), yarim harita. Ilerleme: ilk yetenek agaci ekrani.
Rey burada kolyeyi ilk kez cevirir - sessiz karakter ani."*

`tests/test_chapter03.py` ile ayni desen: bolum bassiz **oynaniyor**, elle
gezmek yerine. Bu bolumde dovus olmadigi icin testlerin cogu bir seyin
**olmadigini** dogruluyor - dusman yok, replik yok, tus istenmiyor.
Olumsuz sartlar sessizce bozulur: birinin ileride buraya bir Suruklenen
koymasi kimseyi uyarmaz, bu test uyarir.

Calistir:
    python tests/test_chapter04.py
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
    ECHO_TIER_CLEAR, ECHO_TIER_MURKY, JOURNAL_PAGE_FRAMES,
    NECKLACE_MOMENT_FRAMES, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.core.input import Action  # noqa: E402
from src.scenes import chapter04_render as render  # noqa: E402
from src.scenes.chapter04 import (  # noqa: E402
    FLAG_HALF_MAP, FLAG_NECKLACE, FLAG_RESTED, Chapter04Scene,
)
from src.ui import i18n  # noqa: E402
from src.world.rooms.chapter04 import (  # noqa: E402
    FIRE_TILE, HALF_MAP_TILE, JOURNAL_TILE, LEVEL, NECKLACE_TILE,
    ROOM_STARTS, SECRETS_TOTAL,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def make_scene(game: Game, character: str = "rey") -> Chapter04Scene:
    """Sahneyi bastan kurar. **`Game` yeniden yaratilmiyor** - bu makinede
    `pygame.quit()` sonrasi `pygame.init()` 40 saniye suruyor (DEVIR.md
    6/22). Tek `Game`, sonda tek `shutdown()`."""
    game.scenes.set_root(Chapter04Scene, transition=False, character=character)
    game.scenes._flush()
    return game.scenes.current


def idle(game: Game, scene, frames: int) -> None:
    for _ in range(frames):
        game.input.begin_frame()
        game.input.end_frame()
        scene.update()


def press(game: Game, scene, action) -> None:
    """Bir tusa taze basar - `pressed()` yalnizca bu karede true doner."""
    game.input.begin_frame()
    game.input._activate(action)
    game.input._deactivate(action)
    game.input.end_frame()
    scene.update()


def teleport(scene, tile_x: int, tile_y: int = 13) -> None:
    """Oyuncuyu bir tile'in **uzerine** koyar.

    `tile_y` govdenin icinde durdugu bos satir; ayaklar onun altina
    oturur. Katı tile ile cakisan govde tamamen donuyor (DEVIR.md 6/20),
    o yuzden cagiran taraf bos satir vermek zorunda.
    """
    scene.player.body.set_feet(tile_x * TILE_SIZE + TILE_SIZE * 0.5,
                               (tile_y + 1) * TILE_SIZE)
    scene.player.body.vx = 0.0
    scene.player.body.vy = 0.0


def main() -> int:
    i18n.set_language("tr")
    game = Game()

    # --- 1. Harita: dort oda, sifir dusman -----------------------------------
    print("--- harita ---")
    check(len(ROOM_STARTS) == 4, "dort oda", str(len(ROOM_STARTS)))
    counts: dict[str, int] = {}
    for placement in LEVEL.placements:
        counts[placement.kind] = counts.get(placement.kind, 0) + 1
    # Nefes bolumu: haritada dusman **isareti** bile olmamali.
    enemy_kinds = ("shambler", "climber", "bloated", "shadow_shambler",
                   "miniboss", "dummy")
    present = [k for k in enemy_kinds if counts.get(k)]
    check(not present, "haritada hicbir dusman isareti yok", ", ".join(present))
    check(counts.get("player") == 1, "tek dogum noktasi")
    check(counts.get("chest") == 1, "bir sandik", str(counts.get("chest")))
    check(counts.get("exit") == 1, "bir cikis")
    check(SECRETS_TOTAL == 0, "gizli alan yok - nefes bolumu")

    # --- 2. Dogum noktasi tamamen bos tile'da --------------------------------
    # DEVIR.md 6/20: govdesi kati tile ile cakisan aktor tamamen donuyor.
    scene = make_scene(game)
    spawn = LEVEL.first("player")
    solid_rows = [r for r in (spawn.tile_y, spawn.tile_y - 1)
                  if scene.tilemap.is_solid(spawn.tile_x, r)]
    check(not solid_rows, "dogum noktasinin iki satiri da bos",
          f"kati satirlar {solid_rows}")
    idle(game, scene, 30)
    check(scene.player.body.grounded, "oyuncu zemine basiyor")
    check(abs(scene.player.body.center_x - spawn.x) < TILE_SIZE,
          "oyuncu dogum noktasinda duruyor (govde sikismadi)")

    # --- 3. Butun odalar gezilse de tek dusman dogmuyor -----------------------
    print("\n--- dovus yok ---")
    for name, start in ROOM_STARTS:
        teleport(scene, start + 2)
        idle(game, scene, 3)
        check(scene.room == name, f"{name} odasina girildi", scene.room)
    check(scene.enemies == [], "hicbir odada dusman dogmadi",
          str(len(scene.enemies)))

    # --- 4. Kamp: dinlenme, ates, iyilesme, yetenek agaci kancasi ------------
    print("\n--- kamp ---")
    scene = make_scene(game)
    scene.player.health = 10
    teleport(scene, FIRE_TILE[0], FIRE_TILE[1])
    idle(game, scene, 2)
    check(not scene.fire_lit, "ates basta sonuk")
    check(scene.toast_frames > 0, "ates yaninda dinlenme ipucu gosteriliyor")
    check("[" not in scene.toast, "ipucu metni cozuldu (ham anahtar degil)",
          scene.toast)

    opened: list[bool] = []
    scene.open_skill_tree = lambda: opened.append(True)   # kanca gozlemleniyor
    press(game, scene, Action.INTERACT)
    check(scene.rested, "INTERACT ile dinlenildi")
    check(scene.fire_lit, "dinlenince sonmus ates yeniden yandi")
    check(scene.player.health == scene.player.max_health,
          "dinlenince can doldu", f"{scene.player.health}")
    check(scene.save_data.flags.get(FLAG_RESTED) is True,
          "kayit bayragi yazildi", FLAG_RESTED)
    check(opened == [True], "yetenek agaci kancasi tam bir kez cagrildi",
          str(len(opened)))

    # Kanca **bos** olmali - ekran ayri bir iste yaziliyor.
    fresh = make_scene(game)
    check(fresh.open_skill_tree() is None,
          "open_skill_tree() bos kanca (henuz ekran acmiyor)")

    # --- 5. Kelimesiz gunluk --------------------------------------------------
    print("\n--- kelimesiz gunluk ---")
    scene = make_scene(game)
    check(scene.journal_alpha == 0.0, "gunluk basta kapali")
    teleport(scene, JOURNAL_TILE[0], JOURNAL_TILE[1])
    idle(game, scene, 20)
    check(scene.journal_alpha >= 1.0, "yaklasinca acildi",
          f"{scene.journal_alpha:.2f}")
    check(scene.journal_page == 0, "ilk sayfadan basliyor")
    idle(game, scene, JOURNAL_PAGE_FRAMES)
    check(scene.journal_page == 1, "sayfa kendi cevrildi (tus gerekmiyor)",
          str(scene.journal_page))
    check(render.page_count() == 4, "gunlukte dort sayfa var",
          str(render.page_count()))
    # Kelimesizlik: sayfalarda yalnizca piktogram var, metin yok.
    known = set(render.GLYPHS)
    unknown = [name for page in render.PAGES for name, *_ in page
               if name not in known]
    check(not unknown, "her sayfa ogesi tanimli bir piktogram",
          ", ".join(unknown))
    palette_names = {tone for page in render.PAGES for *_, tone in page}
    from src.art import palette  # noqa: E402
    bad = [n for n in palette_names if palette.color(n) is None]
    check(not bad, "piktogram renkleri paletten", ", ".join(bad))

    teleport(scene, JOURNAL_TILE[0] + 8, JOURNAL_TILE[1])
    idle(game, scene, 30)
    check(scene.journal_alpha == 0.0, "uzaklasinca kapandi")
    check(scene.journal_page == 0, "kapaninca ilk sayfaya donuyor")

    # --- 6. Yarim harita ------------------------------------------------------
    print("\n--- yarim harita ---")
    scene = make_scene(game)
    check(not scene.map_taken, "harita basta yerde")
    teleport(scene, HALF_MAP_TILE[0], HALF_MAP_TILE[1])
    idle(game, scene, 3)
    check(scene.map_taken, "dokununca alindi (tus istemiyor)")
    check(scene.save_data.flags.get(FLAG_HALF_MAP) is True,
          "kayit bayragi yazildi", FLAG_HALF_MAP)

    # Harita sahanligin **ustunde**: altindan gecen oyuncu almamali.
    scene = make_scene(game)
    teleport(scene, HALF_MAP_TILE[0], 13)
    idle(game, scene, 3)
    check(not scene.map_taken,
          "ana zeminden gecerken alinmiyor (dikey mesafe sayiliyor)")

    # --- 7. Kolye ani - kelimesiz --------------------------------------------
    print("\n--- kolye ani ---")
    scene = make_scene(game)
    scene.echo.tier = ECHO_TIER_MURKY
    teleport(scene, ROOM_STARTS[3][1] + 2)
    idle(game, scene, 3)
    check(scene.room == "esik", "esik odasina girildi", scene.room)
    scene.dialogue.stop()                 # odaya giris repligini kapat
    teleport(scene, NECKLACE_TILE[0], NECKLACE_TILE[1])
    idle(game, scene, 3)
    check(scene.necklace_active, "kolye ani kendiliginden basladi")
    check(scene.dialogue.done, "an KELIMESIZ - replik acilmadi")
    idle(game, scene, NECKLACE_MOMENT_FRAMES)
    check(scene.necklace_done, "an tamamlandi")
    check(scene.echo.tier == ECHO_TIER_CLEAR,
          "Yanki bir kademe berraklasti", str(scene.echo.tier))
    check(scene.save_data.flags.get(FLAG_NECKLACE) is True,
          "kayit bayragi yazildi", FLAG_NECKLACE)

    # Replik surerken baslamiyor - ama tetik kuruluyor ve replik bitince
    # calisiyor (oyuncu ani kaciramaz).
    scene = make_scene(game)
    teleport(scene, ROOM_STARTS[3][1] + 2)
    idle(game, scene, 3)
    teleport(scene, NECKLACE_TILE[0], NECKLACE_TILE[1])
    idle(game, scene, 3)
    check(not scene.necklace_active, "replik ekrandayken an baslamiyor")
    check(scene.necklace_ready, "tetik kuruldu, sirasini bekliyor")
    scene.dialogue.stop()
    teleport(scene, NECKLACE_TILE[0] + 6, NECKLACE_TILE[1])   # noktadan uzakta
    idle(game, scene, 3)
    check(scene.necklace_active,
          "replik bitince an basliyor - oyuncu uzaklassa bile kaciramiyor")

    # --- 8. Ardo: Yanki yok, replikler onun agzindan --------------------------
    print("\n--- Ardo ---")
    ardo = make_scene(game, character="ardo")
    check(not ardo.has_echo, "Ardo'nun Yankisi yok")
    line = ardo.dialogue.current
    check(line is not None and line.speaker == "ardo",
          "giris repligi Ardo'nun agzindan",
          line.speaker if line else "replik yok")
    check(line is not None and line.key == "line.ch04_ardo_enter",
          "Ardo kendi metnini aliyor", line.key if line else "-")
    ardo.dialogue.stop()
    teleport(ardo, ROOM_STARTS[3][1] + 2)
    idle(game, ardo, 3)
    ardo.dialogue.stop()
    teleport(ardo, NECKLACE_TILE[0], NECKLACE_TILE[1])
    idle(game, ardo, 3 + NECKLACE_MOMENT_FRAMES)
    check(ardo.necklace_done, "Ardo da ani yasiyor (jest karaktere ozel degil)")

    # Rey'de giris repligi Yanki'nin.
    rey = make_scene(game)
    line = rey.dialogue.current
    check(line is not None and line.speaker == "echo",
          "Rey'de giris repligi Yanki'nin",
          line.speaker if line else "replik yok")

    # --- 9. Cikis ve bolum sonu ----------------------------------------------
    print("\n--- cikis ---")
    scene = make_scene(game)
    exit_at = LEVEL.first("exit")
    teleport(scene, exit_at.tile_x, exit_at.tile_y)
    idle(game, scene, 2)
    check(scene.finished, "cikisa varinca bolum bitti")
    game.scenes._flush()
    end = game.scenes.current
    rows = end._rows()
    check(any(r[0] == "chapter_end.gold" for r in rows),
          "bolum sonu ekrani acildi")
    check(not any(r[0] == "chapter_end.secrets" for r in rows),
          "gizli alan satiri YOK (bu bolumde gizli alan yok)")
    check(not any(r[0] == "chapter_end.purple_flame" for r in rows),
          "Mor Alev satiri YOK (Bolum 3'e ait)")
    game.scenes.pop()
    game.scenes._flush()

    # --- 10. Erisilebilirlik ---------------------------------------------------
    print("\n--- erisilebilirlik ---")
    sys.path.insert(0, str(ROOT / "tools"))
    from tools.reachability import validate  # noqa: E402
    report = validate(LEVEL.terrain_rows, (spawn.tile_x, spawn.tile_y + 1),
                      "bolum 4")
    check(report.ok, "her basilabilir nokta ulasilabilir", report.summary())

    # --- 11. Dil anahtarlari ----------------------------------------------------
    print("\n--- dil ---")
    keys = ("chapter.record_room", "chapter04.rested", "chapter04.map_found",
            "chapter04.gold_found", "chapter04.hint_rest",
            "line.ch04_echo_enter", "line.ch04_ardo_enter",
            "line.ch04_echo_camp", "line.ch04_ardo_camp",
            "line.ch04_echo_map", "line.ch04_ardo_map",
            "line.ch04_echo_exit", "line.ch04_ardo_exit")
    for code in ("tr", "en"):
        i18n.set_language(code)
        missing = [k for k in keys if i18n.t(k) == f"[{k}]"]
        check(not missing, f"{code}: butun Bolum 4 anahtarlari cozuluyor",
              ", ".join(missing))
    i18n.set_language("tr")

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Bolum 4 tasarim belgesine uyuyor.")
    return 0


raise SystemExit(main())
