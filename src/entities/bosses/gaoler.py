"""Zindanci - BOSS 2, Bolum 13.

`docs/gdd.md` 8 tablosu: *"2 | B13 | Cemo kovalamacasi"*.
`docs/gdd.md` 10: *"13 | Cemo | Kovalamaca, **BOSS 2**"*.

## Katman 2 burada BITIYOR, o yuzden Katman 2'nin sinavi

Curumus Olan (BOSS 1, B6) uc fazinda Katman 1'in uc dusmanini geri
getiriyordu - `rotted_one.py`: *"boss yeni bir sey ogretmiyor, tierin
sinavini yapiyor"*. Zindanci ayni isi Lanetli Muhafizlar icin yapiyor:

    Faz 0  GARDIYAN   Kalkanli'nin izi   YON      onden gecilmez
    Faz 1  ZINCIR     Mizrakli + Okcu    MESAFE   menzilin disindan
                                         ZAMAN    ve ucan anahtarlar
    Faz 2  ZINDAN     Komutan'in izi     SAYI     cagiriyor

Dort dusman uc faza sigdi cunku Mizrakli ile Okcu ayni fazda iki ayri
hamle: biri erisim, oteki mermi. Dordunu dorde bolmek fazlari
kisaltirdi ve her biri ezberlenemeden gecerdi.

## Fener - bu boss'un tek imzasi

Arena karanlik. Zindanci **feneri tasiyor**, yani odadaki tek guvenilir
isik o. Sonucu alisildik boss ritminin tersi:

    normal boss:  uzak dur, tell'i oku, pencerede gir
    Zindanci:     uzaklasirsan GORMUYORSUN

Fener her fazda bir kademe soluyor (parlak -> catlak -> kirik). Yani
dovus ilerledikce oda karariyor: zorluk sayilarla degil **gorunurlukle**
tirmaniyor. Faz 2'de fener kiriliyor ve arenanin mangallari (Bolum 3'un
sistemi, `docs/bolum-03.md`: *"isikla arena kontrolu -> B13"*) tek isik
kaynagi oluyor. O da bir ekonomi: oyuncu yakiyor, Zindanci sonduruyor.

**Karanlik tell'i gizlemiyor.** `CLAUDE.md` 7 baglayici: her saldiri en
az 14 kare onceden okunabilir. Fener sonse bile gozleri yaniyor ve tell
sirasinda tehlike rengine donuyor (`draw_extra`). Yani karanlik
**konumu** gizliyor, **niyeti** degil. Bir boss'un adil olmasi tam
olarak bu ayrimda.

Rey'in Yankisi bu fazda dogal bir avantaj - ama **kodda hicbir istisna
yok**: `echo_view.draw_reveal` zaten dusmanlari ciziyor, yani Yanki
karanligi bedavaya deliyor. Ardo'nun Yankisi olmadigi icin mangallara
mecbur. Asimetri yazilmadi, **var olan sistemlerden dustu** - ve
`docs/dovus-sistemi.md` 8'in "Rey/Ardo farki" maddesine denk geliyor.

## Neden Katman 1 cagiriyor

Faz 2'de cagirdigi sey muhafiz degil **Suruklenen**: bu zindanda
cürüyüp kalmis mahkumlar. Askeri takviye daha tutarli olurdu ama daha
az anlamli - Zindanci'nin isi insan tutmak, ve tuttuklari boyle
bitiyor. Oyuncu Cemo'yu ararken onlarla dovusuyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.combat.hitbox import DamageResult, Hitbox, Team, melee_rect
from src.config import (
    GAOLER_CALL_COUNT, GAOLER_CALL_LIMIT, GAOLER_EYE_LIGHT_RADIUS,
    GAOLER_EYE_TELL_RADIUS,
    GAOLER_CHAIN_DAMAGE, GAOLER_CHAIN_REACH, GAOLER_CONTACT_RANGE,
    GAOLER_EYE_GLOW, GAOLER_GUARD_PUSHBACK, GAOLER_HEALTH,
    GAOLER_KEYS_DAMAGE, GAOLER_KEYS_LIFE, GAOLER_KEYS_SPEED,
    GAOLER_LANTERN_DIM, GAOLER_LANTERN_RADIUS, GAOLER_POISE,
    GAOLER_SLAM_DAMAGE, GAOLER_SLAM_REACH, GAOLER_SNUFF_RANGE,
    GAOLER_SPEED, GAOLER_SWING_DAMAGE, GAOLER_SWING_REACH, TILE_SIZE,
)
from src.entities.boss import Boss
from src.entities.enemy import EnemyState

# --- Hamle siralari - **sabit**, ogrenilebilir -------------------------------
# `docs/derinlestirme.md` 4.2: rastgele bir boss ogrenilemez, yalnizca
# sinir bozar. Her fazin ritmi bir Katman 2 dusmanini animsatiyor.
MOVES = {
    0: ("swing", "swing", "slam"),              # Kalkanli: yakin, gardli
    1: ("chain", "keys", "swing", "keys"),      # Mizrakli + Okcu
    2: ("call", "chain", "slam", "snuff"),      # Komutan + isik ekonomisi
}

TELL = {"swing": 18, "slam": 26, "chain": 22, "keys": 20, "call": 28,
        "snuff": 16}
ACTIVE = {"swing": 6, "slam": 8, "chain": 7, "keys": 3, "call": 2,
          "snuff": 4}
RECOVER = {"swing": 24, "slam": 38, "chain": 30, "keys": 22, "call": 34,
           "snuff": 20}

# Fenerin faz basina yaricapi. Ucuncusu 0 - kirildi.
LANTERN_RADIUS = (GAOLER_LANTERN_RADIUS, GAOLER_LANTERN_DIM, 0.0)


class Gaoler(Boss):
    """Zindanci - uc faz, Katman 2'nin dort dersi, bir fener."""

    body_width = 24
    body_height = 42
    max_health = GAOLER_HEALTH
    poise = GAOLER_POISE

    tell_frames = TELL["swing"]
    active_frames = ACTIVE["swing"]
    recover_frames = RECOVER["swing"]
    attack_damage = GAOLER_SWING_DAMAGE
    attack_reach = GAOLER_SWING_REACH
    attack_height = 30
    attack_knockback = 3.4
    move_speed = GAOLER_SPEED
    contact_range = GAOLER_CONTACT_RANGE

    # Iki gecis: %66'da Zincir fazi, %33'te Zindan fazi + fener kirilir.
    phases = (0.66, 0.33)
    sprite_name = "gaoler"
    body_colour = "stone_dark"
    boss_name_key = "boss.gaoler"
    # Kalkanli ile ayni tell sesi: ikisi de zirhli, ikisi de
    # Katman 2. Ses akrabaligi dusman ailesini de anlatiyor.
    tell_sound = "enemy_tell"
    death_sound = "shambler_death"

    def __init__(self, scene, x: float, y: float) -> None:
        super().__init__(scene, x, y)
        self.animator = Animator(self.sprite_name)
        self.sprite_foot_y = CHARACTERS[self.sprite_name].foot_y
        self.move_index = 0
        self.move = "swing"
        self.called = 0
        # Fenerin catlak sayisi = faz. Ayri bir alan tutmuyoruz;
        # `lantern_radius` fazdan okuyor, yani ikisi ayrisamaz.
        self.lantern_broken = False
        self.guard_hits = 0          # onden savusturulan vurus sayisi

    # --- Fener ---------------------------------------------------------------
    @property
    def lantern_radius(self) -> float:
        return LANTERN_RADIUS[min(self.phase, len(LANTERN_RADIUS) - 1)]

    def _update_lantern(self) -> None:
        """Feneri her karede isiga bildiriyor.

        `LightState` Bolum 3'ten (`src/systems/light.py`). Kaynak
        anahtari sabit oldugu icin tasinan bir kaynak gibi davraniyor -
        ayri bir "boss isigi" kavrami gerekmedi.
        """
        light = getattr(self.scene, "light", None)
        if light is None:
            return
        if self.dead:
            light.remove_static("gaoler_lantern")
            light.remove_static("gaoler_eyes")
            return

        radius = self.lantern_radius
        if radius <= 0.0:
            light.remove_static("gaoler_lantern")
        else:
            light.set_static("gaoler_lantern", self.body.center_x,
                             self.body.center_y - 6, radius)

        # **Gozler de bir isik.** Karartma maskesi aktorlerin ustune
        # cizildigi icin, gozleri yalnizca `draw_extra`da cizmek
        # yetmiyordu - maske onlari da yutuyordu. Isik olarak yazilinca
        # karanligi gercekten deliyorlar.
        #
        # Fener kirildiktan sonra boss'un tek gorunur parcasi bu, ve
        # tell sirasinda buyuyor: `CLAUDE.md` 7'nin "14 kare onceden
        # okunabilir" kurali karanlikta ancak boyle korunuyor.
        telling = self.state in (EnemyState.TELL, EnemyState.ATTACK)
        light.set_static("gaoler_eyes", self.body.center_x,
                         self.body.top + 8,
                         GAOLER_EYE_TELL_RADIUS if telling
                         else GAOLER_EYE_LIGHT_RADIUS)

    # --- Gard (Faz 0 - Kalkanli'nin izi) --------------------------------------
    @property
    def guarding(self) -> bool:
        """Faz 0'da ve toparlanmiyorken gard acik.

        Toparlanma penceresinde gard dusuyor: Kalkanli'nin dersi "arkaya
        gec" ama boss olcusunde tek cozum birakmak zalimce olurdu.
        Sabirli oyuncu onden de girebilmeli - yalnizca dogru anda.
        """
        return (self.phase == 0 and not self.dead
                and self.state is not EnemyState.RECOVER
                and self.state is not EnemyState.STAGGER)

    def _from_front(self, direction) -> bool:
        return direction[0] != 0 and (direction[0] > 0) == (self.facing < 0)

    def take_damage(self, box, direction):
        if self.guarding and self._from_front(direction):
            # **Hasar gecmiyor**, azalmiyor - `rotted_one.py` ve
            # `shieldbearer.py` ile ayni gerekce: azalma sayisal bir sey
            # olurdu ve oyuncu farki gormeden vurmaya devam ederdi.
            # Gecmemek bir KURAL, ve kurallar ogretilir.
            self.guard_hits += 1
            player = self.player
            if player is not None:
                player.body.vx = math.copysign(GAOLER_GUARD_PUSHBACK,
                                               -self.facing)
            on_guard = getattr(self.scene, "on_gaoler_guard", None)
            if on_guard:
                on_guard(self)
            return DamageResult(hit=False, blocked=True)
        return super().take_damage(box, direction)

    def on_phase_change(self, phase: int) -> None:
        super().on_phase_change(phase)
        self.move_index = 0          # yeni ritim bastan
        if phase >= 2 and not self.lantern_broken:
            self._break_lantern()

    def _break_lantern(self) -> None:
        """Fener kiriliyor - arena kararir.

        Bu bir hamle degil bir **gecis**: oyuncu ne yaparsa yapsin
        oluyor. Boss'un en pahali ani (faz zirhi) zaten burada, yani
        kirilma tam gorulecek karede.
        """
        self.lantern_broken = True
        light = getattr(self.scene, "light", None)
        if light is not None:
            light.remove_static("gaoler_lantern")
        self.scene.particles.burst(self.body.center_x, self.body.center_y - 6,
                                   22, path="spark", speed=(0.9, 2.8))
        self.scene.game.play_sound("torch_light")
        on_dark = getattr(self.scene, "on_lantern_broken", None)
        if on_dark:
            on_dark(self)

    # --- Hamle secimi ---------------------------------------------------------
    def _next_move(self) -> str:
        order = MOVES.get(min(self.phase, 2), MOVES[0])
        move = order[self.move_index % len(order)]
        self.move_index += 1
        # **Bos tell yok.** Yapilamayacak bir hamlenin tell'ini
        # oynatmak oyuncuya sistemi yanlis ogretir: bir tehdit
        # gorup hicbir sey olmayinca "okumak ise yaramiyor" sonucunu
        # cikarir. Iki durumda sira atlaniyor:
        if move == "call" and self.called >= GAOLER_CALL_LIMIT:
            move = "slam"
        elif move == "snuff" and self._nearest_lit() is None:
            # Sonduruleсek mangal yoksa - zaten karanlik, saldirsin.
            move = "chain"
        return move

    def _nearest_lit(self):
        """Menzildeki en yakin YANAN mangal. Yoksa None."""
        braziers = getattr(self.scene, "braziers", None)
        if not braziers:
            return None
        best = None
        best_distance = GAOLER_SNUFF_RANGE ** 2
        for brazier in braziers:
            if not brazier.lit:
                continue
            dx = brazier.x - self.body.center_x
            dy = brazier.y - self.body.center_y
            distance = dx * dx + dy * dy
            if distance <= best_distance:
                best, best_distance = brazier, distance
        return best

    def _begin_tell(self) -> None:
        self.move = self._next_move()
        # Alt sinir 14 kare BAGLAYICI (`Enemy.__init_subclass__` yukleme
        # aninda dogruluyor).
        self.tell_frames = TELL[self.move]
        super()._begin_tell()

    def _begin_attack(self) -> None:
        self.active_frames = ACTIVE[self.move]
        self.recover_frames = RECOVER[self.move]
        super()._begin_attack()

    # --- Hamleler -------------------------------------------------------------
    def _spawn_attack(self) -> None:
        handler = {
            "swing": self._do_swing, "slam": self._do_slam,
            "chain": self._do_chain, "keys": self._do_keys,
            "call": self._do_call, "snuff": self._do_snuff,
        }.get(self.move)
        if handler is not None:
            handler()

    def _do_swing(self) -> None:
        """Balta savurmasi - yakin, hizli. Gardin arkasindaki tehdit."""
        rect = melee_rect(self.body, self.facing, GAOLER_SWING_REACH,
                          self.attack_height)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=GAOLER_SWING_DAMAGE, active_frames=ACTIVE["swing"],
            knockback=3.4,
        ))
        self._notify("gaoler_swing")

    def _do_slam(self) -> None:
        """Yere carpma - **uzaklasarak** gecilir, kacinmayla degil."""
        reach = GAOLER_SLAM_REACH
        rect = pygame.Rect(int(self.body.center_x - reach),
                           int(self.body.bottom - 22), reach * 2, 24)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=GAOLER_SLAM_DAMAGE, active_frames=ACTIVE["slam"],
            knockback=4.2, knockback_up=1.8,
        ))
        self.scene.particles.burst(self.body.center_x, self.body.bottom, 16,
                                   path="dust", speed=(0.8, 2.4))
        self._notify("gaoler_slam")

    def _do_chain(self) -> None:
        """Zincir - Mizrakli'nin dersi boss olcusunde.

        Menzil 62 piksel; oyuncunun kilici ~16. Fark mekanigin kendisi:
        "geri cekil" bu hamlede ISE YARAMIYOR, iceri girmek gerekiyor.
        Faz 0'in "arkaya gec" cozumuyle birlikte oyuncu iki zit
        refleksi ayni dovuste kullanmak zorunda.
        """
        rect = melee_rect(self.body, self.facing, GAOLER_CHAIN_REACH, 18)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=GAOLER_CHAIN_DAMAGE, active_frames=ACTIVE["chain"],
            knockback=3.0,
        ))
        self._notify("gaoler_chain")

    def _do_keys(self) -> None:
        """Anahtar demetini firlatiyor - Okcu'nun dersi.

        Mermi altyapisi (`Hitbox.velocity`, `stop_on_solid`) Okcu icin
        yazilmisti. Burada **ikinci kez** kullaniliyor ve hicbir sey
        eklemek gerekmedi - sinir dogru yerdeymis.
        """
        rect = pygame.Rect(int(self.body.center_x + self.facing * 12),
                           int(self.body.center_y - 4), 7, 7)
        self.scene.hitboxes.spawn(Hitbox(
            rect=rect, owner=self, targets=Team.PLAYER,
            damage=GAOLER_KEYS_DAMAGE, active_frames=GAOLER_KEYS_LIFE,
            knockback=2.4,
            velocity=(self.facing * GAOLER_KEYS_SPEED, -0.35),
            stop_on_solid=True,
        ))
        self.scene.game.play_sound("swing_light")
        self._notify("gaoler_keys")

    def _do_call(self) -> None:
        """Mahkumlari cagiriyor - Komutan'in dersi.

        Cagirdiklari **Katman 1**: bu zindanda cürüyüp kalmislar.
        Gerekce modul basliginda.
        """
        from src.entities.enemies.shambler import Shambler
        spawned = 0
        for index in range(GAOLER_CALL_COUNT):
            if self.called >= GAOLER_CALL_LIMIT:
                break
            side = -1 if index % 2 == 0 else 1
            x = self.body.center_x + side * TILE_SIZE * 3
            spot = self.scene.free_spot_near(x, self.body.bottom, self.body)
            enemy = Shambler(self.scene, spot[0], spot[1])
            enemy.aware = True
            self.scene.enemies.append(enemy)
            self.called += 1
            spawned += 1
            self.scene.particles.burst(spot[0], spot[1] - 8, 10,
                                       path="violet", speed=(0.5, 1.8))
        if spawned:
            self.scene.game.play_sound("rift_open")
        self._notify("gaoler_call")

    def _do_snuff(self) -> None:
        """Yakindaki mangali sonduruyor - faz 2'nin isik ekonomisi.

        Oyuncu yakiyor, o sonduruyor. Bolum 3'un Sonmus Olan'i tam
        tersini yapiyordu (yanan mangal onu sersemletiyordu); burada
        mangal bir **silah degil bir kaynak**, ve kaynak tukeniyor.
        """
        brazier = self._nearest_lit()
        if brazier is None:
            return
        brazier.extinguish()
        self.scene.particles.burst(brazier.x, brazier.y - 6, 12,
                                   path="soot", speed=(0.4, 1.4))
        self.scene.game.play_sound("torch_light")
        self._notify("gaoler_snuff")

    def _notify(self, name: str) -> None:
        hook = getattr(self.scene, "on_boss_move", None)
        if hook:
            hook(self, name)

    # --- Dongu ---------------------------------------------------------------
    def update(self) -> None:
        super().update()
        self._update_lantern()
        self._update_animation()

    def _update_animation(self) -> None:
        if self.dead:
            self.animator.play("death")
        elif self.state is EnemyState.STAGGER:
            self.animator.play("hurt")
        elif self.state in (EnemyState.TELL, EnemyState.ATTACK):
            self.animator.play("attack3" if self.move in ("slam", "call")
                               else "attack1")
        elif abs(self.body.vx) > 0.08:
            self.animator.play("run")
        else:
            self.animator.play("idle")
        self.animator.update()

    # --- Cizim ---------------------------------------------------------------
    def tell_colour(self):
        """Gard aciksa tell rengi degisiyor - "onden gecmez" bilgisi.

        Renk **tek basina** yeterli degil (`CLAUDE.md` 10): sahne ayrica
        gard cizgisini ciziyor (asagida), yani sekil kanali da var.
        """
        if self.guarding:
            return palette.color("bone")
        return super().tell_colour()

    def draw_extra(self, surface: pygame.Surface, offset) -> None:
        self._draw_lantern(surface, offset)
        self._draw_guard(surface, offset)
        self._draw_eyes(surface, offset)

    def _draw_lantern(self, surface: pygame.Surface, offset) -> None:
        """Fener - sprite'ta degil burada, cunku **degisiyor**.

        Parlak -> catlak -> kirik. Bir sprite karesine cakilsaydi faz
        gecisi gorunmez olurdu; oysa bu boss'un ilerlemesini anlatan
        tek gorsel o.
        """
        if self.dead:
            return
        ox, oy = offset
        x = int(self.body.center_x - self.facing * 13) - ox
        y = int(self.body.center_y - 10) - oy
        # Sap - fener kirildiktan sonra da elinde kaliyor.
        surface.fill(palette.color("stone_darkest"), (x, y - 6, 1, 6))
        if self.lantern_broken:
            # Kirik kafes: iki egik parca. Sekil kanali - oyuncu
            # "sondu" degil "KIRILDI" gorsun.
            surface.fill(palette.color("stone_dark"), (x - 3, y, 3, 2))
            surface.fill(palette.color("stone_dark"), (x + 1, y + 1, 3, 2))
            return
        dim = self.phase >= 1
        flicker = 0.72 + 0.28 * math.sin(self.frames * 0.14)
        if dim:
            # Catlak fener: daha hizli, daha duzensiz titriyor.
            flicker *= 0.62 + 0.38 * math.sin(self.frames * 0.41)
        surface.fill(palette.color("stone_dark"), (x - 3, y - 1, 7, 8))
        core = tuple(int(c * flicker)
                     for c in palette.color("ember_light" if not dim
                                            else "ember"))
        surface.fill(core, (x - 2, y, 5, 6))
        surface.fill(palette.color("stone_darkest"), (x - 3, y + 6, 7, 1))

    def _draw_guard(self, surface: pygame.Surface, offset) -> None:
        """Gard cizgisi - "bu taraf gecmez" SEKIL olarak.

        Renk korlugu icin renk tek basina yetmez (`CLAUDE.md` 10):
        gardin varligi bir cizgiyle de anlatiliyor. Vurus savusturulunca
        kalinlasiyor - geri bildirim.
        """
        if not self.guarding:
            return
        ox, oy = offset
        x = int(self.body.center_x + self.facing * (self.body_width // 2 + 2))
        top = int(self.body.top + 6) - oy
        thickness = 1 + min(2, self.guard_hits % 3)
        surface.fill(palette.color("stone_light"),
                     (x - ox, top, thickness, self.body_height - 12))

    def _draw_eyes(self, surface: pygame.Surface, offset) -> None:
        """Karanlikta gozler - **tell'in adil kalmasi buna bagli.**

        `CLAUDE.md` 7: her saldiri en az 14 kare onceden okunabilir.
        Fener kirildiktan sonra govde karanlikta kayboluyor ama gozler
        kalmali, yoksa kural cignenir. Tell sirasinda tehlike rengine
        donuyorlar - yani karanlik konumu gizliyor, niyeti degil.
        """
        if self.dead:
            return
        ox, oy = offset
        x = int(self.body.center_x) - ox
        y = int(self.body.top + 8) - oy
        telling = self.state in (EnemyState.TELL, EnemyState.ATTACK)
        base = palette.color("danger_bright" if telling else "ember_light")
        pulse = (GAOLER_EYE_GLOW / 255.0) * (
            1.0 if telling else 0.72 + 0.28 * math.sin(self.frames * 0.1))
        colour = tuple(int(c * pulse) for c in base)
        surface.fill(colour, (x - 4 + (self.facing > 0) * 2, y, 2, 2))
        surface.fill(colour, (x + 1 + (self.facing > 0) * 2, y, 2, 2))

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"hamle {self.move}  gard {self.guarding}  fener "
            f"{self.lantern_radius:.0f}  cagrilan {self.called}"
        ]
