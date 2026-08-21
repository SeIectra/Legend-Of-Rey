"""Savas sistemi: hitbox/hurtbox, hasar, geri tepme, dokunulmazlik.

Merkezi bir kural var: **kimse dogrudan kimseye hasar vermez.** Saldiran taraf
kisa omurlu bir `Hitbox` yaratir; sistem her kare hitbox'lari hedeflerle
kesistirir. Bunun getirileri:

  * Bir saldiri ayni dusmana iki kez vuramaz (`already_hit` kumesi).
  * Vurus geri bildirimi (hitstop, sarsinti, partikul, ses) tek yerde toplanir;
    her dusman kendi vurus efektini ayri ayri uydurmaz.
  * Parry, zirh, zayif nokta gibi kurallar tek bir cozum noktasinda yasar.

Eski kodda saldiri dogrudan `enemy.take_damage()` cagiriyordu; bu yuzden tek
tus basisi ayni dusmana kare basina bir kez, yani saniyede 60 kez vurabiliyordu.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

import pygame

from lore.constants import MASK_ENEMY, MASK_PLAYER


class DamageType(Enum):
    PHYSICAL = auto()
    FIRE = auto()
    ARCANE = auto()
    HAZARD = auto()      # Diken, ucurum - parry edilemez, zirh delmez


@dataclass
class Hitbox:
    """Kisa omurlu bir hasar hacmi."""

    rect: pygame.Rect
    damage: int
    owner: object
    target_mask: int                 # Kimlere vurur (MASK_PLAYER / MASK_ENEMY)
    knockback: float = 120.0
    knockback_up: float = 60.0
    lifetime: float = 0.1
    damage_type: DamageType = DamageType.PHYSICAL
    hitstop: float = 0.06
    shake: float = 0.18
    pierce: bool = False             # Vurdugu hedefte yok olmasin mi
    stagger: float = 0.22
    follow: object = None            # Sahibini takip etsin mi (dx, dy ofsetiyle)
    offset: tuple[int, int] = (0, 0)
    already_hit: set = field(default_factory=set)
    expired: bool = False

    def update(self, dt: float) -> None:
        self.lifetime -= dt
        if self.lifetime <= 0.0:
            self.expired = True
        if self.follow is not None:
            body = getattr(self.follow, "body", None)
            if body is not None:
                self.rect.centerx = int(body.centerx + self.offset[0])
                self.rect.centery = int(body.centery + self.offset[1])


@dataclass
class DamageResult:
    hit: bool = False
    killed: bool = False
    blocked: bool = False
    parried: bool = False
    amount: int = 0


class CombatSystem:
    """Tum aktif hitbox'lari tutar ve her kare cozer."""

    def __init__(self, scene) -> None:
        self.scene = scene
        self.hitboxes: list[Hitbox] = []
        self.pending_numbers: list[tuple[float, float, int, tuple]] = []

    def clear(self) -> None:
        self.hitboxes.clear()
        self.pending_numbers.clear()

    def spawn(self, hitbox: Hitbox) -> Hitbox:
        self.hitboxes.append(hitbox)
        return hitbox

    def attack(self, owner, rect: pygame.Rect, damage: int, target_mask: int,
               **kwargs) -> Hitbox:
        return self.spawn(Hitbox(rect=rect, damage=damage, owner=owner,
                                 target_mask=target_mask, **kwargs))

    # --- Cozum --------------------------------------------------------------
    def update(self, dt: float, player, enemies) -> None:
        for box in self.hitboxes:
            box.update(dt)
            if box.target_mask & MASK_ENEMY:
                for enemy in enemies:
                    if enemy.dead or enemy in box.already_hit:
                        continue
                    if box.rect.colliderect(enemy.hurtbox):
                        self._resolve(box, enemy)
                        if not box.pierce:
                            box.expired = True
                            break
            if box.target_mask & MASK_PLAYER and player is not None:
                if not player.dead and player not in box.already_hit:
                    if box.rect.colliderect(player.hurtbox):
                        self._resolve(box, player)
                        if not box.pierce:
                            box.expired = True

        self.hitboxes = [b for b in self.hitboxes if not b.expired]

    def _resolve(self, box: Hitbox, target) -> None:
        box.already_hit.add(target)

        # Yon: hitbox'in merkezinden hedefe. Sifir olursa saldiranin yonu.
        dx = target.body.centerx - box.rect.centerx
        direction = 1 if dx >= 0 else -1
        if abs(dx) < 1.0:
            direction = getattr(box.owner, "facing", 1)

        result = target.take_damage(
            box.damage,
            source=box.owner,
            direction=direction,
            knockback=box.knockback,
            knockback_up=box.knockback_up,
            damage_type=box.damage_type,
            stagger=box.stagger,
        )
        if result is None:
            result = DamageResult(hit=True, amount=box.damage)

        if result.parried:
            self.scene.on_parry(target, box)
            return
        if not result.hit:
            return

        self.scene.on_hit(box, target, result)


# --- Yardimcilar ------------------------------------------------------------
def melee_rect(body, facing: int, reach: int, height: int,
               forward: int = 0, vertical: int = 0) -> pygame.Rect:
    """Yakin dovus hitbox'i: govdenin onunde, yone gore aynalanmis."""
    width = reach
    x = body.centerx + (forward if facing > 0 else -forward - width)
    y = body.centery - height * 0.5 + vertical
    return pygame.Rect(int(x), int(y), width, height)


def knockback_vector(direction: int, force: float, up: float) -> tuple[float, float]:
    return (direction * force, -up)
