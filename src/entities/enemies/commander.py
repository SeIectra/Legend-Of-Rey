"""Komutan - Katman 2'nin dorduncu ve son uyesi.

`docs/gdd.md` 7: *"Komutan - takviye cagirir, **kalabalik yonetimi**."*

## Dordu birlikte bir cumle kuruyor

    Kalkanli   yon      arkaya gec
    Mizrakli   mesafe   menzilinin disindan vuruyor
    Okcu       zaman    baskasiyla dovusurken vuruyor
    Komutan    SAYI     yalniz dovusmeni engelliyor

Ilk ucu tek basina cozulen bilmecelerdi. Komutan onlarin **birlesimi**:
kendisi zayif ama surekli takviye cagiriyor, yani oyuncu "once kimi"
sorusunu cevaplamak zorunda. Dogru cevap her zaman o.

## Cagirma bir SALDIRI

Ayri bir "cagirma" durumu yazilmadi: cagirma normal saldiri
dongusunun (`TELL -> ATTACK -> RECOVER`) icinde. Kazanc, tell'in
zaten okunur olmasi - oyuncu cagirmayi **gorup** kesebiliyor.

Kesme gercek: `Enemy.take_damage` sendeleyince `on_attack_cancelled`
cagriliyor ve cagirma iptal oluyor. Yani "komutani sustur" bir slogan
degil bir mekanik.

## Ust sinir sart

`SUMMON_LIMIT` olmadan oyuncu ne kadar yavassa o kadar cok dusman
gelirdi - yani zorluk beceriyle **ters** orantili olurdu, ki bu bir
olum sarmalinin tanimi. Sinirli olunca komutan bir sayaç degil bir
oncelik sorusu oluyor.

Ayrica `AttackTokenManager` zaten ayni anda en fazla iki dusmanin
saldirmasina izin veriyor (`CLAUDE.md` 7), yani kalabalik ekrani
doldursa bile saldiri hakki korunuyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.config import (
    COMMANDER_ACTIVE_FRAMES, COMMANDER_DAMAGE, COMMANDER_HEALTH,
    COMMANDER_POISE, COMMANDER_REACH, COMMANDER_RECOVER_FRAMES,
    COMMANDER_SPEED, COMMANDER_SUMMON_LIMIT, COMMANDER_SUMMON_RANGE,
    COMMANDER_TELL_FRAMES, TILE_SIZE,
)
from src.entities.enemy import Enemy, EnemyState


class Commander(Enemy):
    """Kendisi zayif, cagirdiklari degil."""

    sprite_name = "commander"
    max_health = COMMANDER_HEALTH
    poise = COMMANDER_POISE
    move_speed = COMMANDER_SPEED
    contact_range = COMMANDER_SUMMON_RANGE
    tell_frames = COMMANDER_TELL_FRAMES
    active_frames = COMMANDER_ACTIVE_FRAMES
    recover_frames = COMMANDER_RECOVER_FRAMES
    damage = COMMANDER_DAMAGE
    # "ember" bir RENK. `brass` bir golge ZINCIRI ve
    # `palette.color()` onu tanimaz - projede bu tuzaga uc kez
    # dusuldu (`steel`, `brass`).
    body_colour = "ember"
    silhouette_scale = 1.05

    # Cagirdigi tip. Sinif adi degil **yol**: bolum kendi listesinden
    # baska bir tip verebilsin diye (`summon_path`).
    summon_path = "src.entities.enemies.shambler:Shambler"

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.summoned = 0
        # Cagirma isareti - tell boyunca buyuyor.
        self.banner = 0.0

    @property
    def can_summon(self) -> bool:
        return self.summoned < COMMANDER_SUMMON_LIMIT

    def _can_attack(self) -> bool:
        # Sinir dolduysa cagirmiyor - ve saldiri hakkini da tutmuyor.
        if not self.can_summon:
            return False
        return super()._can_attack()

    def _think(self) -> None:
        if self.state is EnemyState.TELL:
            self.banner = self.tell_progress
        elif self.state is not EnemyState.ATTACK:
            self.banner *= 0.88
        super()._think()

    def on_attack_cancelled(self) -> None:
        """Sendeleyince cagirma **iptal**.

        "Komutani sustur" bir slogan degil bir mekanik: tell sirasinda
        vurulursa takviye gelmiyor. Bu olmasaydi oyuncunun onu once
        oldurmesinin bir anlami kalmazdi.
        """
        self.banner = 0.0
        super().on_attack_cancelled()

    def _spawn_attack(self) -> None:
        """Takviye cagiriyor - hasar veren bir kutu **yok**.

        Komutanin saldirisi bir vurus degil bir olay. Ayrica hasar
        verseydi hem cagirir hem doverdi ve "kendisi zayif" tasarimi
        bozulurdu.
        """
        if not self.can_summon:
            return
        target = self._summon_spot()
        if target is None:
            return
        enemy = self._make_summon(*target)
        if enemy is None:
            return
        self.summoned += 1
        enemy.aware = True
        self.scene.enemies.append(enemy)
        self.scene.particles.burst(target[0], target[1] - 8, 14,
                                   path="violet", speed=(0.6, 2.2))
        self.scene.game.play_sound("rift_open")
        on_summon = getattr(self.scene, "on_commander_summon", None)
        if on_summon:
            on_summon(self, enemy)

    def _make_summon(self, x: float, y: float):
        module_name, class_name = self.summon_path.split(":")
        try:
            cls = getattr(__import__(module_name, fromlist=[class_name]),
                          class_name)
        except (ImportError, AttributeError):
            return None
        return cls(self.scene, x, y)

    def _summon_spot(self) -> tuple[float, float] | None:
        """Yaninda **bos ve zeminli** bir yer.

        Duvarin icine ya da bosluga cagirmak iki ayri hataydi: biri
        sikismis bir dusman, oteki dusup kaybolan bir dusman. Ikisi de
        oyuncuya "bozuk" gorunurdu.
        """
        tilemap = getattr(self.scene, "tilemap", None)
        if tilemap is None:
            return None
        feet_y = self.body.feet[1]
        for dx in (-28, 28, -44, 44, -60, 60):
            x = self.body.center_x + dx
            probe = self.body.rect.copy()
            probe.centerx = int(x)
            probe.bottom = int(feet_y)
            if tilemap.solid_overlap(probe):
                continue
            # Ayagin **hemen altinda** zemin var mi?
            #
            # Ilk surum butun govdeyi bir tile asagi kaydirip
            # bakiyordu; govde 32 piksel oldugu icin kaydirilmis
            # dikdortgen hala havada kaliyordu ve kontrol **hicbir
            # zaman** gecmiyordu - komutan tek bir takviye
            # cagiramiyordu. Ince bir serit dogru soru.
            ground = pygame.Rect(probe.x, int(feet_y), probe.width, 2)
            if not tilemap.solid_overlap(ground):
                continue
            return (x, feet_y)
        return None

    # --- Cizim ---------------------------------------------------------------
    def draw_extra(self, surface: pygame.Surface, offset) -> None:
        """Sancak - cagirmanin tell'i.

        Bir dusmanin "birazdan takviye gelecek" demesi ancak gorunur
        olursa adil olur. Sancak tell boyunca yukseliyor; kesilirse
        aniden dusuyor.
        """
        if self.banner < 0.05:
            return
        ox, oy = offset
        x = int(self.body.center_x) - ox
        y = int(self.body.center_y) - oy - 14
        height = int(14 * self.banner)
        surface.fill(palette.color("earth_dark"), (x, y - height, 2, height))
        wave = int(math.sin(self.state_frames * 0.3) * 2)
        tone = "danger_bright" if self.banner > 0.7 else "ember_light"
        surface.fill(palette.color(tone),
                     (x + 2, y - height + wave, 8, 5))
