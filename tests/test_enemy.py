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
    BLOATED_BLAST_DAMAGE, CLIMBER_PATIENCE_FRAMES,
    ENEMY_UNREACHABLE_PATIENCE_FRAMES, ENEMY_MIN_TELL_FRAMES,
    MAX_SIMULTANEOUS_ATTACKERS, SHAMBLER_BEAT_FRAMES, TILE_SIZE,
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


# Tek Game, defalarca sahne. `Game.shutdown()` `pygame.quit()` cagiriyor
# ve bu makinede bir sonraki `pygame.init()` 40 SANIYE suruyor (olculdu
# 23.08.2026; kodla ilgisi yok, SDL yeniden baslatma maliyeti). Bu dosya
# 17 kez kapatip aciyordu - tek basina 11 dakika. Sahne durumu zaten
# `set_root` ile sifirlaniyor, Game'i tazelemeye gerek yok.
_GAME: Game | None = None


def make_scene(game: Game | None = None) -> tuple[Game, CombatRoomScene]:
    global _GAME
    if _GAME is None:
        _GAME = Game()
    _GAME.scenes.set_root(CombatRoomScene, transition=False)
    _GAME.scenes._flush()
    return _GAME, _GAME.scenes.current


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

    # --- 8b. Tirmanan - oyuncu hic tam altina girmezse "sabir" ile birakir --
    # Arda'nin canli oynanis geri bildirimi: oda duzeni oyuncuyu Tirmanan'in
    # tam altindan gecirmeyebilir - o zaman sonsuza kadar tavanda "yapisik"
    # kaliyordu. Oyuncu yakinken (farkinda) ama hic tam altina girmeden.
    print("\n--- tirmanan (sabir ile birakma) ---")
    game, scene = make_scene()
    climber = place(scene, Climber, 20, tile_y=3)
    scene.enemies = [climber]
    scene.tokens.clear()
    # Yakinda ama YANINDA duruyor, tam altinda degil - overhead_player
    # hep False kalsin diye CLIMBER_TRIGGER_X'in disinda ama
    # ENEMY_SIGHT_RANGE icinde.
    scene.player.body.x = climber.body.center_x + 60
    scene.player.body.y = climber.body.y
    patient_dropped_at = None
    for frame in range(CLIMBER_PATIENCE_FRAMES + Climber.tell_frames + 20):
        step(game, scene)
        if frame == 0:
            check(not climber.overhead_player,
                  "test kurulumu: oyuncu hic tam altina girmiyor")
        if not climber.hanging:
            # `frame` 0-indeksli - bu noktada gerceklesmis GUNCELLEME
            # sayisi `frame + 1`. Artik sabir dususu token beklemeden
            # ANINDA gerceklesiyor (eskiden araya bir TELL suresi
            # giriyordu ve bu +1 fark hicbir zaman fark edilmiyordu).
            patient_dropped_at = frame + 1
            break
    check(patient_dropped_at is not None,
          "oyuncu hic tam altina girmese de sabir esiginde birakiyor",
          f"{patient_dropped_at}")
    if patient_dropped_at is not None:
        check(patient_dropped_at >= CLIMBER_PATIENCE_FRAMES,
              "sabir esiginden ONCE birakmiyor (erken tetiklenmiyor)",
              f"{patient_dropped_at} >= {CLIMBER_PATIENCE_FRAMES}")

    # --- 8c. Tirmanan - saldiri hakki HICBIR ZAMAN yok, yine de birakir -----
    # 8b, `tokens.clear()` ile bos bir yonetici kullaniyor ve odada TEK
    # Tirmanan var - hakki hep bedavadan aliyordu. Gercek oyunda ayni oda
    # ayni anda birden fazla dusman barindirinca (Arda'nin ekran goruntusu:
    # dorduncu dusman ayni ekranda) hak MAX_SIMULTANEOUS_ATTACKERS(2) ile
    # sinirli. Sabir dususu hakka bagli olsaydi (eski kod: `(overhead or
    # patient) and tokens.request(...)`) hak surekli baskalarinda kalabilir
    # ve sabir hicbir sey garanti etmezdi - "hala yukarida" hatasinin asil
    # kaynagi buydu. Bu sahte yonetici hakki **hicbir zaman** vermeyerek o
    # senaryoyu belirsizliksiz kurar (gercek yoneticinin kendi zaman-asimi
    # TOKEN_HOLD_MAX_FRAMES=150, CLIMBER_PATIENCE_FRAMES=150 ile ayni kareye
    # denk geldigi icin gercek yoneticiyle bu ayrimi net kurmak zor olurdu).
    class _NeverAvailable:
        def request(self, enemy: object) -> bool:
            return False

        def release(self, enemy: object, cooldown: int = 0) -> None:
            pass

        def force_release(self, enemy: object, cooldown: int = 0) -> None:
            pass

        def update(self) -> None:
            pass

        def clear(self) -> None:
            pass

        @property
        def active_count(self) -> int:
            return 0

    print("\n--- tirmanan (saldiri hakki hic verilmese de sabirla birakir) ---")
    game, scene = make_scene()
    climber = place(scene, Climber, 20, tile_y=3)
    scene.enemies = [climber]
    scene.tokens = _NeverAvailable()
    scene.player.body.x = climber.body.center_x + 60   # aware ama tam altinda degil
    scene.player.body.y = climber.body.y
    never_dropped_at = None
    for frame in range(CLIMBER_PATIENCE_FRAMES + 30):
        step(game, scene)
        if not climber.hanging:
            never_dropped_at = frame
            break
    check(never_dropped_at is not None,
          "saldiri hakki hicbir zaman yokken de sabir esiginde birakiyor",
          f"{never_dropped_at}")
    if never_dropped_at is not None:
        check(climber.state is not EnemyState.TELL,
              "bu birakma bir saldiri TELL'i degil - hakka bagli olmayan dogrudan dusme",
              f"state={climber.state}")

    # --- 8d. Tirmanan - surekli isiktan kacsa da sabir esiginde birakir -----
    # `_fleeing_light` sabir sayacindan ONCE `return` ediyordu (Bolum 3 Oda
    # 3 bulmacasinda statik yakilan mesaleler icin eklendi). Kacis yonu
    # oyuncunun konumundan turetiliyor, isik kaynaginin konumundan degil -
    # oyuncu pek hareket etmezse Tirmanan isik yaricapindan hic cikamayabilir
    # ve sayac hic baslamadigi icin sonsuza dek kacar - 8b/8c'nin kanitladigi
    # garantiyi bu tek dal delip geciyordu. Bu test statik, hareket etmeyen
    # bir isik kaynagiyla (Tirmanan'in tam ustunde, genis yaricap - kacis asla
    # disina cikmaz) sabir sayacinin yine de isleyip esik dolunca dustugunu
    # dogruluyor.
    from src.systems.light import LightState  # noqa: E402 (yalnizca bu testte)

    print("\n--- tirmanan (surekli isiktan kacsa da sabirla birakir) ---")
    game, scene = make_scene()
    climber = place(scene, Climber, 20, tile_y=3)
    scene.enemies = [climber]
    scene.tokens.clear()
    scene.light = LightState()
    scene.light.set_static("test_mesale", climber.body.center_x,
                            climber.body.center_y, 200.0)
    scene.player.body.x = climber.body.center_x   # oyuncu hic hareket etmiyor
    scene.player.body.y = climber.body.y
    check(climber._fleeing_light,
          "test kurulumu: Tirmanan isiktan kaciyor")
    fled_dropped_at = None
    for frame in range(CLIMBER_PATIENCE_FRAMES + 30):
        step(game, scene)
        if not climber.hanging:
            fled_dropped_at = frame
            break
    check(fled_dropped_at is not None,
          "surekli isiktan kacsa bile sabir esiginde birakiyor",
          f"{fled_dropped_at}")
    if fled_dropped_at is not None:
        check(fled_dropped_at + 1 >= CLIMBER_PATIENCE_FRAMES,
              "sabir esiginden ONCE birakmiyor (erken tetiklenmiyor)",
              f"{fled_dropped_at + 1} >= {CLIMBER_PATIENCE_FRAMES}")

    # --- 8e. Tirmanan - isiktan kacarken vurulursa yine de ANINDA duser -----
    # `_fleeing_light` STAGGER/TELL kontrolunden ONCE `return` ediyordu -
    # isik alaninda vurulan bir Tirmanan "yukarida kalip sikismasin" diye
    # var olan STAGGER-de-aninda-dusme garantisini (docstring: "Asiliyken
    # vurulursa duser") kacirip sabir esigine kadar (150 kare) asili
    # kalabiliyordu. Bu test isik alani icindeyken poise'ini kirip ayni
    # karede/hemen sonraki karede dustugunu dogruluyor - 150 kare
    # beklenmiyor.
    print("\n--- tirmanan (isiktan kacarken vurulursa aninda duser) ---")
    game, scene = make_scene()
    climber = place(scene, Climber, 20, tile_y=3)
    scene.enemies = [climber]
    scene.tokens.clear()
    scene.light = LightState()
    scene.light.set_static("test_mesale", climber.body.center_x,
                            climber.body.center_y, 200.0)
    scene.player.body.x = climber.body.center_x
    scene.player.body.y = climber.body.y
    check(climber._fleeing_light,
          "test kurulumu: Tirmanan isiktan kaciyor")
    for _ in range(climber.poise):
        climber.take_damage(
            Hitbox(rect=climber.body.rect.copy(), damage=1, owner=scene.player,
                   targets=Team.ENEMY, poise_damage=1),
            (1.0, 0.0))
    check(climber.state is EnemyState.STAGGER,
          "test kurulumu: poise kirildi, STAGGER'da")
    step(game, scene)
    check(not climber.hanging,
          "isiktan kacarken vurulan Tirmanan sabir beklemeden aninda duser",
          f"hanging={climber.hanging}")

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
    #
    # Ikinci tur (Arda'nin "hala yapisik" geri bildirimi, 22.08.2026): bosuna
    # saldirmamak yetmiyordu - dusman sonsuza dek yukarida bekleyebiliyordu.
    # Simdi sabir esigi (ENEMY_UNREACHABLE_PATIENCE_FRAMES) dolunca en yakin
    # kenari arayip oradan iniyor.
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

    # Once: sabir esigine kadar ne bosuna saldirir ne de kipirdar.
    bad_states = 0
    for _ in range(ENEMY_UNREACHABLE_PATIENCE_FRAMES - 10):
        step(game, scene)
        if stuck.state in (EnemyState.TELL, EnemyState.ATTACK):
            bad_states += 1
    check(stuck.aware, "dusman oyuncunun farkina variyor (goruş bozulmadi)")
    check(bad_states == 0,
          "sabir esigine kadar erisilemez hedefe TELL/ATTACK denemesi YAPMIYOR",
          f"{bad_states} kare TELL/ATTACK durumunda")
    check(abs(stuck.body.y - start_y) < 2.0,
          "sabir esigine kadar platformdan dusmuyor",
          f"y={stuck.body.y:.1f} (baslangic {start_y:.1f})")

    # Sonra: sabir dolunca kenari bulup iniyor - sonsuza dek "yapisik" kalmiyor.
    for _ in range(600):
        step(game, scene)
        if stuck.body.y > start_y + 4.0:
            break
    check(stuck.body.y > start_y + 4.0,
          "sabir dolunca en yakin kenari bulup platformdan iniyor",
          f"y={stuck.body.y:.1f} (baslangic {start_y:.1f})")

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

    # --- 10c. Dikey erisim - oyuncuyu HIC gormeden kopuk platformdan iner ---
    # 10b'nin ayni-sinif ikizi: onceki sayac yalnizca `_approach()` icinde,
    # yani dusman zaten APPROACH durumundaysa (`aware` VE saldiri hakki
    # varken) isliyordu. Bolum duzeni oyuncuyu bir dusmanin gorus menzili
    # icine hic sokmayabilir (orn. baska bir koridordan gecer) - o zaman
    # sayac hic baslamiyor ve dusman kopuk bir platformda gorunur sekilde
    # sonsuza dek kaliyordu. Simdi erisilebilirlik farkindaliktan BAGIMSIZ
    # olculuyor (bkz. enemy.py::_update_reachability).
    print("\n--- dikey erisim (hic farkinda olmadan kopuk platformdan iner) ---")
    game, scene = make_scene()
    # Orta kat sol parcasi: satir 10, sutun 14-17 - iki yani da bosluk.
    stray = place(scene, Shambler, 15, tile_y=9)
    scene.enemies = [stray]
    scene.tokens.clear()
    scene.player.body.x = 40 * TILE_SIZE      # Cok uzakta - gorus menzili disi
    scene.player.body.y = 12 * TILE_SIZE
    check(not stray._vertically_reachable(scene.player),
          "test kurulumu: oyuncu dikeyde erisilemez")
    start_y = stray.body.y
    left_at = None
    was_ever_aware = False
    for frame in range(ENEMY_UNREACHABLE_PATIENCE_FRAMES + 90):
        step(game, scene)
        was_ever_aware = was_ever_aware or stray.aware
        if stray.body.y > start_y + 4.0:
            left_at = frame
            break
    check(left_at is not None,
          "oyuncuyu hic gormeden de kopuk platformdan inmeye basliyor",
          f"{left_at} kare")
    check(not was_ever_aware,
          "test kurulumu: dusman hic 'farkinda' olmadi - yalnizca sabirla indi",
          f"aware={was_ever_aware}")

    # --- 11. Sonmus Olan - "surukleme" hamlesi ATTACK'ta kilitlenmiyor ------
    # `ExtinguishedOne._think()`'in eski hali `state is ATTACK and
    # move=="drag"` oldugunda `super()._think()`'i HIC cagirmadan
    # donuyordu. Tabanin ATTACK dalinin yaptigi iki sey - hitbox'i acan
    # `_spawn_attack()` ve `active_frames` sonrasi RECOVER'a gecis -
    # hicbir zaman calismiyordu. `MOVES` dizisinde "surukleme" iki kez var
    # (4 hamlenin 2'si) - boss'un ilk birkac saldirisindan biri kacinilmaz
    # olarak bu hamleye denk gelip ATTACK'ta sonsuza dek kilitleniyordu
    # (hicbir hasar vermeden, hicbir yere gecmeden) - mini-boss dovusu
    # tamamen oynanmaz hale geliyordu.
    from src.entities.enemies.extinguished_one import (  # noqa: E402
        DRAG_ACTIVE, DRAG_RECOVER, ExtinguishedOne,
    )

    print("\n--- sonmus olan (surukleme ATTACK'ta kilitlenmiyor) ---")
    game, scene = make_scene()
    boss = ExtinguishedOne(scene, 20 * TILE_SIZE, 13 * TILE_SIZE)
    scene.enemies = [boss]
    scene.tokens.clear()
    boss.move_index = 1              # _next_move() -> "drag" ilk hamle olsun
    boss._begin_tell()
    check(boss.move == "drag", "test kurulumu: ilk hamle 'surukleme'")
    for _ in range(boss.tell_frames):
        step(game, scene)
    check(boss.state is EnemyState.ATTACK,
          "tell bitince ATTACK'a geciyor", f"state={boss.state}")
    boxes_before = len(scene.hitboxes.boxes)
    step(game, scene)                # spawn karesi - attack_spawned burada True olur
    check(len(scene.hitboxes.boxes) > boxes_before,
          "surukleme hitbox'i gercekten aciliyor (_spawn_attack calisti)",
          f"{boxes_before} -> {len(scene.hitboxes.boxes)}")
    stuck = True
    for _ in range(DRAG_ACTIVE + DRAG_RECOVER + 5):
        step(game, scene)
        if boss.state is not EnemyState.ATTACK:
            stuck = False
            break
    check(not stuck,
          "surukleme ATTACK'ta sonsuza dek kilitlenmiyor - RECOVER/ORBIT'e geciyor",
          f"state={boss.state}")

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

    if _GAME is not None:
        _GAME.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Dusman AI belgedeki kurallara uyuyor.")
    return 0


# `pygame.init()` DEGIL. O, joystick alt sistemini de acar ve bu
# makinede 40 SANIYE surer (olculdu 30.08.2026 - bir surucu sorunu,
# kodla ilgisi yok). 21 test paketi bunu ayri ayri odedigi icin butun
# paket 14 dakikayi asiyordu.
#
# `src/core/game.py` de tam olarak bu yolu izliyor; test oyunla ayni
# sekilde acilsin. Ses gerekirse `synth.init_mixer()` cagrilir.
pygame.display.init()
pygame.font.init()
raise SystemExit(main())
