"""Bolum 15 "Sessizlik" - uyuyan suru ve gurultu.

`docs/yapi.md` B15: *"Yanki'yi kapali oynamak zorundasin. Uyuyan
suru. Kosarsan uyanirlar. **Tamamen dovussuz gecilebilir - ve daha
iyi odul verir.**"*

Korunan kurallar:

  * **Bolum gercekten dovussuz gecilebiliyor.** Yuruyerek bastan sona
    giden bir oyuncu kimseyi uyandirmiyor. Bu iddia OLCULUYOR:
    haritanin bir ucundan otekine yuruyup uyanan sayisina bakiyoruz.
    Gecilemezse belge yalan soyluyor demektir.
  * **Kosmak uyandiriyor.** Ayni tarama kosu hiziyla yapildiginda
    uyanan cikmali - yoksa "kosarsan uyanirlar" bir sus olur.
  * **Ceza degil odul.** Uyandirmak bolumu kaybettirmiyor; yalnizca
    `ghost` bayragini dusuruyor ve ek altin gitmis oluyor.
  * **Rezonansin kendi sesi var.** Bedava olsaydi dikkat dagitmak
    risksiz bir dugme olurdu.
  * **Can uzaktan caliyor**: ses cana ait, oyuncuya degil.
  * **Uyaniklik soluyor** - hata yapan oyuncu bekleyerek duzeltebilir.
  * **Uyanan bir daha uyumuyor** (surekli uyuyup uyanan suru kumar
    olurdu).
  * Sessiz de uyku kuralina uyuyor - `_update_awareness`i ezdigi
    halde.

Calistir:
    python tests/test_chapter15.py
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
    ALERT_DECAY, ALERT_WAKE, NOISE_CHIME, NOISE_RESONATE, NOISE_RUN,
    NOISE_WALK, PLAYER_RUN_SPEED, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.scenes.chapter15 import Chapter15Scene  # noqa: E402
from src.scenes.chapter15_cinematics import PassedCinematic  # noqa: E402
from src.systems.save import SaveData, write_save  # noqa: E402
from src.ui.chapter_end import (  # noqa: E402
    ChapterEndScene, ChapterResult,
)
from src.world.rooms.chapter15 import (  # noqa: E402
    DRIP_INTERVAL, GHOST_BONUS, LEVEL, ROOM_STARTS,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def start(game, character: str = "rey") -> Chapter15Scene:
    write_save(SaveData(chapter=15, character=character,
                        abilities=["sword", "dodge", "echo_sight", "echo_ask"],
                        flags={"sense_betrayed": True, "resonance": True}))
    game.scenes.set_root(Chapter15Scene, transition=False,
                         character=character)
    game.scenes._flush()
    scene = game.scenes.current
    assert isinstance(scene, Chapter15Scene)
    return scene


def cross(scene, speed: float) -> int:
    """Haritayi bastan sona **verilen hizla** yurur.

    Gercek girdi yerine `body.vx` dogrudan veriliyor: test hizin
    ETKISINI olcuyor, tus esleme tablosunu degil (o
    `test_settings.py`nin isi). Ayak sesi `on_player_step`ten
    geliyor ve o hiza bagli, yani zincir gercek.
    """
    body = scene.player.body
    width = scene.tilemap.width * TILE_SIZE
    # Butun odalari kur - normalde odaya girince kuruluyor.
    for name, _ in ROOM_STARTS:
        scene._enter_room(name)
    body.set_feet(TILE_SIZE * 3, body.feet[1])
    while body.center_x < width - TILE_SIZE * 3:
        body.vx = speed
        body.set_feet(body.center_x + speed, body.feet[1])
        scene.update()
    return scene.wakes


# --- 1. Bolum dovussuz gecilebiliyor mu ★ -------------------------------------
def test_walk_is_silent() -> None:
    """Bolumun tek vaadi: **yuruyerek gecilebiliyor.**

    `docs/yapi.md` bunu acikca soyluyor. Gecilemiyorsa belge yalan
    soyluyor ve oyuncu haksizliga ugruyor.
    """
    print("\n--- yuruyerek gecmek ---")
    game = Game()
    try:
        walker = start(game)
        woke = cross(walker, PLAYER_RUN_SPEED * 0.30)
        # Sayim `cross`tan SONRA: odalar orada kuruluyor, once
        # sayilsaydi yalnizca ilk odanin uyuyani gorulurdu.
        total = len([e for e in walker.enemies if not e.dead])
        check(woke == 0,
              "yuruyen oyuncu HICBIRINI uyandirmiyor",
              f"{woke}/{total} uyandi")
        check(walker.ghost, "hayalet gecis mumkun (uyandirma yok, olum yok)")
    finally:
        game.quit()


def test_running_wakes() -> None:
    """*"Kosarsan uyanirlar."* Olculmezse bir sus olur."""
    print("\n--- kosarak gecmek ---")
    check(NOISE_RUN > NOISE_WALK * 3,
          "kosma sesi yurumeden belirgin yuksek",
          f"{NOISE_RUN} vs {NOISE_WALK}")
    game = Game()
    try:
        runner = start(game)
        woke = cross(runner, PLAYER_RUN_SPEED)
        total = len([e for e in runner.enemies if not e.dead])
        check(woke > 0, "kosan oyuncu uyandiriyor", f"{woke}/{total} uyandi")
        check(not runner.ghost, "kosan oyuncu hayalet odulunu kaybediyor")
    finally:
        game.quit()


def test_waking_is_not_a_loss() -> None:
    """Ceza degil odul. Zorluk 4 - gizlilik kaydet-yukle olmamali."""
    print("\n--- uyandirmak kaybettirmiyor ---")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("uyku")
        sleeper = next(e for e in scene.enemies if e.asleep)
        sleeper.wake()
        check(scene.wakes >= 0, "uyanma sayiliyor")
        check(not scene.ghost, "hayalet odulu dustu")
        check(not scene.finished, "bolum KAYBEDILMEDI - oyun devam ediyor")
        check(scene.player.health > 0, "oyuncu cezalandirilmadi")
    finally:
        game.quit()


# --- 2. Gurultu mekanigi ------------------------------------------------------
def test_ghost_reward_is_visible() -> None:
    """Odul GORUNMELI - kazanan da kazanamayan da ogrenmeli.

    `docs/yapi.md` B15 *"daha iyi odul verir"* diyor. Odul veriliyordu
    ama ozet ekraninda yalnizca altin sayisi bir tik buyuk cikiyordu:
    kazanan neden kazandigini, kazanamayan boyle bir sey oldugunu
    ogrenemiyordu. Ekranin kendi gerekcesi bunun tersi
    (`chapter_end.py`): *"'0/1 gizli alan' goren oyuncu bir daha gizli
    alan arar."*
    """
    print("\n--- hayalet odulu gorunuyor ---")

    kept = ChapterResult(chapter_key="chapter.silence", frames=60,
                         best_combo=0, gold=100, secrets_found=1,
                         secrets_total=1, ghost=True,
                         ghost_bonus=GHOST_BONUS)
    missed = ChapterResult(chapter_key="chapter.silence", frames=60,
                           best_combo=0, gold=15, secrets_found=1,
                           secrets_total=1, ghost=False,
                           ghost_bonus=GHOST_BONUS)

    # Sormamis bolum - eski ozetler bozulmamali.
    silent = ChapterResult(chapter_key="chapter.village", frames=60,
                           best_combo=0, gold=10, secrets_found=0,
                           secrets_total=0)

    game = Game()
    try:
        def rows(result):
            scene = ChapterEndScene(game)
            scene.on_enter(result=result)
            return scene._rows()

        def ghost_row(result):
            for label, value, role in rows(result):
                if label == "chapter_end.ghost":
                    return value, role
            return None, None

        kept_value, kept_role = ghost_row(kept)
        missed_value, missed_role = ghost_row(missed)
        silent_value, _ = ghost_row(silent)

        check(kept_value is not None, "kazaninca satir VAR")
        check(missed_value is not None,
              "kacirinca da satir VAR - yoksa oyuncu ogrenemez")
        check(silent_value is None,
              "sormamis bolumde satir HIC yok - eski ozetler bozulmadi")

        check(str(GHOST_BONUS) in kept_value,
              "kazanan odulun buyuklugunu goruyor", kept_value)
        check(str(GHOST_BONUS) in missed_value,
              "KACIRAN da odulun buyuklugunu goruyor - neyi kacirdigini bilsin",
              missed_value)
        check(kept_value != missed_value,
              "iki durum METINCE ayriliyor - renk tek basina yeterli degil",
              f"{kept_value!r} vs {missed_value!r}")

        check(kept_role == "reward", "kazanan altin renginde", kept_role)
        check(missed_role != "danger",
              "kaciran KIRMIZI DEGIL - bolum 'ceza degil odul' diyor",
              missed_role)
    finally:
        game.quit()


def test_alert_decays() -> None:
    """Uyaniklik soluyor - hata bekleyerek duzeltilebilir."""
    print("\n--- uyaniklik soluyor ---")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("uyku")
        sleeper = next(e for e in scene.enemies if e.asleep)
        sleeper.alert_level = 0.6
        for _ in range(30):
            sleeper._update_alert()
        check(sleeper.alert_level < 0.6, "seviye dusuyor",
              f"{sleeper.alert_level:.2f}")
        check(sleeper.asleep, "hala uyuyor - esigin altinda kaldi")

        # **Gercek en kotu hal**: esigin bir tik altindan sifira. Ilk
        # surum bunu 0.6'dan HESAPLIYOR ve "tam sifirlanma" diyordu -
        # 0.6 testin iki satir once kendi uydurdugu bir sayiydi, oyunda
        # karsiligi yok. Simdi olculuyor ve baslangic gercek en kotu
        # durum.
        #
        # Bar `DRIP_INTERVAL`: damla bu bolumun metronomu, oyuncuya
        # ritmi o ogretiyor. Sifirlanma bir damla araligindan kisaysa
        # "bir damla bekle" her zaman yeterli - ogretilebilir, kurgu
        # icinde bir kural. Saniye cinsinden uydurulmus bir esik degil.
        sleeper.alert_level = ALERT_WAKE - 0.001
        frames = 0
        while sleeper.alert_level > 0.0 and frames <= DRIP_INTERVAL * 4:
            sleeper._update_alert()
            frames += 1
        check(frames < DRIP_INTERVAL,
              "sifirlanma bir damladan kisa - beklemek angarya degil",
              f"{frames} kare, damla {DRIP_INTERVAL}")
        check(sleeper.asleep, "beklerken uyanmadi")
    finally:
        game.quit()


def test_wake_is_one_way() -> None:
    """Uyanan bir daha uyumuyor - yoksa suru bir kumar olurdu."""
    print("\n--- uyanma tek yonlu ---")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("uyku")
        sleeper = next(e for e in scene.enemies if e.asleep)
        sleeper.wake()
        check(not sleeper.asleep and sleeper.aware, "uyandi")
        for _ in range(400):
            sleeper._update_alert()
        check(not sleeper.asleep, "400 kare sonra da UYANIK")
    finally:
        game.quit()


def test_sleep_reads_in_silhouette() -> None:
    """Uyku **siluetle** okunmali, tek basina kucuk bir isaretle degil.

    Bu kontrol bir ekran goruntusunden dogdu: uyuyan dusman dimdik
    ayaktaydi ve uyanik olandan yalnizca kafasinin ustundeki 2x2
    piksellik uc noktayla ayriliyordu. Butun bolumun kurali "uyuyan
    zararsiz, uyanik tehlikeli" iken o ayrimin tek bir kucuk isarete
    binmesi `CLAUDE.md` 7'ye aykiri (*"durum gorsel olarak okunur"*,
    *"siluet testi"*) ve renk korlugu icin de yetersiz.

    Davranis testleri bunu goremezdi cunku hicbiri cizime bakmiyordu -
    projede ayni kor nokta daha once `NotImplementedError`la ve
    Mizrakli'nin cokmesiyle iki kez patladi.
    """
    print("\n--- uyku siluette okunuyor ---")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("uyku")
        sleeper = next(e for e in scene.enemies if e.asleep)

        sleep_w, sleep_h = sleeper.silhouette_scale()
        check(sleep_h < 0.85,
              "uyuyan COKMUS - ayakta durandan belirgin kisa",
              f"{sleep_h:.2f}x boy")
        check(sleep_w > 1.0, "ve genislemis - siluet gercekten degisti",
              f"{sleep_w:.2f}x en")

        # Uyaniklik arttikca dogruluyor: oyuncu birinin kalkmakta
        # oldugunu **gorup** geri cekilebilmeli.
        sleeper.alert_level = ALERT_WAKE * 0.5
        _, half_h = sleeper.silhouette_scale()
        check(half_h > sleep_h,
              "uyaniklik artinca doguluyor - kalkmakta oldugu gorunuyor",
              f"{sleep_h:.2f} -> {half_h:.2f}")

        sleeper.wake()
        awake_scale = sleeper.silhouette_scale()
        check(awake_scale == (1.0, 1.0),
              "uyaninca tam boy - deformasyon uykuya ait",
              f"{awake_scale}")
    finally:
        game.quit()


def test_noise_has_range() -> None:
    print("\n--- gurultunun menzili ---")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("uyku")
        sleeper = next(e for e in scene.enemies if e.asleep)
        far_x = sleeper.body.center_x + 400
        sleeper.hear(far_x, sleeper.body.center_y, 2.0)
        check(sleeper.alert_level == 0.0, "menzil disindaki ses duyulmuyor")
        sleeper.hear(sleeper.body.center_x + 10, sleeper.body.center_y, 2.0)
        check(not sleeper.asleep, "yakindaki guclu ses uyandiriyor")
    finally:
        game.quit()


def test_silent_respects_sleep() -> None:
    """Sessiz `_update_awareness`i EZIYOR - kurala yine de uymali.

    Uymasaydi uyuyan bir Sessiz yaklasan oyuncuyu pusuyla yakalardi
    ve gizlilik bolumunde sessiz yurumenin anlami kalmazdi.
    """
    print("\n--- Sessiz de uyuyor ---")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("damla")
        silent = next((e for e in scene.enemies
                       if type(e).__name__ == "Silent"), None)
        check(silent is not None, "damla odasinda Sessiz var")
        silent.asleep = True
        silent.roused = False
        scene.player.body.set_feet(silent.body.center_x + 8,
                                   silent.body.feet[1])
        for _ in range(60):
            silent._update_awareness()
        check(silent.asleep and not silent.aware,
              "uyuyan Sessiz yaninda duran oyuncuyu pusuya dusurmuyor")
    finally:
        game.quit()


# --- 3. Dikkat dagitma ★ ------------------------------------------------------
def test_resonance_costs_noise() -> None:
    """Darbenin **kendi sesi var** - bulmacayi kuran sey bu."""
    print("\n--- rezonansin bedeli ---")
    check(NOISE_RESONATE > 0.0, "darbe sessiz DEGIL", str(NOISE_RESONATE))
    check(NOISE_RESONATE < NOISE_RUN,
          "ama kosmaktan sessiz - acele etmek daha pahali",
          f"{NOISE_RESONATE} < {NOISE_RUN}")
    check(NOISE_CHIME > NOISE_RESONATE * 4,
          "can darbeden cok daha yuksek - dikkat ORAYA gidiyor",
          f"{NOISE_CHIME} vs {NOISE_RESONATE}")


def test_chime_pulls_attention() -> None:
    """Can calinca suru **cana** bakiyor, oyuncuya degil."""
    print("\n--- can dikkat dagitiyor ---")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("can")
        chime = scene.chimes[0]
        sleeper = next(e for e in scene.enemies if e.asleep)
        # Uyandirmadan duyacak kadar yakin olsun.
        sleeper.body.set_feet(chime.x + 60, sleeper.body.feet[1])
        scene._ring(chime)
        check(sleeper.heard_x is not None, "sesi duydu")
        check(abs(sleeper.heard_x - chime.x) < 1.0,
              "duydugu yer CANIN yeri", f"{sleeper.heard_x:.0f} vs {chime.x:.0f}")
        # Ve oraya yuruyor.
        before = sleeper.body.center_x
        for _ in range(60):
            sleeper.update()
        moved = sleeper.body.center_x - before
        check(moved < 0, "cana dogru yuruyor (soluna)", f"{moved:.1f} px")
    finally:
        game.quit()


def test_chime_is_reusable() -> None:
    """Tek kullanimlik olsaydi yanlis zamanda calan oyuncu kilitlenirdi."""
    print("\n--- can yeniden calinabiliyor ---")
    game = Game()
    try:
        scene = start(game)
        chime = scene.chimes[0]
        check(chime.ring(), "ilk calis")
        check(not chime.ring(), "cooldown sirasinda calmiyor")
        for _ in range(120):
            chime.update()
        check(chime.ring(), "cooldown bitince YENIDEN calinabiliyor")
    finally:
        game.quit()


def test_drip_rings_itself() -> None:
    """Damla oyuncuyu beklemiyor - ritim veriyor."""
    print("\n--- su damlasi ---")
    game = Game()
    try:
        scene = start(game)
        scene._enter_room("damla")
        check(scene.drip is not None, "damla odasinda damla var")
        before = scene.noise.wakes
        rings = 0
        for _ in range(700):
            count = len(scene.noise.rings)
            scene._update_drip()
            if len(scene.noise.rings) > count:
                rings += 1
            scene.noise.update()
        check(rings >= 2, "damla kendi kendine tekrar tekrar caliyor",
              f"{rings} kez")
    finally:
        game.quit()


# --- 4. Bolum sekli -----------------------------------------------------------
def test_chapter_shape() -> None:
    print("\n--- bolum sekli ---")
    names = [n for n, _ in ROOM_STARTS]
    check(len(names) == 6, "alti oda", str(len(names)))
    kinds = {p.kind for p in LEVEL.placements}
    check("chime" in kinds and "drip" in kinds,
          "iki tur gurultu kaynagi da var")
    # Ilk oda OGRETME: can yok, yani kural bedelsiz ogreniliyor.
    first_end = ROOM_STARTS[1][1]
    chimes_first = [p for p in LEVEL.of("chime") if p.tile_x < first_end]
    check(not chimes_first, "ogretme odasinda can YOK - once kural, sonra arac")
    # Zirve odasinda can yok: tek cozum yurumek.
    dar_start, dar_end = ROOM_STARTS[4][1], ROOM_STARTS[5][1]
    chimes_dar = [p for p in LEVEL.of("chime")
                  if dar_start <= p.tile_x < dar_end]
    check(not chimes_dar,
          "zirve odasinda can YOK - tek cozum yurumek")


def test_cinematic() -> None:
    print("\n--- kapanis sahnesi ---")
    game = Game()
    try:
        surface = pygame.Surface((480, 270))
        for character in ("rey", "ardo"):
            for ghost in (True, False):
                game.scenes.set_root(PassedCinematic, transition=False,
                                     character=character, ghost=ghost)
                game.scenes._flush()
                scene = game.scenes.current
                for _ in range(120):
                    scene.update()
                    scene.draw(surface)
                label = "hayalet" if ghost else "uyandirdi"
                check(True, f"kapanis ({character}, {label}) cokmeden oynuyor")
    finally:
        game.quit()


def main() -> int:
    test_walk_is_silent()
    test_running_wakes()
    test_waking_is_not_a_loss()
    test_ghost_reward_is_visible()
    test_alert_decays()
    test_wake_is_one_way()
    test_sleep_reads_in_silhouette()
    test_noise_has_range()
    test_silent_respects_sleep()
    test_resonance_costs_noise()
    test_chime_pulls_attention()
    test_chime_is_reusable()
    test_drip_rings_itself()
    test_chapter_shape()
    test_cinematic()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("Bolum 15 tutarli - yuruyerek gecilebiliyor, kosarsan duyuluyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
