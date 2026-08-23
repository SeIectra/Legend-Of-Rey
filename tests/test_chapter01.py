"""Bolum 1 dogrulamasi - Ardo'nun Rey'e ozel ogretileri almadigi.

`docs/gdd.md`: Ardo egitimli bir yabanci, Rey'in ogrenme yayini tekrar
oynamiyor. Ama Bolum 1'in Yanki Gorusu ogretisi (`on_echo_tutorial`)
karakter kontrolu olmadan yazilmisti: Ardo da (Yanki'si olmadigi halde)
"Yanki Gorusu kazandin" bildirimini goruyordu - hicbir mekanik karsiligi
olmayan bir gucu acmasi isteniyordu (Arda'nin bildirdigi hata).

Calistir:
    python tests/test_chapter01.py
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

from src.core.game import Game  # noqa: E402
from src.scenes.chapter01 import Chapter01Scene  # noqa: E402
from src.systems import abilities  # noqa: E402
from src.world.rooms.chapter01 import ECHO_TUTORIAL_TILE, PROLOGUE  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def make_scene(game: Game, character: str) -> Chapter01Scene:
    game.scenes.set_root(Chapter01Scene, transition=False, character=character)
    game.scenes._flush()
    scene = game.scenes.current
    scene.beat_index = len(PROLOGUE)          # prologu atla, dogrudan oyna
    return scene


def idle(game: Game, scene, frames: int) -> None:
    for _ in range(frames):
        game.input.begin_frame()
        game.input.end_frame()
        scene.update()


def main() -> int:
    game = Game()

    # --- Ardo: Yanki yok, ogreti tetiklenmemeli ------------------------------
    print("--- Ardo: Yanki Gorusu ogretisi ---")
    ardo = make_scene(game, "ardo")
    check(ardo.echo is None, "Ardo'nun Yanki'si yok")
    check(not ardo.player.has(abilities.ECHO_SIGHT),
          "Ardo basta Yanki Gorusu'ne sahip degil (zaten olmamali)")

    ardo.player.body.set_feet(ECHO_TUTORIAL_TILE.x, ECHO_TUTORIAL_TILE.feet_y)
    ardo.player.body.vx = ardo.player.body.vy = 0.0
    idle(game, ardo, 5)
    check(not ardo.player.has(abilities.ECHO_SIGHT),
          "ogreti tetiklenince de Ardo Yanki Gorusu KAZANMIYOR")
    check(ardo.toast == "", "hicbir bildirim gosterilmedi", repr(ardo.toast))
    check(ardo.echo_taught,
          "tetikleyici yine de 'ogretildi' isaretleniyor - tekrar denenmiyor")
    game.shutdown()

    # --- Rey: ayni ogreti hala calismali (fix asiri kisitlamiyor) -----------
    print("\n--- Rey: Yanki Gorusu ogretisi hala calisiyor ---")
    game2 = Game()
    rey = make_scene(game2, "rey")
    check(rey.echo is not None, "Rey'in Yankisi var")
    rey.player.body.set_feet(ECHO_TUTORIAL_TILE.x, ECHO_TUTORIAL_TILE.feet_y)
    rey.player.body.vx = rey.player.body.vy = 0.0
    idle(game2, rey, 5)
    check(rey.player.has(abilities.ECHO_SIGHT),
          "Rey ogretiyle Yanki Gorusu'nu kazaniyor")
    game2.shutdown()

    # --- Ardo zaten kilicla basliyor - yerde ikinci bir kilic gormemeli -----
    # Arda'nin bildirdigi celiski: "karakter kilici almadan once de kilici
    # oluyor" - Ardo zaten silahli baslarken sahne yine de bir "al beni"
    # kilic prop'u gosteriyordu.
    print("\n--- Ardo zaten silahli - yerde ikinci kilic YOK ---")
    game3 = Game()
    ardo2 = make_scene(game3, "ardo")
    check(ardo2.player.has(abilities.SWORD),
          "Ardo basta zaten kilica sahip")
    check(ardo2.sword_pos is None,
          "Ardo icin yerde kilic prop'u YOK (celiskili gorunmesin)")
    game3.shutdown()

    print("\n--- Rey icin yerde kilic prop'u hala var ---")
    game4 = Game()
    rey2 = make_scene(game4, "rey")
    check(not rey2.player.has(abilities.SWORD),
          "Rey basta kilica sahip degil")
    check(rey2.sword_pos is not None,
          "Rey icin yerde kilic prop'u duruyor (bulunacak)")
    game4.shutdown()

    # --- Prolog: pasif oyuncu (hic onaylamiyor) hicbir repligi kaybetmez ----
    # Arda'nin bildirdigi "bunlar cok anlamsiz cumleler" hatasi: cok-replikli
    # bir beat'te ("gift": Cemo + Rey) ikinci satir onayla gecilmedigi surece
    # bir sonraki beat baslayinca `self.say(...)` kuyrugu **sessizce**
    # degistiriyordu - ilk oturumdaki bir oyuncunun "onayla" tusunu bilmesi
    # beklenemez, o yuzden Rey'in tesekkuru hicbir zaman ekrana gelmiyordu.
    # Bu test hic girdi vermeden butun prologu oynatir ve 5 repligin de
    # (atlanmadan) en az bir kere gorundugunu dogrular.
    print("\n--- prolog: pasif oyuncu replik kaybetmiyor ---")
    game5 = Game()
    game5.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game5.scenes._flush()
    prolog_scene = game5.scenes.current
    seen_keys: list[str] = []
    last_key = None
    for _ in range(sum(frames for frames, _ in PROLOGUE) + 60):
        game5.input.begin_frame()
        game5.input.end_frame()
        prolog_scene.update()
        cur = prolog_scene.dialogue.current
        key = cur.key if cur else None
        if key is not None and key != last_key:
            seen_keys.append(key)
        last_key = key
    for expected_key in ("line.ch01_echo_first", "line.ch01_cemo_gift",
                         "line.ch01_rey_thanks", "line.ch01_echo_rift",
                         "line.ch01_echo_alone"):
        check(expected_key in seen_keys,
              f"pasif oyuncu da '{expected_key}' repligini goruyor",
              ", ".join(seen_keys))
    game5.shutdown()

    # --- Kolye gercekten EL DEGISTIRIYOR ------------------------------------
    # Eskiden `necklace` "alone" adiminda sessizce True oluyordu: oyunun
    # butun hikayesi o kolyeye asili ama oyuncu onun kendisine gectigi ani
    # hic gormuyordu. Artik Cemo'dan firlayip bir yay cizerek geliyor ve
    # VARDIGI karede aliniyor.
    # `make_scene()` prologu ATLIYOR (beat_index = len(PROLOGUE)) - hediye
    # prologun icinde oldugu icin onunla test edilemez. Pasif oyuncu
    # testindeki gibi sahneyi dogrudan kuruyoruz.
    print("\n--- kolye ucusu: Cemo'dan oyuncuya ---")
    game6 = Game()
    game6.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game6.scenes._flush()
    gift = game6.scenes.current
    check(not gift.necklace, "baslangicta kolye YOK")
    check(gift.gift_frames < 0, "baslangicta kolye havada degil")

    saw_flight = False
    flight_positions: list[tuple[float, float]] = []
    got_at = None
    for frame in range(sum(f for f, _ in PROLOGUE) + 60):
        game6.input.begin_frame()
        game6.input.end_frame()
        gift.update()
        if gift.gift_flying:
            saw_flight = True
            flight_positions.append(gift.gift_position())
        if gift.necklace and got_at is None:
            got_at = frame

    check(saw_flight, "kolye havada bir sure gorunuyor (ucus var)")
    check(got_at is not None, "kolye sonunda oyuncuya geciyor", str(got_at))
    check(len(flight_positions) > 1, "ucus birden fazla kare suruyor",
          f"{len(flight_positions)} kare")
    if len(flight_positions) > 2:
        # Yay: orta noktanin yuksekligi iki ucun ortalamasindan YUKARIDA
        # olmali (ekran koordinatinda kucuk y = yukari). Duz gitseydi
        # "isinlandi" gibi okunurdu.
        first_y = flight_positions[0][1]
        last_y = flight_positions[-1][1]
        mid_y = flight_positions[len(flight_positions) // 2][1]
        check(mid_y < (first_y + last_y) * 0.5,
              "ucus DUZ degil, yay ciziyor (firlatilmis nesne gibi)",
              f"orta {mid_y:.1f} < ortalama {(first_y + last_y) * 0.5:.1f}")
    game6.shutdown()

    # --- Koyluler: gezinir, yarik acilinca evlerine kacar -------------------
    # Arda'nin istegi: "ilk basta etrafta koyluler dolasabilir. Olaylar
    # patlak verdiginde koyluler evlerine kacsin." Prologun anlatimi
    # "sakin koy -> yarik -> kayip" uzerine kurulu; koy yasamiyorsa
    # kaybedilen sey de soyut kaliyor.
    print("\n--- koyluler: gezinme ve kacis ---")
    game7 = Game()
    game7.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game7.scenes._flush()
    village = game7.scenes.current

    check(len(village.villagers) >= 3, "koyde birden fazla koylu var",
          str(len(village.villagers)))
    start_positions = [v.x for v in village.villagers]

    # Yarik acilmadan once: gezinirler, hicbiri kacmaz.
    for _ in range(120):
        game7.input.begin_frame(); game7.input.end_frame()
        village.update()
    check(not village.villagers_fled, "yarik acilmadan kimse kacmiyor")
    moved = sum(1 for v, x0 in zip(village.villagers, start_positions)
                if abs(v.x - x0) > 1.0)
    check(moved > 0, "koyluler gercekten geziniyor (yerlerinde durmuyorlar)",
          str(moved) + " koylu hareket etti")
    check(all(v.state == "wander" for v in village.villagers),
          "hepsi hala gezinme durumunda")

    # Prologun geri kalanini oynat: yarik acilir, koyluler kacar.
    for _ in range(sum(f for f, _ in PROLOGUE) + 240):
        game7.input.begin_frame(); game7.input.end_frame()
        village.update()
    check(village.villagers_fled, "yarik acilinca kacis tetiklendi")
    check(not village.villagers,
          "butun koyluler evlerine girdi (listeden dustuler)",
          str(len(village.villagers)) + " kaldi")
    game7.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Bolum 1 karakter-ozel ogreti kurallarina uyuyor.")
    return 0


raise SystemExit(main())
