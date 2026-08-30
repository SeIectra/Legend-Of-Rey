"""Dusman temel sinifi - durum makinesi, ritim imzasi, tell.

Su an uc tip var (Katman 1). Altyapi ona genisleyecek sekilde kuruldu:
Katman 2 kalkanli/mizrakli/okcu/komutan, Katman 3 sessiz/yankilayan/bolunen
(docs/gdd.md 7). Alt sinif genelde yalnizca **sayilar ve bir-iki kanca**
verir; durum makinesi burada kalir.

## Iki baglayici kural

**Tell (on isaret) - en az 14 kare.** Her saldiri onceden okunabilir olmali:
poz degisimi **ve** renk vurgusu. Okunamayan hasar oyuncuya haksizlik gibi
gelir. `ENEMY_MIN_TELL_FRAMES` alt sinir; alt siniflar daha uzun verebilir,
kisa veremez - `__init_subclass__` bunu yukleme aninda kontrol eder.

**Ritim imzasi.** Her tipin sabit, ogrenilebilir bir saldiri ritmi var
(docs/derinlestirme.md 4.2). Rastgele saldiran dusman ogrenilemez, sadece
sinir bozar. Bu yuzden zamanlamalarda `random` **yok**: ayni tip her zaman
ayni ritmi calar, oyuncu onu ezberler ve ustunluk kurar.

## Can bari yok

Durum gorsel olarak okunur (CLAUDE.md 7): sendeleme, renk koyulasmasi,
hiz dusmesi. Bar yalnizca boss'ta.

## Renk korlugu

Tell yalnizca renkle anlatilmaz. Tehlike rengiyle parlama **ve** siluet
degisimi (kabarma/cokme) birlikte gider - renk gormeyen oyuncu sekli gorur.
"""
from __future__ import annotations

import math
from enum import Enum, auto


from src.art import palette
from src.combat.hitbox import Hitbox, Team, melee_rect
from src.config import (
    ENEMY_APPROACH_SPEED, ENEMY_LOSE_RANGE, ENEMY_MIN_TELL_FRAMES,
    ENEMY_ORBIT_SPEED, ENEMY_SIGHT_RANGE, ORBIT_RADIUS_MAX, ORBIT_RADIUS_MIN,
    ORBIT_SLOT_WIDTH,
)
from src.entities import enemy_navigation
from src.entities.actor import Actor


class EnemyState(Enum):
    IDLE = auto()        # Oyuncuyu gormedi
    APPROACH = auto()    # Hakki var, yaklasiyor
    ORBIT = auto()       # Hakki yok, kusatmada bekliyor
    TELL = auto()        # Saldiri on isareti - okunabilir olmali
    ATTACK = auto()      # Hitbox acik
    RECOVER = auto()     # Toparlaniyor
    STAGGER = auto()     # Poise kirildi
    DEAD = auto()


class Enemy(Actor):
    """Butun dusmanlarin atasi."""

    team = Team.ENEMY
    iframes_on_hit = 0              # Combo kesilmesin

    # --- Alt siniflarin ezdigi degerler ---
    tell_frames: int = 18
    active_frames: int = 4
    recover_frames: int = 24
    attack_damage: int = 8
    attack_reach: int = 14
    attack_height: int = 16
    attack_knockback: float = 1.4
    move_speed: float = 0.5
    contact_range: float = 18.0     # Bu mesafede saldiriya baslar
    sprite_name: str = "shambler"
    body_colour: str = "echo_dark"  # Kutu kipinde govde rengi (RENK adi, zincir degil)
    # Yanki (ve Iz Surme) bu dusmani gosteriyor mu?
    #
    # `docs/gdd.md` 7, Katman 3: *"Sessiz - Yanki onu gostermez."*
    # Bayrak burada cunku gizlenme dusmanin bir OZELLIGI; gorunum
    # katmani yalnizca soruyor. Alternatif `echo_view` icinde tip
    # kontrolu yapmakti - gorunum katmaninin dusman tiplerini bilmesi
    # yanlis yonde bir bagimlilik olurdu.
    echo_visible: bool = True
    # Ses (Gorev 10) - alt sinif kendi tipine gore ezer. Bos dize = ek ses
    # calinmasin (orn. Sismek zaten patlama sesiyle olur, ustune binmesin).
    tell_sound: str = "enemy_tell"
    death_sound: str = "shambler_death"

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Tell suresi belgeden gelen alt siniri asla ihlal edemez. Bir gun
        # biri "daha zorlu olsun" diye 6 kare yazarsa oyun yuklenirken durur,
        # oyun sirasinda degil.
        if cls.tell_frames < ENEMY_MIN_TELL_FRAMES:
            raise ValueError(
                f"{cls.__name__}.tell_frames={cls.tell_frames} - "
                f"en az {ENEMY_MIN_TELL_FRAMES} olmali "
                f"(docs/dovus-sistemi.md 6, baglayici)")

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.state = EnemyState.IDLE
        self.state_frames = 0
        # Dogumdan beri gecen kare - **durumdan bagimsiz**.
        # `state_frames` her durum degisiminde sifirlaniyor, yani
        # titresim/nabiz gibi SUREKLI gorseller icin kullanilamaz:
        # dusman saldirmaya baslayinca fener birden ziplardi.
        #
        # Iki dosya bu sayacin varligini zaten varsayiyordu
        # (`echoing.py` sahte isaret parildamasi, `gaoler.py` fener) ve
        # ikisi de `draw_extra` cagrilir cagrilmaz cokuyordu. Testler
        # cizimi hic cagirmadigi icin sessizce duruyordu.
        self.frames = 0
        self.aware = False
        self.orbit_side = 1              # Oyuncunun hangi yaninda bekliyor
        self.orbit_slot = 0.0            # Yorunge icindeki yeri
        self._attack_spawned = False
        # Oyuncu dikeyde erisilemezken gecen kare sayisi - bir esigi
        # asinca dusman en yakin kenari arayip oradan iner (bkz.
        # _update_reachability / _think).
        self._unreachable_frames = 0
        self.speed_scale = float(
            scene.game.settings.get("enemy_speed", 1.0)) if scene else 1.0

    # --- Sorgular -----------------------------------------------------------
    @property
    def player(self):
        return getattr(self.scene, "player", None)

    @property
    def telegraphing(self) -> bool:
        """Tell suruyor mu - cizim ve ses buna bakar."""
        return self.state is EnemyState.TELL

    @property
    def tell_progress(self) -> float:
        """Tell'in ne kadari gecti (0..1). Parlama bununla siddetlenir."""
        if self.state is not EnemyState.TELL or self.tell_frames <= 0:
            return 0.0
        return min(1.0, self.state_frames / self.tell_frames)

    def _set_state(self, state: EnemyState) -> None:
        if self.state is state:
            return
        self.state = state
        self.state_frames = 0

    # --- Hasar --------------------------------------------------------------
    def take_damage(self, box, direction):
        result = super().take_damage(box, direction)
        if not result.hit:
            return result
        if result.killed:
            self._set_state(EnemyState.DEAD)
            self.scene.tokens.force_release(self)
        elif result.staggered:
            # Sendeleme saldiriyi **iptal eder** - oyuncunun odulu bu.
            self._set_state(EnemyState.STAGGER)
            self.scene.tokens.force_release(self)
            self.on_attack_cancelled()
        self.aware = True
        return result

    def on_attack_cancelled(self) -> None:
        """Saldiri yarida kesildi. Alt sinif temizlik yapabilir."""

    def die(self) -> None:
        super().die()
        self._set_state(EnemyState.DEAD)
        on_died = getattr(self.scene, "on_enemy_died", None)
        if on_died:
            on_died(self)

    # --- Dongu --------------------------------------------------------------
    def draw(self, surface, offset) -> None:
        """Her dusman cizilebilir - **varsayilan burada.**

        `Actor.draw` soyut (`NotImplementedError`). Cizim uc yerde ayri
        ayri yazilmisti: `Shambler`, `Boss` ve iki mini-boss. Dogrudan
        `Enemy`den tureyen uc dusman - Mizrakli, Okcu, Komutan -
        hicbirine girmiyordu ve **ekrana girdikleri an oyunu
        cokutuyorlardi.**

        Bolum 11 bunu canli tasiyordu: salonda bir Mizrakli var ve
        kamera onu gordugu an `NotImplementedError`. Davranis testleri
        yesildi cunku hicbiri cizim cagirmiyordu; 30.08.2026'da
        `tests/test_enemies.py` her dusmanin cizimini calistirmaya
        baslayinca ortaya cikti.

        Alt siniflarda kalan ayni tanimlar zararsiz - ama artik
        gerekli degil.
        """
        from src.entities.enemy_render import draw_enemy
        draw_enemy(self, surface, offset)

    def draw_extra(self, surface, offset) -> None:
        """Govdenin ustune cizilen dusmana ozel ekler. Varsayilan: yok.

        `enemy_render.draw_enemy` her dusmanda cagiriyor. Kanca burada
        **acikca** tanimli, cunku alt siniflarin yarisinda vardi
        yarisinda yoktu ve cagiran taraf `getattr` ile yoklamak
        zorunda kalirdi - yazim hatasi olan bir `draw_extar` sessizce
        hicbir sey yapardi.
        """

    def update(self) -> None:
        if self.dead:
            self.remove = True
            return

        self.frames += 1
        self.state_frames += 1
        self._update_awareness()
        self._update_reachability()
        self._think()

        # Actor.update yercekimi ve hareketi yapar; durum makinesi vx'i
        # ayarladiktan **sonra** cagrilmali.
        super().update()

    def _update_awareness(self) -> None:
        player = self.player
        if player is None or player.dead:
            self.aware = False
            return
        distance = self.distance_to(player)
        # Histerezis: tek esik olsaydi sinirdaki dusman acip kapanirdi.
        if not self.aware and distance <= ENEMY_SIGHT_RANGE:
            self.aware = True
        elif self.aware and distance > ENEMY_LOSE_RANGE:
            self.aware = False

    def _update_reachability(self) -> None:
        """Dikey erisilebilirlik takibi - bkz. `enemy_navigation.py`."""
        enemy_navigation.update_reachability(self)

    def _think(self) -> None:
        """Durum makinesi. Alt sinif genelde bunu ezmez."""
        if self.state is EnemyState.STAGGER:
            self.body.approach_vx(0.0, 0.35)
            if self.stagger_frames <= 0:
                self._set_state(EnemyState.ORBIT)
            return

        if self.state is EnemyState.TELL:
            self._face_player()
            self.body.approach_vx(0.0, 0.5)     # Tell sirasinda durur - okunur
            if self.state_frames >= self.tell_frames:
                self._begin_attack()
            return

        if self.state is EnemyState.ATTACK:
            if not self._attack_spawned:
                self._spawn_attack()
                self._attack_spawned = True
            if self.state_frames >= self.active_frames:
                self._set_state(EnemyState.RECOVER)
            return

        if self.state is EnemyState.RECOVER:
            self.body.approach_vx(0.0, 0.3)
            if self.state_frames >= self.recover_frames:
                self.scene.tokens.release(self)
                self._set_state(EnemyState.ORBIT)
            return

        if self._try_escape_unreachable():
            return

        if not self.aware:
            self._set_state(EnemyState.IDLE)
            self.body.approach_vx(0.0, 0.2)
            return

        # Hakki varsa yaklas, yoksa kusatmada bekle.
        if self.scene.tokens.request(self):
            self._set_state(EnemyState.APPROACH)
            self._approach()
        else:
            self._set_state(EnemyState.ORBIT)
            self._orbit()

    def _try_escape_unreachable(self) -> bool:
        """Sikisma kacisi - bkz. `enemy_navigation.py`."""
        return enemy_navigation.try_escape_unreachable(self)

    # --- Hareket ------------------------------------------------------------
    def _face_player(self) -> None:
        player = self.player
        if player is None:
            return
        if abs(player.body.center_x - self.body.center_x) > 2.0:
            self.facing = 1 if player.body.center_x > self.body.center_x else -1

    def _vertically_reachable(self, player) -> bool:
        """Oyuncu dikeyde erisilebilir mi - bkz. `enemy_navigation.py`."""
        return enemy_navigation.vertically_reachable(self, player)

    def _approach(self) -> None:
        player = self.player
        if player is None:
            return
        self._face_player()
        distance = self.distance_to(player)
        # Erisilebilirlik artik `_update_reachability()` ile her karede,
        # bu fonksiyondan bagimsiz olarak izleniyor (bkz. `_think()`'in
        # basindaki kenar-arama kontrolu) - burada yalnizca okunuyor.
        reachable = self._vertically_reachable(player)

        if (distance <= self.contact_range and reachable
                and self._can_attack()):
            self._begin_tell()
            return

        speed = self.move_speed * self.speed_scale * ENEMY_APPROACH_SPEED / 0.5
        self.body.approach_vx(self.facing * speed, 0.25)

    def _orbit(self) -> None:
        """Kusatma: yaklas ama girme, yerini koru.

        Bekleyenler ust uste binmesin diye her dusmana kimliginden turetilen
        sabit bir yuva veriliyor. Rastgele olsaydi ayni dusman her karede
        baska yere gitmek isterdi ve titrerdi.
        """
        player = self.player
        if player is None:
            return
        self._face_player()

        slot = self._orbit_offset()
        target_x = player.body.center_x + slot
        delta = target_x - self.body.center_x
        if abs(delta) < 3.0:
            self.body.approach_vx(0.0, 0.2)
            return
        speed = self.move_speed * self.speed_scale * ENEMY_ORBIT_SPEED / 0.5
        self.body.approach_vx(math.copysign(speed, delta), 0.2)

    def _orbit_offset(self) -> float:
        """Oyuncuya gore beklenecek yatay ofset. Dusman basina sabit."""
        # id() sabit ama tahmin edilemez; yuva dagilimi duzgun olsun diye
        # kucuk bir karistirma yapiliyor. Kare kare degismedigi icin titremez.
        index = (id(self) >> 4) % 6
        side = 1 if index % 2 == 0 else -1
        depth = index // 2                       # 0, 1, 2
        span = ORBIT_RADIUS_MAX - ORBIT_RADIUS_MIN
        radius = ORBIT_RADIUS_MIN + (span * depth / 2.0)
        return side * (radius + depth * ORBIT_SLOT_WIDTH * 0.0)

    # --- Saldiri ------------------------------------------------------------
    def _can_attack(self) -> bool:
        """Alt sinif ek kosul koyabilir (Sismek patlamayi baska turlu yapar)."""
        return True

    def _begin_tell(self) -> None:
        self._set_state(EnemyState.TELL)
        self._attack_spawned = False
        on_tell = getattr(self.scene, "on_enemy_tell", None)
        if on_tell:
            on_tell(self)

    def _begin_attack(self) -> None:
        self._set_state(EnemyState.ATTACK)
        self._attack_spawned = False

    def _spawn_attack(self) -> None:
        """Hitbox'i acar. Hasar **daima** buradan gecer - dogrudan
        `take_damage` cagrilmaz (src/combat/hitbox.py)."""
        rect = melee_rect(self.body, self.facing, self.attack_reach,
                          self.attack_height)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=self.attack_damage, active_frames=self.active_frames,
            knockback=self.attack_knockback,
        ))
        on_swing = getattr(self.scene, "on_enemy_attack", None)
        if on_swing:
            on_swing(self)

    # --- Cizim --------------------------------------------------------------
    def tell_colour(self) -> palette.RGB:
        """Tell parlamasinin rengi.

        `enemy_tell` rolu bu is icin zaten tanimliydi - yeni rol eklemedik.
        Tell'in sonuna dogru daha parlak tona geciyoruz ki "simdi geliyor"
        ani ayrica okunsun.
        """
        if self.tell_progress > 0.65:
            return palette.color("danger_bright")
        return palette.role("enemy_tell")

    def silhouette_scale(self) -> tuple[float, float]:
        """Tell sirasinda siluet degisimi - renk korlugu icin sart.

        Renk gormeyen oyuncu sekli gorur: dusman tell boyunca kabarir.
        Squash ile birlestigi icin cizim tarafinda ayrica is yok.
        """
        if self.state is EnemyState.TELL:
            grow = 0.18 * self.tell_progress
            return (1.0 - grow * 0.4, 1.0 + grow)
        return (1.0, 1.0)
