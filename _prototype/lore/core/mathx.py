"""Kucuk matematik yardimcilari: lerp, easing, 2B vektor, rastgelelik."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

TAU = math.tau


def clamp(value: float, lo: float, hi: float) -> float:
    return lo if value < lo else hi if value > hi else value


def sign(value: float) -> int:
    return (value > 0) - (value < 0)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def inv_lerp(a: float, b: float, v: float) -> float:
    return 0.0 if b == a else clamp((v - a) / (b - a), 0.0, 1.0)


def remap(v: float, a0: float, a1: float, b0: float, b1: float) -> float:
    return lerp(b0, b1, inv_lerp(a0, a1, v))


def approach(current: float, target: float, delta: float) -> float:
    """`current` degerini `target`a en fazla `delta` kadar yaklastirir.

    Hiz degisimlerinde lerp yerine bunu kullan: kare hizindan bagimsiz ve
    hedefe gercekten ulasir (lerp asimptotik yaklasir, tam varmaz).
    """
    if current < target:
        return min(current + delta, target)
    return max(current - delta, target)


def damp(current: float, target: float, smoothing: float, dt: float) -> float:
    """Kare hizindan bagimsiz ussel yumusatma.

    `smoothing`: 1 saniyede kalan mesafe orani (0.001 = cok hizli, 0.5 = yavas).
    """
    return target + (current - target) * (smoothing ** dt)


# --- Easing -----------------------------------------------------------------
def ease_in_quad(t: float) -> float:
    return t * t


def ease_out_quad(t: float) -> float:
    return 1.0 - (1.0 - t) ** 2


def ease_in_out_quad(t: float) -> float:
    return 2 * t * t if t < 0.5 else 1 - ((-2 * t + 2) ** 2) / 2


def ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def ease_out_back(t: float, overshoot: float = 1.70158) -> float:
    c3 = overshoot + 1
    return 1 + c3 * (t - 1) ** 3 + overshoot * (t - 1) ** 2


def ease_out_elastic(t: float) -> float:
    if t in (0.0, 1.0):
        return t
    c4 = TAU / 3
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


def ease_out_bounce(t: float) -> float:
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    if t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


# --- Vektor -----------------------------------------------------------------
@dataclass(slots=True)
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x + o.x, self.y + o.y)

    def __sub__(self, o: "Vec2") -> "Vec2":
        return Vec2(self.x - o.x, self.y - o.y)

    def __mul__(self, k: float) -> "Vec2":
        return Vec2(self.x * k, self.y * k)

    __rmul__ = __mul__

    def __iter__(self):
        yield self.x
        yield self.y

    @property
    def length(self) -> float:
        return math.hypot(self.x, self.y)

    @property
    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalized(self) -> "Vec2":
        n = self.length
        return Vec2(self.x / n, self.y / n) if n else Vec2()

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    def set(self, x: float, y: float) -> None:
        self.x, self.y = x, y

    @property
    def int_tuple(self) -> tuple[int, int]:
        return int(self.x), int(self.y)


def angle_to(ax: float, ay: float, bx: float, by: float) -> float:
    return math.atan2(by - ay, bx - ax)


def from_angle(angle: float, length: float = 1.0) -> Vec2:
    return Vec2(math.cos(angle) * length, math.sin(angle) * length)


def dist(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(bx - ax, by - ay)


def dist_sq(ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    return dx * dx + dy * dy


# --- Rastgelelik ------------------------------------------------------------
def rand_range(a: float, b: float) -> float:
    return random.uniform(a, b)


def rand_sign() -> int:
    return random.choice((-1, 1))


def chance(p: float) -> bool:
    return random.random() < p


def weighted_choice(options: dict) -> object:
    """{secenek: agirlik} sozlugunden agirlikli secim."""
    total = sum(options.values())
    if total <= 0:
        return next(iter(options))
    roll = random.random() * total
    upto = 0.0
    for key, weight in options.items():
        upto += weight
        if roll <= upto:
            return key
    return next(iter(options))
