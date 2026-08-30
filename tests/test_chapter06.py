"""Bolum 6 "ARDO" - team-up, agirlik plakalari, BOSS 1.

`docs/yapi.md` B6 + `docs/gdd.md` 10. Uc yeni sistem bir arada:
yoldas, plakalar, boss. Test her birinin **tasarim sozunu** koruyor,
kodun calistigini degil.

Korunan kurallar:

  * Yoldas **secmedigin** karakter (`docs/gdd.md` 3, kanon)
  * Yoldas **olmez**, diz coker - yoksa dovus koruma gorevine doner ve
    plaka bulmacasi cozulemez hale gelir
  * Yoldas **oynamiyor, yardim ediyor**: hasari oyuncunun altinda,
    tasmasi var
  * Kapi **butun plakalar** basiliyken aciliyor - tek plaka yetmez,
    yoksa beraberlik anlamsizlasir
  * Bir kisi iki plakaya birden **basamaz** (mesafe yeterli)
  * Boss'un Faz 2 **muhru** yalnizca plakalarla kiriliyor
  * Boss atlanamiyor: cikis boss olmeden acilmiyor
  * Sikisma odasi bastan **cikmaz**, yoldas gelince aciliyor

Calistir:
    python tests/test_chapter06.py
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
    COMPANION_DAMAGE, COMPANION_LEASH, PLATE_STUN_FRAMES, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.entities.companion import other_character  # noqa: E402
from src.scenes.chapter06 import Chapter06Scene, RESCUE_DELAY  # noqa: E402
from src.world.rooms.chapter06 import (  # noqa: E402
    ARENA_PLATE_A_TILE, ARENA_PLATE_B_TILE, CORNER_WALL_ROWS,
    CORNER_WALL_TILE, LEVEL, ROOM_STARTS, TEACH_PLATE_A_TILE,
    TEACH_PLATE_B_TILE,
)

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


def place(actor, tile) -> None:
    """Aktoru BOS bir tile'a koyar - DEVIR 6/20'nin uc kez yasanan hatasi."""
    actor.body.set_feet(tile[0] * TILE_SIZE + TILE_SIZE * 0.5,
                        tile[1] * TILE_SIZE)
    actor.body.vx = actor.body.vy = 0.0


def main() -> int:
    game = Game()

    # --- 1. Yoldas kanona uyuyor -------------------------------------------
    print("--- yoldas: SECMEDIGIN karakter ---")
    check(other_character("rey") == "ardo"
          and other_character("ardo") == "rey",
          "`docs/gdd.md` 3: secmedigin taraf geliyor")

    for played, expected in (("rey", "ardo"), ("ardo", "rey")):
        game.scenes.set_root(Chapter06Scene, transition=False,
                             character=played)
        game.scenes._flush()
        scene = game.scenes.current
        check(scene.companion_key == expected,
              f"{played} oynanirken yoldas {expected}",
              scene.companion_key)

    game.scenes.set_root(Chapter06Scene, transition=False, character="rey")
    game.scenes._flush()
    scene = game.scenes.current

    # --- 2. Sikisma odasi gercekten cikmaz ---------------------------------
    print("\n--- kose: gercekten sikisiyor ---")
    check(all(scene.tilemap.is_solid(CORNER_WALL_TILE, row)
              for row in CORNER_WALL_ROWS),
          "kose duvari bastan KAPALI - kacacak yer yok")
    check(scene.companion is None, "yoldas henuz yok")
    check(len(scene.enemies) >= 3, "kosede yaratiklar var",
          str(len(scene.enemies)))

    # --- 3. Yoldas geliyor ve yaratiklari BICIYOR --------------------------
    print("\n--- kurtarma ---")
    step(game, RESCUE_DELAY + 6)
    check(scene.rescued, "yoldas geldi")
    check(scene.companion is not None, "yoldas nesnesi var")
    check(all(e.dead for e in scene.enemies),
          "uc yaratik da bicildi - ilk izlenim 'yardimci' degil GUCLU")
    check(all(not scene.tilemap.is_solid(CORNER_WALL_TILE, row)
              for row in CORNER_WALL_ROWS),
          "duvar acildi - kurtarilmanin somut karsiligi var")
    # Soru isareti artik SAHNENIN icinde ciziliyor (30.08.2026): giris
    # bir sinematik oldu ve balonu iki yerde cizmek ikisinin ayrismasi
    # demekti. Burada sahnenin acildigi dogrulaniyor; balonun kendisi
    # `test_entrance()`'ta.
    game.scenes._flush()
    from src.scenes.chapter06_cinematics import ArdoEntranceCinematic
    check(isinstance(game.scenes.current, ArdoEntranceCinematic),
          "giris sinematigi aciliyor - `docs/gdd.md` 10 'havali giris'")
    game.scenes.pop()
    game.scenes._flush()

    companion = scene.companion

    # --- 4. Yoldas OLMEZ ----------------------------------------------------
    # Olmesi dovusu koruma gorevine cevirir VE plaka bulmacasini
    # cozulemez hale getirir - ikisi de bolumu bozar.
    print("\n--- yoldas olmez, diz coker ---")
    box = Hitbox(rect=companion.body.rect.copy(), damage=999,
                 owner=None, targets=Team.PLAYER, active_frames=2)
    companion.take_damage(box, (1.0, 0.0))
    check(not companion.dead, "yoldas OLMEDI")
    check(companion.downed, "diz cokmus")
    check(companion.health > 0, "cani sifirin ustunde",
          str(companion.health))
    companion.down_frames = 1
    step(game, 3)
    check(not companion.downed, "kendi kendine kalkti")

    # --- 5. Yoldas oynamiyor, YARDIM ediyor --------------------------------
    print("\n--- yoldas oynamiyor ---")
    from src.config import CHAIN
    check(COMPANION_DAMAGE < CHAIN[0].damage,
          "yoldasin hasari oyuncunun ILK vurusundan az - oldurme oyuncunun isi",
          f"{COMPANION_DAMAGE} < {CHAIN[0].damage}")
    check(COMPANION_LEASH > 0,
          "tasma var - odanin obur ucuna gitmiyor", str(COMPANION_LEASH))

    # --- 6. Plakalar: tek kisi ikisine birden basamaz ----------------------
    print("\n--- plakalar: bir kisi yetmiyor ---")
    gap = abs(TEACH_PLATE_A_TILE[0] - TEACH_PLATE_B_TILE[0]) * TILE_SIZE
    check(gap > 64,
          "ogretme plakalari birbirinden UZAK - tek kisi ikisine basamaz",
          f"{gap:.0f} px")
    arena_gap = abs(ARENA_PLATE_A_TILE[0] - ARENA_PLATE_B_TILE[0]) * TILE_SIZE
    check(arena_gap > 64, "arena plakalari da uzak", f"{arena_gap:.0f} px")

    plate_a, plate_b = scene.teach_plates
    place(scene.player, (TEACH_PLATE_A_TILE[0], TEACH_PLATE_A_TILE[1]))
    place(companion, (TEACH_PLATE_A_TILE[0] + 4, TEACH_PLATE_A_TILE[1]))
    companion.hold_x = None
    step(game, 4)
    check(plate_a.held and not plate_b.held,
          "tek kisi tek plaka basiyor")
    check(not scene.teach_gate.satisfied,
          "kapi acilmiyor - `all()`, bir tanesi yetmez")

    # --- 7. Ikisi birden basinca kapi aciliyor -----------------------------
    print("\n--- ikisi birlikte: kapi aciliyor ---")
    place(companion, (TEACH_PLATE_B_TILE[0], TEACH_PLATE_B_TILE[1]))
    companion.hold(plate_b.centre_x)
    step(game, 6)
    check(plate_a.held and plate_b.held, "iki plaka da basili")
    check(scene.teach_gate.open, "kapi ACILDI")

    # Bir kez acilan kapi acik kaliyor - plakadan inince tekrar kapanmak
    # oyuncuyu hapsedebilir ve "cozdum" hissini geri alirdi.
    place(scene.player, (TEACH_PLATE_A_TILE[0] - 6, TEACH_PLATE_A_TILE[1]))
    place(companion, (TEACH_PLATE_A_TILE[0] - 8, TEACH_PLATE_A_TILE[1]))
    companion.release()
    step(game, 40)
    check(scene.teach_gate.open, "kapi ACIK KALDI")

    # --- 8. Boss: muhur yalnizca plakalarla kiriliyor ----------------------
    print("\n--- BOSS 1: Faz 2 muhru ---")
    place(scene.player, (ROOM_STARTS[3][1] + 6, 14))
    step(game, 8)
    boss = scene.boss
    check(boss is not None, "boss dogdu")
    check(boss.phases == (0.62, 0.30), "iki faz gecisi", str(boss.phases))
    check(not boss.sealed, "Faz 0'da muhur YOK")

    # Faz 2'ye zorla
    boss.health = int(boss.max_health * 0.25)
    boss.on_phase_change(2)
    boss.phase = 2
    check(boss.sealed, "Faz 2'de muhur var")
    check(not boss.vulnerable, "muhurluyken vurulmuyor")

    before = boss.health
    hit = Hitbox(rect=boss.body.rect.copy(), damage=50, owner=scene.player,
                 targets=Team.ENEMY, active_frames=2)
    result = boss.take_damage(hit, (1.0, 0.0))
    check(not result.hit and boss.health == before,
          "hasar GECMIYOR (azalmiyor) - kural, sayi degil",
          f"{before} -> {boss.health}")

    # --- 9. Plakalar muhru kiriyor -----------------------------------------
    print("\n--- plakalar muhru kiriyor ---")
    place(scene.player, (ARENA_PLATE_A_TILE[0], ARENA_PLATE_A_TILE[1]))
    place(companion, (ARENA_PLATE_B_TILE[0], ARENA_PLATE_B_TILE[1]))
    companion.hold(scene.arena_plates[1].centre_x)
    step(game, 6)
    check(all(p.held for p in scene.arena_plates), "iki arena plakasi basili")
    check(boss.stun_frames > 0, "MUHUR KIRILDI", str(boss.stun_frames))
    check(boss.vulnerable, "artik vurulabiliyor")
    check(boss.stun_frames <= PLATE_STUN_FRAMES,
          "pencere sinirli - sonsuz degil")

    before = boss.health
    boss.take_damage(hit, (1.0, 0.0))
    check(boss.health < before, "pencerede hasar GECIYOR",
          f"{before} -> {boss.health}")

    # --- 10. Boss atlanamiyor ----------------------------------------------
    print("\n--- boss atlanamaz ---")
    exit_at = LEVEL.first("exit")
    scene.boss_defeated = False
    place(scene.player, (exit_at.tile_x, exit_at.tile_y + 1))
    step(game, 4)
    check(not scene.finished,
          "boss olmeden cikis calismiyor")

    game.shutdown()

    test_entrance()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Bolum 6: havali giris konusuyor, yoldas kanona uygun, "
          "plakalar beraberlik istiyor, boss atlanamiyor.")
    return 0


def test_entrance() -> None:
    """"Havali giris" - `docs/gdd.md` 10'un bastan istedigi sahne.

    Belgede vardi, kodda yoktu: kurtaris tek karede oluyordu ve oyuncu
    hicbir seyi goremiyordu (Arda, 30.08.2026: *"bahsettigim havali
    giris hic olmadi ve karakter tanitilmadi"*).

    Korunan kurallar:
      * Kurtaris **sahne aciyor** - artik tek kare degil
      * Roller kanondan: girisi SECMEDIGIN karakter yapiyor
      * Sahnede **replik var** - Arda'nin acik istegi, ve bir soru
        isareti kimin geldigini soylemiyor
      * Carpma karesinde hitstop var (`CLAUDE.md` 7'nin dili)
    """
    print("\n--- havali giris ---")
    from src.scenes.chapter06_cinematics import (
        ArdoEntranceCinematic, LANDING_FREEZE,
    )
    for played, saviour in (("rey", "ardo"), ("ardo", "rey")):
        game = Game()
        try:
            game.scenes.set_root(Chapter06Scene, transition=False,
                                 character=played)
            game.scenes._flush()
            scene = game.scenes.current
            scene._rescue()
            game.scenes._flush()
            top = game.scenes.current
            check(isinstance(top, ArdoEntranceCinematic),
                  f"{played}: kurtaris sinematik aciyor",
                  type(top).__name__)
            if not isinstance(top, ArdoEntranceCinematic):
                continue

            actor = top.actor("saviour")
            check(actor is not None and actor.animator.character == saviour,
                  f"{played} oynanirken girisi {saviour} yapiyor")
            check(top.actor("cornered").animator.character == played,
                  f"{played}: kosede oyuncu var")
            check(sum(1 for n in top.actor_order if n.startswith("creature"))
                  == 3, "uc yaratik sahnede")

            spoken = [p for p in top.panels if p.dialogue_lines]
            check(len(spoken) == 3, "uc replikli tanisma",
                  f"{len(spoken)} panel")
            speakers = {line.speaker for p in spoken
                        for line in p.dialogue_lines}
            check(speakers == {"rey", "ardo"},
                  "iki karakter de konusuyor", str(sorted(speakers)))

            landing = next(p for p in top.panels if p.name == "carpma")
            freeze = max(c.freeze for c in landing.cues)
            check(freeze == LANDING_FREEZE, "carpmada hitstop var",
                  f"{freeze} kare")

            # Sahne gercekten oynuyor ve ciziyor mu?
            for _ in range(140):
                game.input.begin_frame()
                game.input.end_frame()
                game.scenes.update()
                game.frame += 1
            game.canvas.fill((0, 0, 0))
            top.draw(game.canvas)
            painted = pygame.transform.average_color(game.canvas)[:3] != (0, 0, 0)
            check(painted, f"{played}: sahne ekrana ciziliyor")
        finally:
            game.shutdown()


raise SystemExit(main())
