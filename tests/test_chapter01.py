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


def fresh(game: Game, character: str = "rey") -> Chapter01Scene:
    """Sahneyi bastan kurar - Game'i YENIDEN YARATMADAN.

    `Game.shutdown()` `pygame.quit()` cagiriyor ve bu makinede bir
    sonraki `pygame.init()` 40 saniye suruyor (olculdu 23.08.2026; kodla
    ilgisi yok, SDL yeniden baslatma maliyeti). Yedi ayri Game yaratmak
    testi 284 saniyeye cikariyordu. Sahne durumu zaten `set_root` ile
    sifirlaniyor - Game'i tazelemeye gerek yok.
    """
    game.scenes.set_root(Chapter01Scene, transition=False, character=character)
    game.scenes._flush()
    return game.scenes.current


def make_scene(game: Game, character: str) -> Chapter01Scene:
    game.scenes.set_root(Chapter01Scene, transition=False, character=character)
    game.scenes._flush()
    scene = game.scenes.current
    scene.beat_index = len(PROLOGUE)          # prologu atla, dogrudan oyna
    return scene


def confirm(game: Game, step: int, scene) -> None:
    """Okuyan bir oyuncuyu taklit eder - yazi bitince onaylar.

    31.08.2026'dan beri prolog replikleri oyuncuyu **bekliyor**
    (Arda: *"kullanici basana kadar yazilar gecmesin"*). Yani prologun
    icini test eden her dongu artik onaylamak zorunda; pasif bir
    dongu ilk replikte duruyor.

    KEYDOWN **ve** KEYUP birlikte gonderiliyor: `_activate` tus zaten
    basiliysa yeni bir "press" saymiyor (dogru davranis - klavye
    tekrari combo'yu bozardi), yani birakmadan ikinci kez basilamiyor.
    """
    if not (scene.dialogue.active and scene.dialogue.complete):
        return
    if step % 24:
        return
    game.input.handle_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    game.input.handle_event(
        pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN))


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

    # --- Rey: ayni ogreti hala calismali (fix asiri kisitlamiyor) -----------
    print("\n--- Rey: Yanki Gorusu ogretisi hala calisiyor ---")
    rey = make_scene(game, "rey")
    check(rey.echo is not None, "Rey'in Yankisi var")
    rey.player.body.set_feet(ECHO_TUTORIAL_TILE.x, ECHO_TUTORIAL_TILE.feet_y)
    rey.player.body.vx = rey.player.body.vy = 0.0
    idle(game, rey, 5)
    check(rey.player.has(abilities.ECHO_SIGHT),
          "Rey ogretiyle Yanki Gorusu'nu kazaniyor")

    # --- Ardo zaten kilicla basliyor - yerde ikinci bir kilic gormemeli -----
    # Arda'nin bildirdigi celiski: "karakter kilici almadan once de kilici
    # oluyor" - Ardo zaten silahli baslarken sahne yine de bir "al beni"
    # kilic prop'u gosteriyordu.
    print("\n--- Ardo zaten silahli - yerde ikinci kilic YOK ---")
    ardo2 = make_scene(game, "ardo")
    check(ardo2.player.has(abilities.SWORD),
          "Ardo basta zaten kilica sahip")
    check(ardo2.sword_pos is None,
          "Ardo icin yerde kilic prop'u YOK (celiskili gorunmesin)")

    print("\n--- Rey icin yerde kilic prop'u hala var ---")
    rey2 = make_scene(game, "rey")
    check(not rey2.player.has(abilities.SWORD),
          "Rey basta kilica sahip degil")
    check(rey2.sword_pos is not None,
          "Rey icin yerde kilic prop'u duruyor (bulunacak)")

    # --- Prolog: replikler OYUNCUYU BEKLIYOR --------------------------------
    # Arda, canli oynanis (31.08.2026): *"ilk sahnede koyde Rey ile Cemo
    # konusurken cok hizli geciyor, kullanici basana kadar yazilar
    # gecmesin."*
    #
    # Bu bolumun garantisi 31.08.2026'da **degisti**. Eskiden replikler
    # `auto_advance=True` ile aciliyordu ve test "pasif oyuncu hicbir
    # repligi kaybetmesin" diye yaziliydi. Artik beat zamanlayicisi
    # replige tabi: pasif oyuncu **ilerlemiyor**, ve bu bir hata degil
    # istenen davranis.
    #
    # Iki sey birden korunmali:
    #   1. Onaylamayan oyuncu ilk repligin uzerinde DURUYOR.
    #   2. Onaylayan oyuncu bes repligin hepsini SIRAYLA goruyor -
    #      hicbiri bir sonraki beat tarafindan sessizce ezilmiyor
    #      (Arda'nin "bunlar cok anlamsiz cumleler" hatasi buydu).
    print("\n--- prolog: replikler oyuncuyu bekliyor ---")
    game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game.scenes._flush()
    idle_scene = game.scenes.current
    for _ in range(sum(frames for frames, _ in PROLOGUE) + 300):
        game.input.begin_frame()
        game.input.end_frame()
        idle_scene.update()
    current = idle_scene.dialogue.current
    check(current is not None and current.key == "line.ch01_echo_first",
          "onaylamayan oyuncu ILK replikte duruyor",
          current.key if current else "replik yok")
    check(idle_scene.beat_index <= 1,
          "prolog ilerlemedi - beat zamanlayicisi replige tabi",
          f"beat {idle_scene.beat_index}")

    print("\n--- prolog: onaylayan oyuncu hepsini goruyor ---")
    game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game.scenes._flush()
    prolog_scene = game.scenes.current
    seen_keys: list[str] = []
    last_key = None
    for step in range(sum(frames for frames, _ in PROLOGUE) + 900):
        game.input.begin_frame()
        confirm(game, step, prolog_scene)
        game.input.end_frame()
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
              f"onaylayan oyuncu '{expected_key}' repligini goruyor",
              ", ".join(seen_keys))

    # --- Kolye gercekten EL DEGISTIRIYOR ------------------------------------
    # Eskiden `necklace` "alone" adiminda sessizce True oluyordu: oyunun
    # butun hikayesi o kolyeye asili ama oyuncu onun kendisine gectigi ani
    # hic gormuyordu. Artik Cemo'dan firlayip bir yay cizerek geliyor ve
    # VARDIGI karede aliniyor.
    # `make_scene()` prologu ATLIYOR (beat_index = len(PROLOGUE)) - hediye
    # prologun icinde oldugu icin onunla test edilemez. Pasif oyuncu
    # testindeki gibi sahneyi dogrudan kuruyoruz.
    print("\n--- kolye ucusu: Cemo'dan oyuncuya ---")
    game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game.scenes._flush()
    gift = game.scenes.current
    check(not gift.necklace, "baslangicta kolye YOK")
    check(gift.gift_frames < 0, "baslangicta kolye havada degil")

    saw_flight = False
    flight_positions: list[tuple[float, float]] = []
    got_at = None
    for frame in range(sum(f for f, _ in PROLOGUE) + 900):
        game.input.begin_frame()
        confirm(game, frame, gift)
        game.input.end_frame()
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

    # --- Koyluler: gezinir, yarik acilinca evlerine kacar -------------------
    # Arda'nin istegi: "ilk basta etrafta koyluler dolasabilir. Olaylar
    # patlak verdiginde koyluler evlerine kacsin." Prologun anlatimi
    # "sakin koy -> yarik -> kayip" uzerine kurulu; koy yasamiyorsa
    # kaybedilen sey de soyut kaliyor.
    print("\n--- koyluler: gezinme ve kacis ---")
    game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game.scenes._flush()
    village = game.scenes.current

    check(len(village.villagers) >= 3, "koyde birden fazla koylu var",
          str(len(village.villagers)))
    start_positions = [v.x for v in village.villagers]

    # Yarik acilmadan once: gezinirler, hicbiri kacmaz.
    for _ in range(120):
        game.input.begin_frame(); game.input.end_frame()
        village.update()
    check(not village.villagers_fled, "yarik acilmadan kimse kacmiyor")
    moved = sum(1 for v, x0 in zip(village.villagers, start_positions)
                if abs(v.x - x0) > 1.0)
    check(moved > 0, "koyluler gercekten geziniyor (yerlerinde durmuyorlar)",
          str(moved) + " koylu hareket etti")
    check(all(v.state == "wander" for v in village.villagers),
          "hepsi hala gezinme durumunda")

    # Prologun geri kalanini oynat: yarik acilir, koyluler kacar.
    for frame in range(sum(f for f, _ in PROLOGUE) + 900):
        game.input.begin_frame()
        confirm(game, frame, village)
        game.input.end_frame()
        village.update()
    check(village.villagers_fled, "yarik acilinca kacis tetiklendi")
    check(not village.villagers,
          "butun koyluler evlerine girdi (listeden dustuler)",
          str(len(village.villagers)) + " kaldi")

    # --- Yanki Rey'in laneti: Ardo onu DUYMAZ ------------------------------
    # Olculdu (24.08.2026): prolog replikleri karakterden bagimsiz
    # oynuyordu. Ardo da mor sesi duyuyordu - ona yol gostermeyi teklif
    # eden bir ses duyup sonra o yetenegi hic almiyordu. Ayrica tesekkur
    # repligi sabit "rey" konusmaciyla yaziliydi: Ardo oynarken ekranda
    # "REY" etiketi cikiyordu.
    print("\n--- Yanki Rey'e ozel, replikler oynanan karaktere ait ---")

    def prologue_lines(character: str):
        game.scenes.set_root(Chapter01Scene, transition=False,
                             character=character)
        game.scenes._flush()
        scene = game.scenes.current
        seen, last = [], None
        for frame in range(sum(f for f, _ in PROLOGUE) + 900):
            game.input.begin_frame()
            confirm(game, frame, scene)
            game.input.end_frame()
            scene.update()
            cur = scene.dialogue.current
            key = (cur.speaker, cur.key) if cur else None
            if key is not None and key != last:
                seen.append(key)
            last = key
        return seen

    rey_lines = prologue_lines("rey")
    ardo_lines = prologue_lines("ardo")

    check(any(sp == "echo" for sp, _ in rey_lines),
          "Rey Yanki'yi duyuyor",
          str(sum(1 for sp, _ in rey_lines if sp == "echo")) + " replik")
    check(not any(sp == "echo" for sp, _ in ardo_lines),
          "Ardo Yanki'yi DUYMUYOR (Yanki Rey'in laneti)",
          ", ".join(sp for sp, _ in ardo_lines))
    check(not any(sp == "rey" for sp, _ in ardo_lines),
          "Ardo oynarken hicbir replik REY etiketiyle cikmiyor",
          ", ".join(sp for sp, _ in ardo_lines))
    check(any(sp == "ardo" for sp, _ in ardo_lines),
          "Ardo kendi sesiyle konusuyor (motivasyonu yaziliyor)",
          str(sum(1 for sp, _ in ardo_lines if sp == "ardo")) + " replik")

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Bolum 1 karakter-ozel ogreti kurallarina uyuyor.")
    return 0


raise SystemExit(main())
