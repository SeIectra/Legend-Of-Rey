"""Olum sonrasi kontrol noktasi - oyuncu ODANIN basindan devam ediyor mu.

DEVIR acik madde 8'di: "Checkpoint yok. Oyuncu olunce sahne yeniden
kurulmuyor." Sonra `PlayScene.restart()` yazildi ama bolumun **basina**
donuyordu - on dakikalik bir bolumun sonunda olmek her seyi bastan
oynamak demekti.

Tasarim karari: **kismi geri alma YOK.** Sahne yine tamamen bastan
kuruluyor (yoksa kapilar/anahtarlar/arena muhru/su seviyesi gibi
degismezlerden biri mutlaka bayat kalir), sonra oyuncu oldugu odanin
basina isinlaniyor ve o odanin dusmanlari yeniden doguyor.

Korunan kurallar:

  * Kontrol noktasi oda degisiminde ve **yalnizca yerdeyken** aliniyor
    (havada alinsaydi bosluga dusen oyuncu bosluga geri dogardi)
  * Olum sonrasi oyuncu **bolumun degil odanin** basinda
  * Sahne gercekten **bastan kurulmus** oluyor (can dolu, dusmanlar var)
  * Anlati **tekrarlanmiyor** - `entered_rooms` tasiniyor
  * Oda kullanmayan sahneler (Bolum 1) bozulmuyor

Calistir:
    python tests/test_checkpoint.py
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

from src.config import TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.scenes.chapter02 import Chapter02Scene  # noqa: E402
from src.world.rooms.chapter02 import ROOM_STARTS  # noqa: E402

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


def main() -> int:
    game = Game()
    game.scenes.set_root(Chapter02Scene, transition=False, character="rey")
    game.scenes._flush()
    scene = game.scenes.current

    start_x = scene.player.body.center_x
    step(game, 10)

    print("--- baslangic ---")
    check(scene.checkpoint_room == scene.room,
          "ilk oda kontrol noktasi olarak alindi", scene.checkpoint_room)
    first_room = scene.checkpoint_room

    # --- 1. Ileri bir odaya gec ---------------------------------------------
    # **Dusmani olan** bir oda seciyoruz (5 = "patlayanlar"). Ilk surumde
    # 3. oda ("yanki_odasi") secilmisti ve orada dusman YOK - "dusmanlar
    # yeniden dogdu" kontrolu `0 == 0` diyerek geciyordu, yani hicbir sey
    # kanitlamiyordu. Gecen ama bos bir test testsizlikten daha kotu:
    # guvence gibi gorunuyor.
    # Arenadan onceki bir oda, yani boss'a ozel davranislar karismiyor.
    print("\n--- ileri odaya gecis ---")
    target_index = 5
    target_name, target_start = ROOM_STARTS[target_index]
    scene.player.body.set_feet((target_start + 3) * TILE_SIZE,
                               scene.player.body.bottom)
    scene.player.body.vx = scene.player.body.vy = 0.0
    step(game, 12)
    check(scene.room == target_name, "oyuncu yeni odada", scene.room)
    check(scene.checkpoint_room == target_name,
          "kontrol noktasi yeni odaya tasindi", scene.checkpoint_room)
    check(scene.checkpoint_room != first_room,
          "ilk odada takili kalmadi")
    saved_x = scene.checkpoint_x
    narrated = set(scene.entered_rooms)

    # --- 2. Havada kontrol noktasi ALINMIYOR --------------------------------
    # Bosluga dusup olen oyuncu tekrar boslukta dogsaydi sonsuz olum
    # dongusune girerdi.
    print("\n--- havada kaydetmiyor ---")
    scene.checkpoint_room = "sahte_oda"      # degisim tespit edilsin
    scene.player.body.set_feet(scene.player.body.center_x,
                               scene.player.body.bottom - TILE_SIZE * 3)
    scene.player.body.vy = -1.0
    scene.player.body.grounded = False
    scene._update_checkpoint()
    check(scene.checkpoint_room == "sahte_oda",
          "havadayken kontrol noktasi GUNCELLENMEDI",
          scene.checkpoint_room)
    scene.checkpoint_room = target_name
    scene.checkpoint_x = saved_x

    # --- 3. Olum: odanin basindan devam -------------------------------------
    print("\n--- olum sonrasi ---")
    scene.player.health = 0
    scene.player.die()
    check(scene.player.dead, "oyuncu oldu")

    scene.restart()
    check(not scene.player.dead, "yeni oyuncu diri")
    check(scene.player.health == scene.player.max_health,
          "can dolu", f"{scene.player.health}/{scene.player.max_health}")
    check(scene.room == target_name,
          "BOLUMUN degil ODANIN basinda", scene.room)
    check(abs(scene.player.body.center_x - saved_x) < 2.0,
          "tam olarak kontrol noktasinda",
          f"{scene.player.body.center_x:.0f} ~ {saved_x:.0f}")
    check(scene.player.body.center_x > start_x + TILE_SIZE * 10,
          "bolumun basina DONMEDI",
          f"{scene.player.body.center_x:.0f} vs {start_x:.0f}")

    # --- 4. Sahne gercekten bastan kuruldu ----------------------------------
    # Kismi geri alma olsaydi bayat durum kalirdi. Tam kurulum tek
    # guvenilir yol; bedeli odayi bastan oynamak.
    print("\n--- sahne taze ---")
    check(scene.boss is None or not scene.boss_defeated,
          "arena durumu taze")
    check(not scene.finished, "bolum bitmis sayilmiyor")
    check(scene.hitboxes.active_count == 0, "eski hitbox kalmadi",
          str(scene.hitboxes.active_count))

    # --- 5. Odanin dusmanlari yeniden dogdu ---------------------------------
    print("\n--- odanin dusmanlari geri geldi ---")
    from src.world.rooms.chapter02 import LEVEL
    end = (ROOM_STARTS[target_index + 1][1]
           if target_index + 1 < len(ROOM_STARTS) else 10_000)
    expected = sum(1 for kind in ("shambler", "climber", "bloated")
                   for spot in LEVEL.of(kind)
                   if target_start <= spot.tile_x < end)
    check(expected > 0,
          "secilen odada gercekten dusman VAR - kontrol bos degil",
          str(expected))
    check(len(scene.enemies) == expected,
          "odanin dusmanlari yeniden dogdu",
          f"{len(scene.enemies)} == {expected}")

    # --- 6. Anlati tekrarlanmiyor -------------------------------------------
    # Ust uste olen oyuncuya ayni replikleri okutmak ogut olur.
    print("\n--- anlati tekrarlanmiyor ---")
    check(narrated <= scene.entered_rooms,
          "girilmis odalar tasindi - replikler yeniden calmiyor",
          f"{len(scene.entered_rooms)} oda")

    # --- 7. Oda kullanmayan sahne bozulmuyor --------------------------------
    print("\n--- Bolum 1 (oda yok) bozulmuyor ---")
    from src.scenes.chapter01 import Chapter01Scene
    game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game.scenes._flush()
    village = game.scenes.current
    step(game, 10)
    check(village.checkpoint_room == "",
          "oda kullanmayan sahnede kontrol noktasi bos kaliyor",
          repr(village.checkpoint_room))
    village.player.health = 0
    village.player.die()
    village.restart()          # patlamamali
    check(not village.player.dead,
          "oda kullanmayan sahnede restart yine calisiyor - oyuncu diri")
    check(village.player.health == village.player.max_health,
          "cani da dolu",
          f"{village.player.health}/{village.player.max_health}")

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Kontrol noktasi: oda basindan devam, sahne taze, anlati sessiz.")
    return 0


raise SystemExit(main())
