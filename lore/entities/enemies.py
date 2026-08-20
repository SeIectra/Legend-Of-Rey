"""Dusmanlar ve yapay zekalari.

Her dusman ayni durum makinesini kullanir:

    patrol -> alert -> chase -> windup -> attack -> recover
                 ^                                    |
                 +------------- stagger <-------------+

**Windup fazi pazarlik konusu degildir.** Saldiridan once dusman gorunur bir
hazirlik pozuna girer ve rengi degisir. Oyuncu buna bakarak kacar, parry eder
ya da vurur. Windup'siz saldiri "haksiz" hissettirir; oyunun zorlugu tepki
suresinden degil, karar vermekten gelmelidir.

Kenar algilama da ayni felsefeden: dusmanlar ucuruma yurumez. Eski koddaki
"oyuncuya dogru sabit hizla git" davranisi dusmanlarin haritadan dusmesine ve
duvarlara gomulmesine yol aciyordu.
"""
from __future__ import annotations

import math
import random

import pygame

from lore.constants import MASK_ENEMY, MASK_PLAYER
from lore.core.mathx import approach, clamp, rand_range
from lore.entities.entity import Animator, Entity
from lore.gfx.sprites import ARCHETYPES, build_sprite_set
from lore.systems.combat import DamageResult, DamageType, melee_rect
from lore.systems.physics import ledge_ahead, line_of_sight, wall_ahead


class Enemy(Entity):
    """Tum dusmanlarin temeli."""

    sprite_key = "goblin"
    max_health = 3
    body_w = 10
    body_h = 16
    team_mask = MASK_ENEMY

    # AI ayarlari (alt siniflar ezer)
    patrol_speed = 26.0
    chase_speed = 62.0
    sight_range = 110.0
    # Arkadan fark etme mesafesi. Yumruk menzili ~13 piksel oldugu icin bu deger
    # ondan kucuk olmak zorunda: aksi halde dusman sen vurmadan doner ve Act I'in
    # tek saldiri yolu olan sirttan vurus hicbir zaman calismaz.
    sight_behind = 11.0
    # Kosarak yaklasirsan duyulursun. Gizlilik boylece bir *karar* olur:
    # yavas git ve vur, ya da hizli git ve dovus.
    sight_behind_running = 52.0
    running_threshold = 62.0    # Bu hizin ustu "kosuyor" sayilir
    lose_range = 190.0
    attack_range = 20.0
    windup_time = 0.34
    attack_time = 0.16
    recover_time = 0.40
    damage = 1
    knockback = 150.0
    reach = 18
    attack_height = 16
    essence_drop = (2, 5)
    armored = False             # Zirhli: parry edilmeden tam hasar almaz
    flying = False
    can_be_backstabbed = True

    def __init__(self, scene, x: float, y: float, **options) -> None:
        super().__init__(scene, x, y)
        self.gravity_enabled = not self.flying
        self.body.gravity_scale = 0.0 if self.flying else 1.0

        spec = ARCHETYPES[self.sprite_key]
        self.sprite_foot_y = spec.foot_y
        sprite_set = scene.app.assets.generated(
            f"sprites:{self.sprite_key}", lambda: build_sprite_set(spec))
        self.anim = Animator(
            sprite_set,
            fps={"idle": 6, "walk": 9, "run": 12, "attack1": 14, "hurt": 12,
                 "death": 8, "fall": 7},
            looping={"idle": True, "walk": True, "run": True, "fall": True,
                     "attack1": False, "hurt": False, "death": False},
        )

        self.state = "patrol"
        self.state_timer = 0.0
        self.facing = options.get("facing", random.choice((-1, 1)))
        self.home_x = x
        self.patrol_range = float(options.get("patrol", 64))
        self.aggro = False
        self.attack_spawned = False
        self.alert_timer = 0.0
        self.death_timer = 0.0
        self.think_timer = 0.0

    # --- Algi ---------------------------------------------------------------
    def can_see(self, player) -> bool:
        if player is None or player.dead:
            return False
        dx = player.body.centerx - self.body.centerx
        dy = player.body.centery - self.body.centery
        if abs(dy) > 48.0:
            return False
        distance = abs(dx)
        facing_player = (dx > 0) == (self.facing > 0)
        if facing_player:
            limit = self.sight_range
        elif abs(player.body.vx) > self.running_threshold:
            limit = self.sight_behind_running     # Ayak sesleri ele veriyor
        else:
            limit = self.sight_behind
        if distance > limit:
            return False
        return line_of_sight(self.scene.tilemap, self.body.centerx,
                             self.body.centery, player.body.centerx,
                             player.body.centery)

    # --- Ana dongu ----------------------------------------------------------
    def update(self, dt: float) -> None:
        self.iframes = max(0.0, self.iframes - dt)
        self.flash = max(0.0, self.flash - dt)

        if self.dead:
            self._update_death(dt)
            return

        if self.stagger > 0.0:
            self.stagger -= dt
            self.body.vx = approach(self.body.vx, 0.0, 320.0 * dt)
            self._step_physics(dt)
            self.anim.play("hurt")
            self.anim.update(dt)
            return

        player = self.scene.player
        self.state_timer -= dt

        handler = getattr(self, f"_state_{self.state}", None)
        if handler is not None:
            handler(dt, player)

        self._step_physics(dt)
        self._update_animation(dt)

    def _step_physics(self, dt: float) -> None:
        if self.gravity_enabled:
            self.body.apply_gravity(dt)
        self.body.move(self.scene.tilemap, dt)

    # --- Durumlar -----------------------------------------------------------
    def _state_patrol(self, dt: float, player) -> None:
        if self.can_see(player):
            self._enter_alert()
            return

        # Ucuruma ya da duvara gelince don. Devriye alanindan da tasma.
        if (ledge_ahead(self.body, self.scene.tilemap, self.facing)
                or wall_ahead(self.body, self.scene.tilemap, self.facing)
                or abs(self.body.centerx - self.home_x) > self.patrol_range):
            self.facing *= -1
            self.state_timer = rand_range(0.3, 0.9)
            self.body.vx = 0.0
            return

        if self.state_timer <= 0.0:
            self.body.vx = approach(self.body.vx, self.facing * self.patrol_speed,
                                    200.0 * dt)
        else:
            self.body.vx = approach(self.body.vx, 0.0, 300.0 * dt)

    def _enter_alert(self) -> None:
        self.state = "alert"
        self.state_timer = 0.28
        self.aggro = True
        self.body.vx = 0.0
        self.scene.spawn_alert(self)

    def _state_alert(self, dt: float, player) -> None:
        """Kisa sasirma anı: oyuncuya tepki suresi tanir."""
        self.body.vx = approach(self.body.vx, 0.0, 400.0 * dt)
        if player is not None:
            self.facing = 1 if player.body.centerx > self.body.centerx else -1
        if self.state_timer <= 0.0:
            self.state = "chase"

    def _state_chase(self, dt: float, player) -> None:
        if player is None or player.dead:
            self._give_up()
            return
        dx = player.body.centerx - self.body.centerx
        distance = abs(dx)
        if distance > self.lose_range:
            self._give_up()
            return

        self.facing = 1 if dx > 0 else -1

        if distance <= self.attack_range and self._can_attack(player):
            self.state = "windup"
            self.state_timer = self.windup_time
            self.body.vx = 0.0
            return

        # Ucurumun kenarinda dur. Ucabiliyorsak umursamayiz.
        if not self.flying and ledge_ahead(self.body, self.scene.tilemap, self.facing):
            self.body.vx = approach(self.body.vx, 0.0, 400.0 * dt)
            return

        self.body.vx = approach(self.body.vx, self.facing * self.chase_speed,
                                420.0 * dt)
        if self.flying:
            dy = player.body.centery - self.body.centery
            self.body.vy = approach(self.body.vy, clamp(dy * 2.2, -50, 50),
                                    260.0 * dt)

    def _can_attack(self, player) -> bool:
        return abs(player.body.centery - self.body.centery) < 26.0

    def _give_up(self) -> None:
        self.state = "patrol"
        self.state_timer = rand_range(0.4, 1.2)
        self.aggro = False

    def _state_windup(self, dt: float, player) -> None:
        self.body.vx = approach(self.body.vx, 0.0, 500.0 * dt)
        if self.state_timer <= 0.0:
            self.state = "attack"
            self.state_timer = self.attack_time
            self.attack_spawned = False
            self.anim.play("attack1", restart=True)

    def _state_attack(self, dt: float, player) -> None:
        if not self.attack_spawned:
            self.attack_spawned = True
            self.perform_attack(player)
        if self.state_timer <= 0.0:
            self.state = "recover"
            self.state_timer = self.recover_time

    def _state_recover(self, dt: float, player) -> None:
        self.body.vx = approach(self.body.vx, 0.0, 300.0 * dt)
        if self.state_timer <= 0.0:
            self.state = "chase" if self.aggro else "patrol"

    # --- Saldiri ------------------------------------------------------------
    def perform_attack(self, player) -> None:
        rect = melee_rect(self.body, self.facing, self.reach, self.attack_height,
                          forward=2)
        self.scene.combat.attack(
            self, rect, self.damage, MASK_PLAYER,
            knockback=self.knockback, knockback_up=110.0,
            lifetime=0.10, hitstop=0.03, shake=0.10,
        )
        self.scene.app.audio.play("swing", pitch=-2.0, pos=self.body.center)

    # --- Hasar --------------------------------------------------------------
    def take_damage(self, amount: int, source=None, direction: int = 1,
                    knockback: float = 120.0, knockback_up: float = 60.0,
                    damage_type: DamageType = DamageType.PHYSICAL,
                    stagger: float = 0.2) -> DamageResult:
        if self.dead or self.iframes > 0.0:
            return DamageResult(hit=False)

        # Sirttan vurus: dusman oyuncuyu fark etmemisse uc kat hasar.
        # Act I'de Rey silahsiz; tek gercek saldiri yolu budur.
        backstab = (self.can_be_backstabbed and not self.aggro
                    and direction == self.facing)
        if backstab:
            amount *= 3
            self.scene.on_backstab(self)

        if self.armored and not backstab and damage_type == DamageType.PHYSICAL:
            # Zirh: hasar yarilanir (asagi yuvarlanmaz, en az 1 kalir).
            amount = max(1, amount // 2)

        self.health -= amount
        self.iframes = 0.06                 # Ayni karede iki kez vurulmayi onler
        self.flash = self.flash_time
        self.stagger = stagger
        self.body.vx = direction * knockback
        if not self.flying:
            self.body.vy = -knockback_up
        self.aggro = True

        # Vurulan dusman oyuncuyu hemen fark eder ve ona doner.
        if self.state in ("patrol", "alert"):
            self.state = "chase"
        self.facing = -direction

        result = DamageResult(hit=True, amount=amount)
        if self.health <= 0:
            self.health = 0
            result.killed = True
            self.die(source)
        return result

    def die(self, source=None) -> None:
        if self.dead:
            return
        self.dead = True
        self.death_timer = 0.9
        self.anim.play("death", restart=True)
        self.scene.app.audio.play("death", pitch=2.0, pos=self.body.center)
        self.scene.on_enemy_died(self)

    def _update_death(self, dt: float) -> None:
        self.death_timer -= dt
        self.body.vx = approach(self.body.vx, 0.0, 260.0 * dt)
        if self.gravity_enabled:
            self.body.apply_gravity(dt)
        self.body.move(self.scene.tilemap, dt)
        self.anim.update(dt)
        if self.death_timer <= 0.0:
            self.remove = True

    # --- Animasyon ----------------------------------------------------------
    def _update_animation(self, dt: float) -> None:
        if self.state in ("attack", "windup"):
            state = "attack1"
        elif not self.body.grounded and not self.flying:
            state = "fall"
        elif abs(self.body.vx) > 34.0:
            state = "run"
        elif abs(self.body.vx) > 4.0:
            state = "walk"
        else:
            state = "idle"
        self.anim.play(state)
        # Windup sirasinda animasyon donar: hazirlik pozu net okunur.
        speed = 0.0 if self.state == "windup" else 1.0
        self.anim.update(dt, speed if speed else 0.05)

    def draw(self, surface, camera) -> None:
        # Windup sirasinda kirmizi parlama: saldirinin geliyor oldugunun isareti.
        if self.state == "windup" and int(self.state_timer * 24) % 2 == 0:
            image = self.anim.image
            if image is not None:
                from lore.gfx.forge import tint
                flipped = image if self.facing > 0 else pygame.transform.flip(
                    image, True, False)
                warn = tint(flipped, (255, 120, 90), 0.55)
                ox, oy = camera.offset
                surface.blit(warn, (
                    int(self.body.centerx - warn.get_width() * 0.5) - ox,
                    int(self.body.y + self.body.h - self.sprite_foot_y) - oy))
                return
        super().draw(surface, camera)


# --- Somut dusmanlar --------------------------------------------------------
class Grunt(Enemy):
    """Goblin. Temel yakin dovus, kalabalik halinde tehlikeli."""
    sprite_key = "goblin"
    max_health = 3
    chase_speed = 66.0
    attack_range = 20.0
    windup_time = 0.32
    damage = 1
    essence_drop = (2, 4)


class Archer(Enemy):
    """Mesafeyi korur, ok atar. Yaklasinca geri ceker."""
    sprite_key = "archer"
    max_health = 2
    body_w = 10
    body_h = 16
    chase_speed = 52.0
    sight_range = 165.0
    attack_range = 130.0
    windup_time = 0.55
    attack_time = 0.12
    recover_time = 0.85
    damage = 1
    essence_drop = (3, 6)
    retreat_range = 56.0

    def _state_chase(self, dt: float, player) -> None:
        if player is None or player.dead:
            self._give_up()
            return
        dx = player.body.centerx - self.body.centerx
        distance = abs(dx)
        if distance > self.lose_range:
            self._give_up()
            return
        self.facing = 1 if dx > 0 else -1

        # Cok yaklastiysa geri cekil - ama ucurumdan dusme.
        if distance < self.retreat_range:
            back = -self.facing
            if not ledge_ahead(self.body, self.scene.tilemap, back):
                self.body.vx = approach(self.body.vx, back * self.chase_speed,
                                        320.0 * dt)
                return
            self.body.vx = approach(self.body.vx, 0.0, 400.0 * dt)

        if distance <= self.attack_range and self._can_attack(player):
            self.state = "windup"
            self.state_timer = self.windup_time
            self.body.vx = 0.0
            return
        if not ledge_ahead(self.body, self.scene.tilemap, self.facing):
            self.body.vx = approach(self.body.vx, self.facing * self.chase_speed,
                                    300.0 * dt)

    def _can_attack(self, player) -> bool:
        return abs(player.body.centery - self.body.centery) < 34.0

    def perform_attack(self, player) -> None:
        from lore.entities.projectile import Projectile
        if player is None:
            return
        dx = player.body.centerx - self.body.centerx
        dy = player.body.centery - self.body.centery
        angle = math.atan2(dy * 0.55, dx)       # Hafif duz atis: kacmasi kolay
        self.scene.spawn_projectile(Projectile(
            self.scene, self.body.centerx + self.facing * 6, self.body.centery,
            angle, speed=168.0, kind="arrow", owner=self,
            target_mask=MASK_PLAYER, damage=self.damage, gravity=110.0))
        self.scene.app.audio.play("shoot", pitch=-1.0, pos=self.body.center)


class Skeleton(Enemy):
    """Bir kez dirilir. Ikinci olumu kalicidir."""
    sprite_key = "skeleton"
    max_health = 4
    chase_speed = 58.0
    attack_range = 24.0
    windup_time = 0.42
    reach = 22
    damage = 1
    essence_drop = (4, 7)

    def __init__(self, scene, x: float, y: float, **options) -> None:
        super().__init__(scene, x, y, **options)
        self.revived = False
        self.revive_timer = 0.0

    def die(self, source=None) -> None:
        if not self.revived:
            # Ilk olum gecici: kemikler dagilir, sonra toplanir.
            self.revived = True
            self.revive_timer = 1.6
            self.health = 0
            self.dead = True
            self.death_timer = 999.0        # _update_death silmesin
            self.anim.play("death", restart=True)
            self.scene.app.audio.play("break", pos=self.body.center)
            self.scene.spawn_effect("ring", self.body.center, ramp="bone",
                                    radius=16)
            return
        super().die(source)

    def _update_death(self, dt: float) -> None:
        if self.revived and self.revive_timer > 0.0:
            self.revive_timer -= dt
            self.body.vx = approach(self.body.vx, 0.0, 300.0 * dt)
            self.body.apply_gravity(dt)
            self.body.move(self.scene.tilemap, dt)
            self.anim.update(dt)
            if self.revive_timer <= 0.0:
                self._revive()
            return
        super()._update_death(dt)

    def _revive(self) -> None:
        self.dead = False
        self.health = max(2, self.max_health // 2)
        self.state = "chase"
        self.aggro = True
        self.iframes = 0.3
        self.anim.play("idle", restart=True)
        self.scene.app.audio.play("boss_roar", volume=0.4, pos=self.body.center)
        self.scene.spawn_effect("ring", self.body.center, ramp="azure", radius=20)


class Brute(Enemy):
    """Zirhli, yavas, sert vuran. Parry ya da sirttan vurus ister."""
    sprite_key = "brute"
    max_health = 9
    body_w = 16
    body_h = 26
    patrol_speed = 18.0
    chase_speed = 44.0
    sight_range = 130.0
    attack_range = 28.0
    windup_time = 0.62          # Uzun hazirlik: okunur ve kacilabilir
    attack_time = 0.20
    recover_time = 0.70
    damage = 2
    knockback = 260.0
    reach = 28
    attack_height = 24
    armored = True
    essence_drop = (10, 16)
    iframe_time = 0.05

    def perform_attack(self, player) -> None:
        super().perform_attack(player)
        self.body.vx = self.facing * 90.0       # Vurusla birlikte one atilir
        self.scene.camera.add_trauma(0.20)

    def die(self, source=None) -> None:
        super().die(source)
        self.scene.camera.add_trauma(0.4)
        self.scene.spawn_effect("ring", self.body.center, ramp="ember", radius=28)


class Wisp(Enemy):
    """Ucan yanki. Yercekimsiz, sinus egrisiyle suzulur."""
    sprite_key = "assassin"
    max_health = 2
    body_w = 10
    body_h = 12
    flying = True
    patrol_speed = 30.0
    chase_speed = 74.0
    sight_range = 140.0
    attack_range = 18.0
    windup_time = 0.30
    damage = 1
    essence_drop = (3, 6)
    can_be_backstabbed = False

    def __init__(self, scene, x: float, y: float, **options) -> None:
        super().__init__(scene, x, y, **options)
        self.home_y = y
        self.phase = rand_range(0.0, math.tau)

    def _state_patrol(self, dt: float, player) -> None:
        if self.can_see(player):
            self._enter_alert()
            return
        self.phase += dt * 1.4
        self.body.vx = math.cos(self.phase) * self.patrol_speed
        self.body.vy = math.sin(self.phase * 1.7) * 22.0
        self.facing = 1 if self.body.vx >= 0 else -1
        if abs(self.body.centerx - self.home_x) > self.patrol_range:
            self.body.vx *= -1


class Assassin(Enemy):
    """Yaklasana kadar neredeyse gorunmez; hizli ve kirilgan."""
    sprite_key = "assassin"
    max_health = 3
    chase_speed = 96.0
    sight_range = 150.0
    attack_range = 20.0
    windup_time = 0.22
    recover_time = 0.30
    damage = 1
    knockback = 120.0
    essence_drop = (6, 10)

    def draw(self, surface, camera) -> None:
        if not self.aggro and not self.dead:
            image = self.anim.image
            if image is not None:
                ghost = image if self.facing > 0 else pygame.transform.flip(
                    image, True, False)
                ghost = ghost.copy()
                ghost.set_alpha(70)
                ox, oy = camera.offset
                surface.blit(ghost, (
                    int(self.body.centerx - ghost.get_width() * 0.5) - ox,
                    int(self.body.y + self.body.h - self.sprite_foot_y) - oy))
                return
        super().draw(surface, camera)


class Mage(Enemy):
    """Uzaktan buyu firlatir, yaklasilinca kacar."""
    sprite_key = "mage"
    max_health = 3
    chase_speed = 46.0
    sight_range = 175.0
    attack_range = 145.0
    windup_time = 0.72
    recover_time = 1.0
    damage = 1
    essence_drop = (8, 13)
    retreat_range = 70.0

    _state_chase = Archer._state_chase
    _can_attack = Archer._can_attack

    def perform_attack(self, player) -> None:
        from lore.entities.projectile import Projectile
        if player is None:
            return
        angle = math.atan2(player.body.centery - self.body.centery,
                           player.body.centerx - self.body.centerx)
        # Uc yonlu yelpaze: tek bir bosluktan gecmek gerekir.
        for spread in (-0.22, 0.0, 0.22):
            self.scene.spawn_projectile(Projectile(
                self.scene, self.body.centerx, self.body.centery - 4,
                angle + spread, speed=112.0, kind="hex", owner=self,
                target_mask=MASK_PLAYER, damage=self.damage, gravity=0.0,
                lifetime=3.0))
        self.scene.app.audio.play("shoot", pitch=3.0, pos=self.body.center)


ENEMY_TYPES: dict[str, type[Enemy]] = {
    "grunt": Grunt,
    "goblin": Grunt,
    "archer": Archer,
    "skeleton": Skeleton,
    "brute": Brute,
    "wisp": Wisp,
    "assassin": Assassin,
    "mage": Mage,
}


def spawn_enemy(scene, kind: str, x: float, y: float, **options) -> Enemy | None:
    cls = ENEMY_TYPES.get(kind)
    if cls is None and kind == "gaoler":
        # Gecikmeli import: boss.py bu dosyayi (Enemy icin) ust seviyede
        # import ediyor, tersi daire olusturur.
        from lore.entities.boss import Gaoler
        cls = Gaoler
    if cls is None:
        print(f"[enemies] bilinmeyen dusman turu: {kind}")
        return None
    return cls(scene, x, y, **options)
