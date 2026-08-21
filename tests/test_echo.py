"""Yanki sistemi dogrulamasi - Gorev 3.

`docs/gdd.md` 4 baglayici. Buradaki her kontrol **oynanis hissini**
koruyor, kodun calistigini degil:

  * Uc kademe, olunce duser, SESSIZ dip
  * Yardim ve bedel **ayni** egriden besleniyor - biri olmadan digeri yok
  * BERRAK asla yalan soylemez, kademe dustukce yalan artar
  * Kolye asla yalan soylemez - secim gercek bir secim olsun
  * Kolye ile Yanki celisebilir

Calistir:
    python tests/test_echo.py
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

from src.config import (  # noqa: E402
    ECHO_DAMAGE_TAKEN_MULTIPLIER, ECHO_TIER_CLEAR, ECHO_TIER_MURKY,
    ECHO_TIER_SILENT,
)
from src.systems.compass import Compass, contradicts  # noqa: E402
from src.systems.echo import (  # noqa: E402
    COMBO_TO_RESTORE, Answer, EchoState, FALL_FRAMES, RISE_FRAMES,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


class FakeBody:
    def __init__(self, x: float) -> None:
        self.center_x = x
        self.center_y = 0.0


class FakePlayer:
    def __init__(self, x: float = 0.0) -> None:
        self.body = FakeBody(x)


def hold(echo: EchoState, frames: int, down: bool = True) -> None:
    for _ in range(frames):
        echo.update(down)


def main() -> int:
    # --- 1. Kademeler (BAGLAYICI) -------------------------------------------
    print("--- kademeler ---")
    echo = EchoState(tier=ECHO_TIER_CLEAR, seed=1)
    check(echo.tier == ECHO_TIER_CLEAR, "BERRAK baslangic", echo.tier_name())

    check(echo.weaken() and echo.tier == ECHO_TIER_MURKY,
          "olunce bir kademe duser", echo.tier_name())
    check(echo.weaken() and echo.tier == ECHO_TIER_SILENT,
          "ikinci olum SESSIZ", echo.tier_name())
    check(not echo.weaken() and echo.tier == ECHO_TIER_SILENT,
          "SESSIZ dip - daha asagi inmez (olum sarmali engelli)")

    check(echo.restore() and echo.tier == ECHO_TIER_MURKY,
          "iyilesme bir kademe kaldirir")
    echo.restore()
    check(not echo.restore() and echo.tier == ECHO_TIER_CLEAR,
          "BERRAK tavan")

    check(COMBO_TO_RESTORE == 20,
          "20 combo bir kademe iyilestirir", str(COMBO_TO_RESTORE))

    # --- 2. Yardim ve bedel ayni egriden ------------------------------------
    # Ikisi ayri degiskene baglansaydi biri gun "vinyeti azaltalim" der ve
    # mekanigin kalbi sessizce olurdu.
    print("\n--- yardim ve bedel ayni egriden ---")
    echo = EchoState(tier=ECHO_TIER_CLEAR, seed=2)
    check(echo.sight_range == 0.0 and echo.vignette == 0.0,
          "kapaliyken ne yardim ne bedel")
    check(echo.damage_multiplier == 1.0, "kapaliyken savunma normal")

    hold(echo, RISE_FRAMES)
    check(echo.strength >= 0.99, "acilma egrisi doldu",
          f"{echo.strength:.2f} / {RISE_FRAMES} kare")
    check(echo.sight_range > 0 and echo.vignette > 0,
          "acikken ikisi birden var",
          f"menzil {echo.sight_range:.0f}  vinyet {echo.vignette:.2f}")
    check(abs(echo.damage_multiplier - ECHO_DAMAGE_TAKEN_MULTIPLIER) < 0.01,
          "acikken savunma duser", f"x{echo.damage_multiplier:.2f}")

    # Yarim aciktayken **ikisi de** yarim olmali.
    echo = EchoState(tier=ECHO_TIER_CLEAR, seed=3)
    hold(echo, RISE_FRAMES // 2)
    check(0.3 < echo.strength < 0.7, "yarim acik", f"{echo.strength:.2f}")
    check(echo.vignette > 0 and echo.sight_range > 0,
          "yarim acikken ikisi de yarim",
          f"menzil {echo.sight_range:.0f} vinyet {echo.vignette:.2f}")

    # Kapanma acilmadan **yavas** - "dugme" degil "hal".
    hold(echo, 200, down=True)
    hold(echo, FALL_FRAMES - 1, down=False)
    check(echo.strength > 0.0, "birakinca aninda kesilmiyor",
          f"{echo.strength:.2f}")
    check(FALL_FRAMES > RISE_FRAMES, "kapanma acilmadan yavas",
          f"{RISE_FRAMES} -> {FALL_FRAMES}")

    # --- 3. Menzil kademeye bagli -------------------------------------------
    print("\n--- menzil ---")
    ranges = {}
    for tier in (ECHO_TIER_CLEAR, ECHO_TIER_MURKY, ECHO_TIER_SILENT):
        e = EchoState(tier=tier, seed=4)
        hold(e, RISE_FRAMES)
        ranges[tier] = e.sight_range
    check(ranges[ECHO_TIER_CLEAR] > ranges[ECHO_TIER_MURKY] > 0,
          "BERRAK BULANIK'tan uzagi gorur",
          f"{ranges[ECHO_TIER_CLEAR]:.0f} > {ranges[ECHO_TIER_MURKY]:.0f}")
    check(ranges[ECHO_TIER_SILENT] == 0.0, "SESSIZ hicbir sey gostermez")

    # --- 4. Yalan (BAGLAYICI - mekanigin kalbi) ------------------------------
    print("\n--- Yanki yalan soyleyebilir ---")
    echo = EchoState(tier=ECHO_TIER_CLEAR, seed=5)
    clear_answers = set()
    for _ in range(200):
        echo.ask_cooldown = 0
        clear_answers.add(echo.ask())
    check(clear_answers == {Answer.TRUTH},
          "BERRAK **asla** yalan soylemez - guven once kurulur",
          str(sorted(a.name for a in clear_answers)))

    echo = EchoState(tier=ECHO_TIER_MURKY, seed=7)
    lies = 0
    total = 400
    for _ in range(total):
        echo.ask_cooldown = 0
        if echo.ask() is Answer.LIE:
            lies += 1
    ratio = lies / total
    check(0.2 < ratio < 0.5, "BULANIK bazen yalan soyler",
          f"%{ratio * 100:.0f}")

    echo = EchoState(tier=ECHO_TIER_SILENT, seed=8)
    echo.ask_cooldown = 0
    check(echo.ask() is Answer.NONE, "SESSIZ cevap vermez")

    # Bekleme suresi: sorup durmak mumkun olmamali.
    echo = EchoState(tier=ECHO_TIER_CLEAR, seed=9)
    first = echo.ask()
    second = echo.ask()
    check(first is not Answer.NONE and second is Answer.NONE,
          "arka arkaya sorulamiyor - bekleme suresi var")

    # --- 5. Kolye pusulasi ---------------------------------------------------
    print("\n--- kolye pusulasi ---")
    compass = Compass()
    player = FakePlayer(x=0.0)
    compass.update(player)
    check(compass.warmth == 0.0, "hedef yokken soguk")

    compass.set_target(400.0, 0.0)
    compass.update(player)
    far = compass.warmth
    compass.set_target(40.0, 0.0)
    compass.update(player)
    near = compass.warmth
    check(near > far, "yaklastikca isinir", f"{far:.2f} -> {near:.2f}")
    check(near >= 0.99, "cok yakinda tam sicak", f"{near:.2f}")

    compass.set_target(400.0, 0.0)
    compass.update(player)
    slow = compass.beat_period
    compass.set_target(40.0, 0.0)
    compass.update(player)
    fast = compass.beat_period
    check(fast < slow, "yaklastikca kalp atisi hizlanir",
          f"{slow} -> {fast} kare")

    check(compass.direction_from(player) == 1, "sagdaki hedefi sag gosterir")
    compass.set_target(-40.0, 0.0)
    compass.update(player)
    check(compass.direction_from(player) == -1, "soldaki hedefi sol gosterir")

    # --- 6. Celiski (temanin durdugu yer) ------------------------------------
    print("\n--- kolye ile Yanki celisebilir ---")
    compass.set_target(120.0, 0.0)        # kolye sagi gosteriyor
    compass.update(player)
    check(contradicts(compass, player, echo_direction=-1),
          "kolye sagi, Yanki solu gosterirse celiski var")
    check(not contradicts(compass, player, echo_direction=1),
          "ayni yonu gosterirlerse celiski yok")
    check(not contradicts(compass, player, echo_direction=0),
          "Yanki sessizken celiski yok")

    # --- 7. Bedel gercekten bedel mi (ekranda olculur) ----------------------
    # Bu kontrol bir hatayi yakalamak icin degil, **yasanani tekrar
    # yasamamak** icin var. Yanki'nin bedeli uc kez ust uste ters yone
    # dondu: `BLEND_RGB_ADD` alfayi agirlik olarak kullanmadigi icin ekran
    # kararacagina parliyordu, bir keresinde de cizim sirasi yuzunden -
    # siluetler ve duvar parlamalari karartmanin ustune biniyordu.
    #
    # Goz bunu "biraz aydinlik olmus" diye gecistirebiliyor. Olcum
    # gecistirmiyor.
    print("\n--- bedel ekranda olculuyor ---")
    import numpy as np

    from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
    from src.core.game import Game
    from src.scenes.chapter01 import Chapter01Scene
    from src.systems import abilities as ab

    game = Game()
    game.scenes.set_root(Chapter01Scene, transition=False, character="rey")
    game.scenes._flush()
    scene = game.scenes.current
    scene.player.grant(ab.ECHO_SIGHT)
    scene.beat_index = 99                      # prologu atla
    canvas = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))

    def brightness() -> float:
        canvas.fill((0, 0, 0))
        scene.draw(canvas)
        return float(np.mean(pygame.surfarray.array3d(canvas)))

    def run(frames: int, echo_key: bool) -> None:
        for _ in range(frames):
            game.input.begin_frame()
            if echo_key:
                game.input.handle_event(
                    pygame.event.Event(pygame.KEYDOWN, key=pygame.K_k))
            game.input.end_frame()
            scene.update()

    run(20, echo_key=False)
    lit = brightness()
    run(25, echo_key=True)
    dimmed = brightness()

    check(dimmed < lit, "Yanki acilinca ekran KARARIYOR (parlamiyor)",
          f"{lit:.1f} -> {dimmed:.1f}")
    check(lit - dimmed > 0.5, "kararma fark edilir olcude",
          f"{lit - dimmed:.2f}")
    game.shutdown()
    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Yanki sistemi belgedeki kurallara uyuyor.")
    return 0


pygame.init()
raise SystemExit(main())
