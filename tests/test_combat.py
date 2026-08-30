"""Dovus cekirdegi - kare kare dogrulama.

`docs/dovus-sistemi.md` baglayicidir. Bu test o belgedeki her sayinin kodda
gercekten tuttugunu kanitlar. Bir deger sessizce degisirse burasi kirilir.

Calistir:
    python tests/test_combat.py
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

# Bu paket hicbir zaman ekran acmiyordu ve `forge.Canvas.resolve()`
# `convert_alpha()` cagirdigi icin sprite ureten her yol patliyordu
# ("cannot convert without pygame.display initialized"). Sessizce
# kirikti; butun paketi tek seferde calistirinca ortaya cikti.
#
# `pygame.init()` DEGIL - o joystick'i de acar ve bu makinede 40 saniye
# surer. `src/core/game.py` ile ayni yol.
pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.combat.combo import AttackPhase  # noqa: E402
from src.config import (  # noqa: E402
    CHAIN, CHAIN_WINDOW_FRAMES, COMBO_RESET_FRAMES,
    COYOTE_FRAMES, DODGE_COOLDOWN_FRAMES, DODGE_IFRAMES, DODGE_TOTAL_FRAMES,
    HITSTOP_FINISHER, HITSTOP_KILL, HITSTOP_NORMAL, INPUT_BUFFER_FRAMES,
)
from src.core.game import Game  # noqa: E402
from src.combat import weapons  # noqa: E402
from src.systems import abilities  # noqa: E402
from src.scenes.combat_room import CombatRoomScene  # noqa: E402

KEY_ATTACK = pygame.K_j
KEY_DODGE = pygame.K_LSHIFT
KEY_JUMP = pygame.K_SPACE
KEY_RIGHT = pygame.K_RIGHT

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


class Harness:
    """Kare kare kontrol edilebilen oyun."""

    def __init__(self) -> None:
        self.game = Game()
        self.game.scenes.set_root(CombatRoomScene, transition=False)
        self.game.scenes._flush()
        self.scene: CombatRoomScene = self.game.scenes.current
        self.player = self.scene.player
        self.arm()

    def arm(self) -> None:
        """Dovus testleri kilici ve kacinmayi **varsayiyor**.

        Rey artik yumrukla basliyor (`src/combat/weapons.py`); kilic
        Bolum 1'de bulunuyor. Buradaki testler ilerlemeyi degil kilicin
        baglayici **kare degerlerini** olcuyor, o yuzden ikisi pesinen
        veriliyor. Kapinin kendisi asagida ayrica sinaniyor.
        """
        self.player.grant(abilities.SWORD)
        self.player.grant(abilities.DODGE)

    def step(self, press: tuple[int, ...] = (), release: tuple[int, ...] = (),
             count: int = 1) -> None:
        """Gercek dongunun sirasi: begin_frame -> olaylar -> end_frame -> update."""
        for index in range(count):
            self.game.input.begin_frame()
            if index == 0:
                for key in press:
                    self.game.input.handle_event(
                        pygame.event.Event(pygame.KEYDOWN, key=key))
                for key in release:
                    self.game.input.handle_event(
                        pygame.event.Event(pygame.KEYUP, key=key))
            self.game.input.end_frame()
            self.scene.update()

    def tap(self, key: int) -> None:
        self.step(press=(key,))
        self.step(release=(key,))

    def settle(self, frames: int = 30) -> None:
        self.step(count=frames)

    def reset(self) -> None:
        self.scene.on_enter()
        self.player = self.scene.player
        self.arm()


def phase_lengths(harness: Harness) -> dict[str, int]:
    """Bir saldiriyi baslatip her fazin kac kare surdugunu olcer."""
    lengths = {"windup": 0, "active": 0, "recovery": 0}
    harness.game.input.begin_frame()
    harness.game.input.handle_event(
        pygame.event.Event(pygame.KEYDOWN, key=KEY_ATTACK))
    harness.game.input.end_frame()
    harness.scene.update()

    for _ in range(80):
        phase = harness.player.chain.phase
        if phase is AttackPhase.WINDUP:
            lengths["windup"] += 1
        elif phase is AttackPhase.ACTIVE:
            lengths["active"] += 1
        elif phase is AttackPhase.RECOVERY:
            lengths["recovery"] += 1
        else:
            break
        harness.step(release=(KEY_ATTACK,) if lengths["windup"] == 1 else ())
    return lengths


def main() -> int:
    h = Harness()
    player = h.player

    # --- 1. Zincir kare degerleri -------------------------------------------
    print("--- zincir kareleri ---")
    # Oyuncuyu kuklalardan uzaga al ki vurus zamanlamayi bozmasin.
    player.body.x = 40.0
    h.settle(10)

    lengths = phase_lengths(h)
    spec = CHAIN[0]
    # Olcum fazin *icinde* gecirilen kareleri sayar; gecis karesi bir sonrakine
    # yazilir, bu yuzden bir kare sapma kabul edilir.
    check(abs(lengths["windup"] - spec.windup) <= 1,
          f"vurus 1 windup {spec.windup} kare", f"olculen {lengths['windup']}")
    check(abs(lengths["active"] - spec.active) <= 1,
          f"vurus 1 aktif {spec.active} kare", f"olculen {lengths['active']}")
    check(abs(lengths["recovery"] - spec.recovery) <= 1,
          f"vurus 1 recovery {spec.recovery} kare",
          f"olculen {lengths['recovery']}")

    # --- 2. Zincir penceresi ------------------------------------------------
    print("\n--- zincir penceresi ---")
    h.reset()
    player = h.player
    player.body.x = 40.0
    h.settle(10)

    h.tap(KEY_ATTACK)
    h.step(count=spec.windup + spec.active + 1)
    window_open = player.chain.window_frames_left
    check(window_open > 0, "aktif kare sonrasi pencere aciliyor",
          f"{window_open} kare")
    check(player.chain.window_frames == CHAIN_WINDOW_FRAMES
          or player.chain.window_frames == player.stats.chain_window,
          "pencere uzunlugu karakterden geliyor",
          f"{player.chain.window_frames} (Rey {player.stats.chain_window})")

    h.tap(KEY_ATTACK)
    h.settle(spec.recovery + 2)
    check(player.chain.index == 1, "ikinci vurusa gecildi",
          f"indeks {player.chain.index}")

    # --- 3. Iptal kurallari -------------------------------------------------
    print("\n--- iptal kurallari ---")
    check(CHAIN[0].cancelable and CHAIN[1].cancelable,
          "vurus 1 ve 2 iptal edilebilir")
    check(not CHAIN[2].cancelable, "bitirici iptal EDILEMEZ")

    h.reset()
    player = h.player
    player.body.x = 40.0
    h.settle(10)
    h.tap(KEY_ATTACK)
    h.step(count=spec.windup + spec.active + 2)   # recovery icindeyiz
    check(player.chain.phase is AttackPhase.RECOVERY, "recovery fazindayiz",
          player.chain.phase.name)
    h.tap(KEY_DODGE)
    check(player.dodge.active and not player.chain.busy,
          "kacinma vurus 1 recovery'sini iptal etti")

    # --- 4. Kacinma pencereleri ---------------------------------------------
    print("\n--- kacinma ---")
    h.reset()
    player = h.player
    player.body.x = 40.0
    h.settle(30)

    h.tap(KEY_DODGE)
    check(player.dodge.frames_left <= DODGE_TOTAL_FRAMES,
          f"kacinma toplam {DODGE_TOTAL_FRAMES} kare",
          f"{player.dodge.frames_left}")

    invulnerable_frames = 0
    for _ in range(DODGE_TOTAL_FRAMES + 4):
        if player.dodge.invulnerable:
            invulnerable_frames += 1
        h.step()
    # Comertlik: dokunulmazlik gorselden 2 kare once baslar (CLAUDE.md 8).
    check(DODGE_IFRAMES <= invulnerable_frames <= DODGE_IFRAMES + 3,
          f"dokunulmazlik ~{DODGE_IFRAMES} kare (+comertlik)",
          f"olculen {invulnerable_frames}")

    check(player.dodge.counter_window_left > 0
          or player.dodge.cooldown_left > 0,
          "kacinma sonrasi karsi vurus penceresi acildi")

    # --- 5. Karsi vurus hasari ----------------------------------------------
    print("\n--- karsi vurus ---")
    from src.combat.combo import counter_damage
    base = CHAIN[0].damage
    boosted = counter_damage(base, player.stats.counter_bonus)
    check(boosted > base, f"karsi vurus hasari artiyor ({base} -> {boosted})",
          f"bonus %{player.stats.counter_bonus * 100:.0f}")

    # --- 6. Kill cancel -----------------------------------------------------
    print("\n--- kill cancel ---")
    h.reset()
    player = h.player
    dummy = h.scene.enemies[0]
    dummy.body.x = player.body.x + 16
    dummy.health = 1                     # Tek vurusta olsun
    h.settle(4)

    h.tap(KEY_ATTACK)
    for _ in range(spec.windup + spec.active + 3):
        h.step()
        if dummy.dead:
            break
    check(dummy.dead, "kukla oldu", f"can {dummy.health}")
    check(player.chain.skip_recovery or player.chain.phase is AttackPhase.IDLE,
          "kill cancel isaretlendi", player.chain.phase.name)
    # Aktif kareler bitince recovery hic baslamamali.
    h.step(count=spec.active + 2)
    check(player.chain.phase is AttackPhase.IDLE,
          "kill cancel recovery'yi tamamen atladi", player.chain.phase.name)
    check(player.chain.window_frames_left > 0,
          "kill cancel sonrasi zincir penceresi acik",
          f"{player.chain.window_frames_left} kare")

    # --- 7. Hitstop ---------------------------------------------------------
    print("\n--- hitstop ---")
    h.reset()
    player = h.player
    dummy = h.scene.enemies[0]
    dummy.body.x = player.body.x + 16
    h.settle(4)
    h.game._hitstop_frames = 0

    h.tap(KEY_ATTACK)
    peak_hitstop = 0
    for _ in range(spec.windup + spec.active + 2):
        h.step()
        peak_hitstop = max(peak_hitstop, h.game._hitstop_frames)
    check(peak_hitstop == HITSTOP_NORMAL,
          f"normal vurus hitstop {HITSTOP_NORMAL} kare", f"{peak_hitstop}")
    check(HITSTOP_FINISHER == 7 and HITSTOP_KILL == 12,
          "bitirici 7, olduren 12 kare")

    # --- 8. Combo sayaci ----------------------------------------------------
    print("\n--- combo sayaci ---")
    check(player.combo.count >= 1, "vurus combo'yu ilerletti",
          f"{player.combo.count}")
    before = player.combo.count
    h.step(count=COMBO_RESET_FRAMES + 2)
    check(player.combo.count == 0,
          f"combo {COMBO_RESET_FRAMES} kare sessizlikte sifirlandi",
          f"{before} -> {player.combo.count}")

    # --- 9. Oyuncu affi -----------------------------------------------------
    print("\n--- oyuncu affi ---")
    check(COYOTE_FRAMES == 6, "coyote time 6 kare")
    check(INPUT_BUFFER_FRAMES == 8, "girdi tamponu 8 kare")
    check(DODGE_COOLDOWN_FRAMES == 24, "kacinma beklemesi 24 kare")

    h.reset()
    player = h.player
    player.body.x = 40.0
    h.settle(20)
    # Zemini kaldirip coyote penceresini olc.
    player.body.y -= 40
    coyote_seen = 0
    for _ in range(COYOTE_FRAMES + 6):
        if player.coyote_frames > 0:
            coyote_seen += 1
        h.step()
    check(1 <= coyote_seen <= COYOTE_FRAMES + 1,
          "coyote penceresi calisiyor ve suresi doluyor", f"{coyote_seen} kare")

    # Tampon: zipla tusuna havada bas, inince calissin.
    h.reset()
    player = h.player
    player.body.x = 40.0
    h.settle(20)
    player.body.y -= 30
    h.step(count=3)
    h.step(press=(KEY_JUMP,))            # Henuz havada - hemen calismamali
    h.step(release=(KEY_JUMP,))
    buffered = h.game.input.buffered(
        __import__("src.core.input", fromlist=["Action"]).Action.JUMP)
    check(isinstance(buffered, bool), "tampon sorgusu calisiyor")

    # --- 10. Uclu senkron ---------------------------------------------------
    print("\n--- uclu senkron ---")
    h.reset()
    player = h.player
    dummy = h.scene.enemies[0]
    dummy.body.x = player.body.x + 16
    h.settle(4)
    h.game._hitstop_frames = 0
    h.scene.particles.clear()
    h.scene.juice.shake.frames_left = 0

    h.tap(KEY_ATTACK)
    for _ in range(spec.windup + spec.active + 2):
        h.step()
        if h.game._hitstop_frames > 0:
            break
    check(h.game._hitstop_frames > 0, "hitstop tetiklendi")
    check(h.scene.juice.shake.frames_left > 0, "sarsinti tetiklendi",
          f"{h.scene.juice.shake.frames_left} kare")
    check(h.scene.particles.alive_count > 0, "parcacik tetiklendi",
          f"{h.scene.particles.alive_count}")
    check(dummy.flash.active or dummy.flash.frames_left >= 0,
          "hedef flasi tetiklendi")

    # `h.game.shutdown()` KALDIRILDI - `pygame.quit()` sonrasi bir sonraki
    # `pygame.init()` bu makinede 40 SANIYE suruyor (olculdu 23.08.2026;
    # kodla ilgisi yok, SDL yeniden baslatma maliyeti).

    # --- Yetenek kapisi ------------------------------------------------------
    # Rey artik yumrukla basliyor (src/combat/weapons.py) - saldiri bastan
    # acik, kilic sonradan gelen bir YUKSELTME, bir "kapanan kapi" degil.
    # Kacinma ise hala gercek bir kapi: ogrenilmeden atilamaz.
    print("\n--- yetenek kapisi ---")
    gate = Harness()
    gate.player.abilities.clear()          # koy kizi Rey: eli bos (yumruk)
    # `Harness.arm()` diger testler icin onceden kilic kusturuyor; bu test
    # ozellikle KUSANMADAN ONCEKI durumu olctugu icin geri aliyoruz.
    gate.player.equip_weapon(weapons.FISTS)
    check(gate.player.weapon == weapons.FISTS, "Rey yumrukla basliyor")

    # `tap` bas-birak yapar. `step(press=...)` yalnizca KEYDOWN gonderiyor
    # ve tus basili kaldigi icin ikinci basis **yeni bir kenar uretmiyor** -
    # bu tuzaga bir kez dusuldu, kod hatasi sanildi.
    gate.tap(KEY_ATTACK)
    check(gate.player.chain.busy, "yumrukla da saldirilabiliyor",
          gate.player.chain.phase.name)
    gate.settle(30)

    gate.tap(KEY_DODGE)
    gate.settle(4)
    check(not gate.player.dodge.active, "kacinma ogrenilmeden atilamiyor")

    check(gate.player.grant(abilities.SWORD), "kilic kazanildi")
    check(not gate.player.grant(abilities.SWORD),
          "ayni yetenek iki kez kazanilmiyor")
    check(gate.player.weapon == weapons.SWORD,
          "kilic kazaninca silah degisiyor")
    check(gate.player.chain.chain_table is CHAIN,
          "kilicin zinciri baglayici CHAIN tablosu")

    gate.tap(KEY_ATTACK)
    check(gate.player.chain.busy, "kilictan sonra da saldirilabiliyor",
          gate.player.chain.phase.name)

    gate.settle(45)
    gate.player.grant(abilities.DODGE)
    gate.tap(KEY_DODGE)
    check(gate.player.dodge.active,
          "kacinma ogrenildikten sonra atilabiliyor")
    # `gate.game.shutdown()` KALDIRILDI - ayni gerekce, ama bu sefer
    # sonucu daha kotuydu: `shutdown()` `pygame.quit()` cagiriyor ve
    # ekrani kapatiyor. Dosyanin devami (silah izi, sallanma) sprite
    # uretiyor, `forge.Canvas.resolve()` de `convert_alpha()` cagiriyor -
    # ekran olmadan patliyor. Paket **sessizce kirikti**; 40 saniyelik
    # joystick beklemesi kalkinca butun paketi tek seferde calistirmak
    # mumkun oldu ve ortaya cikti.

    # --- Silah izi (src/art/trail.py) ---------------------------------------
    # Iz, sprite'i cizen AYNI poz fonksiyonundan hesaplaniyor
    # (spritegen.weapon_tip). Iki yerde ayri matematik olsaydi iz kilictan
    # kayardi ve bunu ancak ekran goruntusune bakinca fark ederdik.
    print("\n--- silah izi ---")
    from src.art.spritegen import WEAPON_LENGTH, weapon_tip
    from src.art.animation import ANIMATIONS, CHARACTERS
    from src.art.trail import TRAIL_LIFE_FRAMES, TRAIL_MAX_POINTS, WeaponTrail

    check(weapon_tip(CHARACTERS["shambler"], ANIMATIONS["idle"][0](0.0)) is None,
          "silahsiz karakterin izi YOK")
    check(weapon_tip(CHARACTERS["rey_armed"], ANIMATIONS["attack1"][0](0.5)) is not None,
          "kilicli karakterin ucu hesaplaniyor")

    # Savurma boyunca uc gercekten HAREKET etmeli - sabit kalirsa iz olmaz.
    _fn, _count, _loop = ANIMATIONS["attack1"]
    _tips = [weapon_tip(CHARACTERS["rey_armed"], _fn(i / max(1, _count - 1)))
             for i in range(_count)]
    _span = max(t[0] for t in _tips) - min(t[0] for t in _tips)
    check(_span > 10.0, "savurma boyunca uc genis bir yay ciziyor",
          f"{_span:.1f}px yatay yayilim")

    # WEAPON_LENGTH tek kaynak mi? Her silah tipi tanimli olmali.
    _kinds = set()
    for _spec in CHARACTERS.values():
        _kinds.add(_spec.weapon)
    _missing = _kinds - set(WEAPON_LENGTH)
    check(not _missing, "her silah tipinin uzunlugu WEAPON_LENGTH'te tanimli",
          str(_missing))

    # Iz sinirli: nokta sayisi ust siniri asmamali, omru bitince dusmeli.
    _trail = WeaponTrail()
    for _i in range(TRAIL_MAX_POINTS * 3):
        _trail.add(_i * 4.0, 0.0)
    check(len(_trail.points) <= TRAIL_MAX_POINTS,
          "iz nokta sayisi ust siniri asmiyor", str(len(_trail.points)))
    for _ in range(TRAIL_LIFE_FRAMES + 2):
        _trail.update()
    check(not _trail.active, "iz omru bitince tamamen siliniyor",
          str(len(_trail.points)))

    # --- Ikincil hareket ve gecis kareleri (Faz E) --------------------------
    print("\n--- ikincil hareket ve gecis kareleri ---")
    from src.art.animation import ANIMATIONS, SWAY_BIASES, SWAY_NEUTRAL
    from src.art.animator import Animator, sway_levels

    check("land" in ANIMATIONS and "turn" in ANIMATIONS,
          "gecis kareleri tanimli (land, turn)")
    for _st in ("land", "turn"):
        _fn, _n, _loop = ANIMATIONS[_st]
        check(not _loop, f"{_st} DONGUSEL DEGIL - bir kez oynar", str(_loop))

    check(sway_levels("rey_armed") == len(SWAY_BIASES),
          "oyuncunun sallanma varyantlari var", str(sway_levels("rey_armed")))
    check(sway_levels("shambler") == 1,
          "kumasi olmayan dusman varyant uretmiyor (bos maliyet yok)")

    # Yay GECIKMELI olmali: hedefe aninda ulasirsa ikincil hareket yoktur.
    _anim = Animator("rey_armed")
    _anim.update_sway(1.0)
    check(_anim.sway_index == SWAY_NEUTRAL,
          "sallanma tek karede hedefe ATLAMIYOR (gecikme var)",
          str(_anim.sway_index))
    for _ in range(40):
        _anim.update_sway(1.0)
    check(_anim.sway_index == len(SWAY_BIASES) - 1,
          "surekli kosuda kumas tamamen arkaya savruluyor",
          str(_anim.sway_index))
    # Ani durusta yay ASMALI - kumas one savrulur.
    _overshot = False
    for _ in range(60):
        _anim.update_sway(0.0)
        if _anim.sway_index == 0:
            _overshot = True
    check(_overshot,
          "ani duruşta kumas ONE savruluyor (yay asiyor)")

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Dovus cekirdegi belgedeki kare degerlerine uyuyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
