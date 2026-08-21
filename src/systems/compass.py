"""Kolye pusulasi - Cemo'nun birakti sey.

`docs/derinlestirme.md` 3.1. Cemo'nun kolyesi bir pusula: ona yaklastikca
isinir, parildar, kalp atisi ritmi hizlanir.

## Kritik: kolye ile Yanki **celisebilir**

Ikisi farkli yonler gosterdiginde oyuncu hangisine guvenecegini secer.
Oyunun temasi bu tek mekanikte duruyor:

  * **Yanki** kafasindaki ses - yardim ediyor gibi gorunen, aslinda cagiran
  * **Kolye** kardesinden kalan somut nesne - sessiz ama yalan soylemiyor

B14'teki donusun oyuncu tarafindaki hazirligi budur. Oyuncu daha twist'i
gormeden, kendi elleriyle "sese mi nesneye mi guveneyim" sorusunu defalarca
cevaplamis olur. Twist geldiginde surpriz degil, **onay** gibi gelir - iyi
donus boyle calisir.

Kolye **hicbir zaman yalan soylemez**. Bu bilincli asimetri: yalan
soyleyebilen bir sesin yaninda hep dogru soyleyen bir nesne olmasi, secimi
gercek bir secim yapar. Ikisi de guvenilmez olsaydi oyuncu ikisini de yok
sayar ve mekanik olurdu.
"""
from __future__ import annotations

import math

# Isinma menzili - bu mesafenin icinde parilti baslar.
WARM_RANGE = 420.0
HOT_RANGE = 90.0

# Kalp atisi: uzakta yavas, yakinda hizli (kare cinsinden periyot).
BEAT_SLOW = 78
BEAT_FAST = 22


class Compass:
    """Kolyenin hedefe gore durumu."""

    def __init__(self) -> None:
        self.target: tuple[float, float] | None = None
        self.frame = 0
        self.distance = float("inf")

    def set_target(self, x: float, y: float) -> None:
        self.target = (x, y)

    def clear(self) -> None:
        self.target = None

    # --- Dongu --------------------------------------------------------------
    def update(self, player) -> None:
        self.frame += 1
        if self.target is None:
            self.distance = float("inf")
            return
        self.distance = math.hypot(self.target[0] - player.body.center_x,
                                   self.target[1] - player.body.center_y)

    # --- Sorgular -----------------------------------------------------------
    @property
    def warmth(self) -> float:
        """0 uzak, 1 cok yakin. Parilti ve ritim bundan turer."""
        if self.target is None or self.distance >= WARM_RANGE:
            return 0.0
        if self.distance <= HOT_RANGE:
            return 1.0
        span = WARM_RANGE - HOT_RANGE
        return max(0.0, min(1.0, 1.0 - (self.distance - HOT_RANGE) / span))

    def direction_from(self, player) -> int:
        """Hedefin yonu: -1 sol, +1 sag, 0 (hedef yok ya da tam ustunde).

        Oyuncuya **gore** hesaplanir; mutlak konumun tek basina anlami yok.
        """
        if self.target is None:
            return 0
        delta = self.target[0] - player.body.center_x
        if abs(delta) < 4.0:
            return 0
        return 1 if delta > 0 else -1

    @property
    def beat_period(self) -> int:
        """Kalp atisi periyodu - yaklastikca kisalir."""
        warmth = self.warmth
        return int(BEAT_SLOW + (BEAT_FAST - BEAT_SLOW) * warmth)

    @property
    def pulse(self) -> float:
        """0..1 - kalp atisinin o andaki degeri. Cizim bunu kullanir."""
        if self.warmth <= 0.0:
            return 0.0
        phase = (self.frame % self.beat_period) / self.beat_period
        # Iki vurus: kalp atisi "tak-tak" seklinde, tek sinus degil.
        first = math.exp(-((phase - 0.00) * 9.0) ** 2)
        second = math.exp(-((phase - 0.22) * 9.0) ** 2) * 0.6
        return min(1.0, (first + second) * self.warmth)


def contradicts(compass: Compass, player, echo_direction: int) -> bool:
    """Kolye ile Yanki farkli yon mu gosteriyor?

    Sahne bunu sorup oyuncuya **gostermeden** kendi kararini vermesini
    bekliyor. "Celisiyor!" diye bir uyari cizmiyoruz: celiskiyi fark etmek
    oyuncunun isi, ve fark ettigi an mekanigin isledigi andir.
    """
    own = compass.direction_from(player)
    return own != 0 and echo_direction != 0 and own != echo_direction
