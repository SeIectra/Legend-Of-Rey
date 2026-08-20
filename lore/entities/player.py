"""Rey - oyuncu karakteri.

Bu dosya oyunun hissini belirleyen sayilari barindirir. Her biri deneyle
ayarlandi; degistirirken tek tek degistir.

Bir platformerin "adil" hissetmesini saglayan uc yardim burada:

  * **Coyote time** - kenardan dustukten sonra 0.10 sn daha ziplayabilirsin.
    Oyuncu tam kenarda ziplamak ister; bu pencere olmadan oyun "kaydi" der.
  * **Jump buffer** - yere inmeden hemen once basilan zipla yutulmaz, inince
    calisir. Girdi katmani zaten aksiyonlari tamponluyor.
  * **Apex hang** - ziplamanin tepe noktasinda yercekimi azalir. Havadaki
    kontrol suresi uzar, hedefe nisan almak kolaylasir.

Kombo sistemi girdiyi *kuyruga alir*: saldiri animasyonu bitmeden basilan tus
bir sonraki vurusa gecer. Boylece oyuncu tusa tam zamaninda basmak zorunda
kalmaz, ritim tutturmaya odaklanir.
"""
from __future__ import annotations


from lore.constants import MASK_ENEMY, MASK_PLAYER
from lore.core.input import Action
from lore.core.mathx import approach, clamp
from lore.entities.entity import Animator, Entity
from lore.gfx.sprites import ARCHETYPES, build_sprite_set
from lore.systems.combat import DamageResult, DamageType, melee_rect

# --- His ayarlari -----------------------------------------------------------
RUN_SPEED = 118.0
GROUND_ACCEL = 900.0
AIR_ACCEL = 620.0
GROUND_FRICTION = 1150.0
AIR_FRICTION = 260.0

JUMP_SPEED = 312.0
JUMP_CUT = 0.42             # Tus birakilinca yukari hiz bu oranla kirpilir
COYOTE_TIME = 0.10
APEX_THRESHOLD = 42.0       # Bu hizin altinda yercekimi azalir
APEX_GRAVITY = 0.62

DASH_SPEED = 268.0
DASH_TIME = 0.16
DASH_COOLDOWN = 0.42
DASH_IFRAMES = 0.15

WALL_SLIDE_SPEED = 62.0
WALL_JUMP_X = 168.0
WALL_JUMP_Y = 246.0
WALL_STICK_TIME = 0.12      # Duvardan ayrilirken yatay girdiyi kisa sure yut

# Kombo: (sure, hasar, menzil, geri tepme, ileri atilma)
COMBO = [
    {"state": "attack1", "time": 0.30, "damage": 1, "reach": 20, "height": 16,
     "knockback": 150.0, "lunge": 46.0, "hit_at": 0.42},
    {"state": "attack2", "time": 0.32, "damage": 1, "reach": 22, "height": 20,
     "knockback": 170.0, "lunge": 52.0, "hit_at": 0.45},
    {"state": "attack3", "time": 0.40, "damage": 2, "reach": 26, "height": 14,
     "knockback": 260.0, "lunge": 96.0, "hit_at": 0.48},
]
COMBO_WINDOW = 0.30         # Saldiri bitince zinciri surdurme suresi

PUNCH = {"state": "attack1", "time": 0.26, "damage": 1, "reach": 13, "height": 14,
         "knockback": 90.0, "lunge": 18.0, "hit_at": 0.45}

BACKSTAB_MULTIPLIER = 3     # Uyarisiz dusmana arkadan vurus


class Player(Entity):
    sprite_key = "rey"
    max_health = 6              # Yarim kalp = 1 birim
    team_mask = MASK_PLAYER
    body_w = 10
    body_h = 20
    iframe_time = 0.75

    def __init__(self, scene, x: float, y: float, save=None) -> None:
        super().__init__(scene, x, y)
        self.save = save
        self.max_health = save.max_health if save else Player.max_health
        self.health = save.health if save else self.max_health
        self.essence = save.essence if save else 0

        self.has_blade = save.has_blade if save else False
        self.abilities = set(save.abilities) if save else set()
        self.spells = list(save.spells) if save else []
        self.active_spell = self.spells[0] if self.spells else None

        self._build_sprites()

        # Durum
        self.state = "idle"
        self.coyote = 0.0
        self.jump_held = False
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.wall_dir = 0
        self.wall_stick = 0.0
        self.attack_timer = 0.0
        self.attack_index = -1
        self.attack_hit_spawned = False
        self.combo_window = 0.0
        self.queued_attack = False
        self.hurt_timer = 0.0
        self.death_timer = 0.0
        self.step_timer = 0.0
        self.air_time = 0.0
        self.can_double_jump = False

    # --- Kurulum ------------------------------------------------------------
    def _build_sprites(self) -> None:
        key = "rey_armed" if self.has_blade else "rey"
        spec = ARCHETYPES[key]
        self.sprite_foot_y = spec.foot_y
        sprite_set = self.scene.app.assets.generated(
            f"sprites:{key}", lambda: build_sprite_set(spec))
        self.anim = Animator(
            sprite_set,
            fps={"idle": 7, "run": 13, "fall": 8, "land": 14, "dash": 16,
                 "hurt": 10, "death": 7, "attack1": 17, "attack2": 16,
                 "attack3": 13, "wall_slide": 6, "cast": 9},
            looping={"idle": True, "run": True, "walk": True, "fall": True,
                     "wall_slide": True, "jump": False, "land": False,
                     "dash": False, "hurt": False, "death": False,
                     "attack1": False, "attack2": False, "attack3": False,
                     "crouch": False, "cast": False},
        )

    def grant_blade(self) -> None:
        if self.has_blade:
            return
        self.has_blade = True
        self._build_sprites()

    def has(self, ability: str) -> bool:
        return ability in self.abilities

    # --- Durum sorgulari ----------------------------------------------------
    @property
    def busy(self) -> bool:
        """Girdiyi yok sayan bir durumda miyiz?"""
        return self.attack_timer > 0.0 or self.dash_timer > 0.0 \
            or self.hurt_timer > 0.0 or self.dead

    @property
    def invulnerable(self) -> bool:
        return self.iframes > 0.0 or self.dash_timer > DASH_TIME - DASH_IFRAMES

    # --- Ana guncelleme -----------------------------------------------------
    def update(self, dt: float) -> None:
        if self.dead:
            self._update_dead(dt)
            return

        inp = self.scene.app.input
        self.iframes = max(0.0, self.iframes - dt)
        self.flash = max(0.0, self.flash - dt)
        self.dash_cooldown = max(0.0, self.dash_cooldown - dt)
        self.combo_window = max(0.0, self.combo_window - dt)
        self.wall_stick = max(0.0, self.wall_stick - dt)

        if self.hurt_timer > 0.0:
            self._update_hurt(dt)
        elif self.dash_timer > 0.0:
            self._update_dash(dt)
        elif self.attack_timer > 0.0:
            self._update_attack(dt, inp)
        else:
            self._update_free(dt, inp)

        self._apply_physics(dt)
        self._update_animation(dt)
        self._check_hazards()

    # --- Serbest hareket ----------------------------------------------------
    def _update_free(self, dt: float, inp) -> None:
        move = inp.axis_x
        if abs(move) < 0.2:
            move = 0.0
        # Duvardan ayrildiktan hemen sonra yatay girdiyi yut: duvar ziplamasi
        # tusa basili tutan oyuncuda geri duvara yapismaz.
        if self.wall_stick > 0.0:
            move = 0.0

        if move != 0.0:
            self.facing = 1 if move > 0 else -1

        accel = GROUND_ACCEL if self.body.grounded else AIR_ACCEL
        friction = GROUND_FRICTION if self.body.grounded else AIR_FRICTION
        if move != 0.0:
            self.body.vx = approach(self.body.vx, move * RUN_SPEED, accel * dt)
        else:
            self.body.vx = approach(self.body.vx, 0.0, friction * dt)

        # Zemin temasi ve coyote penceresi
        if self.body.grounded:
            self.coyote = COYOTE_TIME
            self.can_double_jump = self.has("double_jump")
            if not self.body.was_grounded and self.air_time > 0.25:
                self._on_land()
            self.air_time = 0.0
        else:
            self.coyote = max(0.0, self.coyote - dt)
            self.air_time += dt

        self._update_wall_state(inp)

        # Zipla
        if inp.buffered(Action.JUMP):
            if self.wall_dir != 0 and self.has("wall_jump"):
                inp.consume(Action.JUMP)
                self._wall_jump()
            elif self.coyote > 0.0:
                inp.consume(Action.JUMP)
                self._jump()
            elif self.can_double_jump:
                inp.consume(Action.JUMP)
                self.can_double_jump = False
                self._jump(double=True)

        # Degisken zipla yuksekligi
        if not inp.held(Action.JUMP) and self.body.vy < 0.0 and self.jump_held:
            self.body.vy *= JUMP_CUT
            self.jump_held = False

        # Dash
        if inp.buffered(Action.DASH) and self.dash_cooldown <= 0.0:
            if self.has("dash"):
                inp.consume(Action.DASH)
                self._start_dash()
                return
            if inp.pressed(Action.DASH):
                # Kilitli yetenege basinca sessiz kalmak en kotu geri bildirim:
                # oyuncu tusun bozuk oldugunu sanir.
                inp.consume(Action.DASH)
                self.scene.show_toast("Atilma yetenegini henuz ogrenmedin.")
                self.scene.app.audio.play("ui_back")

        # Saldiri
        if inp.buffered(Action.ATTACK):
            inp.consume(Action.ATTACK)
            self._start_attack()
            return

        # Tek yonlu platformdan asagi in
        self.body.drop_through = (inp.held(Action.DOWN)
                                  and inp.held(Action.JUMP)
                                  and self.body.on_platform)

        # Etkilesim
        if inp.pressed(Action.INTERACT):
            self.scene.try_interact(self)

    def _update_wall_state(self, inp) -> None:
        """Duvara yapisma: sadece havada, duvara dogru basiliyken ve dusuyorken."""
        self.wall_dir = 0
        if self.body.grounded or self.body.vy < 0.0:
            return
        if not self.has("wall_jump"):
            return
        if self.body.wall_right and inp.axis_x > 0.3:
            self.wall_dir = 1
        elif self.body.wall_left and inp.axis_x < -0.3:
            self.wall_dir = -1
        if self.wall_dir != 0:
            self.body.vy = min(self.body.vy, WALL_SLIDE_SPEED)
            self.facing = -self.wall_dir      # Duvara bakar

    def _jump(self, double: bool = False) -> None:
        self.body.vy = -JUMP_SPEED * (0.88 if double else 1.0)
        self.coyote = 0.0
        self.jump_held = True
        self.air_time = 0.01
        self.scene.app.audio.play("jump", pitch=1.5 if double else 0.0,
                                  pos=self.body.center)
        self.scene.spawn_dust(self.body.feet, count=4)
        if double:
            self.scene.spawn_effect("ring", self.body.center, ramp="azure",
                                    radius=14)

    def _wall_jump(self) -> None:
        self.body.vx = -self.wall_dir * WALL_JUMP_X
        self.body.vy = -WALL_JUMP_Y
        self.facing = -self.wall_dir
        self.wall_stick = WALL_STICK_TIME
        self.wall_dir = 0
        self.jump_held = True
        self.scene.app.audio.play("jump", pitch=-1.0, pos=self.body.center)
        self.scene.spawn_dust((self.body.centerx, self.body.centery), count=5)

    def _on_land(self) -> None:
        self.scene.app.audio.play("land", pos=self.body.center)
        self.scene.spawn_dust(self.body.feet, count=6)
        if self.air_time > 0.55:
            self.scene.camera.add_trauma(0.12)

    # --- Dash ---------------------------------------------------------------
    def _start_dash(self) -> None:
        self.dash_timer = DASH_TIME
        self.dash_cooldown = DASH_COOLDOWN
        self.body.vx = self.facing * DASH_SPEED
        self.body.vy = 0.0
        self.anim.play("dash", restart=True)
        self.scene.app.audio.play("dash", pos=self.body.center)
        self.scene.spawn_dust(self.body.feet, count=8)
        self.scene.camera.add_trauma(0.10)

    def _update_dash(self, dt: float) -> None:
        self.dash_timer -= dt
        # Dash boyunca yercekimi yok: mesafe tahmin edilebilir kalir.
        self.body.vy = 0.0
        self.body.vx = self.facing * DASH_SPEED
        self.scene.spawn_afterimage(self)
        if self.dash_timer <= 0.0:
            self.dash_timer = 0.0
            self.body.vx *= 0.45

    # --- Saldiri ------------------------------------------------------------
    def _start_attack(self) -> None:
        if not self.has_blade:
            spec = PUNCH
            self.attack_index = 0
        else:
            # Kombo penceresi acikken zinciri ilerlet, degilse bastan basla.
            if self.combo_window > 0.0:
                self.attack_index = (self.attack_index + 1) % len(COMBO)
            else:
                self.attack_index = 0
            spec = COMBO[self.attack_index]

        self.attack_timer = spec["time"]
        self.attack_hit_spawned = False
        self.queued_attack = False
        self.anim.play(spec["state"], restart=True)
        # Ileri atilma: saldiri hem hareket hem hasar. Havada daha az.
        lunge = spec["lunge"] * (0.55 if not self.body.grounded else 1.0)
        self.body.vx = self.facing * lunge
        self.scene.app.audio.play("swing", pitch=self.attack_index * 1.5 - 1.0,
                                  pos=self.body.center)

    def _update_attack(self, dt: float, inp) -> None:
        spec = self._attack_spec()
        self.attack_timer -= dt

        # Saldiri sirasinda hafif yon kontrolu: tamamen kilitlemek kotu hissettirir
        if abs(inp.axis_x) > 0.3 and self.attack_timer < spec["time"] * 0.4:
            self.body.vx = approach(self.body.vx, inp.axis_x * RUN_SPEED * 0.5,
                                    GROUND_ACCEL * 0.5 * dt)
        else:
            self.body.vx = approach(self.body.vx, 0.0, GROUND_FRICTION * 0.7 * dt)

        progress = 1.0 - (self.attack_timer / spec["time"])
        if not self.attack_hit_spawned and progress >= spec["hit_at"]:
            self.attack_hit_spawned = True
            self._spawn_attack_hitbox(spec)

        # Sonraki vurusu kuyruga al
        if inp.buffered(Action.ATTACK) and progress > 0.35:
            inp.consume(Action.ATTACK)
            self.queued_attack = True

        # Dash saldiriyi iptal edebilir: akici his icin onemli
        if inp.buffered(Action.DASH) and self.has("dash") and self.dash_cooldown <= 0.0:
            inp.consume(Action.DASH)
            self.attack_timer = 0.0
            self._start_dash()
            return

        if self.attack_timer <= 0.0:
            self.attack_timer = 0.0
            self.combo_window = COMBO_WINDOW if self.has_blade else 0.0
            if self.queued_attack and self.has_blade:
                self._start_attack()

    def _attack_spec(self) -> dict:
        if not self.has_blade:
            return PUNCH
        return COMBO[clamp(self.attack_index, 0, len(COMBO) - 1)]

    def _spawn_attack_hitbox(self, spec: dict) -> None:
        rect = melee_rect(self.body, self.facing, spec["reach"], spec["height"],
                          forward=2)
        self.scene.combat.attack(
            self, rect, spec["damage"], MASK_ENEMY,
            knockback=spec["knockback"],
            knockback_up=40.0 if self.attack_index < 2 else 90.0,
            lifetime=0.09,
            hitstop=0.05 + self.attack_index * 0.02,
            shake=0.14 + self.attack_index * 0.06,
            pierce=self.attack_index == 2,
            stagger=0.18 + self.attack_index * 0.08,
        )
        ramp = "bone" if self.has_blade else "ash"
        self.scene.spawn_slash(rect.center, self.facing, spec["reach"], ramp)

    # --- Hasar --------------------------------------------------------------
    def take_damage(self, amount: int, source=None, direction: int = 1,
                    knockback: float = 120.0, knockback_up: float = 60.0,
                    damage_type: DamageType = DamageType.PHYSICAL,
                    stagger: float = 0.2) -> DamageResult:
        if self.dead or self.invulnerable:
            return DamageResult(hit=False)

        self.health -= amount
        self.iframes = self.iframe_time
        self.flash = self.flash_time
        self.hurt_timer = 0.26
        self.attack_timer = 0.0
        self.dash_timer = 0.0
        self.combo_window = 0.0
        self.body.vx = direction * knockback
        self.body.vy = -knockback_up

        self.scene.app.audio.play("hurt", pos=self.body.center)
        self.scene.app.input.rumble(0.5, 0.7, 180)
        self.scene.camera.add_trauma(0.45)
        self.scene.app.hitstop(0.09)
        self.scene.on_player_hurt(amount)

        result = DamageResult(hit=True, amount=amount)
        if self.health <= 0:
            self.health = 0
            result.killed = True
            self.die(source)
        return result

    def _update_hurt(self, dt: float) -> None:
        self.hurt_timer -= dt
        self.body.vx = approach(self.body.vx, 0.0, 420.0 * dt)
        if self.hurt_timer <= 0.0:
            self.hurt_timer = 0.0

    def die(self, source=None) -> None:
        if self.dead:
            return
        self.dead = True
        self.death_timer = 1.5
        self.body.vx = 0.0
        self.body.vy = -140.0
        self.anim.play("death", restart=True)
        self.scene.app.audio.play("death", pos=self.body.center)
        self.scene.camera.add_trauma(0.7)
        self.scene.app.hitstop(0.18)
        self.scene.on_player_died()

    def _update_dead(self, dt: float) -> None:
        self.death_timer = max(0.0, self.death_timer - dt)
        self.body.apply_gravity(dt)
        self.body.vx = approach(self.body.vx, 0.0, 300.0 * dt)
        self.body.move(self.scene.tilemap, dt)
        if self.anim:
            self.anim.update(dt)

    def _check_hazards(self) -> None:
        if self.dead or self.invulnerable:
            return
        hazards = self.scene.tilemap.hazard_rects(self.body.rect)
        if not hazards:
            return
        # Dikenden geri tepme her zaman merkezden disari: oyuncu tuzaga
        # tekrar tekrar dusmesin.
        direction = 1 if self.body.centerx >= hazards[0].centerx else -1
        self.take_damage(1, direction=direction, knockback=150.0,
                         knockback_up=170.0, damage_type=DamageType.HAZARD)

    # --- Toplama ------------------------------------------------------------
    def add_essence(self, amount: int) -> None:
        self.essence += amount
        self.scene.app.audio.play("essence", pitch=(self.essence % 5) * 0.8)

    # --- Fizik ve animasyon -------------------------------------------------
    def _apply_physics(self, dt: float) -> None:
        if self.dash_timer <= 0.0:
            # Apex hafifligi: ziplamanin tepesinde yercekimi azalir.
            scale = APEX_GRAVITY if abs(self.body.vy) < APEX_THRESHOLD else 1.0
            if self.wall_dir != 0:
                scale = 0.55
            self.body.apply_gravity(dt, scale)
        self.body.move(self.scene.tilemap, dt)
        self.body.drop_through = False

    def _update_animation(self, dt: float) -> None:
        if self.dead:
            state = "death"
        elif self.hurt_timer > 0.0:
            state = "hurt"
        elif self.dash_timer > 0.0:
            state = "dash"
        elif self.attack_timer > 0.0:
            state = self._attack_spec()["state"]
        elif self.wall_dir != 0:
            state = "wall_slide"
        elif not self.body.grounded:
            state = "jump" if self.body.vy < -20.0 else "fall"
        elif abs(self.body.vx) > 12.0:
            state = "run"
        else:
            state = "idle"

        self.anim.play(state)
        # Kosu animasyonu gercek hiza baglanir: yavaslarken adimlar da yavaslar.
        speed = 1.0
        if state == "run":
            speed = clamp(abs(self.body.vx) / RUN_SPEED, 0.45, 1.35)
            self._footsteps(dt, speed)
        self.anim.update(dt, speed)

    def _footsteps(self, dt: float, speed: float) -> None:
        self.step_timer -= dt * speed
        if self.step_timer <= 0.0:
            self.step_timer = 0.28
            self.scene.app.audio.play("step", volume=0.7,
                                      pitch=(self.scene.app.frame % 3) - 1,
                                      pos=self.body.center, dedupe=False)
            self.scene.spawn_dust(self.body.feet, count=1)

    # --- Kayit --------------------------------------------------------------
    def write_save(self, save) -> None:
        save.health = self.health
        save.max_health = self.max_health
        save.essence = self.essence
        save.has_blade = self.has_blade
        save.abilities = sorted(self.abilities)
        save.spells = list(self.spells)

    def debug_lines(self) -> list[str]:
        b = self.body
        return [
            f"POS {b.x:6.1f},{b.y:6.1f}  VEL {b.vx:6.1f},{b.vy:6.1f}",
            f"GND {int(b.grounded)} WALL {self.wall_dir:+d} COY {self.coyote:.2f}",
            f"ST {self.anim.state:10s} HP {self.health}/{self.max_health} "
            f"ESS {self.essence}",
        ]
