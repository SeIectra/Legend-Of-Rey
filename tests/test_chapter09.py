"""Bolum 9 "Can Kulesi" - dikey bolum, sira bulmacasi, firlatma.

`docs/yapi.md` B9: *"Dikey bolum. Rezonans ile uc cani dogru sirada
calmak, sira ipucu duvardaki freskte. Team-up firlatma - Ardo seni
platformlara firlatir."*

Korunan kurallar:

  * **Katlar y'ye gore.** Sekiz bolumdur odalar x'e gore diziliyordu;
    burada satira bakiliyor. Biri `_room_at` desenini kopyalayip
    yapistirirsa bu test kirilsin.
  * **Firlatma zorunlu.** Katlar arasi mesafe ziplama zarfindan
    buyuk - kule tek basina tirmanilamiyor. Sayi olculuyor, tahmin
    edilmiyor.
  * **Tek seferlik impuls** (`docs/yapi.md` 118: *"fizik motoru
    gerekmez"*). Iki taraf da yerde ve yakin olmali; bekleme
    zincirlemeyi onluyor.
  * **Yanlis sira cezasiz.** Canlar sifirlaniyor, oyuncu kaybetmiyor.
    Bir bulmaca geri alinabilir olmali.
  * **Yoldas kaybolmuyor.** Firlatilan yukari cikiyor, atan asagida
    kaliyor ve `Companion`'in yol bulmasi yok - yetisme mekanizmasi
    olmasa yoldas kalici olarak kaybolurdu.

Calistir:
    python tests/test_chapter09.py
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
    MAX_JUMP_HEIGHT_TILES, PLAYER_JUMP_SPEED, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.scenes.chapter09 import CATCHUP_FRAMES, Chapter09Scene  # noqa: E402
from src.scenes.chapter09_cinematics import TrustCinematic  # noqa: E402
from src.systems import boost  # noqa: E402
from src.systems.save import SaveData, write_save  # noqa: E402
from src.world.rooms.chapter09 import (  # noqa: E402
    BELL_ORDER, BELL_TILES, EXIT_DOOR_COLUMN, EXIT_DOOR_ROWS, FLOOR_NAMES,
    FLOOR_ROWS, LEVEL,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def start(game, character: str = "rey") -> Chapter09Scene:
    write_save(SaveData(chapter=9, character=character,
                        abilities=["sword", "dodge", "echo_sight"],
                        flags={"resonance": True}))
    game.scenes.set_root(Chapter09Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter09Scene)
    return scene


# --- 1. Dikey ----------------------------------------------------------------
def test_vertical() -> None:
    print("\n--- dikey kule ---")
    game = Game()
    try:
        scene = start(game)
        check(len(FLOOR_ROWS) == len(FLOOR_NAMES) == 5, "bes kat")

        # Katlar **y**'ye gore secilıyor: ayni x'te farkli yukseklikler
        # farkli kat vermeli.
        top = scene._floor_at(FLOOR_ROWS[-1] * TILE_SIZE)
        bottom = scene._floor_at(FLOOR_ROWS[0] * TILE_SIZE)
        check(top != bottom, "kat SATIRA gore secilıyor",
              f"{bottom} / {top}")
        check(bottom == FLOOR_NAMES[0], "en asagi taban", bottom)
        check(top == FLOOR_NAMES[-1], "en yukari tepe", top)

        # Katlar arasi mesafe ziplama zarfini **asmali**, yoksa
        # firlatma mekanigi gereksiz olurdu.
        spacing = FLOOR_ROWS[0] - FLOOR_ROWS[1]
        check(spacing > MAX_JUMP_HEIGHT_TILES,
              "katlar tek basina tirmanilamiyor",
              f"{spacing} tile > {MAX_JUMP_HEIGHT_TILES}")
    finally:
        game.shutdown()


# --- 2. Firlatma -------------------------------------------------------------
def test_boost() -> None:
    print("\n--- firlatma ---")
    game = Game()
    try:
        scene = start(game)
        check(not scene.boost.unlocked, "basta KILITLI")
        check(not scene.boost.launch(scene.companion, scene.player, True),
              "kilitliyken firlatma yok")

        scene._teach_boost()
        game.scenes._flush()
        check(isinstance(game.scenes.current, TrustCinematic),
              "ogretme aninda guven sahnesi aciliyor",
              type(game.scenes.current).__name__)
        game.scenes.pop()
        game.scenes._flush()

        # Iki taraf da YERDE ve YAKIN olmali.
        scene.companion.body.set_feet(scene.player.body.center_x + 12,
                                      scene.player.body.feet[1])
        scene.player.body.grounded = True
        scene.companion.body.grounded = True
        check(scene.boost.ready(scene.companion, scene.player),
              "yan yana ve yerdeyken hazir")

        scene.player.body.grounded = False
        check(not scene.boost.ready(scene.companion, scene.player),
              "HAVADAYKEN firlatma yok - cift ziplama ayri bir yetenek")
        scene.player.body.grounded = True

        scene.companion.body.set_feet(
            scene.player.body.center_x + boost.BOOST_RANGE * 3,
            scene.player.body.feet[1])
        check(not scene.boost.ready(scene.companion, scene.player),
              "UZAKTAN firlatma yok - goremedigine kendini birakamazsin")
        scene.companion.body.set_feet(scene.player.body.center_x + 12,
                                      scene.player.body.feet[1])

        # Tek seferlik impuls: dikey hiz veriliyor, fizik motoru yok.
        launched = scene.boost.launch(scene.companion, scene.player, True)
        check(launched, "firlatma calisti")
        check(scene.player.body.vy < -PLAYER_JUMP_SPEED,
              "ziplamadan DAHA yukari itiyor",
              f"vy={scene.player.body.vy:.2f} (zipla {-PLAYER_JUMP_SPEED})")
        check(not scene.player.body.grounded, "artik havada")

        check(not scene.boost.launch(scene.companion, scene.player, True),
              "bekleme zincirlemeyi onluyor",
              f"{scene.boost.cooldown} kare")

        # Guclu olan daha yukari atiyor - roller karakterden turuyor.
        #
        # `cooldown` YETMIYOR: `ready()` `active`e de bakiyor ve onceki
        # firlatmanin animasyon karesi (`frames`) hala sayiyor. Ikisini
        # birden sifirlamak gerek - testi yazarken bunu atlayinca iki
        # olcum de 0.00 cikti ve kontrol hakli olarak kirildi.
        def relaunch(strong: bool) -> float:
            scene.boost.cooldown = 0
            scene.boost.frames = 0
            scene.player.body.grounded = True
            scene.player.body.vy = 0.0
            scene.boost.launch(scene.companion, scene.player, strong=strong)
            return scene.player.body.vy

        strong_vy = relaunch(True)
        light_vy = relaunch(False)
        check(strong_vy < light_vy,
              "guclu olan (Ardo) daha yukari atiyor",
              f"{strong_vy:.2f} < {light_vy:.2f}")
    finally:
        game.shutdown()


# --- 3. Can sirasi -----------------------------------------------------------
def test_bells() -> None:
    print("\n--- can sirasi ---")
    game = Game()
    try:
        scene = start(game)
        check(len(scene.bells) == len(BELL_ORDER) == 3, "uc can")
        check(sorted(BELL_ORDER) == [0, 1, 2],
              "sira butun canlari kapsiyor", str(BELL_ORDER))
        # Sira **konumdan bagimsiz** olmali: en usttekini once calmak
        # zorunda kalirsa kule bir tirmanis olur, dolasma degil.
        check(BELL_ORDER != (0, 1, 2),
              "sira konum siralamasindan FARKLI", str(BELL_ORDER))
        # Canlar farkli katlarda: bulmaca haritayi ogretiyor.
        floors = {scene._floor_at(y * TILE_SIZE) for _, y in BELL_TILES}
        check(len(floors) == 3, "uc can uc ayri katta", str(sorted(floors)))

        def ring(index: int) -> None:
            scene._ring(scene.bells[index])

        # --- Yanlis sira: cezasiz sifirlama ---
        wrong = next(i for i in range(3) if i != BELL_ORDER[0])
        ring(wrong)
        check(scene.rung == [], "yanlis sira hepsini sifirliyor")
        check(all(not b.triggered for b in scene.bells),
              "canlar yeniden calinabilir")
        check(not scene.solved, "bulmaca cozulmedi")
        # Ceza yok: can, altin, geri gonderme - hicbiri.
        check(scene.player.health == scene.player.max_health,
              "yanlis sira CAN goturmuyor")

        # --- Dogru sira ---
        for index in BELL_ORDER:
            scene.bells[index].reset()
            ring(index)
        check(scene.solved, "dogru sira bulmacayi cozuyor")
        check(not scene.tilemap.is_solid(EXIT_DOOR_COLUMN,
                                         EXIT_DOOR_ROWS.start),
              "kapi aciliyor")
    finally:
        game.shutdown()


# --- 4. Yoldas kaybolmuyor ---------------------------------------------------
def test_catchup() -> None:
    print("\n--- yoldas tirmaniyor ---")
    game = Game()
    try:
        scene = start(game)
        # Oyuncu iki kat yukari, yoldas asagida - firlatmadan sonraki
        # dogal durum.
        scene.player.body.set_feet(200.0, FLOOR_ROWS[2] * TILE_SIZE)
        scene.player.body.grounded = True
        scene.companion.body.set_feet(200.0, FLOOR_ROWS[0] * TILE_SIZE)
        far = scene.companion.body.feet[1] - scene.player.body.feet[1]
        check(far > 0, "yoldas gercekten asagida", f"{far:.0f} piksel")

        for _ in range(CATCHUP_FRAMES + 5):
            scene._update_catchup()
        gap = abs(scene.companion.body.feet[1] - scene.player.body.feet[1])
        check(gap < TILE_SIZE * 3, "yoldas yetisti", f"{gap:.0f} piksel")
        check(not scene.tilemap.solid_overlap(scene.companion.body.rect),
              "ve duvarin icine konmadi")
    finally:
        game.shutdown()


# --- 5. Bolum sonu -----------------------------------------------------------
def test_chapter_end() -> None:
    print("\n--- bolum sonu ---")
    game = Game()
    try:
        scene = start(game)
        check(scene.chapter_number == 9, "bolum numarasi 9")
        exit_at = LEVEL.first("exit")
        scene.player.body.set_feet(exit_at.x + 4, exit_at.feet_y)
        scene._check_exit()
        check(not scene.finished,
              "bulmaca COZULMEDEN cikis calismiyor - kule atlanamaz")
        scene.solved = True
        scene._check_exit()
        check(scene.finished, "cozulunce cikis calisiyor")
        check(scene.save_data.chapter == 9, "kayda bolum 9 yaziliyor")
        check(scene.save_data.flags.get("boost") is True,
              "firlatma kayda yaziliyor - sonraki bolumlerde duruyor")
    finally:
        game.shutdown()


def main() -> int:
    print("=== BOLUM 9: CAN KULESI ===")
    test_vertical()
    test_boost()
    test_bells()
    test_catchup()
    test_chapter_end()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("Can Kulesi: dikey, firlatma zorunlu, sira cezasiz.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
