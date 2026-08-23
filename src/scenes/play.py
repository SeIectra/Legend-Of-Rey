"""Oynanabilir sahne temeli - bolumler ve test odasi bundan turer.

Dovus odasi bir donem butun bu baglantiyi kendi icinde tutuyordu. Bolum 1
gelince ayni sey ikinci kez yazilacakti; **game feel'in tek gecis noktasi
olmasi** tam da bunu yasaklıyor (CLAUDE.md 7): hitstop, sarsinti ve parcacik
tek bir `on_hit()` cagrisindan tetiklenmeli. Iki kopya olsaydi biri
guncellenir digeri geride kalirdi ve fark "bir sahnede vurus daha iyi
hissettiriyor" diye ortaya cikardi - bulmasi cok zor bir hata.

Alt sinif yalnizca **sahneyi** kurar: tilemap, oyuncu, dusmanlar, kamera
sinirlari. Dongu, hasar cozumu, kalicilik ve kancalarin tamami burada.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.ambience import Ambience
from src.art.particles import ParticleField
from src.combat.attack_token import AttackTokenManager
from src.combat.hitbox import HitboxManager, Team
from src.config import (
    COMBO_THRESHOLD_HIGH, COMBO_THRESHOLD_MID, HARD_LAND_AIR_FRAMES,
    INTERNAL_WIDTH, NECKLACE_BEAT_MIN_WARMTH, TILE_SIZE,
)
from src.systems.echo import COMBO_TO_RESTORE
from src.core.camera import Camera
from src.core.input import Action
from src.core.juice import ImpactEvent, ImpactWeight, Juice
from src.core.scene import Scene
from src.entities.character_stats import ARDO, REY
from src.entities.player import Player
from src.systems import abilities
from src.systems.compass import Compass
from src.systems.echo import Answer, EchoState
from src.systems.save import read_save
from src.ui import echo_view
from src.ui.chapter_card import ChapterCard
from src.ui.dialogue import Dialogue
from src.ui import text
from src.ui.hud import HUD
from src.ui.i18n import t
from src.world.decals import DecalField

HUD_MARGIN = 6


class _WallTarget:
    """Yanki'nin parlatacagi duvar. `echo_view` `.rect` bekliyor."""

    __slots__ = ("rect",)

    def __init__(self, rect) -> None:
        self.rect = rect


class PlayScene(Scene):
    """Oynanabilir bir alan: tilemap, oyuncu, dusmanlar, game feel."""

    # Adim sesi zemine gore degil **sahneye** gore degisir (SES-LISTESI 2:
    # "Taş zeminde"/"Toprak/koy zemininde") - zindan varsayilan, Bolum 1
    # (koy) kendi degerini ezer.
    footstep_sound = "step_stone"

    # Bolum basi karti - alt sinif ikisini de verirse gosterilir.
    # `0` = kart yok (dovus test odasi, temel dogrulama ekrani gibi
    # bolum olmayan sahneler).
    chapter_number: int = 0
    chapter_name_key: str = ""

    # Odanin havasi (src/art/ambience.py). Bos = atmosfer katmani yok.
    # `particles` olaylar icin (vurus/olum), bu SUREKLI olan sey - oda
    # hicbir sey olmasa bile yasiyor gorunsun.
    ambience_preset: str = ""

    def setup(self) -> None:
        """Alt sinif sahneyi burada kurar.

        `self.tilemap` ve `self.player` **zorunlu**; `self.enemies` istege
        bagli (varsayilan bos).
        """
        raise NotImplementedError

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.enemies: list = []
        self.toast = ""
        self.toast_frames = 0
        self.total_hits = 0

        self.particles = ParticleField()
        self.juice = Juice(self.game, spawn_particles=self._emit_particles)
        # Ekran sarsintisi ayarlardan gelir - erisilebilirlik icin kapatilabilir.
        shake = float(self.game.settings.get("screen_shake", 1.0))
        self.juice.configure(shake_enabled=shake > 0.0, shake_scale=shake)
        self.hitboxes = HitboxManager(on_hit=self.on_hit)
        # Ayni anda en fazla 2 dusman saldirabilir.
        self.tokens = AttackTokenManager()
        self.camera = Camera()
        self.save_data, _ = read_save()
        self.hud = HUD(self.game)

        # Yanki yalnizca Rey'de. Ardo'da `None` kalir ve kod her yerde
        # "Yanki var mi?" diye dallanmaz - `has_echo` tek yerde sorulur.
        self.echo = (EchoState(tier=self.echo_tier)
                     if self.character != "ardo" else None)
        self._echo_was_active = False   # echo_open/close kenar tespiti icin
        self.compass = Compass()
        self._beat_index = -1            # necklace_beat kenar tespiti icin
        self.breakables: list = []
        # Diyalog oynanisi **durdurmuyor**: oyuncu konusma surerken
        # yuruyebilir. Durdursaydik her replik bir kesinti olurdu ve oyuncu
        # okumak yerine gecmeye calisirdi.
        self.dialogue = Dialogue()

        # Bolum basi karti - alt sinif `chapter_number`/`chapter_name_key`
        # verirse gosterilir. Ara sahne DEGIL, bindirme: oynanisi
        # durdurmuyor, oyuncu ilk kareden itibaren yuruyebilir.
        self.card = (ChapterCard(self.chapter_number, self.chapter_name_key)
                     if self.chapter_number else None)
        self.ambience = (Ambience(self.ambience_preset)
                         if self.ambience_preset else None)

        self.setup()

        self.camera.set_bounds(self.tilemap.bounds)
        self.decals = DecalField(*self.tilemap.bounds.size)
        self.camera.snap_to(self.player.body.center_x, self.player.body.center_y)

    # --- Yardimcilar --------------------------------------------------------
    def make_player(self, x: float, y: float) -> Player:
        stats = ARDO if self.character == "ardo" else REY
        return Player(self, x, y, stats)

    @property
    def gold(self) -> int:
        return self.save_data.gold if self.save_data else 0

    @property
    def echo_tier(self) -> int:
        return self.save_data.echo_tier if self.save_data else 2

    # --- Dongu --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if self.game.input.pressed(Action.PAUSE):
            from src.ui.pause import PauseScene
            self.scenes.push(PauseScene, save_data=self.save_data)

    def update(self) -> None:
        self.player.update()
        self.tokens.update()
        for enemy in self.enemies:
            enemy.update()
        self.enemies = [e for e in self.enemies if not e.remove]

        self.hitboxes.update({
            Team.ENEMY: self.enemies,
            Team.PLAYER: [self.player],
        })

        self.particles.update()
        self.juice.update()
        self.camera.shake_offset = self.juice.shake.offset
        self.camera.update(self.player.body.center_x,
                           self.player.body.center_y - 6,
                           facing=self.player.facing,
                           grounded=self.player.body.grounded)

        if self.echo is not None:
            self.echo.update(self.echo_held())
            self._update_echo_audio()
            if self.game.input.pressed(Action.ECHO_ASK):
                self.on_echo_ask()
        self.compass.update(self.player)
        self._update_necklace_audio()
        self.dialogue.update(self.game)
        if self.card is not None:
            self.card.update()
        if self.ambience is not None:
            self.ambience.update(self.camera.offset)
        # Kirilabilir duvarlar Yanki ile parliyor. Liste kucuk (oda basina
        # birkac tane), her karede uretmek sorun degil.
        self.breakables = [_WallTarget(r)
                           for r in self.tilemap.breakable_rects()]

        self.hud.update(self.player, self.gold, self.echo_tier)
        if self.toast_frames > 0:
            self.toast_frames -= 1
        self.update_scene()

    def echo_held(self) -> bool:
        """Yanki bu karede acik mi?

        Normalde tusun kendisi. Bolum, anlatimin gerektirdigi anlarda
        (Bolum 2'nin Yanki odasi: ses **kendiliginden** yukselir) bunu
        ezebilsin diye ayri bir kanca. Ezme `EchoState`'in icine
        yazilsaydi bedel muhasebesi iki yere dagilirdi.
        """
        return self.game.input.held(Action.ECHO)

    def update_scene(self) -> None:
        """Alt sinifa ait kare islemleri (tetikleyiciler, anlatim)."""

    def say(self, *lines, auto_advance: bool = False) -> None:
        """Replik dizisi baslatir. `lines` `Line` nesneleri.

        `auto_advance=True` yalnizca bir sahne-zamanlayicisiyla yarisan
        (orn. Bolum 1'in prolog beat'leri) dizilerde kullanilir - normal
        kesif/dovus repligi oyuncu onaylayana kadar ekranda kalir.
        """
        self.dialogue.start(tuple(lines), auto_advance=auto_advance)

    # --- Yanki --------------------------------------------------------------
    def on_echo_ask(self) -> None:
        """Oyuncu Yanki'ya soru sordu. Alt sinif cevabin **anlamini** verir.

        Taban yalnizca cevabin turunu uretiyor (dogru/eksik/yalan); o
        cevabin neyi gosterdigine bolum karar veriyor - cikis mi, gizli oda
        mi, Cemo mu.
        """
        if self.echo is None:
            return
        answer = self.echo.ask()
        self.game.play_sound("echo_ask", bus="volume_echo")
        # `echo_answer_lie` **bilerek** `echo_answer_truth` ile ayni dalga
        # formu (sfx_world.py) - kulaktan ayirt edilebilir olsaydi mekanik
        # olurdu (docs/dovus-sistemi.md 5).
        answer_sound = {
            Answer.TRUTH: "echo_answer_truth",
            Answer.PARTIAL: "echo_answer_partial",
            Answer.LIE: "echo_answer_lie",
        }.get(answer)
        if answer_sound:
            self.game.play_sound(answer_sound, bus="volume_echo")

    def _update_echo_audio(self) -> None:
        """Yanki acilirken/kapanirken kenar tespiti - `EchoState` kendisi
        sesle ilgilenmiyor (systems/ katmani salt mantik), kenar burada.

        Surekli `echo_loop` dongusu **kaldirildi** (Arda'nin canli oynanis
        geri bildirimi, 22.08.2026: "cizirti gibi, rahatsiz edici").
        Sentezlenmis surekli/donguluk sesler bu oturumda genel olarak
        guvenilir bulunmadi; kisa, nedeni belli tek seferlik sesler
        (echo_open/close gibi) kaliyor.
        """
        active = self.echo.active
        if active and not self._echo_was_active:
            self.game.play_sound("echo_open", bus="volume_echo")
        elif not active and self._echo_was_active:
            self.game.play_sound("echo_close", bus="volume_echo")
        self._echo_was_active = active

    def _update_necklace_audio(self) -> None:
        """Kalp atisi periyodu her devri tamamladiginda tek `tak` sesi.

        `Compass.pulse` surekli bir 0..1 egri veriyor (cizim icin); ses
        icin **kenar** gerekiyor - donguyu kendisi saymiyor, burada sayilir.
        """
        if self.compass.warmth <= NECKLACE_BEAT_MIN_WARMTH:
            self._beat_index = -1
            return
        index = self.compass.frame // max(1, self.compass.beat_period)
        if index != self._beat_index:
            self._beat_index = index
            self.game.play_sound("necklace_beat", volume=self.compass.warmth)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("abyss_dark"))
        offset = self.camera.offset

        self.draw_background(surface, offset)
        self.tilemap.draw(surface, offset)
        self.decals.draw(surface, offset)
        for enemy in self.enemies:
            enemy.draw(surface, offset)
        self.player.draw(surface, offset)
        self.particles.draw(surface, offset)
        self.draw_foreground(surface, offset)
        # Atmosfer aktorlerin ONUNDE: toz "odanin icinde" degil "kamerayla
        # oyuncu arasinda" olmali, yoksa zemin dokusu sanilir. Yanki
        # karartmasinin ALTINDA kaliyor - Yanki acikken hava da bulaniyor.
        if self.ambience is not None:
            self.ambience.draw(surface)

        # Sira: once dunya kararir (bedel), sonra gizli seyler o karanligi
        # delerek cikar (kazanc). Ters sirada Yanki acilinca ekran
        # aydinlaniyordu - bedel tam tersine donmustu.
        if self.echo is not None:
            echo_view.draw_dim(surface, self.echo)
            echo_view.draw_reveal(surface, offset, self.echo, self.player,
                                  self.enemies, self.breakables)
            echo_view.draw_answer(surface, offset, self.echo, self.player)

        if self.game.debug_overlay:
            self._draw_hitboxes(surface, offset)
        self._draw_hud(surface)
        self.dialogue.draw(surface, self.game.frame)
        # Kart diyalogun USTUNDE ama Yanki saciliminin ALTINDA: bolum
        # adi her zeminde okunmali, ama Yanki acikken o da bulanir.
        if self.card is not None:
            self.card.draw(surface)
        self.draw_overlay(surface)

        # Kromatik kayma en son: arayuz dahil her seyin uzerine. Yanki
        # acikken oyuncu her seyi biraz daha zor goruyor.
        if self.echo is not None:
            echo_view.draw_fringe(surface, self.echo)

    def draw_background(self, surface, offset) -> None: ...

    def draw_foreground(self, surface, offset) -> None: ...

    def draw_overlay(self, surface) -> None: ...

    # --- Game feel kancalari ------------------------------------------------
    def on_hit(self, box, target, result, direction) -> None:
        """Bir vurus degdi. **Ucu birden tek cagridan** - kare kaymasi olmasin."""
        weight = ImpactWeight.NORMAL
        if result.killed:
            weight = ImpactWeight.KILL
        elif box.is_finisher:
            weight = ImpactWeight.FINISHER

        self.juice.on_hit(
            ImpactEvent(
                x=target.body.center_x,
                y=target.body.center_y,
                direction=direction,
                weight=weight,
                particle_path="violet" if box.is_counter else "blood",
                particle_count=10 if box.is_finisher else 6,
            ),
            target_flash=target.flash,
            target_squash=target.squash,
        )

        if box.owner is self.player:
            self.total_hits += 1
            self.player.register_hit()
            self.game.play_sound(self._hit_sound(box, result),
                                 muffled=self._echo_active())
            if box.is_counter:
                self.show_toast(t("combat.counter"))
            if result.killed:
                # Kill cancel: recovery aninda kesilir, akis surer.
                self.player.notify_kill()

    def _hit_sound(self, box, result) -> str:
        if result.killed:
            return "hit_kill"
        if box.is_counter:
            return "hit_counter"
        if box.is_finisher:
            return "hit_heavy"
        return "hit_light"

    def _echo_active(self) -> bool:
        return self.echo is not None and self.echo.active

    def on_enemy_died(self, enemy) -> None:
        self.juice.explosion(enemy.body.center_x, enemy.body.center_y,
                             ImpactWeight.FINISHER)
        self.particles.burst(enemy.body.center_x, enemy.body.center_y, 16,
                             path="blood", speed=(1.0, 3.0))
        # Parcaciklar soner, leke kalir: koridora donunce dovusun izi durur.
        self.decals.splatter(enemy.body.center_x, enemy.body.feet[1], amount=10)
        # Bos dize = sessiz kal (orn. Sismek zaten patlama sesiyle oldu,
        # ustune binmesin - src/entities/enemies/bloated.py).
        if enemy.death_sound:
            self.game.play_sound(enemy.death_sound)

    def on_enemy_tell(self, enemy) -> None:
        """Tell basladi - hangi ses calinacagini dusmanin kendi tipi
        soyluyor (`Enemy.tell_sound`, varsayilan genel "enemy_tell")."""
        self.game.play_sound(enemy.tell_sound, muffled=self._echo_active())

    def on_climber_drop(self, enemy) -> None:
        """Tirmanan tavandan koptu - toz doksun, telegraf tamamlansin."""
        self.particles.burst(enemy.body.center_x, enemy.body.bottom, 5,
                             direction=(0.0, 1.0), path="dust",
                             speed=(0.2, 0.7), life=(10, 20), gravity=0.03)
        self.game.play_sound("climber_drop")

    def on_bloated_explode(self, enemy) -> None:
        """Patlama radyal - yonlu degil (docs/derinlestirme.md 1.2)."""
        self.juice.explosion(enemy.body.center_x, enemy.body.center_y,
                             ImpactWeight.KILL)
        self.particles.burst(enemy.body.center_x, enemy.body.center_y, 22,
                             path="spark", speed=(1.2, 3.6))
        self.decals.scorch(enemy.body.center_x, enemy.body.feet[1])
        self.game.play_sound("bloated_explode")

    def on_combo_threshold(self, player, threshold: int) -> None:
        # Saldirgan oynayan kademesini geri kazanir (DEVIR gorev 3.1).
        # Korkak oynayan iyilesemez - can siseleri nadir tutuluyor.
        if (threshold >= COMBO_TO_RESTORE and self.echo is not None
                and self.echo.restore()):
            self.on_echo_tier_changed(self.echo.tier, gained=True)
        if threshold >= COMBO_THRESHOLD_HIGH:
            self.show_toast(t("combat.combo_echo", count=threshold))
        elif threshold >= COMBO_THRESHOLD_MID:
            self.show_toast(t("combat.combo_health", count=threshold))
        else:
            self.show_toast(t("combat.combo", count=threshold))

    def on_combo_reset(self) -> None: ...

    def on_player_attack(self, player, index: int) -> None:
        """Zincir bir sonraki vurusa gecti - degip degmemesinden bagimsiz,
        kilic her savrulduğunda calar (SES-LISTESI 1: "vurus degmese de
        calar")."""
        self.game.play_sound(
            "swing_heavy" if player.chain.is_finisher else "swing_light")

    def on_attack_swing(self, player, box) -> None:
        """Vurus kirilabilir duvara degdi mi?

        Hitbox sistemi yalnizca **varliklara** bakiyor; duvar bir tile.
        Burada ayrica sorulmasi gerekiyor - yoksa oyuncu duvara vurur ve
        hicbir sey olmaz.
        """
        broken: list[pygame.Rect] = []
        for rect in self.tilemap.breakable_rects():
            if not box.rect.colliderect(rect):
                continue
            tx = rect.x // TILE_SIZE
            ty = rect.y // TILE_SIZE
            if self.tilemap.break_at(tx, ty):
                broken.append(rect)
                self.particles.burst(rect.centerx, rect.centery, 8,
                                     path="dust", speed=(0.5, 1.8))
                self.decals.splatter(rect.centerx, rect.bottom, amount=4,
                                     path="soot", spread=7.0)
        if broken:
            self.juice.explosion(player.body.center_x, player.body.center_y,
                                 ImpactWeight.NORMAL)
            self.on_wall_broken(broken)

    def on_wall_broken(self, rects: list[pygame.Rect]) -> None:
        """Gizli gecit acildi. `rects` yikilan tile'lar.

        Hangi duvarin yikildigi bolume soyleniyor: bir bolumde birden fazla
        kirilabilir duvar olabiliyor ve hepsi ayni sey anlamina gelmiyor
        (Bolum 2: biri yolu aciyor, digeri gizli odayi).
        """
        self.show_toast(t("echo.wall_broken"), frames=120)

    def on_player_jump(self, player) -> None:
        self.particles.burst(player.body.feet[0], player.body.feet[1], 4,
                             direction=(0.0, -1.0), path="dust",
                             speed=(0.3, 0.9), life=(8, 16), gravity=0.04)
        self.game.play_sound("jump")

    def on_player_land(self, player, air_frames: int) -> None:
        self.particles.burst(player.body.feet[0], player.body.feet[1], 6,
                             direction=(0.0, -1.0), path="dust",
                             speed=(0.4, 1.2), life=(10, 20), gravity=0.05)
        hard = air_frames >= HARD_LAND_AIR_FRAMES
        self.game.play_sound("land_hard" if hard else "land_soft")

    def on_player_dodge(self, player) -> None:
        self.particles.burst(player.body.center_x, player.body.feet[1], 8,
                             direction=(-player.facing, 0.0), path="dust",
                             speed=(0.5, 1.6), life=(10, 22), gravity=0.03)
        self.game.play_sound("dodge")

    def on_dodge_trail(self, player) -> None:
        if player.dodge.frames_left % 3 == 0:
            self.particles.burst(player.body.center_x, player.body.center_y, 1,
                                 direction=(-player.facing, 0.0), path="echo",
                                 speed=(0.1, 0.4), life=(8, 14), gravity=0.0)

    def on_player_step(self, player) -> None:
        """Adim - hangi ses calinacagi sahnenin `footstep_sound`'undan gelir
        (zemine gore degil **sahneye** gore, bkz. sinif tanimi)."""
        self.game.play_sound(self.footstep_sound, muffled=self._echo_active())

    def on_player_hurt(self, player, result) -> None:
        self.show_toast(t("combat.hurt"))
        self.game.play_sound("player_hurt", muffled=self._echo_active())

    def on_echo_tier_changed(self, tier: int, gained: bool) -> None:
        """Kademe degisti. Asamali aciga cikarma: yalnizca **degisince**
        gosteriliyor (CLAUDE.md 9)."""
        # Anahtarlar **acikca** yazili: f-string ile kurulan anahtari
        # tests/test_lang.py kaynak taramasinda goremiyor ve "olu anahtar"
        # sayiyor. Bu tuzaga ikinci kez dusuldu.
        self.show_toast(t("echo.tier_up" if gained else "echo.tier_down"),
                        frames=120)
        self.game.play_sound("echo_tier_up" if gained else "echo_tier_down",
                             bus="volume_echo")

    def on_player_died(self, player) -> None:
        # Olunce Yanki bir kademe zayiflar. Dip SESSIZ - daha asagi inmez,
        # olum sarmali boyle engelleniyor (docs/gdd.md 4).
        if self.echo is not None and self.echo.weaken():
            self.on_echo_tier_changed(self.echo.tier, gained=False)
        self.show_toast(t("combat.died"))
        self.game.play_sound("player_death")

    def on_ability_gained(self, ability: str) -> None:
        """Yetenek kazanildi. Bir sey **kazanmis** olmali - sessiz gecmesin.

        Paylasilan (chapter01.py'den tasindi): her bolum kendi yetenek
        anini yasiyor, ama "kazanmak" hep ayni goruntu/ses/yaziya sahip
        olmali - dagitilsaydi biri farkli hissettirirdi.
        """
        self.show_toast(t(abilities.label_key(ability)), frames=180)
        self.juice.explosion(self.player.body.center_x,
                             self.player.body.center_y, ImpactWeight.NORMAL)
        self.particles.burst(self.player.body.center_x,
                             self.player.body.center_y, 14,
                             path="spark", speed=(0.6, 2.2))
        self.game.play_sound("item_pickup")

    def _emit_particles(self, event: ImpactEvent) -> None:
        self.particles.burst(event.x, event.y, event.particle_count,
                             direction=event.direction, path=event.particle_path)

    def show_toast(self, message: str, frames: int = 72) -> None:
        self.toast = message
        self.toast_frames = frames

    def _draw_hitboxes(self, surface: pygame.Surface,
                       offset: tuple[int, int]) -> None:
        ox, oy = offset
        for box in self.hitboxes.boxes:
            pygame.draw.rect(surface, palette.color("danger_bright"),
                             box.rect.move(-ox, -oy), 1)
        for actor in [self.player, *self.enemies]:
            pygame.draw.rect(surface, palette.color("echo"),
                             actor.hurtbox.move(-ox, -oy), 1)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        # Asamali aciga cikarma: bilgi yalnizca ilgili oldugunda gorunur.
        self.hud.draw(surface, self.player, self.gold, self.echo_tier)
        if self.toast_frames > 0:
            text.draw(surface, self.toast, INTERNAL_WIDTH // 2, 42,
                      color=palette.color("violet_bright"), align="center",
                      outline=True)

    def debug_lines(self) -> list[str]:
        return [
            *self.player.debug_lines(),
            f"hitbox {self.hitboxes.active_count}  "
            f"parcacik {self.particles.alive_count}  "
            f"sarsinti {self.juice.shake.frames_left}",
            f"dusman {len(self.enemies)}  hak {self.tokens.active_count}  "
            f"leke {self.decals.count}",
        ]
