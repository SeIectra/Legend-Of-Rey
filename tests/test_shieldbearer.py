"""Kalkanli dogrulamasi - "onden vurulmaz, arkaya gec" GERCEKTEN calisiyor mu.

Katman 2'nin ilk uyesi. Sinanan sey davranis degil **ders**: oyuncunun
onden vurmasi ise yaramamali, arkadan vurmasi acikca odullendirilmeli,
ve dusman cozulemez olmamali (yani bir sure sonra donmeli).

Korunan kurallar:

  * Onden gelen vurus **bloklaniyor** - hasar yok
  * Blok oyuncunun **zincirini kiriyor** (Katman 2'nin dersi)
  * Arkadan gelen vurus **tam hasar + kesin sendeleme**
  * Saldirirken/toparlanirken kalkan **inik** - ikinci gecerli cevap
  * Donme **gecikmeli ama kesin** - arkada durmak sonsuz bir sigsinak degil
  * Donusten **once parlama var** - sessizce donmuyor
  * Tell suresi baglayici alt siniri (14 kare) asmiyor

Calistir:
    python tests/test_shieldbearer.py
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

from src.combat.hitbox import Hitbox, Team  # noqa: E402
from src.config import (  # noqa: E402
    ENEMY_MIN_TELL_FRAMES, SHIELDBEARER_TURN_FRAMES,
    SHIELDBEARER_TURN_TELL_FRAMES, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.entities.enemies.shieldbearer import Shieldbearer  # noqa: E402
from src.entities.enemy import EnemyState  # noqa: E402
from src.scenes.chapter05 import Chapter05Scene  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def strike(scene, guard: Shieldbearer, *, from_behind: bool,
           damage: int = 10) -> tuple:
    """Kalkanli'ya bir vurus indirir ve sonucu doner.

    Hitbox **hangi yonde acildigiyla** okunuyor (`attacked_from_behind`),
    o yuzden dikdortgeni gercekten o tarafa koyuyoruz - bayrak gecmek
    testi gercek koddan koparirdi.
    """
    side = -guard.facing if from_behind else guard.facing
    rect = pygame.Rect(int(guard.body.center_x + side * 10) - 4,
                       int(guard.body.center_y) - 8, 8, 16)
    box = Hitbox(rect=rect, damage=damage, owner=scene.player,
                 targets=Team.ENEMY, active_frames=3)
    before = guard.health
    result = guard.take_damage(box, (float(side), 0.0))
    return result, before - guard.health


def place(actor, tile_x: int, tile_y: int) -> None:
    """Aktoru BOS bir tile'a koyar.

    DEVIR 6/20: govdesi kati tile ile cakisan aktor tamamen doniyor ve
    `grounded=True` diyor. Bu projede uc kez uretimde, uc kez de testlerin
    kendi yerlesiminde yasandi - yerlestirme her zaman ayaktan yapiliyor.
    """
    actor.body.set_feet(tile_x * TILE_SIZE + TILE_SIZE * 0.5,
                        (tile_y + 1) * TILE_SIZE)
    actor.body.vx = actor.body.vy = 0.0


def main() -> int:
    game = Game()
    game.scenes.set_root(Chapter05Scene, transition=False, character="rey")
    game.scenes._flush()
    scene = game.scenes.current

    # --- 0. Baglayici kural -------------------------------------------------
    print("--- baglayici kural ---")
    check(Shieldbearer.tell_frames >= ENEMY_MIN_TELL_FRAMES,
          "tell suresi alt siniri asmiyor",
          f"{Shieldbearer.tell_frames} >= {ENEMY_MIN_TELL_FRAMES}")

    # --- 1. Bolume gercekten yerlesmis mi -----------------------------------
    print("\n--- Bolum 5'te tek ornek ---")
    from src.world.rooms.chapter05 import LEVEL, WATER_LOW
    spots = LEVEL.of("shieldbearer")
    check(len(spots) == 1, "Bolum 5'te TAM BIR Kalkanli var (DEVIR 3.8)",
          str(len(spots)))

    # Su butun haritada tek duzlem ve `_update_water` onu DUSMANLARA da
    # uyguluyor. Kalkanli su cizgisinin altinda dursaydi yercekimi %40'a
    # iner, yavaslar ve "suda dusman yok" karari sessizce delinirdi.
    # Cozum kodda degil zeminde (Oda 3'un tabani bir tile yukarida) -
    # o yuzden burada zemini dogruluyoruz, bir bayragi degil.
    spot = spots[0]
    scene.water.level = WATER_LOW
    dry_guard = Shieldbearer(scene, spot.x, spot.feet_y)
    scene.water.apply(dry_guard.body)
    check(dry_guard.body.gravity_scale == 1.0,
          "Kalkanli KURU zeminde - su alcakken bile batmiyor",
          f"gravity_scale {dry_guard.body.gravity_scale:.2f}")

    # --- 2. Onden vurulmaz --------------------------------------------------
    print("\n--- onden: bloklaniyor ---")
    guard = Shieldbearer(scene, 0.0, 0.0)
    place(guard, 4, 13)
    place(scene.player, 6, 13)
    guard.facing = 1
    check(guard.guarding, "beklerken kalkan yukarida")

    result, lost = strike(scene, guard, from_behind=False)
    check(not result.hit, "onden gelen vurus DEGMIYOR")
    check(result.blocked, "sonuc 'blocked' olarak isaretli")
    check(lost == 0, "hic can gitmedi", f"{lost}")

    # --- 3. Blok zinciri kiriyor - Katman 2'nin dersi -----------------------
    print("\n--- blok zinciri kiriyor ---")
    scene.player.chain.start(0)
    scene.player.combo.count = 5
    strike(scene, guard, from_behind=False)
    check(scene.player.chain.index == -1,
          "oyuncunun ZINCIRI kirildi", f"index {scene.player.chain.index}")
    check(scene.player.combo.count == 0,
          "combo sayaci sifirlandi", f"{scene.player.combo.count}")

    # --- 4. Arkadan tam hasar + kesin sendeleme -----------------------------
    print("\n--- arkadan: aciik ---")
    guard2 = Shieldbearer(scene, 0.0, 0.0)
    place(guard2, 4, 13)
    guard2.facing = 1
    result, lost = strike(scene, guard2, from_behind=True, damage=10)
    check(result.hit, "arkadan gelen vurus DEGIYOR")
    check(lost == 10, "tam hasar girdi", f"{lost}")
    check(result.staggered, "arkadan vurus KESIN sendeletiyor")
    check(guard2.state is EnemyState.STAGGER, "durum STAGGER",
          guard2.state.name)

    # Poise 4 - normalde tek vurusta sendelemezdi. Testin anlami bu:
    # sendeleme poise'dan degil, **yonden** geliyor.
    check(Shieldbearer.poise > 1,
          "poise 1'den buyuk - yani sendeleme yonden geliyor, sanstan degil",
          str(Shieldbearer.poise))

    # --- 5. Saldirirken kalkan inik - ikinci gecerli cevap ------------------
    print("\n--- toparlanirken: acik ---")
    guard3 = Shieldbearer(scene, 0.0, 0.0)
    place(guard3, 4, 13)
    guard3.facing = 1
    guard3._set_state(EnemyState.RECOVER)
    check(not guard3.guarding, "toparlanirken kalkan INIK")
    result, lost = strike(scene, guard3, from_behind=False, damage=9)
    check(result.hit and lost == 9,
          "toparlanirken ONDEN vurulabiliyor - ikinci cevap calisiyor",
          f"{lost}")

    # --- 6. Donme gecikmeli AMA kesin ---------------------------------------
    # Arkada durmak sonsuz bir siginak olsaydi Kalkanli bir dusman degil
    # bir tahta kukla olurdu.
    print("\n--- donme: gecikmeli ama kesin ---")
    guard4 = Shieldbearer(scene, 0.0, 0.0)
    place(guard4, 8, 13)
    place(scene.player, 6, 13)          # oyuncu SOLDA
    guard4.facing = 1                   # Kalkanli SAGA bakiyor -> oyuncu arkada
    guard4.aware = True
    check(guard4._player_is_behind(), "oyuncu arkada sayiliyor")

    turned_at = -1
    flash_seen = False
    for frame in range(SHIELDBEARER_TURN_FRAMES * 3):
        guard4.aware = True             # gorus mesafesi testi degil bu
        guard4.update()
        place(scene.player, 6, 13)      # oyuncu kipirdamiyor
        if guard4.turn_tell_frames > 0:
            flash_seen = True
        if guard4.facing == -1:
            turned_at = frame
            break
    check(turned_at > 0, "Kalkanli sonunda DONDU", f"{turned_at}. karede")
    check(turned_at >= SHIELDBEARER_TURN_FRAMES,
          "aninda donmedi - arkaya gecmek gercek bir pencere aciyor",
          f"{turned_at} >= {SHIELDBEARER_TURN_FRAMES}")
    check(flash_seen,
          "donmeden ONCE parlama var - sessizce donmuyor",
          f"{SHIELDBEARER_TURN_TELL_FRAMES} kare")

    # --- 7. Donunce arkasi yine kapaniyor -----------------------------------
    print("\n--- donunce yon gercekten degisti ---")
    result, lost = strike(scene, guard4, from_behind=False)
    check(not result.hit,
          "donduktan sonra ONDEN yine vurulmuyor - yon gercekten degisti")

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Kalkanli: onden kapali, arkadan acik, gecikmeli ama kesin doner.")
    return 0


raise SystemExit(main())
