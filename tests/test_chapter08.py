"""Bolum 8 "Ates Basi" - nefes bolumu + Yanki Rezonansi.

`docs/yapi.md` B8: *"Dovus yok. Ates, iki siluet... Yanki Rezonansi
burada ogrenilir - Ardo ona sesi silah olarak kullanmayi gosterir.
Yanki ilk kez Ardo hakkinda fisildar."*

Korunan kurallar:

  * **Sifir dusman.** `docs/yapi.md` 114: nefes bolumleri sifir dovus
    kodu ister. Bir gun buraya "biraz aksiyon" eklemek cazip gelecek;
    o an bu test kirilsin.
  * **Rezonans kilitli basliyor** - ara sahne aciyor. Oncesinde tus
    hicbir sey yapmiyor ("bozuk mu?" degil "henuz yok").
  * **Ses gecikmeli varir.** Halka genisliyor; uzaktaki kristal
    darbenin ilk karesinde degil, ses oraya VARINCA kiriliyor. Anlik
    olsaydi gorunmez bir el olurdu.
  * **Mandal yuruyerek ulasilamaz** - mekanigin butun noktasi bu.
  * **Yanki kademesi geri geliyor** (`docs/gdd.md` 41).
  * Fisilti sahnesi **iki oynanista farkli**: Rey'de Yanki konusuyor,
    Ardo'da Iz Surme gosteriyor.

Calistir:
    python tests/test_chapter08.py
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

# `pygame.init()` DEGIL - joystick alt sistemi bu makinede 40 saniye
# suruyor. `src/core/game.py` ile ayni yol.
pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.config import MAX_JUMP_GAP_TILES, TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.scenes.chapter08 import Chapter08Scene  # noqa: E402
from src.scenes.chapter08_cinematics import (  # noqa: E402
    FiresideCinematic, WhisperCinematic,
)
from src.systems import resonance  # noqa: E402
from src.systems.save import SaveData, write_save  # noqa: E402
from src.world.rooms.chapter08 import (  # noqa: E402
    FIRE_TILE, GATE_CRYSTAL_TILE, LATCH_DOOR_ROWS, LATCH_DOOR_TILE,
    LATCH_TILE_ABS, LEVEL, ROOM_STARTS,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def start(game, character: str = "rey") -> Chapter08Scene:
    write_save(SaveData(chapter=8, character=character,
                        abilities=["sword", "dodge", "echo_sight"]))
    game.scenes.set_root(Chapter08Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter08Scene)
    return scene


def settle(scene, frames: int) -> None:
    for _ in range(frames):
        scene.resonance.update()
        scene._update_crystals()


# --- 1. Nefes bolumu ---------------------------------------------------------
def test_breather() -> None:
    print("\n--- nefes bolumu ---")
    game = Game()
    try:
        scene = start(game)
        check(len(scene.enemies) == 0, "sifir dusman",
              f"{len(scene.enemies)} dusman")
        # Bolum verisinde de hic dusman isareti olmamali.
        markers = sum(len(LEVEL.of(kind)) for kind in
                      ("shambler", "climber", "bloated", "shieldbearer",
                       "shadow_shambler", "miniboss"))
        check(markers == 0, "oda verisinde de dusman isareti yok",
              f"{markers} isaret")
        check(scene.companion is not None, "yoldas yaninda")
    finally:
        game.shutdown()


# --- 2. Rezonans ogreniliyor -------------------------------------------------
def test_teaching() -> None:
    print("\n--- rezonans ogreniliyor ---")
    game = Game()
    try:
        scene = start(game)
        check(not scene.resonance.unlocked, "basta KILITLI")
        check(not scene.resonance.pulse(0, 0),
              "kilitliyken darbe cikmiyor")

        # Yanki kademesini dusur - nefes bolumu onarmali.
        scene.echo.tier = 0
        scene.player.body.set_feet(FIRE_TILE[0] * TILE_SIZE,
                                   scene.player.body.feet[1])
        scene.update_scene()
        game.scenes._flush()
        check(isinstance(game.scenes.current, FiresideCinematic),
              "atesin yaninda ara sahne aciliyor",
              type(game.scenes.current).__name__)
        game.scenes.pop()
        game.scenes._flush()

        check(scene.resonance.unlocked, "sahne rezonansi aciyor")
        check(scene.echo.tier > 0,
              "Yanki kademesi geri geldi - `docs/gdd.md` 41",
              f"kademe {scene.echo.tier}")
        check(scene.save_data.flags.get("resonance") is True,
              "kayda yaziliyor - olunce kaybolmasin")
    finally:
        game.shutdown()


# --- 3. Ses gecikmeli varir --------------------------------------------------
def test_sound_travels() -> None:
    print("\n--- ses yol aliyor ---")
    game = Game()
    try:
        scene = start(game)
        scene._learn_resonance()
        crystal = scene.gate_crystal
        # Oyuncu kristalden UZAKTA duruyor.
        distance = 70
        scene.player.body.set_feet(crystal.rect.centerx - distance,
                                   scene.player.body.feet[1])
        scene.resonance.pulse(scene.player.body.center_x,
                              crystal.rect.centery)
        scene._update_crystals()
        check(not crystal.triggered,
              "darbenin ILK karesinde kirilmiyor - ses henuz varmadi")

        settle(scene, resonance.PULSE_FRAMES + 5)
        check(crystal.triggered, "ses varinca kiriliyor")
        check(not scene.tilemap.is_solid(*GATE_CRYSTAL_TILE),
              "kirilinca tilemap'te de yol aciliyor")

        # Menzil disindaki bir sey vurulmamali.
        far = scene.teach_crystal
        scene.player.body.set_feet(far.rect.centerx - resonance.PULSE_RANGE * 2,
                                   scene.player.body.feet[1])
        scene.resonance.restore()
        scene.resonance.pulse(scene.player.body.center_x,
                              scene.player.body.center_y)
        settle(scene, resonance.PULSE_FRAMES + 5)
        check(not far.triggered, "menzil disi kirilmiyor - konum onemli")
    finally:
        game.shutdown()


# --- 4. Mandal yuruyerek ulasilamaz ------------------------------------------
def test_latch_unreachable() -> None:
    print("\n--- mandal ---")
    game = Game()
    try:
        scene = start(game)
        rows = list(LEVEL.terrain_rows)
        door_x = LATCH_DOOR_TILE
        latch_x = LATCH_TILE_ABS[0]
        # Kapi sutunu tavandan zemine kati olmali - yani etrafindan
        # dolasilamamali. Mekanigin butun noktasi bu.
        solid = all(rows[row][door_x] == "#" for row in LATCH_DOOR_ROWS)
        check(solid, "mandal odasi duvarla ayrilmis - yuruyerek girilmez")
        check(latch_x > door_x, "mandal duvarin ARDINDA",
              f"kapi {door_x}, mandal {latch_x}")
        # Aciklik da atlanamayacak kadar genis olmali.
        check(latch_x - door_x <= MAX_JUMP_GAP_TILES + 4,
              "mandal ses menzilinde", f"{latch_x - door_x} tile")

        scene._learn_resonance()
        # Oyuncu duvarin **dibine** kadar yuruyebiliyor; darbe oradan
        # atiliyor. Uc tile geriden atildiginda mandal 104 piksel uzakta
        # kaliyor ve menzil 96 - yani mekanik "duvara yaklas" diyor.
        scene.player.body.set_feet((door_x - 1) * TILE_SIZE,
                                   scene.player.body.feet[1])
        scene.resonance.pulse(scene.player.body.center_x,
                              scene.latch.rect.centery)
        settle(scene, resonance.PULSE_FRAMES + 5)
        check(scene.latch.triggered, "ses duvari asiyor")
        check(scene.door_open and not scene.tilemap.is_solid(
            door_x, LATCH_DOOR_ROWS.start), "kapi aciliyor")
    finally:
        game.shutdown()


# --- 5. Ara sahneler ---------------------------------------------------------
def test_cinematics() -> None:
    print("\n--- ara sahneler ---")
    for played in ("rey", "ardo"):
        game = Game()
        try:
            game.scenes.set_root(FiresideCinematic, transition=False,
                                 character=played)
            game.scenes._flush()
            fire = game.scenes.current
            spoken = [p for p in fire.panels if p.dialogue_lines]
            check(len(spoken) == 4, f"{played}: ates basi dort replikli",
                  f"{len(spoken)} panel")
            speakers = {line.speaker for p in spoken
                        for line in p.dialogue_lines}
            check(speakers == {"rey", "ardo"},
                  f"{played}: ikisi de konusuyor", str(sorted(speakers)))

            # Fisilti: iki oynanista FARKLI konusmaci.
            game.scenes.set_root(WhisperCinematic, transition=False,
                                 character=played)
            game.scenes._flush()
            whisper = game.scenes.current
            said = [line.speaker for p in whisper.panels
                    for line in p.dialogue_lines]
            expected = "echo" if played == "rey" else "ardo"
            check(expected in said,
                  f"{played}: fisiltiyi {expected} tasiyor", str(said))
            check(len(whisper.actors) == 1,
                  "yoldas sahnede YOK - fisilti onun arkasindan geliyor")

            for _ in range(160):
                game.input.begin_frame()
                game.input.end_frame()
                game.scenes.update()
                game.frame += 1
            game.canvas.fill((0, 0, 0))
            whisper.draw(game.canvas)
            painted = pygame.transform.average_color(
                game.canvas)[:3] != (0, 0, 0)
            check(painted, f"{played}: fisilti ekrana ciziliyor")
        finally:
            game.shutdown()


# --- 6. Bolum sonu -----------------------------------------------------------
def test_chapter_end() -> None:
    print("\n--- bolum sonu ---")
    game = Game()
    try:
        scene = start(game)
        check(scene.chapter_number == 8, "bolum numarasi 8")
        check([n for n, _ in ROOM_STARTS] == ["ates", "ogrenme", "gecit",
                                              "cikis"],
              "dort oda, dogru sirada")
        exit_at = LEVEL.first("exit")
        scene.player.body.x = float(exit_at.x + 4)
        scene._check_exit()
        check(scene.finished, "cikista bolum bitiyor")
        check(scene.save_data.chapter == 8, "kayda bolum 8 yaziliyor")
    finally:
        game.shutdown()


def main() -> int:
    print("=== BOLUM 8: ATES BASI ===")
    test_breather()
    test_teaching()
    test_sound_travels()
    test_latch_unreachable()
    test_cinematics()
    test_chapter_end()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("Ates Basi: dovussuz, ses yol aliyor, Yanki nihayet konusuyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
