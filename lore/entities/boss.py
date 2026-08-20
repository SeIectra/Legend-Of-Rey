"""Boss dusmanlari.

`Enemy`'nin durum makinesini (`patrol -> alert -> chase -> windup -> attack
-> recover`) oldugu gibi kullanir; ustune tek sey ekler: **can esigine gore
faz gecisi.** Faz degisince kisa bir "hyper armor" penceresi acilir (vurulsa
da sendelemez) ve sahneye kukreme + sarsinti + parcacik bildirilir - oyuncu
"bir sey degisti"yi hemen hisseder, boss'un davranisini degistirdigini
anlamak icin can barina bakmasi gerekmez.

Bu dosya `lore/entities/enemies.py`'yi ust seviyede import eder ama tam
tersi olmaz - `spawn_enemy()` "gaoler" turunu gecikmeli (fonksiyon icinde)
import eder. Aksi halde iki modul birbirini import eder ve daire olusur.
"""
from __future__ import annotations

from lore.entities.enemies import Enemy
from lore.systems.combat import DamageResult, DamageType


class Boss(Enemy):
    """Cok fazli dusman taban sinifi."""

    is_boss = True
    display_name = "Boss"
    phases: tuple[float, ...] = (0.5,)   # can yuzdesi esikleri, kucukten buyuge
    phase_armor_time = 0.5
    phase_fx_ramp = "ember"

    def __init__(self, scene, x: float, y: float, **options) -> None:
        super().__init__(scene, x, y, **options)
        self._phase = 0
        self.phase_armor = 0.0

    def update(self, dt: float) -> None:
        self.phase_armor = max(0.0, self.phase_armor - dt)
        super().update(dt)

    # --- Hasar ve faz gecisi -------------------------------------------------
    def take_damage(self, amount: int, source=None, direction: int = 1,
                    knockback: float = 120.0, knockback_up: float = 60.0,
                    damage_type: DamageType = DamageType.PHYSICAL,
                    stagger: float = 0.2) -> DamageResult:
        if self.phase_armor > 0.0:
            # Faz gecisinin hemen ardindan gelen vurus sendeletmez - boss
            # kukremesinin ortasinda "donup kalmasin".
            stagger = 0.0
        result = super().take_damage(amount, source, direction, knockback,
                                     knockback_up, damage_type, stagger)
        if result.hit and not self.dead:
            self._check_phase()
        return result

    def _check_phase(self) -> None:
        if self.max_health <= 0:
            return
        frac = self.health / self.max_health
        next_index = self._phase
        while next_index < len(self.phases) and frac <= self.phases[next_index]:
            next_index += 1
        if next_index != self._phase:
            self._phase = next_index
            self.on_phase_change(self._phase)

    def on_phase_change(self, phase: int) -> None:
        """Alt siniflar hiz/saldiri degistirmek icin bunu ezer ve super() cagirir."""
        self.phase_armor = self.phase_armor_time
        self.stagger = 0.0
        self.body.vx = 0.0
        self.scene.camera.add_trauma(0.5)
        self.scene.app.hitstop(0.12)
        self.scene.app.audio.play("boss_roar", pos=self.body.center)
        self.scene.spawn_effect("ring", self.body.center, ramp=self.phase_fx_ramp,
                                radius=self.body.w * 1.6)

    # --- Olum ------------------------------------------------------------
    def die(self, source=None) -> None:
        if self.dead:
            return
        super().die(source)
        self.scene.on_boss_defeated(self)


class Gaoler(Boss):
    """Act I finali. Faz 1: agir tirpan salinimi. Faz 2 (can %40 altinda):
    hizlanir, kovalamaca hissi verir - roadmap'in "kacarak/tuzaklarla
    yenilir" ruhu, artik silahli olan oyuncu icin "kacmak da bir secenek"
    hissine donusur (bkz. act1_04'un "Kacmak da bir cozumdur" ipucu).
    """
    sprite_key = "gaoler"
    display_name = "The Gaoler"
    max_health = 40
    body_w = 20
    body_h = 34

    patrol_speed = 0.0
    chase_speed = 40.0
    sight_range = 260.0
    sight_behind = 260.0        # arenada gizlilik yok - hep farkinda
    lose_range = 9999.0         # arenayi asla terk etmez
    attack_range = 30.0
    windup_time = 0.85          # uzun ve net okunur hazirlik
    attack_time = 0.22
    recover_time = 0.55
    damage = 2
    knockback = 280.0
    reach = 30
    attack_height = 30
    armored = True
    essence_drop = (0, 0)       # odul on_boss_defeated'ten geliyor
    can_be_backstabbed = False

    phases = (0.4,)
    phase_fx_ramp = "ember"

    def on_phase_change(self, phase: int) -> None:
        super().on_phase_change(phase)
        self.chase_speed = 96.0
        self.windup_time = 0.55
        self.recover_time = 0.35
        self.scene.hud.show_toast("Gaoler kudurdu!", 2.0)

    def perform_attack(self, player) -> None:
        super().perform_attack(player)
        self.scene.camera.add_trauma(0.25)
