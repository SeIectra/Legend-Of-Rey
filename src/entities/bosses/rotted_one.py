"""Curumus Olan - BOSS 1, Bolum 6.

`docs/gdd.md` 8: dort buyuk boss, ilki B6'da. `docs/gdd.md` 10:
*"6 | ARDO | Havali giris, ilk team-up, **BOSS 1**"*.

## Neden bu boss boyle

Katman 1'in (Curuyenler, B1-B6) **finali**. Mini-boss'lar "buyutulmus
dusman + bir ek hamle" (ucuz, bilincli); boss'un isi baska - `docs/gdd.md`
8: *"kendi arenasi, kendi animasyon seti, faz gecisleri, ezberlenecek
tell'ler"*.

Uc fazin her biri Katman 1'in bir dusmanini geri getiriyor:

    Faz 0  SURUKLENEN   yerde ritim: savurma + hamle
    Faz 1  TIRMANAN     tavana tirmanir, ustune dusar
    Faz 2  SISMEK       yavru dogurur, kendi radyal patlamasi var

Yani boss **yeni bir sey ogretmiyor, tierin sinavini yapiyor**. Oyuncu
alti bolumde ogrendigi uc okumayi tek dovuste sirayla kullanmak zorunda.
Bu, `docs/gdd.md` 9'un "yeni mekanik + eski mekanik = yeni bulmaca"
kuralinin dovus tarafindaki karsiligi.

## Faz 2'nin muhru - **team-up buraya giriyor**

`docs/yapi.md` B6: *"ilk team-up dovusu + agirlik plakalari (ikisi ayri
plakada durmali - beraberlik mekanige giriyor)"*.

Faz 2'ye gecince boss **muhurleniyor**: hicbir vurus islemiyor. Muhur
yalnizca arenanin iki plakasi ayni anda basiliyken kiriliyor ve boss
`PLATE_STUN_FRAMES` boyunca savunmasiz kaliyor.

Tek kisi iki plakaya birden basamaz. Yani oyuncu yoldasa "su plakaya bas"
demek, kendisi otekine kosmak ve boss'u pencerede dovmek zorunda -
**anlati soylemeden**, dovusun kendisi "bunu beraber yapmalisiniz"
diyor. B6'nin tamami zaten bu cumle.

Muhur "hasar azalir" degil "hasar GECMEZ": azalma sayisal bir sey olurdu
ve oyuncu farki fark etmeden vurmaya devam ederdi. Gecmemek bir KURAL, ve
kurallar ogretilir (ayni gerekce `shadow_shambler.py` ve
`shieldbearer.py`'de de yazili).

## Ritim yine sabit

Hamle sirasi rastgele degil (`docs/derinlestirme.md` 4.2). Rastgele bir
boss ogrenilemez, yalnizca sinir bozar.
"""
from __future__ import annotations

import math

import pygame

from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import DamageResult, Hitbox, Team, melee_rect
from src.config import (
    ROTTED_CLIMB_FRAMES, ROTTED_DROP_DAMAGE, ROTTED_DROP_SPEED,
    ROTTED_HEALTH, ROTTED_LUNGE_DAMAGE, ROTTED_LUNGE_SPEED,
    ROTTED_POISE, ROTTED_SPAWN_COUNT, ROTTED_SWEEP_DAMAGE,
    ROTTED_SWEEP_REACH, ROTTED_BURST_DAMAGE, ROTTED_BURST_REACH,
    PLATE_STUN_FRAMES, TILE_SIZE,
)
from src.entities.boss import Boss
from src.entities.enemy import EnemyState

# --- Hamle siralari - **sabit**, ogrenilebilir -------------------------------
# Her fazin ritmi bir Katman 1 dusmanini animsatiyor.
MOVES = {
    0: ("sweep", "sweep", "lunge"),            # Suruklenen: yerde, agir
    1: ("sweep", "climb", "lunge", "climb"),   # Tirmanan: tavan araya girer
    2: ("burst", "spawn", "sweep", "burst"),   # Sismek: alan + yavru
}

TELL = {"sweep": 20, "lunge": 24, "climb": 18, "spawn": 26, "burst": 30}
ACTIVE = {"sweep": 6, "lunge": 8, "climb": 4, "spawn": 2, "burst": 8}
RECOVER = {"sweep": 26, "lunge": 34, "climb": 10, "spawn": 26, "burst": 40}


class RottedOne(Boss):
    """Curumus Olan - uc faz, uc dusmanin izi, bir muhur."""

    body_width = 22
    body_height = 36
    max_health = ROTTED_HEALTH
    poise = ROTTED_POISE

    tell_frames = TELL["sweep"]
    active_frames = ACTIVE["sweep"]
    recover_frames = RECOVER["sweep"]
    attack_damage = ROTTED_SWEEP_DAMAGE
    attack_reach = ROTTED_SWEEP_REACH
    attack_height = 26
    attack_knockback = 3.2
    move_speed = 0.30
    contact_range = 52.0

    # Iki gecis: %62'de Tirmanan fazi, %30'da Sismek fazi + MUHUR.
    phases = (0.62, 0.30)
    sprite_name = "rotted_one"
    body_colour = "moss_dark"
    boss_name_key = "boss.rotted_one"
    tell_sound = "bloated_fuse"
    death_sound = "shambler_death"

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.move_index = 0
        self.move = "sweep"
        self.climb_frames = 0        # tavanda gecirilen kare
        self.spawned = 0
        # Faz 2'nin muhru. `sealed` iken hicbir vurus islemiyor;
        # plakalar basilinca `stun_frames` acilir ve muhur o sure boyunca
        # kalkar.
        self.sealed = False
        self.stun_frames = 0

    # --- Muhur --------------------------------------------------------------
    @property
    def vulnerable(self) -> bool:
        """Vurus isliyor mu. Muhur varken yalnizca sersemken."""
        return (not self.sealed) or self.stun_frames > 0

    def break_seal(self) -> None:
        """Plakalar basildi - muhur bir sure kalkiyor.

        Sahne cagiriyor; boss plakanin ne oldugunu bilmiyor. Ayni ayrim
        `plate.py`'de de var: plaka GIRDI, sonuc baska yerde.
        """
        if not self.sealed or self.stun_frames > 0:
            return
        self.stun_frames = PLATE_STUN_FRAMES
        self._set_state(EnemyState.STAGGER)
        self.stagger_frames = PLATE_STUN_FRAMES
        self.scene.tokens.force_release(self)
        on_break = getattr(self.scene, "on_seal_broken", None)
        if on_break:
            on_break(self)

    def take_damage(self, box, direction):
        if not self.vulnerable:
            # **Hasar gecmiyor**, azalmiyor. Azalma sayisal olurdu ve
            # oyuncu farki gormeden vurmaya devam ederdi; gecmemek bir
            # KURAL ve kurallar ogretilir.
            on_sealed = getattr(self.scene, "on_boss_sealed", None)
            if on_sealed:
                on_sealed(self)
            return DamageResult(hit=False, blocked=True)
        return super().take_damage(box, direction)

    def on_phase_change(self, phase: int) -> None:
        super().on_phase_change(phase)
        self.move_index = 0          # yeni ritim bastan
        if phase >= 2:
            self.sealed = True

    # --- Hamle secimi -------------------------------------------------------
    def _next_move(self) -> str:
        order = MOVES.get(min(self.phase, 2), MOVES[0])
        move = order[self.move_index % len(order)]
        self.move_index += 1
        return move

    def _begin_tell(self) -> None:
        self.move = self._next_move()
        # Her hamlenin kendi tell suresi; alt sinir 14 kare (BAGLAYICI,
        # `Enemy.__init_subclass__` yukleme aninda dogruluyor).
        self.tell_frames = TELL[self.move]
        super()._begin_tell()

    def _begin_attack(self) -> None:
        self.active_frames = ACTIVE[self.move]
        self.recover_frames = RECOVER[self.move]
        super()._begin_attack()

    # --- Hamleler -----------------------------------------------------------
    def _spawn_attack(self) -> None:
        if self.move == "sweep":
            self._do_sweep()
        elif self.move == "lunge":
            self._do_lunge()
        elif self.move == "climb":
            self._do_climb()
        elif self.move == "spawn":
            self._do_spawn()
        elif self.move == "burst":
            self._do_burst()

    def _do_sweep(self) -> None:
        """Genis yatay savurma - **kacinmayla** gecilir (Suruklenen dersi)."""
        rect = melee_rect(self.body, self.facing, ROTTED_SWEEP_REACH,
                          self.attack_height)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=ROTTED_SWEEP_DAMAGE, active_frames=ACTIVE["sweep"],
            knockback=3.2,
        ))
        self._notify("rotted_sweep")

    def _do_lunge(self) -> None:
        """One atilma - **mesafe acarak** gecilir."""
        self.body.vx = self.facing * ROTTED_LUNGE_SPEED
        rect = melee_rect(self.body, self.facing, 28, self.attack_height)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=ROTTED_LUNGE_DAMAGE, active_frames=ACTIVE["lunge"],
            knockback=4.0, follow=self, offset=(20, 0),
        ))
        self._notify("rotted_lunge")

    def _do_climb(self) -> None:
        """Tavana tirmanip oyuncunun ustune duser (Tirmanan dersi).

        Yukari cikarken **vurulabilir** kaliyor: kacan boss cezasiz
        olmamali. Dususun kendisi tehlikeli, tirmanis degil.
        """
        self.climb_frames = ROTTED_CLIMB_FRAMES
        self.body.vy = -ROTTED_DROP_SPEED
        self._notify("rotted_climb")

    def _do_spawn(self) -> None:
        """Yavru dogurur (Sismek dersi - konumlanma)."""
        from src.entities.enemies.bloated import Bloated
        for index in range(ROTTED_SPAWN_COUNT):
            side = -1 if index % 2 == 0 else 1
            x = self.body.center_x + side * TILE_SIZE * 2
            self.scene.enemies.append(Bloated(self.scene, x, self.body.bottom))
            self.spawned += 1
        self._notify("rotted_spawn")

    def _do_burst(self) -> None:
        """Radyal patlama - **uzaklasarak** gecilir, kacinmayla degil.

        Yonsuz oldugu icin kacinmanin yonu ise yaramiyor; tek cozum
        menzil disina cikmak. Uc hamlenin ucu de farkli cozum istiyor -
        ayni cozum ise yarasaydi dovus tek tuslu olurdu.
        """
        reach = ROTTED_BURST_REACH
        rect = pygame.Rect(int(self.body.center_x - reach),
                           int(self.body.center_y - reach),
                           reach * 2, reach * 2)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=ROTTED_BURST_DAMAGE, active_frames=ACTIVE["burst"],
            knockback=4.5, knockback_up=1.6,
        ))
        self._notify("rotted_burst")

    def _notify(self, name: str) -> None:
        hook = getattr(self.scene, "on_boss_move", None)
        if hook:
            hook(self, name)

    # --- Dongu --------------------------------------------------------------
    def _think(self) -> None:
        if self.stun_frames > 0:
            self.stun_frames -= 1
            self.body.approach_vx(0.0, 0.4)
            return
        if self.climb_frames > 0:
            self._update_climb()
            return
        super()._think()

    def _update_climb(self) -> None:
        """Tavanda asili kalir, sonra oyuncunun uzerine duser."""
        self.climb_frames -= 1
        self.body.gravity_scale = 0.0
        player = self.player
        if player is not None and self.climb_frames > 4:
            # Havadayken oyuncunun ustune kayiyor - dusus tahmin
            # edilebilir olmali ama kacinilmasi da gerekmeli.
            delta = player.body.center_x - self.body.center_x
            self.body.approach_vx(math.copysign(1.4, delta) if abs(delta) > 4
                                  else 0.0, 0.2)
        if self.climb_frames == 0:
            self.body.gravity_scale = 1.0
            self.body.vy = ROTTED_DROP_SPEED
            rect = pygame.Rect(int(self.body.center_x - 20),
                               int(self.body.center_y),
                               40, 30)
            self.scene.hitboxes.spawn(Hitbox(
                rect=rect, owner=self, targets=Team.PLAYER,
                damage=ROTTED_DROP_DAMAGE, active_frames=10,
                knockback=3.6, follow=self, offset=(0, 14),
            ))
            self._notify("rotted_drop")

    def _update_animation(self) -> None:
        if self.dead:
            self.animator.play("death")
        elif self.stun_frames > 0 or self.state is EnemyState.STAGGER:
            self.animator.play("hurt")
        elif self.climb_frames > 0:
            self.animator.play("jump")
        elif self.state in (EnemyState.TELL, EnemyState.ATTACK):
            self.animator.play("attack3" if self.move == "burst"
                               else "attack1")
        elif abs(self.body.vx) > 0.08:
            self.animator.play("run")
        else:
            self.animator.play("idle")
        self.animator.update()

    def update(self) -> None:
        super().update()
        self._update_animation()

    # --- Cizim --------------------------------------------------------------
    def tell_colour(self):
        """Muhurluyken tell rengi degisiyor - "simdi vurulmaz" bilgisi.

        Renk **tek basina** yeterli degil (`CLAUDE.md` 10): sahne ayrica
        muhur halkasini ciziyor (`chapter06.py`), yani sekil kanali da var.
        """
        from src.art import palette
        if self.sealed and self.stun_frames <= 0:
            return palette.color("bone")
        return super().tell_colour()

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"hamle {self.move}  muhur {self.sealed}  sersem {self.stun_frames}"
        ]
