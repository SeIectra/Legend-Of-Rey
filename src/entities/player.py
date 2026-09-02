"""Oyuncu: hareket, ziplama, uclu zincir, kacinma, karsi vurus.

Rey ve Ardo ayni sinifi paylasir; sayisal farklar `character_stats.py`'de
(docs/dovus-sistemi.md 8). Rey bilgiyle ve akisla kazanir, Ardo zamanlamayla
ve dayaniklilikla.

Cizim uc kipte calisir (F4): sprite, siluet ve kutu. Kutu kipi "kutularla
eglenceli mi?" sorusunu sprite'lari atmadan sormaya yarar.
"""
from __future__ import annotations

import pygame

from src.combat.combo import (
    AttackPhase, ChainState, ComboCounter, DodgeState, counter_damage,
)
from src.combat.hitbox import Hitbox, Team, melee_rect
from src.config import (
    LAND_FRAMES_HARD, LAND_FRAMES_SOFT, TURN_FRAMES,
    TURN_PIVOT_MIN_SPEED, HARD_LAND_AIR_FRAMES,
    APEX_GRAVITY_SCALE, APEX_SPEED_THRESHOLD, COYOTE_FRAMES, DODGE_SPEED,
     JUMP_CUT_MULTIPLIER, PLAYER_AIR_ACCEL,
    PLAYER_AIR_FRICTION, PLAYER_GROUND_ACCEL, PLAYER_GROUND_FRICTION,
    PLAYER_JUMP_SPEED, PLAYER_RUN_SPEED, STEP_DISTANCE_PX,
)
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.art.trail import WeaponTrail
from src.core.input import NEUTRAL_INPUT, Action
from src.entities.actor import Actor
from src.entities.character_stats import CharacterStats, REY
from src.combat import weapons
from src.entities.player_anim import attack_progress, update_animation
from src.entities.player_render import draw_player
from src.systems import abilities, charms, skilltree

ATTACK_REACH = 22
ATTACK_HEIGHT = 18
FINISHER_REACH = 28
FINISHER_HEIGHT = 22
# Saldiri sirasinda one atilma - saldiri hem hareket hem hasardir.
LUNGE_BY_INDEX = (0.9, 1.1, 2.0)
PLAYER_IFRAMES_ON_HIT = 45
HURT_ANIMATION_FRAMES = 14


class Player(Actor):
    team = Team.PLAYER
    body_width = 10
    body_height = 22
    iframes_on_hit = PLAYER_IFRAMES_ON_HIT
    # Girdiyi bu oyuncu mu aliyor.
    #
    # On alti bolumde sahnede tek bir `Player` var ve hep True. Bolum
    # 17 "Ikili Kule" ikisini birden sahneye koyuyor
    # (`docs/yapi.md` 119: *"iki `Player` nesnesi, aktif olani
    # `active_player` isaretcisiyle degistir"*) ve pasif olani
    # `NEUTRAL_INPUT` ile suruyor.
    controlled = True

    def __init__(self, scene, x: float, y: float,
                 stats: CharacterStats = REY) -> None:
        self.stats = stats
        self.max_health = stats.max_health
        super().__init__(scene, x, y)

        # Yetenek kapisi **tek yerde**. Dagitilsaydi biri mutlaka bir yerde
        # unutulur ve oyuncu henuz almadigi bir seyi yapabilirdi.
        self.abilities: set[str] = abilities.starting_set(stats.name.lower())
        # Takili tilsimlar. Yetenekten ayri tutuluyor: yetenek "yapabilir
        # misin", tilsim "ne kadar iyi yapiyorsun" sorusunu cevapliyor.
        self.charms: set[str] = set()
        # Acilmis yetenek agaci dugumleri. `charms` ile ayni desen:
        # kume, ve etkiler `skilltree.py`'deki toplayicilardan
        # geliyor. `PlayScene` kayittan dolduruyor.
        self.skills: set[str] = set()
        # Govdenin ne kadari suyun altinda (0..1). Sahne her karede
        # yaziyor; animasyon ve ses buna bakiyor. Susuz bolumlerde
        # hep 0.0 kaliyor.
        self.water_ratio = 0.0

        # Silah: Rey yumrukla baslar (kilici Bolum 1'de bulur), Ardo
        # egitimli bir yabanci - kilicla gelir (src/combat/weapons.py).
        # `self.animator`/`self.chain` bu silaha gore kuruluyor; ayri ayri
        # ilklendirilselerdi biri diger degisince unutulurdu.
        self.weapon = weapons.starting_weapon(stats.name.lower())
        self.chain = ChainState(window_frames=stats.chain_window,
                                chain_table=weapons.get(self.weapon).chain)
        self.trail = WeaponTrail()
        # Gecis kareleri (src/art/animation.py::_land/_turn):
        # kalan kare sayisi. 0 = gecis oynamayior.
        self.land_frames = 0
        self.turn_frames = 0
        self._last_facing = 1
        self._apply_weapon_sprite()
        self.dodge = DodgeState(charges=stats.dodge_charges,
                                max_charges=stats.dodge_charges)
        self.combo = ComboCounter()

        self.coyote_frames = 0
        self.jump_held = False
        self.air_frames = 0
        self.hurt_frames = 0        # Hasar animasyonu suresi
        # Anlatimin kontrolu kisa sureligine aldigi anlar (orn. Bolum 1'de
        # sarsintinin Rey'i yere sermesi). Girdi **yok sayilir**, fizik
        # surer - oyuncu dusup yuvarlanir, ekran donmaz.
        self.control_locked = 0
        self.last_hit_was_counter = False
        # Adim sesi - kare sayisi degil, alinan **mesafeye** gore tetiklenir
        # (STEP_DISTANCE_PX): yavas yuruyus de hizli kosu da dogal sikilikta
        # ses uretir.
        self._step_distance = 0.0

    # --- Durum sorgulari ----------------------------------------------------
    @property
    def invulnerable(self) -> bool:
        return self.iframes > 0 or self.dodge.invulnerable

    @property
    def busy(self) -> bool:
        return self.chain.busy or self.dodge.active or self.dead

    @property
    def state_name(self) -> str:
        if self.dead:
            return "olu"
        if self.dodge.active:
            return "kacinma"
        if self.chain.busy:
            return f"vurus{self.chain.index + 1}:{self.chain.phase.name.lower()}"
        if not self.body.grounded:
            return "havada"
        if abs(self.body.vx) > 0.2:
            return "kosu"
        return "bosta"

    # --- Ana guncelleme -----------------------------------------------------
    def update(self) -> None:
        if self.dead:
            self._update_dead()
            return

        # **Kontrol edilmeyen oyuncu komut almiyor** ama her seyi
        # yapmaya devam ediyor: yer cekimi, animasyon, dokunulmazlik,
        # ayak sesi. Bolum 17'de sahnede iki `Player` var ve girdiyi
        # yalnizca aktif olan aliyor (`docs/yapi.md` mekanik 10).
        #
        # Tek satir, cunku girdinin bu metoda tek bir girisi var.
        # `if self.controlled:` dallari serpistirmek ayni seyi bes
        # yerde tekrarlamak olurdu ve biri gunun birinde unutulurdu.
        inp = self.scene.game.input if self.controlled else NEUTRAL_INPUT
        if self.iframes > 0:
            self.iframes -= 1
        if self.hurt_frames > 0:
            self.hurt_frames -= 1
        self.flash.update()
        self.squash.update()
        self.trail.update()
        if self.land_frames > 0:
            self.land_frames -= 1
        if self.turn_frames > 0:
            self.turn_frames -= 1
        # Kosarken yon degistirmek tek karede aynalanma degil, bir PIVOT.
        # Yavas yururken tetiklenmiyor: yerinde donen karakter surekli
        # pivot yapardi ve hareket "kaygan" gorunurdu.
        if (self.facing != self._last_facing and self.body.grounded
                and abs(self.body.vx) > TURN_PIVOT_MIN_SPEED):
            self.turn_frames = TURN_FRAMES
        self._last_facing = self.facing

        self.dodge.update(self.body.grounded)
        if self.combo.update():
            self.scene.on_combo_reset()

        if self.control_locked > 0:
            self.control_locked -= 1
            self.hurt_frames = max(self.hurt_frames, 1)   # yerde
            self.body.approach_vx(0.0, 0.12)
        elif self.dodge.active:
            self._update_dodge()
        else:
            self._update_chain(inp)
            if not self.chain.busy or self.chain.phase is AttackPhase.RECOVERY:
                self._update_movement(inp)
            self._handle_actions(inp)

        self._apply_physics()
        self._update_ground_state()
        self._update_footsteps()
        self._update_animation()

    def _update_footsteps(self) -> None:
        """Yerde ve saldirmiyorken alinan mesafeyi biriktirir.

        Esik asilinca `scene.on_player_step()` cagrilir - hangi ses
        calinacagina (yer tipine gore) sahne karar verir.
        """
        if not self.body.grounded or self.chain.busy:
            self._step_distance = 0.0
            return
        self._step_distance += abs(self.body.vx)
        if self._step_distance >= STEP_DISTANCE_PX:
            self._step_distance -= STEP_DISTANCE_PX
            on_step = getattr(self.scene, "on_player_step", None)
            if on_step:
                on_step(self)

    def _update_animation(self) -> None:
        update_animation(self)

    def _attack_progress(self) -> float:
        return attack_progress(self)

    def _update_movement(self, inp) -> None:
        move = inp.axis_x
        if abs(move) < 0.2:
            move = 0.0

        # Saldiri sirasinda yon kontrolu kisitli - tamamen kilitlemek kotu
        # hissettirir, serbest birakmak vurusu anlamsizlastirir.
        authority = 1.0
        if self.chain.busy:
            authority = 0.45 if self.chain.phase is AttackPhase.RECOVERY else 0.0

        if move != 0.0 and authority > 0.0:
            self.facing = 1 if move > 0 else -1

        speed = PLAYER_RUN_SPEED * self.stats.move_multiplier
        accel = PLAYER_GROUND_ACCEL if self.body.grounded else PLAYER_AIR_ACCEL
        friction = (PLAYER_GROUND_FRICTION if self.body.grounded
                    else PLAYER_AIR_FRICTION)

        if move != 0.0 and authority > 0.0:
            self.body.approach_vx(move * speed * authority, accel)
        else:
            self.body.approach_vx(0.0, friction)

    def has(self, ability: str) -> bool:
        return ability in self.abilities

    def apply_skills(self, keys) -> None:
        """Kayittan gelen yetenekleri uygular.

        `PlayScene` sahne kurulurken cagiriyor. Duz bonuslar (can, zincir
        penceresi, kacinma sarji) **kurulus aninda** biniyor; carpanlar
        (hasar, savunma) her kullanimda toplayicilardan okunuyor.

        Ayrim bilincli: duz bonus bir kez uygulanmali (iki kez cagrilirsa
        can iki kat artardi), carpan ise her seferinde taze hesaplanmali
        (kosullu olanlar var - orn. yalniz combo yuksekken).
        """
        self.skills = set(keys)
        if not self.skills:
            return
        bonus_health = skilltree.max_health_bonus(self.skills)
        if bonus_health:
            self.max_health += bonus_health
            self.health = min(self.max_health, self.health + bonus_health)
        window_bonus = skilltree.chain_window_bonus(self.skills)
        if window_bonus:
            # Taban pencere (`docs/dovus-sistemi.md`, BAGLAYICI) degismiyor;
            # yetenek onun USTUNE ekliyor.
            self.chain.window_frames += window_bonus
        charge_bonus = skilltree.dodge_charge_bonus(self.skills)
        if charge_bonus and hasattr(self.dodge, "max_charges"):
            self.dodge.max_charges += charge_bonus

    def equip(self, charm: str) -> bool:
        """Tilsim tak. Zaten takiliysa `False` doner."""
        if charm in self.charms:
            return False
        self.charms.add(charm)
        return True

    def grant(self, ability: str) -> bool:
        """Yetenek kazandirir. Zaten varsa False doner."""
        if ability in self.abilities:
            return False
        self.abilities.add(ability)
        if ability == abilities.SWORD:
            self.equip_weapon(weapons.SWORD)
        return True

    def equip_weapon(self, key: str) -> None:
        """Silah degistir - yumruktan kilica, ileride hancer/baltaya.

        Zincir tablosu tamamen degisir (`src/combat/weapons.py`); yarim
        kalmis bir vurusun ortasinda silah degismez cunku `grant()` bunu
        yalnizca ability kazanildigi anda cagirir, o an zaten `chain.busy`
        degildir (yetenek diyalog/sandik anlarinda verilir, dovus aninda
        degil). Sprite, ayni iskeletten cikan "_armed" varyanti varsa
        degisir - yumruk kendi "silahsiz" sprite'ini kullanmaya devam eder.
        """
        self.weapon = key
        weapon = weapons.get(key)
        self.chain = ChainState(window_frames=self.stats.chain_window,
                                chain_table=weapon.chain)
        self._apply_weapon_sprite()

    def _apply_weapon_sprite(self) -> None:
        suffix = weapons.get(self.weapon).sprite_suffix
        sprite_name = f"{self.stats.sprite_name}{suffix}"
        if sprite_name not in CHARACTERS:
            sprite_name = self.stats.sprite_name
        self.animator = Animator(sprite_name)
        # Sprite hucresi karakterden buyuk; ayak cizgisini govdenin altina
        # hizalamak icin gerekli. Bilinmezse karakter havada durur.
        self.sprite_foot_y = CHARACTERS[sprite_name].foot_y

    def _handle_actions(self, inp) -> None:
        # Kacinma once bakilir: saldiriyi iptal edebilir, akiciligin kalbi bu.
        if inp.buffered(Action.DODGE) and self._can_dodge():
            inp.consume(Action.DODGE)
            self._start_dodge(inp)
            return

        if inp.buffered(Action.JUMP) and self._can_jump():
            inp.consume(Action.JUMP)
            self._jump()

        # Degisken ziplama yuksekligi
        if not inp.held(Action.JUMP) and self.body.vy < 0.0 and self.jump_held:
            self.body.vy *= JUMP_CUT_MULTIPLIER
            self.jump_held = False

        # Yumruk bastan acik - silah yok sayisi degil, ilk silah. Kilic/hancer/
        # balta zaten `equip_weapon()` ile zincir tablosunu degistiriyor.
        if inp.buffered(Action.ATTACK):
            inp.consume(Action.ATTACK)
            self._request_attack()

    def _can_jump(self) -> bool:
        return (self.coyote_frames > 0 and not self.chain.busy
                and not self.dodge.active)

    def _can_dodge(self) -> bool:
        if not self.has(abilities.DODGE):
            return False
        if not self.dodge.can_dodge:
            return False
        # Vurus 1 ve 2'nin recovery'si iptal edilebilir; bitiricininki edilemez.
        if self.chain.busy and not self.chain.cancelable:
            return False
        return True

    def _jump(self) -> None:
        self.body.vy = -PLAYER_JUMP_SPEED
        self.coyote_frames = 0
        self.jump_held = True
        self.air_frames = 1
        self.squash.jump()
        self.scene.on_player_jump(self)

    def _update_ground_state(self) -> None:
        if self.body.grounded:
            self.coyote_frames = COYOTE_FRAMES
            if not self.body.was_grounded and self.air_frames > 10:
                self.squash.land()
                # Yuksekten inen daha uzun toparlanir - inisin bedeli
                # dususun boyuna bagli olmali.
                self.land_frames = (LAND_FRAMES_HARD
                                    if self.air_frames >= HARD_LAND_AIR_FRAMES
                                    else LAND_FRAMES_SOFT)
                self.scene.on_player_land(self, self.air_frames)
            self.air_frames = 0
        else:
            self.coyote_frames = max(0, self.coyote_frames - 1)
            self.air_frames += 1

    def _apply_physics(self) -> None:
        if not self.dodge.active:
            # Apex hafifligi: ziplamanin tepesinde yercekimi azalir, havadaki
            # kontrol suresi uzar.
            scale = (APEX_GRAVITY_SCALE
                     if abs(self.body.vy) < APEX_SPEED_THRESHOLD else 1.0)
            self.body.apply_gravity(scale)
        self.body.move(self.scene.tilemap)
        self.body.drop_through = False

    # --- Kacinma ------------------------------------------------------------
    def _start_dodge(self, inp) -> None:
        direction = self.facing
        if abs(inp.axis_x) > 0.3:
            direction = 1 if inp.axis_x > 0 else -1
        self.facing = direction
        self.chain.cancel()
        self.dodge.start(direction)
        self.scene.on_player_dodge(self)

    def _update_dodge(self) -> None:
        # Kacinma boyunca yercekimi yok: mesafe tahmin edilebilir kalir.
        self.body.vx = self.dodge.direction * DODGE_SPEED
        self.body.vy = 0.0
        self.scene.on_dodge_trail(self)

    # --- Saldiri ------------------------------------------------------------
    def _request_attack(self) -> None:
        if self.chain.busy:
            self.chain.request_next()
            return
        self.chain.start(self.chain.next_index())
        self._apply_lunge()
        self.scene.on_player_attack(self, self.chain.index)

    def _apply_lunge(self) -> None:
        lunge = LUNGE_BY_INDEX[min(self.chain.index, len(LUNGE_BY_INDEX) - 1)]
        if not self.body.grounded:
            lunge *= 0.55
        self.body.vx = self.facing * lunge

    def _update_chain(self, inp) -> None:
        event = self.chain.update()
        if event == "spawn_hitbox":
            self._spawn_attack_hitbox()
        elif event == "chain":
            self._apply_lunge()
            self.scene.on_player_attack(self, self.chain.index)

    def _spawn_attack_hitbox(self) -> None:
        spec = self.chain.spec
        finisher = self.chain.is_finisher
        reach = FINISHER_REACH if finisher else ATTACK_REACH
        height = FINISHER_HEIGHT if finisher else ATTACK_HEIGHT

        damage = spec.damage
        is_counter = self.dodge.consume_counter()
        if is_counter:
            damage = counter_damage(damage, self.stats.counter_bonus)
        # Tilsim carpani vurus **uretilirken** biniyor; sonradan duzeltmek
        # olum esigini kaydirirdi (src/systems/charms.py).
        if self.charms:
            scale = charms.damage_scale(self.charms, self)
            if scale != 1.0:
                damage = max(1, round(damage * scale))
        # Yetenek agaci carpani da AYNI YERDE biniyor - tilsimla ayni
        # gerekce, ve ikisi carpimsal birlesiyor (bir dugum + bir tilsim
        # ust uste gelirse ikisi de sayiliyor).
        if self.skills:
            skill_scale = skilltree.damage_scale(self.skills, self)
            if skill_scale != 1.0:
                damage = max(1, round(damage * skill_scale))
        self.last_hit_was_counter = is_counter

        box = Hitbox(
            rect=melee_rect(self.body, self.facing, reach, height),
            damage=damage,
            owner=self,
            targets=Team.ENEMY | Team.BREAKABLE,
            knockback=spec.knockback,
            knockback_up=1.4 if finisher else 0.6,
            active_frames=spec.active,
            poise_damage=2 if finisher else 1,
            is_finisher=finisher,
            is_counter=is_counter,
            pierce=finisher,
        )
        self.scene.hitboxes.spawn(box)
        self.scene.on_attack_swing(self, box)

    def notify_kill(self) -> None:
        """Bir dusman oldu: recovery iptal olur (kill cancel).

        Kalabalik dovusun "bicip gecme" hissi tek basina bundan gelir.
        """
        self.chain.kill_cancel()

    def register_hit(self) -> None:
        """Vurus degdi: combo sayacini ilerlet."""
        for threshold in self.combo.register_hit():
            self.scene.on_combo_threshold(self, threshold)

    # --- Hasar --------------------------------------------------------------
    def take_damage(self, box, direction):
        # Yanki acikken savunma duser - bedelin en somut parcasi.
        # Carpani hasar **uygulanmadan** once bindiriyoruz; sonradan
        # duzeltmek olum esigini kaydirirdi.
        echo = getattr(self.scene, "echo", None)
        original = box.damage
        if echo is not None and echo.active:
            box.damage = max(1, round(box.damage * echo.damage_multiplier))
        # Yetenek agacinin SAVUNMA carpani (TAS dali + Yanki SIPER'i).
        # `<1.0` koruma demek. Yanki cezasindan SONRA biniyor: siper
        # yeteneginin isi tam olarak o cezayi hafifletmek, o yuzden onun
        # ustune uygulanmali - once uygulansaydi ceza siperi yutardi.
        if self.skills:
            guard = skilltree.defence_scale(self.skills, self)
            if guard != 1.0:
                box.damage = max(1, round(box.damage * guard))
        try:
            result = super().take_damage(box, direction)
        finally:
            box.damage = original
        if result.hit:
            self.chain.cancel()
            self.combo.reset()
            self.hurt_frames = HURT_ANIMATION_FRAMES
            self.scene.on_player_hurt(self, result)
        return result

    def die(self) -> None:
        super().die()
        self.scene.on_player_died(self)

    def _update_dead(self) -> None:
        self.body.approach_vx(0.0, PLAYER_GROUND_FRICTION)
        self.body.apply_gravity()
        self.body.move(self.scene.tilemap)
        self.flash.update()

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface, offset: tuple[int, int]) -> None:
        draw_player(self, surface, offset)

    def debug_lines(self) -> list[str]:
        return [
            f"{self.stats.name}  {self.state_name}",
            f"can {self.health}/{self.max_health}  combo {self.combo.count}"
            f" (en iyi {self.combo.best})",
            f"kacinma sarj {self.dodge.charges}  "
            f"karsi {self.dodge.counter_window_left}  "
            f"coyote {self.coyote_frames}",
        ]
