"""Bolum 16 "Sirt Sirta" - kaldirma, asist kombo, jest secimi.

`docs/yapi.md` B16: *"Ardo geri doner, havali giris. Ama bu sefer **Rey
de onu kurtarir.** Karsilikli. Mekanik: En uzun team-up. Asist
kombolar zirvede. Bolum sonu: kalp balonu."*

Korunan kurallar:

  * **Bolum yoldassiz da gecilebiliyor.** Yoldas bu bolumde kendi
    kendine kalkmiyor; hicbir gecis ona bagli OLMAMALI, yoksa oyuncu
    onu kaldirmayi anlamadiginda bolum kilitlenirdi. Iddia
    OLCULUYOR - harita bastan sona taraniyor.
  * **Kendi kalkmama YALNIZCA burada.** B6-B15'te yoldas kendi
    kalkiyor; sinif duzeyinde degistirilseydi bes bitmis bolumun
    agirlik plakasi bulmacasi cozulemez olurdu.
  * **Kaldirmanin bedeli var**: uzaklasinca, vurulunca ve tus
    birakilinca ilerleme sifirlaniyor. Bedelsiz olsaydi "once
    ortaligi temizle" karari anlamsizlasirdi.
  * **Kaldirmak kendi kalkmasindan iyi** - yoksa bedeli olur da
    karsiligi olmazdi.
  * **Asist yalnizca bitiricide.** Her vurusta tetiklenseydi yoldas
    oyunu oyuncunun yerine oynardi.
  * **Asist Bolum 16'ya ait** - oteki bolumlerin dovus hissi sessizce
    degismedi.
  * **Jest seciminin yanlis cevabi yok** ve kalp UCUNDE de cikiyor
    (`docs/yapi.md` "bolum sonu: kalp balonu" baglayici).
  * **Ara sahneler iki karakterde de cizim dahil calisiyor** - projede
    iki kez cizim cagirmayan testler yuzunden cokme yasandi.

Calistir:
    python tests/test_chapter16.py
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
    COMPANION_ASSIST_DAMAGE, COMPANION_DAMAGE, COMPANION_HEALTH,
    PLAYER_RUN_SPEED, RESCUE_HEALTH, RESCUE_HOLD_FRAMES, RESCUE_RANGE,
    TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.core.input import Action  # noqa: E402
from src.entities.companion import Companion  # noqa: E402
from src.scenes.chapter16 import Chapter16Scene  # noqa: E402
from src.scenes.chapter16_cinematics import (  # noqa: E402
    HeartCinematic, LiftCinematic, ReturnCinematic,
)
from src.systems.save import SaveData, write_save  # noqa: E402
from src.ui import gesture  # noqa: E402
from src.ui.chapter_end import ChapterEndScene, ChapterResult  # noqa: E402
from src.world.rooms.chapter16 import (  # noqa: E402
    LEVEL, LIFT_BONUS, ROOM_STARTS,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def start(game, character: str = "rey") -> Chapter16Scene:
    write_save(SaveData(
        chapter=16, character=character,
        abilities=["sword", "dodge", "echo_sight", "echo_ask", "boost"],
        flags={"sense_betrayed": True, "resonance": True}))
    game.scenes.set_root(Chapter16Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter16Scene)
    return scene


def with_companion(scene) -> Companion:
    """Yoldasi sahaya alir - normalde "Donus" ara sahnesi yapiyor."""
    companion = scene.summon_companion()
    scene.rescue.unlocked = True
    return companion


# Dusmansiz bir nokta - son odanin ortasi. Kaldirma testleri dovusu
# degil kaldirmayi olcuyor; yaninda bir Okcu varken olcum gurultulu
# olurdu.
QUIET_TILE = 140


def put_down(scene, companion) -> None:
    """Yoldasi sessiz bir yere goturur, diz coktrur, fizigi oturtur.

    `RescueState.reach` ikisinin de **yerde** olmasini ariyor ve
    `body.grounded` ancak bir kare fizik kostuktan sonra dogru oluyor.
    Ilk surum `set_feet`ten hemen sonra soruyordu ve testler "diz
    cokunce teklif ediliyor" satirinda kaliyordu - kod degil olcum
    hataliydi.
    """
    x = QUIET_TILE * TILE_SIZE
    feet_y = companion.body.feet[1]
    companion.body.set_feet(x, feet_y)
    scene.player.body.set_feet(x + 8, feet_y)
    # Sahnenin kendi dongusu - `Body`nin ayri bir `update`i yok ve
    # elle fizik cagirmak sahnenin yaptigindan sapardi. Burada
    # dusman yok (yalnizca ilk oda kurulu) ve en yakin tetikleyici
    # on tile otede, yani tarama gurultusuz.
    for _ in range(6):
        scene.update()
    companion.die()
    for _ in range(2):
        scene.update()


# --- 1. Bolum yoldassiz da gecilebiliyor mu ★ ---------------------------------
def test_passable_without_companion() -> None:
    """En kritik kontrol: **yoldas olmasa da gecilebiliyor.**

    Yoldas bu bolumde kendi kendine kalkmiyor. Bir gecis ona bagli
    olsaydi, mekanigi anlamayan oyuncu bolumu kilitlerdi - ve
    `docs/ekonomi-uretim.md` zorlugu 6 veriyor, duvar degil.
    """
    print("\n--- yoldassiz gecilebiliyor ---")
    game = Game()
    try:
        scene = start(game)
        for name, _ in ROOM_STARTS:
            scene._enter_room(name)
        body = scene.player.body
        width = scene.tilemap.width * TILE_SIZE
        body.set_feet(TILE_SIZE * 3, body.feet[1])
        steps = 0
        while body.center_x < width - TILE_SIZE * 3 and steps < 6000:
            body.vx = PLAYER_RUN_SPEED
            body.set_feet(body.center_x + PLAYER_RUN_SPEED, body.feet[1])
            scene.update()
            steps += 1
            if game.scenes.current is not scene:
                game.scenes.pop()
                game.scenes._flush()
        check(body.center_x >= width - TILE_SIZE * 3,
              "harita bastan sona gecilebiliyor",
              f"{steps} kare, x={body.center_x:.0f}/{width}")
        check(scene.lifts == 0,
              "ve bu tarama hic KALDIRMADAN yapildi - kilit yok")
    finally:
        game.quit()


def test_all_triggers_fire() -> None:
    """Uc ara sahne de tetikleniyor - ozellikle OGRETEN olan."""
    print("\n--- uc ara sahne de tetikleniyor ---")
    game = Game()
    try:
        scene = start(game)
        for name, _ in ROOM_STARTS:
            scene._enter_room(name)
        body = scene.player.body
        width = scene.tilemap.width * TILE_SIZE
        body.set_feet(TILE_SIZE * 3, body.feet[1])
        steps = 0
        while body.center_x < width - TILE_SIZE * 3 and steps < 6000:
            body.vx = PLAYER_RUN_SPEED
            body.set_feet(body.center_x + PLAYER_RUN_SPEED, body.feet[1])
            scene.update()
            steps += 1
            if game.scenes.current is not scene:
                game.scenes.pop()
                game.scenes._flush()
        check(len(scene.fired_triggers) == 3,
              "uc tetikleyici de calisti", str(sorted(scene.fired_triggers)))
        check(scene.companion is not None,
              "yoldas sahaya girdi - 'Donus' tetiklendi")
        check(scene.rescue.unlocked,
              "kaldirma acildi - 'Kaldir' ogretici sahnesi tetiklendi")
    finally:
        game.quit()


# --- 2. Kendi kalkmama - bolumun tezi -----------------------------------------
def test_no_self_recovery_here_only() -> None:
    """Yoldas burada kendi kalkmiyor - ama **yalnizca** burada."""
    print("\n--- kendi kalkmama yalnizca bu bolumde ---")
    check(Companion.self_recovers,
          "SINIF duzeyinde kendi kalkma hala acik - B6-B15 bozulmadi")
    game = Game()
    try:
        scene = start(game)
        companion = with_companion(scene)
        check(not companion.self_recovers,
              "bu bolumun ornegi kendi kalkmiyor")
        put_down(scene, companion)
        for _ in range(600):        # kendi kalkmasindan cok daha uzun
            companion.update()
        check(companion.downed,
              "600 kare sonra HALA yerde - kendi kalkmiyor")
    finally:
        game.quit()


# --- 3. Kaldirma ★ ------------------------------------------------------------
def test_lift_needs_a_held_key() -> None:
    """Basili tut, kalksin. Ve **gercek tusla** - kablo test ediliyor."""
    print("\n--- kaldirma (gercek tus) ---")
    game = Game()
    try:
        scene = start(game)
        companion = with_companion(scene)
        put_down(scene, companion)

        # Gercek KEYDOWN: `_held` KEYUP'a kadar duruyor, yani tus
        # gercekten **basili tutuluyor**. Sahnenin INTERACT'i
        # kaldirmaya baglayip baglamadigi da boylece olculuyor.
        game.input.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        check(game.input.held(Action.INTERACT), "tus basili")

        for _ in range(RESCUE_HOLD_FRAMES + 4):
            if not companion.downed:
                break
            scene._update_rescue()
        check(not companion.downed, "yoldas KALKTI")
        check(scene.lifts == 1, "kaldirma sayildi", str(scene.lifts))
        check(companion.health == RESCUE_HEALTH,
              "kaldirilinca donen can", str(companion.health))
        check(RESCUE_HEALTH > COMPANION_HEALTH // 2,
              "kaldirmak kendi kalkmasindan IYI - bedelin karsiligi",
              f"{RESCUE_HEALTH} vs {COMPANION_HEALTH // 2}")
    finally:
        game.quit()


def test_lift_progress_resets() -> None:
    """Bedel gercek: uzaklasinca, vurulunca, birakinca sifirlaniyor."""
    print("\n--- kaldirmanin bedeli ---")
    game = Game()
    try:
        scene = start(game)
        companion = with_companion(scene)
        put_down(scene, companion)

        for _ in range(RESCUE_HOLD_FRAMES // 2):
            scene.rescue.update(scene.player, companion, True)
        half = scene.rescue.hold
        check(half > 0, "ilerleme birikiyor", str(half))

        scene.rescue.update(scene.player, companion, False)
        check(scene.rescue.hold == 0, "tusu birakinca SIFIR")

        for _ in range(RESCUE_HOLD_FRAMES // 2):
            scene.rescue.update(scene.player, companion, True)
        scene.player.body.set_feet(
            companion.body.center_x + RESCUE_RANGE * 3,
            companion.body.feet[1])
        scene.rescue.update(scene.player, companion, True)
        check(scene.rescue.hold == 0, "uzaklasinca SIFIR")

        scene.player.body.set_feet(companion.body.center_x + 8,
                                   companion.body.feet[1])
        for _ in range(RESCUE_HOLD_FRAMES // 2):
            scene.rescue.update(scene.player, companion, True)
        before = scene.rescue.hold
        scene.on_player_hurt(scene.player, None)
        check(before > 0 and scene.rescue.hold == 0,
              "vurulunca SIFIR - risk gercek", f"{before} -> 0")

        check(companion.downed, "butun bunlar boyunca yoldas hala yerde")
    finally:
        game.quit()


def test_lift_needs_a_downed_companion() -> None:
    """Ayaktakini kaldirmak anlamsiz - ve bir hata olurdu."""
    print("\n--- ayaktakini kaldiramazsin ---")
    game = Game()
    try:
        scene = start(game)
        companion = with_companion(scene)
        scene.player.body.set_feet(companion.body.center_x + 8,
                                   companion.body.feet[1])
        check(not scene.rescue.reach(scene.player, companion),
              "ayakta olana kaldirma teklif edilmiyor")
        put_down(scene, companion)
        check(scene.rescue.reach(scene.player, companion),
              "diz cokunce teklif ediliyor")
    finally:
        game.quit()


def test_rescue_is_locked_before_the_lesson() -> None:
    """Ogretilmeden once tus hicbir sey yapmiyor."""
    print("\n--- ders oncesi kilitli ---")
    game = Game()
    try:
        scene = start(game)
        check(not scene.rescue.unlocked, "bolum basinda kaldirma KAPALI")
        companion = scene.summon_companion()
        put_down(scene, companion)
        for _ in range(RESCUE_HOLD_FRAMES * 2):
            scene.rescue.update(scene.player, companion, True)
        check(companion.downed,
              "kilitliyken tutmak ise yaramiyor - ogretici atlanamaz")
    finally:
        game.quit()


# --- 4. Asist kombo -----------------------------------------------------------
def test_assist_only_on_finisher() -> None:
    """*"Asist kombolar zirvede."* Ama her vurusta DEGIL."""
    print("\n--- asist yalnizca bitiricide ---")
    check(COMPANION_ASSIST_DAMAGE > COMPANION_DAMAGE,
          "asist hasari normalden yuksek",
          f"{COMPANION_ASSIST_DAMAGE} vs {COMPANION_DAMAGE}")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("yalniz")
        companion = with_companion(scene)
        enemy = next(e for e in scene.enemies if not e.dead)
        companion.body.set_feet(enemy.body.center_x - 10,
                                enemy.body.feet[1])

        companion.tell_frames = 0
        companion.attack_frames = 999
        scene.player.chain.start(0)          # bitirici DEGIL
        scene.on_player_attack(scene.player, 0)
        check(companion.tell_frames == 0,
              "bitirici olmayan vurus asist tetiklemiyor")

        # Zincirin sonuna git - `is_finisher` orada True.
        last = scene.player.chain._effective_max
        scene.player.chain.start(last)
        check(scene.player.chain.is_finisher, "zincirin sonundayiz")
        scene.on_player_attack(scene.player, last)
        check(companion.tell_frames > 0, "bitirici asisti TETIKLEDI",
              f"tell {companion.tell_frames}")
        check(companion.attack_frames == 0,
              "asist beklemeyi atliyor - senkron icin sart")
    finally:
        game.quit()


def test_assist_belongs_to_this_chapter() -> None:
    """Bes bitmis bolumun dovus hissi sessizce degismedi."""
    print("\n--- asist bu bolume ait ---")
    import inspect
    for module in ("chapter06", "chapter07", "chapter08", "chapter09"):
        source = inspect.getsource(
            __import__(f"src.scenes.{module}", fromlist=[module]))
        check(".assist()" not in source,
              f"{module} asist cagirmiyor")
    source16 = inspect.getsource(
        __import__("src.scenes.chapter16", fromlist=["chapter16"]))
    check(".assist()" in source16, "bolum 16 cagiriyor")


def test_downed_companion_does_not_fight() -> None:
    """Diz cokmus yoldas asist de yapmiyor - yerde olmanin bedeli."""
    print("\n--- yerdeki yoldas savasmiyor ---")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("yalniz")
        companion = with_companion(scene)
        put_down(scene, companion)
        check(not companion.assist(), "yerdeyken asist YOK")
    finally:
        game.quit()


# --- 5. Jest secimi -----------------------------------------------------------
def test_gesture_has_no_wrong_answer() -> None:
    """Uc secenek, hicbiri yanlis - `docs/derinlestirme.md` 3.3."""
    print("\n--- jest secimi ---")
    choice = gesture.GestureChoice()
    check(len(choice.options) == 3, "uc jest", str(len(choice.options)))
    check(choice.index == 1,
          "varsayilan ORTADA - acele eden oyuncu farkinda olmadan "
          "'elini uzat' demesin")
    icons = {option.icon for option in choice.options}
    check(len(icons) == 3, "uc farkli ikon - siluetle ayriliyorlar",
          str(sorted(icons)))

    # Balonlar sirayla aciliyor; hepsi acilmadan secim yok.
    check(not choice.ready, "hemen hazir degil - balonlar sirayla geliyor")
    check(choice.confirm() is None, "acilmadan onay kabul edilmiyor")
    for _ in range(60):
        choice.update()
    check(choice.ready, "acildi")

    check(choice.move(-1), "sola gidiyor")
    check(choice.current is gesture.REACH, "soldaki 'elini uzat'")
    check(not choice.move(-1), "kenarda SARMIYOR - yerini kaybetme")
    picked = choice.confirm()
    check(picked is gesture.REACH, "secim kaydedildi")
    check(choice.confirm() is None, "iki kez secilemiyor")


def test_gesture_reaches_the_save() -> None:
    """Secim kayda gidiyor - puan degil ton, ama kaybolmuyor."""
    print("\n--- secim kayda gidiyor ---")
    game = Game()
    try:
        scene = start(game)
        scene._remember_gesture(gesture.WITHDRAW)
        check(scene.gesture_key == "withdraw", "sahne hatirliyor",
              scene.gesture_key)
        data = scene.save_data
        check(data is not None
              and data.flags.get("ch16_gesture") == "withdraw",
              "kayda yazildi")
    finally:
        game.quit()


# --- 6. Ara sahneler ★ --------------------------------------------------------
def test_cinematics_play_for_both_characters() -> None:
    """Ikisi de, **cizim dahil**.

    Projede iki kez cizim cagirmayan testler yuzunden cokme yasandi
    (`Actor.draw_extra`, Mizrakli'nin hitbox'i). Bu kontrol o kor
    noktayi kapatiyor.
    """
    print("\n--- ara sahneler (iki karakter, cizim dahil) ---")
    for cls in (ReturnCinematic, LiftCinematic, HeartCinematic):
        for character in ("rey", "ardo"):
            game = Game()
            try:
                game.scenes.set_root(cls, transition=False,
                                     character=character)
                game.scenes._flush()
                scene = game.scenes.current
                for _ in range(240):
                    game.input.begin_frame()
                    game.input.end_frame()
                    game.scenes.update()
                    game.canvas.fill((0, 0, 0, 255))
                    game.scenes.draw(game.canvas)
                    game.frame += 1
                check(True, f"{cls.__name__} ({character}) cokmeden oynuyor")
            except Exception as exc:       # noqa: BLE001 - test raporluyor
                check(False, f"{cls.__name__} ({character})",
                      f"{type(exc).__name__}: {exc}")
            finally:
                game.quit()


def test_heart_appears_for_every_gesture() -> None:
    """Kalp UCUNDE de cikiyor - `docs/yapi.md` bunu acikca soyluyor."""
    print("\n--- kalp ucunde de cikiyor ---")
    for option in gesture.THREE:
        game = Game()
        try:
            game.scenes.set_root(HeartCinematic, transition=False,
                                 character="rey")
            game.scenes._flush()
            scene = game.scenes.current
            # Secim paneline kadar sur, sonra bu jesti sec.
            for _ in range(300):
                game.input.begin_frame(); game.input.end_frame()
                game.scenes.update()
                if scene.choosing and scene.choice.ready:
                    break
            scene.choice.index = gesture.THREE.index(option)
            scene.picked = scene.choice.confirm()
            drawn = False
            for _ in range(400):
                game.input.begin_frame(); game.input.end_frame()
                game.scenes.update()
                game.canvas.fill((0, 0, 0, 255))
                game.scenes.draw(game.canvas)
                game.frame += 1
                panel = scene.panel
                if panel is not None and panel.name == "cevap":
                    drawn = True
            check(drawn, f"'{option.key}' secildi ve kalp paneli oynadi")
        finally:
            game.quit()


# --- 7. Bolum sonu ------------------------------------------------------------
def test_lift_reward_is_visible() -> None:
    """Odul gorunuyor - B15'in hayalet odulunun ayni kalibi."""
    print("\n--- kaldirma odulu gorunuyor ---")
    game = Game()
    try:
        def ghost_row(lifted: bool):
            result = ChapterResult(
                chapter_key="chapter.backtoback", frames=60, best_combo=0,
                gold=100, secrets_found=1, secrets_total=1,
                ghost=lifted, ghost_bonus=LIFT_BONUS)
            end = ChapterEndScene(game)
            end.on_enter(result=result)
            for label, value, role in end._rows():
                if label == "chapter_end.ghost":
                    return value, role
            return None, None

        kept_value, kept_role = ghost_row(True)
        missed_value, missed_role = ghost_row(False)
        check(kept_value is not None and missed_value is not None,
              "satir iki durumda da var")
        check(str(LIFT_BONUS) in missed_value,
              "kaldirmayan da odulun buyuklugunu goruyor", missed_value)
        check(kept_role == "reward" and missed_role != "danger",
              "kazanan altin, kaciran KIRMIZI DEGIL",
              f"{kept_role} / {missed_role}")
    finally:
        game.quit()


def test_chapter_shape() -> None:
    print("\n--- bolum sekli ---")
    check(len(ROOM_STARTS) == 7, "yedi oda", str(len(ROOM_STARTS)))
    kinds = {p.kind for p in LEVEL.placements}
    check("chest" in kinds and "exit" in kinds, "sandik ve cikis var")
    check(len(LEVEL.of("trigger")) == 3, "uc ara sahne tetikleyicisi")
    enemies = [p for p in LEVEL.placements
               if p.kind not in ("player", "chest", "exit", "trigger")]
    check(len(enemies) >= 20, "kalabalik - zorluk 6", f"{len(enemies)} dusman")
    # Ilk oda yoldassiz oynaniyor: orada tetikleyici OLMAMALI, yoksa
    # "yalnizlik" perdesi hic yasanmaz.
    first_end = ROOM_STARTS[1][1]
    check(not any(t.tile_x < first_end for t in LEVEL.of("trigger")),
          "ilk odada tetikleyici yok - yalnizlik perdesi yasaniyor")


def main() -> int:
    test_passable_without_companion()
    test_all_triggers_fire()
    test_no_self_recovery_here_only()
    test_lift_needs_a_held_key()
    test_lift_progress_resets()
    test_lift_needs_a_downed_companion()
    test_rescue_is_locked_before_the_lesson()
    test_assist_only_on_finisher()
    test_assist_belongs_to_this_chapter()
    test_downed_companion_does_not_fight()
    test_gesture_has_no_wrong_answer()
    test_gesture_reaches_the_save()
    test_cinematics_play_for_both_characters()
    test_heart_appears_for_every_gesture()
    test_lift_reward_is_visible()
    test_chapter_shape()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("Bolum 16 tutarli - yoldassiz gecilebiliyor, kaldirmak degerli.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
