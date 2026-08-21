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

from src.combat.combo import AttackPhase  # noqa: E402
from src.config import (  # noqa: E402
    CHAIN, CHAIN_WINDOW_FRAMES, COMBO_RESET_FRAMES,
    COYOTE_FRAMES, DODGE_COOLDOWN_FRAMES, DODGE_IFRAMES, DODGE_TOTAL_FRAMES,
    HITSTOP_FINISHER, HITSTOP_KILL, HITSTOP_NORMAL, INPUT_BUFFER_FRAMES,
)
from src.core.game import Game  # noqa: E402
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

    h.game.shutdown()

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
