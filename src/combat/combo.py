"""Uclu zincir, iptal kurallari, kacinma ve combo sayaci.

Butun sureler **kare** cinsinden (docs/dovus-sistemi.md 1 - baglayici):

    Vurus 1:  4 on /  3 aktif /  8 son  · hasar 10
    Vurus 2:  5 on /  3 aktif /  9 son  · hasar 12
    Vurus 3:  8 on /  5 aktif / 16 son  · hasar 25  (bitirici)

**Akiciligin kalbi iptal kurallaridir:**
  * Vurus 1 ve 2'nin recovery'si kacinma ile iptal edilebilir
  * Vurus 3'un recovery'si iptal EDILEMEZ - bitiriciyi savurmak bir karardir
  * Bir dusman oldugu anda TUM recovery iptal olur (kill cancel)

Kill cancel tek basina oyunu on kat iyi hissettirir. Kalabalikta "bicip gecme"
hissi buradan gelir.

Zincir penceresi girdiyi **kuyruga alir**: animasyon bitmeden basilan tus bir
sonraki vurusa gecer. Oyuncu tam zamaninda basmak zorunda kalmaz, ritim tutar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from src.config import (
    CHAIN, CHAIN_WINDOW_FRAMES, COMBO_RESET_FRAMES, COMBO_THRESHOLD_HIGH,
    COMBO_THRESHOLD_LOW, COMBO_THRESHOLD_MID, COMBO_GOLD_MULTIPLIER_HIGH,
    COMBO_GOLD_MULTIPLIER_LOW, COMBO_GOLD_MULTIPLIER_MID,
    COUNTER_DAMAGE_BONUS, COUNTER_WINDOW_FRAMES, DODGE_COOLDOWN_FRAMES,
    DODGE_GENEROSITY_FRAMES, DODGE_IFRAMES, DODGE_TOTAL_FRAMES,
)


class AttackPhase(Enum):
    IDLE = auto()
    WINDUP = auto()      # Hazirlik - hitbox yok
    ACTIVE = auto()      # Hitbox acik
    RECOVERY = auto()    # Toparlanma - iptal edilebilir mi vurusa bagli


@dataclass
class ChainState:
    """Uclu zincirin kare kare durumu."""

    index: int = -1                  # Su anki vurus (0..2), -1 = bosta
    phase: AttackPhase = AttackPhase.IDLE
    phase_frames_left: int = 0
    window_frames_left: int = 0      # Zinciri surdurme penceresi
    queued: bool = False             # Sonraki vurus kuyruga alindi mi
    hitbox_spawned: bool = False
    window_frames: int = CHAIN_WINDOW_FRAMES
    skip_recovery: bool = False      # Kill cancel aktif karede geldiyse
    # Meşale taşırken tek elle dövüşülür: zincir 3'lü değil 2'li, bitirici
    # yok (docs/bolum-03.md Oda 1). `None` = kısıtlama yok (üç vuruşun
    # hepsi acık). Silah tablosunun kendisi değişmiyor, sadece ne kadarına
    # erişilebildiği.
    max_index: int | None = None
    # Hangi silahın zinciri okunuyor (src/combat/weapons.py). Varsayılan
    # `CHAIN` (kılıç) - Player kuşandığı silaha göre bunu değiştirir,
    # `ChainState`'in kendisi hangi silah olduğunu bilmez.
    chain_table: tuple = CHAIN

    @property
    def busy(self) -> bool:
        return self.phase is not AttackPhase.IDLE

    @property
    def spec(self):
        if 0 <= self.index < len(self.chain_table):
            return self.chain_table[self.index]
        return self.chain_table[0]

    @property
    def _effective_max(self) -> int:
        cap = len(self.chain_table) - 1
        if self.max_index is not None:
            cap = min(cap, self.max_index)
        return cap

    @property
    def is_finisher(self) -> bool:
        return self.index == self._effective_max

    @property
    def cancelable(self) -> bool:
        """Su anki recovery kacinma ile iptal edilebilir mi?"""
        return (self.phase is AttackPhase.RECOVERY
                and self.spec.cancelable)

    # --- Akis ---------------------------------------------------------------
    def start(self, index: int) -> None:
        self.index = index
        self.phase = AttackPhase.WINDUP
        self.phase_frames_left = self.chain_table[index].windup
        self.hitbox_spawned = False
        self.queued = False
        self.window_frames_left = 0

    def request_next(self) -> None:
        """Zincirin devamini kuyruga al. Pencere disindaysa yok sayilir."""
        if self.phase in (AttackPhase.ACTIVE, AttackPhase.RECOVERY):
            self.queued = True

    def cancel(self) -> None:
        """Kacinma ya da hasar ile durumu sifirla."""
        self.index = -1
        self.phase = AttackPhase.IDLE
        self.phase_frames_left = 0
        self.queued = False
        self.hitbox_spawned = False
        self.skip_recovery = False

    def kill_cancel(self) -> None:
        """Dusman oldu: recovery iptal olur, pencere acik kalir.

        **Olum genellikle AKTIF karelerde gelir** - hitbox o sirada aciktir.
        Yalnizca RECOVERY'ye bakmak kill cancel'i pratikte hic calistirmaz;
        bu yuzden aktif fazda bayrak birakilir ve recovery hic baslamaz.

        Zincir indeksi korunur - oyuncu kaldigi yerden devam eder ve
        kalabalikta akis kesilmez.
        """
        if self.phase is AttackPhase.RECOVERY:
            self._finish_with_window()
        elif self.phase is AttackPhase.ACTIVE:
            self.skip_recovery = True

    def _finish_with_window(self) -> None:
        """Saldiriyi bitirir ama zincir penceresini acik birakir."""
        self.phase = AttackPhase.IDLE
        self.phase_frames_left = 0
        self.window_frames_left = self.window_frames

    def update(self) -> str | None:
        """Bir kare ilerletir.

        Doner: "spawn_hitbox" (bu kare hitbox acilmali), "chain" (sonraki
        vurusa gecildi) ya da None.
        """
        if self.window_frames_left > 0:
            self.window_frames_left -= 1
            if self.window_frames_left == 0 and not self.busy:
                self.index = -1

        if not self.busy:
            return None

        self.phase_frames_left -= 1

        if self.phase is AttackPhase.WINDUP and self.phase_frames_left <= 0:
            self.phase = AttackPhase.ACTIVE
            self.phase_frames_left = self.spec.active
            self.hitbox_spawned = True
            return "spawn_hitbox"

        if self.phase is AttackPhase.ACTIVE and self.phase_frames_left <= 0:
            if self.skip_recovery:
                # Aktif karede dusman oldu: recovery hic baslamaz.
                self.skip_recovery = False
                self._finish_with_window()
                if self.queued and self.index < self._effective_max:
                    self.start(self.index + 1)
                    return "chain"
                self.queued = False
                return None
            self.phase = AttackPhase.RECOVERY
            self.phase_frames_left = self.spec.recovery
            self.window_frames_left = self.window_frames
            return None

        if self.phase is AttackPhase.RECOVERY and self.phase_frames_left <= 0:
            self.phase = AttackPhase.IDLE
            if self.queued and self.index < self._effective_max:
                self.start(self.index + 1)
                return "chain"
            self.queued = False
        return None

    def can_start(self) -> bool:
        return not self.busy

    def next_index(self) -> int:
        """Yeni saldiri hangi vurusla baslamali?"""
        if self.window_frames_left > 0 and 0 <= self.index < self._effective_max:
            return self.index + 1
        return 0


@dataclass
class DodgeState:
    """Kacinma: 6 kare dokunulmazlik, 18 kare toplam, 24 kare bekleme."""

    frames_left: int = 0
    cooldown_left: int = 0
    counter_window_left: int = 0
    charges: int = 1
    max_charges: int = 1
    direction: int = 1

    @property
    def active(self) -> bool:
        return self.frames_left > 0

    @property
    def invulnerable(self) -> bool:
        """Dokunulmazlik penceresi.

        Cömertlik: gorsel baslangictan `DODGE_GENEROSITY_FRAMES` kare ONCE
        baslar. Oyuncuya soylenmez; oyun sadece adil hisseder.
        """
        elapsed = DODGE_TOTAL_FRAMES - self.frames_left
        return self.active and elapsed < DODGE_IFRAMES + DODGE_GENEROSITY_FRAMES

    @property
    def can_dodge(self) -> bool:
        return self.charges > 0 and self.cooldown_left <= 0 and not self.active

    def start(self, direction: int) -> None:
        self.frames_left = DODGE_TOTAL_FRAMES
        self.cooldown_left = DODGE_COOLDOWN_FRAMES
        self.direction = direction
        self.charges = max(0, self.charges - 1)

    def update(self, grounded: bool) -> None:
        if self.frames_left > 0:
            self.frames_left -= 1
            if self.frames_left == 0:
                # Kacinma biter bitmez karsi vurus penceresi acilir.
                self.counter_window_left = COUNTER_WINDOW_FRAMES
        if self.cooldown_left > 0:
            self.cooldown_left -= 1
        if self.counter_window_left > 0:
            self.counter_window_left -= 1
        # Sarjlar yerdeyken ve bekleme bitince dolar.
        if grounded and self.cooldown_left <= 0:
            self.charges = self.max_charges

    @property
    def counter_ready(self) -> bool:
        return self.counter_window_left > 0

    def consume_counter(self) -> bool:
        if self.counter_window_left > 0:
            self.counter_window_left = 0
            return True
        return False


@dataclass
class ComboCounter:
    """Vurus sayaci. 90 kare sessizlikte sifirlanir."""

    count: int = 0
    frames_since_hit: int = 0
    best: int = 0
    _crossed: set[int] = field(default_factory=set)

    def register_hit(self) -> list[int]:
        """Bir vurus kaydeder, bu vurusla asilan esikleri doner."""
        self.count += 1
        self.frames_since_hit = 0
        self.best = max(self.best, self.count)

        crossed: list[int] = []
        for threshold in (COMBO_THRESHOLD_LOW, COMBO_THRESHOLD_MID,
                          COMBO_THRESHOLD_HIGH):
            if self.count >= threshold and threshold not in self._crossed:
                self._crossed.add(threshold)
                crossed.append(threshold)
        return crossed

    def update(self) -> bool:
        """True donerse sayac bu kare sifirlandi."""
        if self.count == 0:
            return False
        self.frames_since_hit += 1
        if self.frames_since_hit >= COMBO_RESET_FRAMES:
            self.reset()
            return True
        return False

    def reset(self) -> None:
        self.count = 0
        self.frames_since_hit = 0
        self._crossed.clear()

    @property
    def gold_multiplier(self) -> float:
        if self.count >= COMBO_THRESHOLD_HIGH:
            return COMBO_GOLD_MULTIPLIER_HIGH
        if self.count >= COMBO_THRESHOLD_MID:
            return COMBO_GOLD_MULTIPLIER_MID
        if self.count >= COMBO_THRESHOLD_LOW:
            return COMBO_GOLD_MULTIPLIER_LOW
        return 1.0


def counter_damage(base: int, bonus: float = COUNTER_DAMAGE_BONUS) -> int:
    """Karsi vurus hasari. Kacinmayi savunma degil saldiri hazirligi yapar."""
    return int(round(base * (1.0 + bonus)))
