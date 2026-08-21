"""Kare bazli hitbox ve hasar cozumu.

**Merkezi kural: kimse dogrudan kimseye hasar vermez.** Saldiran taraf kisa
omurlu bir `Hitbox` yaratir; `HitboxManager` her kare hedeflerle kesistirir.

Getirileri:
  * Bir saldiri ayni hedefe iki kez vuramaz (`already_hit` kumesi)
  * Vurus geri bildirimi tek yerde toplanir - her varlik kendi efektini uydurmaz
  * Parry, zirh, zayif nokta gibi kurallar tek cozum noktasinda yasar

Carpisma **alt-dikdortgen** ile yapilir: hitbox sprite'tan kucuktur. Hem hizli
hem oyuncu lehine affedici (docs/derinlestirme.md 8.2). Piksel-mukemmel
carpisma yapilmaz.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Flag, auto

import pygame


class Team(Flag):
    """Kimin kime vurabilecegi. Bayrak - bir hitbox birden fazla takimi vurabilir."""

    NONE = 0
    PLAYER = auto()
    ENEMY = auto()
    BREAKABLE = auto()
    ALL = PLAYER | ENEMY | BREAKABLE


@dataclass
class Hitbox:
    """Belirli karelerde aktif olan bir hasar hacmi."""

    rect: pygame.Rect
    damage: int
    owner: object
    targets: Team

    knockback: float = 1.6              # piksel / kare
    knockback_up: float = 0.9
    active_frames: int = 3
    poise_damage: int = 1               # Sendeleme icin
    is_finisher: bool = False
    is_counter: bool = False            # Karsi vurus - farkli flas rengi
    pierce: bool = False                # Vurdugu hedefte yok olmasin mi
    follow: object = None               # Sahibini takip etsin mi
    offset: tuple[int, int] = (0, 0)

    frames_alive: int = 0
    already_hit: set = field(default_factory=set)
    expired: bool = False

    def update(self) -> None:
        self.frames_alive += 1
        if self.frames_alive >= self.active_frames:
            self.expired = True
        if self.follow is not None:
            body = getattr(self.follow, "body", None)
            if body is not None:
                facing = getattr(self.follow, "facing", 1)
                self.rect.centerx = int(body.center_x + self.offset[0] * facing)
                self.rect.centery = int(body.center_y + self.offset[1])

    def direction_to(self, target_x: float, target_y: float) -> tuple[float, float]:
        """Hitbox merkezinden hedefe birim yon - sarsinti ve geri itme icin."""
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        if abs(dx) < 0.5 and abs(dy) < 0.5:
            facing = getattr(self.owner, "facing", 1)
            return (float(facing), 0.0)
        return (dx, dy)


@dataclass
class DamageResult:
    hit: bool = False
    killed: bool = False
    staggered: bool = False
    blocked: bool = False
    amount: int = 0


class HitboxManager:
    """Aktif hitbox'lari tutar ve her kare cozer."""

    def __init__(self, on_hit=None) -> None:
        self.boxes: list[Hitbox] = []
        # Sahne bunu saglar; vurus degdiginde game feel'i tetikler.
        self._on_hit = on_hit

    def clear(self) -> None:
        self.boxes.clear()

    def spawn(self, box: Hitbox) -> Hitbox:
        self.boxes.append(box)
        return box

    def update(self, targets_by_team: dict[Team, list]) -> None:
        """Her hitbox'i ilerletir ve hedeflerle kesistirir."""
        for box in self.boxes:
            box.update()
            for team, entities in targets_by_team.items():
                if not (box.targets & team):
                    continue
                self._resolve_against(box, entities)
                if box.expired and not box.pierce:
                    break
        self.boxes = [b for b in self.boxes if not b.expired]

    def _resolve_against(self, box: Hitbox, entities: list) -> None:
        for entity in entities:
            if entity in box.already_hit or not _is_hittable(entity):
                continue
            if not box.rect.colliderect(entity.hurtbox):
                continue

            box.already_hit.add(entity)
            direction = box.direction_to(entity.body.center_x, entity.body.center_y)
            result = entity.take_damage(box, direction)

            if result.hit and self._on_hit is not None:
                self._on_hit(box, entity, result, direction)
            if not box.pierce:
                box.expired = True
                return

    @property
    def active_count(self) -> int:
        return len(self.boxes)


def _is_hittable(entity) -> bool:
    return not getattr(entity, "dead", False) \
        and not getattr(entity, "invulnerable", False)


def melee_rect(body, facing: int, reach: int, height: int,
               forward: int = 2) -> pygame.Rect:
    """Yakin dovus hitbox'i: govdenin onunde, yone gore aynalanmis."""
    x = body.center_x + (forward if facing > 0 else -forward - reach)
    y = body.center_y - height * 0.5
    return pygame.Rect(int(x), int(y), reach, height)
