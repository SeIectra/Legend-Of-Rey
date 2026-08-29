"""Yoldas - yaninda dovusen oteki karakter.

`docs/gdd.md` 3, **kanon ve baglayici**:

    "Karakter secimi: Oyun basinda Rey ya da Ardo. SECMEDIGIN, ara
    sahnelerde havali girisi yapan taraf olur."

Yani yoldas sabit degil: Rey oynuyorsan Ardo gelir, Ardo oynuyorsan Rey.
Sinif bunu bir parametreyle degil `scene.character`'in **tersinden**
turetiyor (`other_character`) - iki yerde ayri karar verilseydi biri
gunun birinde unutulurdu.

## Neden `Actor`, `Enemy` degil

Yoldas oyuncunun takimindan (`Team.PLAYER`) ve dusmanlara vuruyor. Bir
`Enemy` alt sinifi yapip takimi degistirmek cazipti ama `Enemy`'nin
durum makinesi **saldiri hakki** (`AttackTokenManager`) ve **kusatma
yorungesi** gibi dusmana ozel seyler tasiyor; yoldasin isi baska. Ortak
olan sey `Actor` (govde, can, sendeleme, animasyon) ve yalnizca o
paylasiliyor.

## Yoldas OLMEZ

`docs/gdd.md` 8: B6 "Ardo'yla ilk beraber dovus". Yoldasin olmesi bu
dovusu bir **koruma gorevine** cevirirdi - oyuncu kendi dovusu yerine
yapay zekayi kollamaya baslar ve iki karakterin esit oldugu izlenimi
yikilir. Bunun yerine cani bitince **diz coker** (`downed`): dovusmez,
plakaya basmaz, ama olmez; bir sure sonra kendi kendine kalkar.

Bu ayni zamanda agirlik plakasi bulmacasini adil tutuyor: yoldas kalici
olarak kaybolabilseydi bulmaca cozulemez hale gelir ve bolum kilitlenirdi.

## Yapay zeka: **yardim eder, oynamaz**

En buyuk risk yoldasin oyunu oyuncunun yerine oynamasi. Uc kural onu
engelliyor:

  * Vurus araligi seyrek (`COMPANION_ATTACK_COOLDOWN`) - dusmani
    temizlemez, mesgul eder.
  * Hasari oyuncunun yarisindan az. Oldurme oyuncunun isi.
  * Oyuncudan uzaklasmaz (`COMPANION_LEASH`) - "nerede bu ya" diye
    aranmak yoldasi bir yuk yapar.

## Emirler

Bulmaca aninda yoldasa "su plakaya bas" demek gerekiyor. Emir bir
**hedef nokta**: `hold(x)` cagrilinca yoldas oraya gidip bekliyor,
`release()` ile serbest kaliyor. Sahne bunu plakadan turetiyor; yoldas
plakanin ne oldugunu bilmiyor.
"""
from __future__ import annotations

import math

from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import Hitbox, Team, melee_rect
from src.config import (
    COMPANION_ATTACK_COOLDOWN, COMPANION_ATTACK_RANGE, COMPANION_DAMAGE,
    COMPANION_DOWN_FRAMES, COMPANION_HEALTH, COMPANION_HOLD_TOLERANCE,
    COMPANION_LEASH, COMPANION_SPEED, COMPANION_TELL_FRAMES,
)
from src.entities.actor import Actor


def other_character(character: str) -> str:
    """Oynanmayan karakter. Kanon: yoldas her zaman bu.

    Tek yerde tanimli - sahne, sinematik ve diyalog ayni yerden soruyor.
    """
    return "rey" if character == "ardo" else "ardo"


class Companion(Actor):
    """Yaninda dovusen oteki karakter. Olmez, diz coker."""

    team = Team.PLAYER
    body_width = 12
    body_height = 22
    max_health = COMPANION_HEALTH
    # Kutu kipinde govde rengi. **RENK adi, zincir degil** - "steel" bir
    # shade chain, palet rengi degil (bu tuzaga proje defalarca dustu).
    body_colour = "bone"

    def __init__(self, scene, x: float, y: float, character: str) -> None:
        super().__init__(scene, x, y)
        self.character = character
        self.animator = Animator(character)
        self.sprite_foot_y = CHARACTERS[character].foot_y
        self.attack_frames = 0        # bir sonraki vurusa kalan
        self.tell_frames = 0          # savurma oncesi okunur an
        self.down_frames = 0          # diz cokmus
        self.hold_x: float | None = None
        self._target = None

    # --- Sorgular -----------------------------------------------------------
    @property
    def player(self):
        return getattr(self.scene, "player", None)

    @property
    def downed(self) -> bool:
        return self.down_frames > 0

    @property
    def holding(self) -> bool:
        """Emredilen noktada duruyor mu - plaka bunu soruyor."""
        if self.hold_x is None or self.downed:
            return False
        return abs(self.body.center_x - self.hold_x) <= COMPANION_HOLD_TOLERANCE

    # --- Emirler ------------------------------------------------------------
    def hold(self, x: float) -> None:
        """Bu noktaya git ve bekle. Dovusu birakir."""
        self.hold_x = float(x)

    def release(self) -> None:
        self.hold_x = None

    # --- Hasar --------------------------------------------------------------
    def take_damage(self, box, direction):
        result = super().take_damage(box, direction)
        if result.hit and self.health <= 0:
            # **Olmuyor, diz cokuyor.** Gerekce modul basliginda.
            self.health = 1
            result.killed = False
            self.down_frames = COMPANION_DOWN_FRAMES
            self.hold_x = None
            on_down = getattr(self.scene, "on_companion_down", None)
            if on_down:
                on_down(self)
        return result

    def die(self) -> None:
        """Yoldas olmez - `Actor.die` bilerek ezildi.

        `health <= 0` yolu `take_damage`'da kesiliyor ama bir gun baska
        bir yerden (cukura dusme, ezilme) cagrilabilir; o zaman da
        olmemeli.
        """
        self.health = 1
        self.down_frames = max(self.down_frames, COMPANION_DOWN_FRAMES)

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        if self.down_frames > 0:
            self.down_frames -= 1
            self.body.approach_vx(0.0, 0.4)
            if self.down_frames == 0:
                # Kalkarken canin bir kismi geri geliyor - yoksa ayaga
                # kalkip aninda tekrar diz cokerdi.
                self.health = max(1, self.max_health // 2)
                on_up = getattr(self.scene, "on_companion_up", None)
                if on_up:
                    on_up(self)
            super().update()
            self._animate()
            return

        if self.attack_frames > 0:
            self.attack_frames -= 1
        if self.tell_frames > 0:
            self.tell_frames -= 1
            if self.tell_frames == 0:
                self._swing()

        self._think()
        super().update()
        self._animate()

    def _think(self) -> None:
        if self.tell_frames > 0:
            self.body.approach_vx(0.0, 0.5)     # savururken durur
            return
        if self.hold_x is not None:
            self._go_to(self.hold_x)
            return

        target = self._pick_target()
        self._target = target
        if target is not None:
            self._engage(target)
        else:
            self._follow()

    def _pick_target(self):
        """En yakin **diri** dusman - ama tasmanin icinde kalani.

        Tasma disina cikip dusman kovalamak yoldasi oyuncudan koparir ve
        "nerede bu ya" hissi yaratir; yoldasin isi oyuncunun yaninda
        olmak.
        """
        player = self.player
        if player is None:
            return None
        best, best_distance = None, COMPANION_LEASH
        for enemy in getattr(self.scene, "enemies", ()):
            if enemy.dead:
                continue
            distance = math.hypot(enemy.body.center_x - player.body.center_x,
                                  enemy.body.center_y - player.body.center_y)
            if distance < best_distance:
                best, best_distance = enemy, distance
        return best

    def _engage(self, target) -> None:
        delta = target.body.center_x - self.body.center_x
        if abs(delta) > 2.0:
            self.facing = 1 if delta > 0 else -1
        if abs(delta) <= COMPANION_ATTACK_RANGE:
            self.body.approach_vx(0.0, 0.35)
            if self.attack_frames <= 0 and self.tell_frames <= 0:
                self._begin_swing()
        else:
            self.body.approach_vx(self.facing * COMPANION_SPEED, 0.25)

    def _follow(self) -> None:
        """Oyuncunun **yaninda** durur, ustunde degil.

        Tam ustune gitseydi iki sprite ust uste biner ve oyuncu kendini
        kaybederdi. Bir omuz mesafesi birakiyor.
        """
        player = self.player
        if player is None:
            return
        side = -1 if player.facing > 0 else 1
        self._go_to(player.body.center_x + side * 18.0)

    def _go_to(self, x: float) -> None:
        delta = x - self.body.center_x
        if abs(delta) < 3.0:
            self.body.approach_vx(0.0, 0.3)
            return
        self.facing = 1 if delta > 0 else -1
        self.body.approach_vx(self.facing * COMPANION_SPEED, 0.25)

    # --- Saldiri ------------------------------------------------------------
    def _begin_swing(self) -> None:
        self.tell_frames = COMPANION_TELL_FRAMES
        on_tell = getattr(self.scene, "on_companion_tell", None)
        if on_tell:
            on_tell(self)

    def _swing(self) -> None:
        rect = melee_rect(self.body, self.facing, 16, 16)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.ENEMY,
            damage=COMPANION_DAMAGE, active_frames=4, knockback=1.4,
        ))
        self.attack_frames = COMPANION_ATTACK_COOLDOWN
        on_swing = getattr(self.scene, "on_companion_attack", None)
        if on_swing:
            on_swing(self)

    # --- Cizim --------------------------------------------------------------
    def _animate(self) -> None:
        if self.downed:
            self.animator.play("hurt")
        elif self.tell_frames > 0:
            self.animator.play("attack1")
        elif abs(self.body.vx) > 0.08:
            self.animator.play("run")
        else:
            self.animator.play("idle")
        self.animator.update()

    # --- `enemy_render.draw_enemy` sozlesmesi -------------------------------
    # Yoldas bir dusman DEGIL ama cizimi ayni: animator + flash + squash +
    # siluet kipi + kutu kipi. Ikinci bir cizici yazmak o dort ozelligi
    # kopyalamak olurdu ve biri gunun birinde geride kalirdi (bu projenin
    # `play.py` basligindaki en eski dersi). Bunun yerine `draw_enemy`'nin
    # bekledigi kucuk sozlesme burada karsilaniyor.
    #
    @property
    def state(self):
        """Yoldasin durumu `EnemyState` diliyle - **yalnizca cizim icin**.

        Yoldasin kendi mantigi bu enum'u kullanmiyor; burada cevriliyor
        cunku `enemy_render` onu okuyor. Ic mantigi da bu enum'a
        baglamak yoldasi bir `Enemy` yapardi ve modul basligindaki
        ayrimi (saldiri hakki / kusatma yorungesi yoldasa ait degil)
        sessizce cignerdi.
        """
        from src.entities.enemy import EnemyState
        if self.downed:
            return EnemyState.STAGGER
        if self.tell_frames > 0:
            return EnemyState.TELL
        return EnemyState.IDLE

    @property
    def state_frames(self) -> int:
        return self.tell_frames if self.tell_frames > 0 else self.down_frames

    @property
    def telegraphing(self) -> bool:
        return self.tell_frames > 0

    @property
    def tell_progress(self) -> float:
        if self.tell_frames <= 0:
            return 0.0
        return 1.0 - self.tell_frames / COMPANION_TELL_FRAMES

    def tell_colour(self):
        """Yoldasin savurma parlamasi - **dusman rengi degil**.

        Dusmanlar tehlike renginde parliyor; yoldas oyuncunun takimindan
        ve onun savurmasi bir uyari degil bir yardim. Kemik tonu ikisini
        bir bakista ayiriyor.
        """
        from src.art import palette
        return palette.color("bone")

    def silhouette_scale(self) -> tuple[float, float]:
        if self.downed:
            return (1.25, 0.72)      # diz cokmus - siluetten okunuyor
        if self.tell_frames > 0:
            grow = 0.12 * self.tell_progress
            return (1.0 - grow * 0.4, 1.0 + grow)
        return (1.0, 1.0)

    def draw(self, surface, offset) -> None:
        from src.entities.enemy_render import draw_enemy
        draw_enemy(self, surface, offset)
