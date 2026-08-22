"""Dusman AI dogrulamasi - Gorev 2.

Bu testlerin hepsi **oynanis hissiyle ilgili** kurallari koruyor. Hicbiri
"kod calisiyor mu" diye sormuyor; hepsi "dovus hala okunabilir mi" diye
soruyor:

  * Saldiri hakki      - ayni anda en fazla 2 saldirgan (BAGLAYICI)
  * Tell suresi        - her saldiri en az 14 kare once okunur (BAGLAYICI)
  * Ritim imzasi       - ayni tip her zaman ayni ritmi calar
  * Sendeleme          - poise kirilinca saldiri iptal olur
  * Ekoloji            - Sismek patlamasi diger dusmanlari da vurur
  * Can bari yok       - durum renk/siluetle okunur

Calistir:
    python tests/test_enemy.py
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

from src.combat.hitbox import Hitbox, Team  # noqa: E402
from src.config import (  # noqa: E402
    BLOATED_BLAST_DAMAGE, ENEMY_MIN_TELL_FRAMES, MAX_SIMULTANEOUS_ATTACKERS,
    SHAMBLER_BEAT_FRAMES, TILE_SIZE,
)
from src.core.game import Game  # noqa: E402
from src.entities.enemies.bloated import Bloated  # noqa: E402
from src.entities.enemies.climber import Climber  # noqa: E402
from src.entities.enemies.shambler import Shambler  # noqa: E402
from src.entities.enemy import Enemy, EnemyState  # noqa: E402
from src.scenes.combat_room import CombatRoomScene  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def make_scene(game: Game | None = None) -> tuple[Game, CombatRoomScene]:
    game = game or Game()
    game.scenes.set_root(CombatRoomScene, transition=False)
    game.scenes._flush()
    return game, game.scenes.current


def step(game, scene, count: int = 1) -> None:
    for _ in range(count):
        game.input.begin_frame()
        game.input.end_frame()
        scene.update()


def place(scene, cls, tile_x: float, tile_y: int = 12):
    return cls(scene, tile_x * TILE_SIZE + TILE_SIZE // 2,
               (tile_y + 1) * TILE_SIZE)


def main() -> int:
    # --- 1. Tell suresi (BAGLAYICI) -----------------------------------------
    print("--- tell suresi ---")
    for cls in (Shambler, Climber, Bloated):
        check(cls.tell_frames >= ENEMY_MIN_TELL_FRAMES,
              f"{cls.__name__}: tell >= {ENEMY_MIN_TELL_FRAMES} kare",
              f"{cls.tell_frames} kare")

    # Alt sinir kod duzeyinde de korunuyor mu? Yukleme aninda patlamali.
    try:
        class Cheater(Enemy):
            tell_frames = 6
        raised = False
    except ValueError:
        raised = True
    check(raised, "kisa tell tanimlamak yukleme aninda hata veriyor")

    # Kutu kipi hata ayiklama yolu oldugu icin normal oyunda hic cizilmiyor
    # ve oradaki bir hata fark edilmeden aylarca durabilir. `body_colour`
    # bir kez zincir adi ("rot") tutuyordu; zincir renk degil, kutu kipi ilk
    # acilista PaletteError ile cokuyordu.
    from src.art import palette
    for cls in (Shambler, Climber, Bloated, Enemy):
        try:
            palette.color(cls.body_colour)
            valid = True
        except palette.PaletteError:
            valid = False
        check(valid, f"{cls.__name__}.body_colour gecerli palet rengi",
              cls.body_colour)

    # --- 2. Saldiri hakki (BAGLAYICI) ---------------------------------------
    print("\n--- saldiri hakki ---")
    game, scene = make_scene()
    check(len(scene.enemies) >= 6, "oda kalabalik",
          f"{len(scene.enemies)} dusman")

    peak = 0
    attacking_peak = 0
    aware_peak = 0
    holders: set[int] = set()
    for _ in range(1200):
        # Oyuncuyu ayakta tut: hareketsiz oyuncu ~1250 karede oluyor ve
        # olunce kimse farkinda kalmiyor, yani olcum bos bir dunyayi
        # olcmeye baslıyordu. Burada sinanan sey hayatta kalma degil,
        # hakkin sira ile dagitilmasi.
        scene.player.health = scene.player.max_health
        scene.player.dead = False
        step(game, scene)
        for enemy in scene.enemies:
            if scene.tokens.holds(enemy):
                holders.add(id(enemy))
        peak = max(peak, scene.tokens.active_count)
        attacking = sum(1 for e in scene.enemies
                        if getattr(e, "state", None) in
                        (EnemyState.TELL, EnemyState.ATTACK))
        attacking_peak = max(attacking_peak, attacking)
        aware_peak = max(aware_peak,
                         sum(1 for e in scene.enemies
                             if getattr(e, "aware", False)))

    # Testin kendi kosulunu kurdugundan emin ol. Once dusmanlar odaya
    # yayilmisti ve altisinin ancak ikisi oyuncuyu goruyordu - yani asil
    # soru ("kalabalik okunabilir mi?") hic sorulmamis oluyordu. Bu kontrol
    # tezgahi bozan bir oda degisikligini yakalar.
    check(aware_peak >= 5, "kalabalik gercekten kuruldu",
          f"ayni anda {aware_peak} dusman farkinda")

    check(peak <= MAX_SIMULTANEOUS_ATTACKERS,
          f"hak sayisi hic {MAX_SIMULTANEOUS_ATTACKERS} asilmadi", str(peak))
    check(attacking_peak <= MAX_SIMULTANEOUS_ATTACKERS,
          f"ayni anda en fazla {MAX_SIMULTANEOUS_ATTACKERS} dusman saldiriyor",
          str(attacking_peak))
    check(peak >= 1, "hak gercekten dagitiliyor", str(peak))

    check(len(holders) >= 3, "hak birden fazla dusmana geciyor - sira donuyor",
          f"{len(holders)} farkli dusman")
    game.shutdown()

    # --- 3. Tell gercekten hitbox'tan once mu? ------------------------------
    print("\n--- tell hitbox'tan once ---")
    game, scene = make_scene()
    scene.enemies = [place(scene, Shambler, 8)]
    enemy = scene.enemies[0]
    scene.player.body.x = 7 * TILE_SIZE
    scene.tokens.clear()

    # Kutu listesini taramak yanlis olcum verir: hitbox degdigi karede
    # tukenip listeden dusuyor, yani "hic acilmamis" gibi gorunuyor.
    # Sahne kancalari tam acilis anini bildiriyor.
    marks: dict[str, int] = {}
    scene.on_enemy_tell = lambda e, m=marks: m.setdefault("tell", m["frame"])
    scene.on_enemy_attack = lambda e, m=marks: m.setdefault("attack", m["frame"])

    for frame in range(400):
        marks["frame"] = frame
        step(game, scene)
        if "attack" in marks:
            break
    tell_started = marks.get("tell")
    hitbox_frame = marks.get("attack")

    if tell_started is not None and hitbox_frame is not None:
        warning = hitbox_frame - tell_started
        check(warning >= ENEMY_MIN_TELL_FRAMES,
              "hitbox tell'den en az 14 kare sonra aciliyor",
              f"{warning} kare")
    else:
        check(False, "tell ve hitbox gozlemlendi",
              f"tell={tell_started} hitbox={hitbox_frame}")
    game.shutdown()

    # --- 4. Ritim imzasi determinist mi? ------------------------------------
    # Ayni kosullarda ayni tip ayni karede saldirmali. Rastgele saldiran
    # dusman ogrenilemez, sadece sinir bozar (docs/derinlestirme.md 4.2).
    print("\n--- ritim imzasi ---")
    first_attack_frames = []
    for _ in range(3):
        game, scene = make_scene()
        scene.enemies = [place(scene, Shambler, 8)]
        enemy = scene.enemies[0]
        scene.player.body.x = 7 * TILE_SIZE
        scene.tokens.clear()
        found = None
        for frame in range(400):
            step(game, scene)
            if enemy.state is EnemyState.ATTACK:
                found = frame
                break
        first_attack_frames.append(found)
        game.shutdown()

    check(len(set(first_attack_frames)) == 1 and first_attack_frames[0] is not None,
          "Suruklenen her denemede ayni karede saldiriyor",
          str(first_attack_frames))

    # Ritim gercekten bekliyor mu? Uc vuruslu ritim en az iki beat surer.
    if first_attack_frames[0] is not None:
        check(first_attack_frames[0] >= SHAMBLER_BEAT_FRAMES,
              "Suruklenen hemen saldirmiyor - ritmi bekliyor",
              f"{first_attack_frames[0]} kare")

    # --- 5. Sendeleme saldiriyi iptal ediyor mu? ----------------------------
    print("\n--- sendeleme saldiriyi iptal eder ---")
    game, scene = make_scene()
    scene.enemies = [place(scene, Shambler, 8)]
    enemy = scene.enemies[0]
    scene.player.body.x = 7 * TILE_SIZE
    scene.tokens.clear()
    for _ in range(400):
        step(game, scene)
        if enemy.state is EnemyState.TELL:
            break
    was_telling = enemy.state is EnemyState.TELL

    # Poise'i kiracak kadar vur.
    for _ in range(enemy.poise):
        enemy.take_damage(
            Hitbox(rect=enemy.body.rect.copy(), damage=1, owner=scene.player,
                   targets=Team.ENEMY, poise_damage=1),
            (1.0, 0.0))
    check(was_telling and enemy.state is EnemyState.STAGGER,
          "poise kirilinca tell iptal oldu", enemy.state.name)
    check(not scene.tokens.holds(enemy),
          "sendeleyen dusman hakki birakti - sira donuyor")
    game.shutdown()

    # --- 6. Ekoloji: Sismek patlamasi dusmanlari da vurur -------------------
    print("\n--- ekoloji: dost ates ---")
    game, scene = make_scene()
    bloated = place(scene, Bloated, 20)
    victim = place(scene, Shambler, 20.8)      # Patlama yaricapi icinde
    far = place(scene, Shambler, 30)           # Disinda
    scene.enemies = [bloated, victim, far]
    victim_health = victim.health
    far_health = far.health

    bloated._explode()
    scene.hitboxes.update({Team.ENEMY: scene.enemies,
                           Team.PLAYER: [scene.player]})

    check(victim.health < victim_health,
          "patlama yakindaki dusmani vurdu",
          f"{victim_health} -> {victim.health}")
    check(far.health == far_health,
          "uzaktaki dusman etkilenmedi", f"{far.health}")
    check(victim_health - victim.health == BLOATED_BLAST_DAMAGE,
          "patlama hasari config'den geliyor",
          str(victim_health - victim.health))

    # Oyuncuya da isliyor mu? Tek tarafli dost ates riski yok eder.
    game.shutdown()
    game, scene = make_scene()
    bloated = place(scene, Bloated, 20)
    scene.enemies = [bloated]
    scene.player.body.x = 20 * TILE_SIZE
    scene.player.body.y = bloated.body.y
    scene.player.iframes = 0
    before = scene.player.health
    bloated._explode()
    scene.hitboxes.update({Team.ENEMY: scene.enemies,
                           Team.PLAYER: [scene.player]})
    check(scene.player.health < before,
          "patlama oyuncuyu da vuruyor - risk gercek",
          f"{before} -> {scene.player.health}")
    game.shutdown()

    # --- 7. Fitil yanınca durmaz -------------------------------------------
    print("\n--- fitil yanınca durmaz ---")
    game, scene = make_scene()
    bloated = place(scene, Bloated, 20)
    scene.enemies = [bloated]
    scene.player.body.x = 20 * TILE_SIZE
    scene.tokens.clear()
    for _ in range(200):
        step(game, scene)
        if bloated.fuse_lit:
            break
    lit = bloated.fuse_lit
    # Sendeletmeye calis - fitil sonmemeli.
    for _ in range(bloated.poise * 2):
        if bloated.remove:
            break
        bloated.take_damage(
            Hitbox(rect=bloated.body.rect.copy(), damage=1, owner=scene.player,
                   targets=Team.ENEMY, poise_damage=1),
            (1.0, 0.0))
    check(lit and (bloated.fuse_lit or bloated.exploded),
          "yanan fitil sendelemeyle sonmuyor",
          f"lit={bloated.fuse_lit} patladi={bloated.exploded}")
    game.shutdown()

    # --- 8. Tirmanan tavanda bekliyor, altindan gecince dusuyor -------------
    print("\n--- tirmanan ---")
    game, scene = make_scene()
    climber = place(scene, Climber, 20, tile_y=3)
    scene.enemies = [climber]
    scene.tokens.clear()
    scene.player.body.x = 5 * TILE_SIZE       # Uzakta
    start_y = climber.body.y
    step(game, scene, 60)
    check(climber.hanging and abs(climber.body.y - start_y) < 1.0,
          "uzaktayken tavanda asili kaliyor",
          f"y={climber.body.y:.1f}")

    scene.player.body.x = climber.body.center_x - 4   # Tam altina gel
    scene.player.body.y = 11 * TILE_SIZE
    dropped_at = None
    for frame in range(200):
        step(game, scene)
        if not climber.hanging:
            dropped_at = frame
            break
    check(dropped_at is not None, "oyuncu altindan gecince birakiyor",
          f"{dropped_at} kare")
    if dropped_at is not None:
        check(dropped_at >= Climber.tell_frames,
              "birakmadan once telegraf var",
              f"{dropped_at} >= {Climber.tell_frames}")
    game.shutdown()

    # --- 9. Can bari yok ----------------------------------------------------
    print("\n--- can bari yok ---")
    source = (ROOT / "src" / "entities" / "enemy_render.py").read_text(
        encoding="utf-8")
    check("health_bar" not in source and "_draw_health_bar" not in source,
          "dusman cizimi can bari cizmiyor (CLAUDE.md 7)")
    # Durum bilgisi baska kanallardan geliyor mu?
    check("silhouette_scale" in
          (ROOT / "src" / "entities" / "enemy.py").read_text(encoding="utf-8"),
          "durum siluetle de anlatiliyor - renk korlugu icin sart")

    # --- 10b. Dikey erisim - "ust platformlara sikisma" hatasi --------------
    # Arda'nin bildirdigi hata: bir dusman kopuk bir platforma cikinca
    # (guclu knockback_up, ya da bolum tasariminda bir yukselti), oyuncu
    # TAM ALTINDAYSA yatay mesafe hep kucuk kaliyor ve dusman erisemeyecegi
    # bir hedefe sonsuza dek TELL/ATTACK denemesi yapiyordu.
    print("\n--- dikey erisim (ust platforma sikisma) ---")
    game, scene = make_scene()
    # `combat_room.py`'nin gercek "ust kat" platformu: satir 7, sutun 18-21.
    # Basilabilir satir 6 - `place()` "tile_y+1" satirina ayak koyar.
    stuck = place(scene, Shambler, 19, tile_y=6)
    scene.enemies = [stuck]
    scene.tokens.clear()
    scene.player.body.x = stuck.body.center_x - stuck.body.width * 0.5
    scene.player.body.y = 12 * TILE_SIZE             # Zeminde - 6 tile asagida
    start_y = stuck.body.y
    bad_states = 0
    for _ in range(600):
        step(game, scene)
        if stuck.state in (EnemyState.TELL, EnemyState.ATTACK):
            bad_states += 1
    check(stuck.aware, "dusman oyuncunun farkina variyor (goruş bozulmadi)")
    check(bad_states == 0,
          "erisilemez hedefe TELL/ATTACK denemesi YAPMIYOR",
          f"{bad_states} kare TELL/ATTACK durumunda")
    check(abs(stuck.body.y - start_y) < 2.0,
          "dusman platformdan dusmuyor - saglam zeminde kaliyor",
          f"y={stuck.body.y:.1f} (baslangic {start_y:.1f})")
    game.shutdown()

    # Ayni oyuncu SEVIYEDEYSE saldiri hala calismali - fix'in asiri
    # kisitlayici olmadigini dogrular.
    game, scene = make_scene()
    reachable = place(scene, Shambler, 20, tile_y=12)
    scene.enemies = [reachable]
    scene.tokens.clear()
    scene.player.body.x = reachable.body.center_x - reachable.body.width * 0.5
    scene.player.body.y = 12 * TILE_SIZE
    attacked = False
    for _ in range(400):
        step(game, scene)
        if reachable.state is EnemyState.ATTACK:
            attacked = True
            break
    check(attacked, "ayni seviyedeyken saldiri hala calisiyor (fix asiri kisitlamiyor)")
    game.shutdown()

    # --- 10. Kalicilik ------------------------------------------------------
    print("\n--- kalici izler ---")
    game, scene = make_scene()
    before = scene.decals.count
    scene.decals.splatter(100, 100, amount=8)
    after_splat = scene.decals.count
    step(game, scene, 120)
    check(after_splat > before, "leke ekleniyor", f"{before} -> {after_splat}")
    check(scene.decals.count == after_splat,
          "lekeler zamanla silinmiyor - bolum boyunca kaliyor",
          str(scene.decals.count))
    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Dusman AI belgedeki kurallara uyuyor.")
    return 0


pygame.init()
raise SystemExit(main())
