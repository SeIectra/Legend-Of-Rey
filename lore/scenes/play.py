"""Oynanis sahnesi - tum sistemlerin bulustugu yer.

Cizim sirasi bilinctir ve degistirilirken dikkat ister:

    gokyuzu -> parallax -> arka tile -> arka prop -> varliklar -> tile
    -> on prop -> parcaciklar -> hava -> ISIK -> parlama -> post-fx -> HUD

Isik varliklardan *sonra* uygulanir ki karakterler de karanlikta kalsin; HUD
ise isiktan sonra cizilir ki arayuz her zaman tam parlaklikta okunsun.

Sahne ayni zamanda geri bildirim merkezidir: `on_hit`, `on_parry`,
`on_enemy_died` gibi kancalar hitstop, sarsinti, partikul ve sesi tek yerde
toplar. Varliklarin kendi efektlerini uydurmasi tutarsizlik uretirdi.
"""
from __future__ import annotations

import math
import random

import pygame


from lore.core.input import Action
from lore.core.mathx import rand_range
from lore.core.scene import Scene
from lore.entities.enemies import spawn_enemy
from lore.entities.pickups import Door, EssenceOrb, HeartPickup, spawn_prop
from lore.entities.player import Player
from lore.gfx import text as gfx_text
from lore.gfx.lighting import GlowLayer, LightMap
from lore.gfx.particles import (
    Afterimage, DamageNumber, ParticleField, SpriteEffect,
)
from lore.gfx.postfx import PostFX
from lore.gfx.tiles import build_impact, build_ring, build_slash
from lore.gfx.ui import HUD
from lore.systems.combat import CombatSystem
from lore.world.level import Level, LevelIndex
from lore.world.parallax import Parallax, Weather

INTERACT_RANGE = 22.0

# Yetenek adlari ve hangi aksiyona bagli olduklari. Bir yetenegi acip tusunu
# soylememek oyuncuyu menuye bakmaya zorlar; ad ile tus hep birlikte gider.
ABILITY_INFO: dict[str, tuple[str, Action, str]] = {
    "dash": ("Atilma", Action.DASH,
             "Kisa bir sicrayis - sirasinda hasar almazsin"),
    "double_jump": ("Cift Ziplama", Action.JUMP,
                    "Havadayken bir kez daha zipla"),
    "wall_jump": ("Duvar Sicramasi", Action.JUMP,
                  "Duvara yaslanip karsiya sicra"),
}


def ability_unlock_text(app, ability: str) -> str:
    """Yetenek adi + tusu + ne ise yaradigi, tek satirda.

    480 piksel genislikte 5x11 fontla ~78 karakter siger; asagidaki metinler
    bu sinira gore yazildi.
    """
    name, action, hint = ABILITY_INFO.get(ability, (ability, Action.JUMP, ""))
    label = app.input.binding_label(action)
    return f"{name} [{label}] - {hint}"


class PlayScene(Scene):
    blocks_update = True
    blocks_draw = True

    def on_enter(self, level_id: str = "", save=None, index=None) -> None:
        self.index: LevelIndex = index or LevelIndex()
        self.save = save

        from lore.core.camera import Camera
        self.camera = Camera()

        self.combat = CombatSystem(self)
        self.particles = ParticleField()
        self.effects: list = []
        self.projectiles: list = []
        self.pickups: list = []
        self.enemies: list = []
        self.props: list = []
        self.damage_numbers: list = []

        self.lights = LightMap()
        self.glow = GlowLayer()
        self.postfx = PostFX(self.app.config)
        self.hud = HUD(self.app)

        self.player: Player | None = None
        self.boss = None
        self.level: Level | None = None
        self.parallax: Parallax | None = None
        self.weather = Weather("none")

        self.paused = False
        self.death_delay = 0.0
        self.pending_level = ""
        self.level_time = 0.0
        self.interact_target = None

        self.camera.shake_scale = float(self.app.config.get("screen_shake", 1.0))
        self.load_level(level_id or self.index.first())

    # --- Bolum yukleme ------------------------------------------------------
    def load_level(self, level_id: str, keep_player: bool = True) -> None:
        definition = self.index.get(level_id)
        if definition is None:
            print(f"[play] bolum bulunamadi: {level_id}")
            if not self.index.all_ids():
                return
            definition = self.index.get(self.index.first())
            if definition is None:
                return

        self.level = Level(definition)
        self.tilemap = self.level.tilemap
        self.level_time = 0.0

        for problem in self.level.validate():
            print(f"[level:{self.level.id}] {problem}")

        self.combat.clear()
        self.particles.clear()
        self.effects.clear()
        self.projectiles.clear()
        self.pickups.clear()
        self.enemies.clear()
        self.props.clear()
        self.damage_numbers.clear()

        self.parallax = Parallax(definition.theme, self.app.assets)
        self.weather = Weather(definition.weather)
        self.lights.set_act(definition.act)
        self.postfx.set_act(definition.act)

        spawn_x, spawn_y = self.level.spawn_point
        if self.player is None or not keep_player:
            self.player = Player(self, spawn_x, spawn_y, self.save)
        else:
            self.player.body.set_feet(spawn_x, spawn_y)
            self.player.body.vx = self.player.body.vy = 0.0
            self.player.dead = False
            self.player.scene = self

        for kind, x, y, options in self.level.entity_spawns():
            enemy = spawn_enemy(self, kind, x, y, **options)
            if enemy is not None:
                self.enemies.append(enemy)

        # Bolumde boss varsa HUD can barinin okuyacagi referans budur. Her
        # bolum yuklemesinde yeniden hesaplanir - olumden sonra yeniden
        # denemede boss da tam canla sifirlanir.
        self.boss = next((e for e in self.enemies if getattr(e, "is_boss", False)),
                         None)

        for kind, x, y, options in self.level.prop_spawns():
            prop = spawn_prop(self, kind, x, y, **options)
            if prop is not None:
                self.props.append(prop)

        self.camera.set_bounds(self.level.bounds)
        self.camera.snap_to(self.player.body.centerx, self.player.body.centery)

        if self.save:
            self.save.level_id = self.level.id
            self.save.act = self.level.act

        if definition.music:
            self.app.audio.play_music(definition.music)
        if self.level.name:
            self.hud.show_level_title(self.level.name)
        if definition.intro:
            self.hud.show_toast(definition.intro, 4.0)

    def transition_to_level(self, target: str) -> None:
        if not target:
            target = self.index.next_after(self.level.id) if self.level else ""
        if not target:
            self.hud.show_toast("Bu yolun sonu... simdilik.")
            return
        self.pending_level = target
        self.app.scenes.transition.start(self._do_transition)

    def _do_transition(self) -> None:
        if self.pending_level:
            if self.save and self.player:
                self.player.write_save(self.save)
                if self.level and self.level.id not in self.save.levels_cleared:
                    self.save.levels_cleared.append(self.level.id)
            self.load_level(self.pending_level)
            self.pending_level = ""

    # --- Girdi --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from lore.scenes.pause import PauseScene
            self.manager.push(PauseScene, save=self.save)

    # --- Guncelleme ---------------------------------------------------------
    def update(self, dt: float) -> None:
        if dt <= 0.0:
            return
        self.level_time += dt
        if self.save:
            self.save.playtime += dt

        self.app.audio.set_listener(*self.camera.view_rect.center)

        if self.player is not None:
            self.player.update(dt)

        for enemy in self.enemies:
            enemy.update(dt)
        for projectile in self.projectiles:
            projectile.update(dt)
        for pickup in self.pickups:
            pickup.update(dt)
        for prop in self.props:
            prop.update(dt)

        self.combat.update(dt, self.player, self.enemies)

        self.particles.update(dt)
        for group in (self.effects, self.damage_numbers):
            for item in group:
                item.update(dt)

        self._prune()
        self._update_interaction()
        self._update_camera(dt)

        self.weather.update(dt)
        self.postfx.update(dt)
        self.postfx.low_health = bool(
            self.player and not self.player.dead
            and self.player.health <= 2)
        self.hud.update(dt, self.player)

        if self.player is not None and self.player.dead:
            self.death_delay += dt
            if self.death_delay > 1.8:
                self._respawn()

        self._check_fall_out()

    def _prune(self) -> None:
        self.enemies = [e for e in self.enemies if not e.remove]
        self.projectiles = [p for p in self.projectiles if not p.remove]
        self.pickups = [p for p in self.pickups if not p.remove]
        self.effects = [e for e in self.effects if not e.remove]
        self.damage_numbers = [d for d in self.damage_numbers if not d.remove]
        self.props = [p for p in self.props if not p.remove]

    def _update_camera(self, dt: float) -> None:
        if self.player is None:
            return
        body = self.player.body
        self.camera.update(dt, body.centerx, body.centery - 6,
                           facing=self.player.facing, grounded=body.grounded)

    def _update_interaction(self) -> None:
        self.interact_target = None
        self.hud.prompt = ""
        if self.player is None or self.player.dead:
            return
        best = None
        best_distance = INTERACT_RANGE
        for prop in self.props:
            if not prop.interactive:
                continue
            distance = math.hypot(prop.x - self.player.body.centerx,
                                  prop.y - self.player.body.centery - 8)
            if distance < best_distance:
                best = prop
                best_distance = distance
        if best is not None:
            self.interact_target = best
            self.hud.prompt = f"[E] {best.prompt}"

    def try_interact(self, player) -> None:
        if self.interact_target is not None:
            self.interact_target.interact(player)

    def _check_fall_out(self) -> None:
        """Haritanin altina dusen oyuncu olur. Sonsuza dusmek hata degil, ceza."""
        if self.player is None or self.player.dead or self.level is None:
            return
        if self.player.body.y > self.level.bounds.bottom + 40:
            self.player.take_damage(99, knockback=0.0, knockback_up=0.0)
            if not self.player.dead:            # Dokunulmazsa yine de geri koy
                self._reset_to_checkpoint()

    def _respawn(self) -> None:
        self.death_delay = 0.0
        if self.save:
            self.save.deaths += 1
        self.player.health = self.player.max_health
        self.player.dead = False
        self.player.iframes = 1.0
        self.player.anim.play("idle", restart=True)
        self._reset_to_checkpoint()
        self.load_level(self.level.id if self.level else self.index.first())

    def _reset_to_checkpoint(self) -> None:
        if self.level is None or self.player is None:
            return
        x, y = self.level.spawn_point
        self.player.body.set_feet(x, y)
        self.player.body.vx = self.player.body.vy = 0.0
        self.camera.snap_to(x, y)

    # --- Geri bildirim kancalari --------------------------------------------
    def on_hit(self, box, target, result) -> None:
        """Bir vurus degdi. Tum duyusal geri bildirim burada toplanir."""
        pos = (target.body.centerx, target.body.centery)
        self.app.hitstop(box.hitstop)
        self.camera.add_trauma(box.shake)
        self.spawn_effect("impact", pos,
                          ramp="gold" if target is not self.player else "blood")
        self.spawn_particles(pos, 6 + result.amount * 2,
                             ramp="blood" if target is not self.player else "ember")
        self.app.audio.play("hit_flesh", pitch=rand_range(-1.5, 1.5), pos=pos)

        if self.app.config.get("damage_numbers", True) and target is not self.player:
            self.damage_numbers.append(
                DamageNumber(pos[0], pos[1] - 10, result.amount,
                             crit=result.amount >= 3))
        if box.owner is self.player:
            self.app.input.rumble(0.25, 0.4, 90)

    def on_parry(self, target, box) -> None:
        pos = (target.body.centerx, target.body.centery)
        self.app.hitstop(0.14)
        self.camera.add_trauma(0.3)
        self.spawn_effect("ring", pos, ramp="gold", radius=20)
        self.app.audio.play("parry", pos=pos)

    def on_backstab(self, enemy) -> None:
        pos = (enemy.body.centerx, enemy.body.centery)
        self.app.hitstop(0.11)
        self.camera.add_trauma(0.26)
        self.spawn_effect("ring", pos, ramp="ember", radius=16)
        self.hud.show_toast("Sirttan vurus!", 1.2)

    def on_enemy_died(self, enemy) -> None:
        pos = (enemy.body.centerx, enemy.body.centery)
        self.camera.add_trauma(0.22)
        self.spawn_particles(pos, 14, ramp="blood")
        low, high = enemy.essence_drop
        for _ in range(random.randint(low, high)):
            self.pickups.append(EssenceOrb(self, pos[0], pos[1], 1))
        # Nadiren kalp dusur - can yonetimini savasa baglar.
        if self.player and self.player.health <= self.player.max_health - 2:
            if random.random() < 0.22:
                self.pickups.append(HeartPickup(self, pos[0], pos[1]))
        if self.save:
            self.save.kills += 1

    def on_boss_defeated(self, boss) -> None:
        """Boss.die() tarafindan cagrilir - on_enemy_died'in ustune biner."""
        pos = (boss.body.centerx, boss.body.centery)
        self.boss = None
        self.camera.add_trauma(0.6)
        self.app.hitstop(0.2)
        self.spawn_particles(pos, 24, ramp="blood")
        self.spawn_effect("ring", pos, ramp="gold", radius=40)
        for _ in range(14):
            self.pickups.append(EssenceOrb(self, pos[0], pos[1], 1))
        # Arenanin kilitli kapisi: boss dusunce acilir. Genel kural -
        # odada kilitli kapi varsa o, o odanin cikisidir.
        for prop in self.props:
            if isinstance(prop, Door) and prop.locked:
                prop.locked = False
        if self.save:
            self.save.flags["act1_boss_cleared"] = True
        self.hud.show_toast(f"{boss.display_name} dustu.", 3.0)

    def on_player_hurt(self, amount: int) -> None:
        self.postfx.flash((220, 40, 50), 0.45, 0.2)

    def on_player_died(self) -> None:
        self.death_delay = 0.0
        self.postfx.flash((160, 20, 30), 0.7, 0.5)
        self.app.audio.duck(0.3)

    def on_checkpoint(self, shrine, first_time: bool) -> None:
        if self.save:
            self.save.checkpoint = shrine.id
            from lore.core.save import save_slot
            self.player.write_save(self.save)
            save_slot(getattr(self.save, "slot", 0), self.save)
        self.hud.show_toast("Yanki kaydedildi." if first_time else "Kayit guncellendi.")

    def on_chest_opened(self, chest) -> None:
        if chest.contents == "essence":
            for _ in range(chest.amount):
                self.pickups.append(
                    EssenceOrb(self, chest.x, chest.y - 8, 1))
        elif chest.contents == "heart_shard":
            self.hud.show_toast("Kalp parcasi bulundu!")
            if self.save:
                self.save.heart_shards += 1
                if self.save.heart_shards % 4 == 0:
                    self.player.max_health += 2
                    self.player.health = self.player.max_health
                    self.hud.show_toast("Azami can arttı!")
        elif chest.contents == "blade":
            self.player.grant_blade()
            self.hud.show_toast("Echobrand senin.", 3.5)
            self.spawn_effect("ring", (chest.x, chest.y - 8), ramp="gold",
                              radius=34)
        elif chest.contents in ("dash", "double_jump", "wall_jump"):
            self.player.abilities.add(chest.contents)
            self.hud.show_toast(ability_unlock_text(self.app, chest.contents), 4.5)
            self.spawn_effect("ring", (chest.x, chest.y - 8), ramp="azure",
                              radius=26)

    def show_toast(self, message: str) -> None:
        self.hud.show_toast(message)

    # --- Efekt uretimi ------------------------------------------------------
    def spawn_particles(self, pos, count: int, ramp: str = "ash",
                        glow: int = 0) -> None:
        self.particles.emit(pos[0], pos[1], count, ramp=ramp, glow=glow,
                            speed=(30.0, 110.0), life=(0.2, 0.55))

    def spawn_dust(self, pos, count: int = 4) -> None:
        self.particles.emit(pos[0], pos[1] - 1, count, ramp="ash",
                            speed=(10.0, 42.0), angle=(-math.pi * 0.85,
                                                       -math.pi * 0.15),
                            life=(0.18, 0.4), gravity=40.0, size=(1.0, 2.0))

    def spawn_effect(self, kind: str, pos, ramp: str = "gold",
                     radius: float = 20.0) -> None:
        if kind == "impact":
            frames = self.app.assets.generated(
                f"fx:impact:{ramp}",
                lambda: [build_impact(i, 4, ramp) for i in range(4)])
            self.effects.append(SpriteEffect(frames, pos[0], pos[1], fps=30,
                                             additive=True))
        elif kind == "ring":
            key = f"fx:ring:{ramp}:{int(radius)}"
            frames = self.app.assets.generated(
                key, lambda: [build_ring(i, 6, ramp, radius) for i in range(6)])
            self.effects.append(SpriteEffect(frames, pos[0], pos[1], fps=22,
                                             additive=True))

    def spawn_slash(self, pos, facing: int, reach: int, ramp: str = "bone") -> None:
        key = f"fx:slash:{ramp}:{reach}"
        frames = self.app.assets.generated(
            key, lambda: [build_slash(i, 4, reach * 1.1, 2.3, ramp)
                          for i in range(4)])
        self.effects.append(SpriteEffect(frames, pos[0], pos[1], fps=34,
                                         flip=facing < 0, additive=True))

    def spawn_afterimage(self, entity) -> None:
        image = entity.anim.image if entity.anim else None
        if image is None:
            return
        if entity.facing < 0:
            image = pygame.transform.flip(image, True, False)
        x = entity.body.centerx - image.get_width() * 0.5
        foot = entity.sprite_foot_y or image.get_height()
        y = entity.body.y + entity.body.h - foot
        self.effects.append(Afterimage(image, x, y))

    def spawn_alert(self, enemy) -> None:
        self.spawn_particles((enemy.body.centerx, enemy.body.y - 4), 3,
                             ramp="gold", glow=120)

    def spawn_projectile(self, projectile) -> None:
        self.projectiles.append(projectile)

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        if self.level is None:
            surface.fill((0, 0, 0))
            return

        if self.parallax:
            self.parallax.draw(surface, self.camera)

        self.tilemap.draw(surface, self.camera)

        for prop in self.props:
            prop.draw(surface, self.camera)

        for pickup in self.pickups:
            pickup.draw(surface, self.camera)
        for enemy in self.enemies:
            if self.camera.is_visible(enemy.hurtbox):
                enemy.draw(surface, self.camera)
        for projectile in self.projectiles:
            projectile.draw(surface, self.camera)
        if self.player is not None:
            self.player.draw(surface, self.camera)

        self.particles.draw(surface, self.camera)
        for effect in self.effects:
            effect.draw(surface, self.camera)

        self.weather.draw(surface)

        self._render_lights(surface)

        for number in self.damage_numbers:
            number.draw(surface, self.camera)

        self.postfx.render(surface)
        self.hud.draw(surface, self.player, self)

        if self.app.debug:
            self._draw_debug(surface)

    def _render_lights(self, surface: pygame.Surface) -> None:
        self.lights.begin()
        for prop in self.props:
            light = prop.light()
            if light is not None:
                x, y, radius, color = light
                self.lights.add(x, y, radius, color)
        if self.player is not None and not self.player.dead:
            # Oyuncunun etrafinda hafif bir isik: karanlik odalarda kaybolmasin.
            self.lights.add(self.player.body.centerx, self.player.body.centery,
                            64.0, (170, 190, 230), 0.75)
        for effect in self.effects:
            if isinstance(effect, SpriteEffect) and effect.additive:
                self.lights.add(effect.x, effect.y, 26.0, (255, 220, 180), 0.6)
        self.lights.render(surface, self.camera)

    def _draw_debug(self, surface: pygame.Surface) -> None:
        self.tilemap.draw_debug(surface, self.camera)
        if self.player:
            self.player.draw_debug(surface, self.camera)
        for enemy in self.enemies:
            enemy.draw_debug(surface, self.camera)
            ox, oy = self.camera.offset
            gfx_text.draw_text(surface, enemy.state,
                               int(enemy.body.centerx) - ox,
                               int(enemy.body.y) - oy - 10,
                               color=(255, 220, 120), align="center")
        ox, oy = self.camera.offset
        for box in self.combat.hitboxes:
            pygame.draw.rect(surface, (255, 90, 90),
                             (box.rect.x - ox, box.rect.y - oy,
                              box.rect.w, box.rect.h), 1)

    def debug_lines(self) -> list[str]:
        lines = [
            f"LVL {self.level.id if self.level else '-'} "
            f"({self.tilemap.w}x{self.tilemap.h})",
            f"ENT dusman={len(self.enemies)} mermi={len(self.projectiles)} "
            f"efekt={len(self.effects)} parca={self.particles.count}",
        ]
        if self.player:
            lines.extend(self.player.debug_lines())
        return lines
