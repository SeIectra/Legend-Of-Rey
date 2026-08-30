"""Bolum 12 "Mektup" - nefes bolumu ve Ardo'nun inis duzenegi.

`docs/yapi.md` B12: *"Ardo'nun gectigi yoldan gidiyorsun. (...)
Yoklugunda anlatilan yakinlik. **Tek bir dovus yok**, sadece iz
surme."*

Korunan kurallar:

  * **Dovus yok.** Haritada tek dusman isareti bulunursa bu test
    kirilsin - bir nefes bolumu zorluk egrisinin parcasi
    (`docs/ekonomi-uretim.md`), dolgu degil.
  * **Kafes gercekten iniyor** ve fren gercekten yavaslatiyor.
    Olculuyor: serbest inis suresi ile frenli inis suresi.
  * **Her iz okunabilir.** Fren basili tam bir inis alti izin
    ALTISINI da buluyor; frensiz inis hicbirini bulmuyor. Ikisi
    arasindaki fark mekanigin tamami.
  * **Iki duvar iki secim**: yanlis tarafta duran oyuncu izi
    okuyamiyor.
  * **Yukari cikilmiyor** - gecilen iz geri gelmiyor.
  * **Oyuncu kuyuya dusemiyor**; kafes onu tasiyor.
  * **Ayni bolum, iki zit mahremiyet**: her izin Rey ve Ardo icin
    AYRI repligi var, ve ikisi de **duz dize** (hesaplanan anahtari
    `test_lang.py` goremiyor - bu bolumde tam o hata yapildi).

Calistir:
    python tests/test_chapter12.py
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
    MARK_READ_SPEED, RIG_BRAKE_SPEED, RIG_FALL_SPEED, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.core.input import Action  # noqa: E402
from src.scenes.chapter12 import Chapter12Scene  # noqa: E402
from src.scenes.chapter12_cinematics import (  # noqa: E402
    CampCinematic, LetterCinematic,
)
from src.systems.save import SaveData, write_save  # noqa: E402
from src.world.rig import Mark, Rig  # noqa: E402
from src.world.rooms.chapter12 import (  # noqa: E402
    LEVEL, MARKS, MARKS_TOTAL, SHAFT_BOTTOM, SHAFT_TOP,
)

failures: list[str] = []

FIGHTERS = ("shambler", "climber", "bloated", "shieldbearer", "spearman",
            "archer", "commander", "silent", "echoing", "splitter",
            "shadow_shambler", "gaoler", "miniboss")


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def start(game, character: str = "rey") -> Chapter12Scene:
    write_save(SaveData(chapter=12, character=character,
                        abilities=["sword", "dodge", "echo_sight",
                                   "echo_ask"]))
    game.scenes.set_root(Chapter12Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter12Scene)
    return scene


def descend(scene, braking: bool, side: int = 0, limit: int = 4000) -> int:
    """Kafesi dibe kadar indirir. Kac kare surdugunu dondurur.

    `side` oyuncunun kafes uzerinde hangi tarafta durdugu (-1 sol,
    +1 sag, 0 orta). Gercek girdiyi taklit etmek yerine dogrudan
    `rig.update` cagriliyor - test frenin ETKISINI olcuyor, tus
    esleme tablosunu degil (o `test_settings.py`nin isi).
    """
    body = scene.player.body
    scene.riding = True
    scene.rig.start()
    frames = 0
    while not scene.rig.landed and frames < limit:
        scene.rig.update(braking)
        scene.rig.carry(body)
        if side:
            body.set_feet(scene.rig.center_x + side * TILE_SIZE * 1.5,
                          scene.rig.y)
        scene._update_marks()
        frames += 1
    return frames


# --- 1. Nefes bolumu: DOVUS YOK ----------------------------------------------
def test_no_combat() -> None:
    print("\n--- nefes bolumu ---")
    kinds = {p.kind for p in LEVEL.placements}
    fighters = kinds & set(FIGHTERS)
    check(not fighters,
          "haritada tek dusman yok - `docs/yapi.md`: *tek bir dovus yok*",
          str(fighters) or "temiz")

    game = Game()
    try:
        scene = start(game)
        for _ in range(120):
            scene.update()
        check(not scene.enemies, "sahne calisirken de dusman dogmuyor",
              str(len(scene.enemies)))
        check(scene.companion is None, "yoldas yok - B10'dan beri yalniz")
    finally:
        game.quit()


# --- 2. Kafes gercekten iniyor, fren gercekten yavaslatiyor ------------------
def test_rig_descends() -> None:
    print("\n--- kafes ---")
    check(RIG_BRAKE_SPEED < MARK_READ_SPEED < RIG_FALL_SPEED,
          "fren hizi okuma esiginin ALTINDA, serbest inis USTUNDE",
          f"{RIG_BRAKE_SPEED} < {MARK_READ_SPEED} < {RIG_FALL_SPEED}")

    game = Game()
    try:
        scene = start(game)
        top = scene.rig.y
        check(not scene.rig.running, "kafes binilmeden inmiyor")

        free = descend(scene, braking=False)
        check(scene.rig.landed, "kafes dibe iniyor")
        check(scene.rig.y > top, "gercekten asagi gitti",
              f"{top:.0f} -> {scene.rig.y:.0f}")

        scene2 = start(game)
        slow = descend(scene2, braking=True)
        check(slow > free * 2,
              "fren inisi belirgin yavaslatiyor",
              f"serbest {free} kare, frenli {slow} kare = {slow/free:.1f}x")
    finally:
        game.quit()


def test_no_going_back() -> None:
    """**Yukari cikilmiyor.** Gerilimin tamami bu kuraldan geliyor."""
    print("\n--- geri donus yok ---")
    rig = Rig(center_x=120.0, top_y=100.0, bottom_y=400.0)
    rig.start()
    heights = []
    # **Sabit kare sayisi degil, inise kadar**: ilk surumde 600 kare
    # yaziliydi ve fren hizinda dibe yetmiyordu - test kodun degil
    # kendi varsayiminin yanlisligini raporluyordu.
    frames = 0
    while rig.running and frames < 5000:
        rig.update(braking=True)
        heights.append(rig.y)
        frames += 1
    check(heights == sorted(heights), "kafes yalnizca ASAGI gidiyor")
    check(rig.y == 400.0 and not rig.running,
          "dipte duruyor, carpmiyor", f"{rig.y} ({frames} kare)")


# --- 3. Izler ★ ---------------------------------------------------------------
def test_marks_readable() -> None:
    """Bolumun tek olcusu: **frenlemek ne kadarini gosteriyor.**"""
    print("\n--- izler ---")
    check(MARKS_TOTAL == 6, "alti iz", str(MARKS_TOTAL))
    sides = {side for _y, side, _k, _a, _kind in MARKS}
    check(sides == {-1, 1}, "izler IKI duvara dagilmis - yurumek bir secim")

    game = Game()
    try:
        # Frensiz: hicbirini goremiyor.
        fast = start(game)
        descend(fast, braking=False)
        check(fast.marks_found == 0,
              "hizli inen HICBIR izi bulamiyor - ceza yok, kayip var",
              f"{fast.marks_found}/{MARKS_TOTAL}")

        # Frenli, sol duvar: yalnizca soldakiler.
        left = start(game)
        descend(left, braking=True, side=-1)
        left_total = sum(1 for _y, s, _k, _a, _kd in MARKS if s < 0)
        check(left.marks_found == left_total,
              "sol tarafta duran yalnizca SOL duvari okuyor",
              f"{left.marks_found}/{left_total}")

        # Frenli, iki tarafi da gezerek: hepsi.
        both = start(game)
        body = both.player.body
        both.riding = True
        both.rig.start()
        frames = 0
        while not both.rig.landed and frames < 4000:
            both.rig.update(True)
            both.rig.carry(body)
            # En yakin izin tarafina gec - "duvara bakmak" bu.
            nearest = min(both.marks, key=lambda m: abs(m.y - body.center_y))
            body.set_feet(both.rig.center_x + nearest.side * TILE_SIZE * 1.5,
                          both.rig.y)
            both._update_marks()
            frames += 1
        check(both.marks_found == MARKS_TOTAL,
              "yavaslayip iki duvara da bakan HEPSINI buluyor",
              f"{both.marks_found}/{MARKS_TOTAL}")
    finally:
        game.quit()


def test_mark_needs_correct_side() -> None:
    print("\n--- dogru taraf ---")
    rig = Rig(center_x=120.0, top_y=0.0, bottom_y=500.0)
    rig.start()
    rig.update(braking=True)
    mark = Mark(tile_y=2, side=+1, key="a", ardo_key="a_ardo")

    class _Body:
        center_x = 140.0        # sagda
        center_y = mark.y

    check(rig.reads(mark, _Body()), "dogru tarafta okunuyor")
    _Body.center_x = 100.0      # solda
    check(not rig.reads(mark, _Body()), "yanlis tarafta OKUNMUYOR")

    _Body.center_x = 140.0
    mark.found = True
    check(not rig.reads(mark, _Body()), "bir kez okunan tekrar okunmuyor")


# --- 4. Oyuncu kuyuya dusemiyor ----------------------------------------------
def test_player_cannot_fall() -> None:
    print("\n--- kuyuya dusme yok ---")
    game = Game()
    try:
        scene = start(game)
        body = scene.player.body
        scene.riding = True
        scene.rig.start()
        for step in range(400):
            scene.rig.update(False)
            # Her karede kenara dogru itmeyi dene.
            body.set_feet(body.center_x + (6 if step % 2 else -6), body.feet[1])
            scene.rig.carry(body)
            check_x = (scene.rig.left - 1 <= body.center_x
                       <= scene.rig.right + 1)
            if not check_x:
                break
        check(scene.rig.left - 1 <= body.center_x <= scene.rig.right + 1,
              "oyuncu kafesin disina cikamiyor",
              f"x={body.center_x:.0f} kafes[{scene.rig.left:.0f}"
              f"..{scene.rig.right:.0f}]")
        check(body.feet[1] == scene.rig.y,
              "ayaklar her karede kafese yaziliyor")
    finally:
        game.quit()


# --- 5. Iki zit mahremiyet ---------------------------------------------------
def test_two_intimacies() -> None:
    """Rey **birakilanlari** goruyor, Ardo **birakilan izleri**."""
    print("\n--- iki mahremiyet ---")
    for _y, _s, key, ardo_key, _k in MARKS:
        check(key != ardo_key, f"{key}: iki karakter icin AYRI replik")
        check(key.startswith("line.") and ardo_key.startswith("line."),
              f"{key}: ikisi de duz dize anahtar")

    game = Game()
    try:
        for character, speaker in (("rey", "rey"), ("ardo", "ardo")):
            scene = start(game, character=character)
            line = scene._voice(MARKS[0][2], MARKS[0][3])
            check(line.speaker == speaker,
                  f"{character}: konusan dogru", line.speaker)
            check(line.key == (MARKS[0][3] if character == "ardo"
                               else MARKS[0][2]),
                  f"{character}: dogru anahtar secildi", line.key)
    finally:
        game.quit()


# --- 6. Bolum akisi ve ara sahneler ------------------------------------------
def test_chapter_flow() -> None:
    print("\n--- akis ---")
    game = Game()
    try:
        scene = start(game)
        check(LEVEL.first("candle_keeper") is not None,
              "Mum Bekcisi ucuncu kez burada (`docs/bolum-03.md` 122)")
        check(len(LEVEL.of("trigger")) == 2, "iki ara sahne tetikleyicisi",
              str(len(LEVEL.of("trigger"))))

        check(not scene.landed, "basta inilmemis")
        descend(scene, braking=True)
        scene._land()
        check(scene.landed and not scene.riding, "dipte kafesten inildi")
        check(scene.player.body.gravity_scale == 1.0,
              "yercekimi geri geldi")
    finally:
        game.quit()


def test_cinematics() -> None:
    print("\n--- ara sahneler ---")
    game = Game()
    try:
        surface = pygame.Surface((480, 270))
        for character in ("rey", "ardo"):
            game.scenes.set_root(CampCinematic, transition=False,
                                 character=character)
            game.scenes._flush()
            for _ in range(90):
                game.scenes.current.update()
                game.scenes.current.draw(surface)
            check(True, f"kamp ({character}) 90 kare cokmeden oynuyor")

            # Uc varyantin ucu de oynamali - `few` varyanti SUCLAMIYOR.
            for found in (0, 3, 6):
                game.scenes.set_root(LetterCinematic, transition=False,
                                     character=character, found=found,
                                     total=MARKS_TOTAL)
                game.scenes._flush()
                for _ in range(90):
                    game.scenes.current.update()
                    game.scenes.current.draw(surface)
                check(True, f"mektup ({character}, {found}/6) oynuyor")
    finally:
        game.quit()


def main() -> int:
    test_no_combat()
    test_rig_descends()
    test_no_going_back()
    test_marks_readable()
    test_mark_needs_correct_side()
    test_player_cannot_fall()
    test_two_intimacies()
    test_chapter_flow()
    test_cinematics()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("Bolum 12 tutarli - dovus yok, kafes iniyor, izler okunuyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
