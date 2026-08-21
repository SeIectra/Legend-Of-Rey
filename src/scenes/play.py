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
from src.art.particles import ParticleField
from src.combat.attack_token import AttackTokenManager
from src.combat.hitbox import HitboxManager, Team
from src.config import (
    COMBO_THRESHOLD_HIGH, COMBO_THRESHOLD_MID, INTERNAL_WIDTH, TILE_SIZE,
)
from src.systems.echo import COMBO_TO_RESTORE
from src.core.camera import Camera
from src.core.input import Action
from src.core.juice import ImpactEvent, ImpactWeight, Juice
from src.core.scene import Scene
from src.entities.character_stats import ARDO, REY
from src.entities.player import Player
from src.systems.compass import Compass
from src.systems.echo import EchoState
from src.systems.save import read_save
from src.ui import echo_view
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
        self.compass = Compass()
        self.breakables: list = []
        # Diyalog oynanisi **durdurmuyor**: oyuncu konusma surerken
        # yuruyebilir. Durdursaydik her replik bir kesinti olurdu ve oyuncu
        # okumak yerine gecmeye calisirdi.
        self.dialogue = Dialogue()

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
            self.echo.update(self.game.input.held(Action.ECHO))
            if self.game.input.pressed(Action.ECHO_ASK):
                self.on_echo_ask()
        self.compass.update(self.player)
        self.dialogue.update(self.game)
        # Kirilabilir duvarlar Yanki ile parliyor. Liste kucuk (oda basina
        # birkac tane), her karede uretmek sorun degil.
        self.breakables = [_WallTarget(r)
                           for r in self.tilemap.breakable_rects()]

        self.hud.update(self.player, self.gold, self.echo_tier)
        if self.toast_frames > 0:
            self.toast_frames -= 1
        self.update_scene()

    def update_scene(self) -> None:
        """Alt sinifa ait kare islemleri (tetikleyiciler, anlatim)."""

    def say(self, *lines) -> None:
        """Replik dizisi baslatir. `lines` `Line` nesneleri."""
        self.dialogue.start(tuple(lines))

    # --- Yanki --------------------------------------------------------------
    def on_echo_ask(self) -> None:
        """Oyuncu Yanki'ya soru sordu. Alt sinif cevabin **anlamini** verir.

        Taban yalnizca cevabin turunu uretiyor (dogru/eksik/yalan); o
        cevabin neyi gosterdigine bolum karar veriyor - cikis mi, gizli oda
        mi, Cemo mu.
        """
        if self.echo is None:
            return
        self.echo.ask()
        self.game.play_ui_sound("echo_ask")

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
            if box.is_counter:
                self.show_toast(t("combat.counter"))
            if result.killed:
                # Kill cancel: recovery aninda kesilir, akis surer.
                self.player.notify_kill()

    def on_enemy_died(self, enemy) -> None:
        self.juice.explosion(enemy.body.center_x, enemy.body.center_y,
                             ImpactWeight.FINISHER)
        self.particles.burst(enemy.body.center_x, enemy.body.center_y, 16,
                             path="blood", speed=(1.0, 3.0))
        # Parcaciklar soner, leke kalir: koridora donunce dovusun izi durur.
        self.decals.splatter(enemy.body.center_x, enemy.body.feet[1], amount=10)

    def on_enemy_tell(self, enemy) -> None:
        """Tell basladi. Ses Gorev 10'da; simdilik gorsel kanal yeter."""
        self.game.play_ui_sound("tell")

    def on_climber_drop(self, enemy) -> None:
        """Tirmanan tavandan koptu - toz doksun, telegraf tamamlansin."""
        self.particles.burst(enemy.body.center_x, enemy.body.bottom, 5,
                             direction=(0.0, 1.0), path="dust",
                             speed=(0.2, 0.7), life=(10, 20), gravity=0.03)

    def on_bloated_explode(self, enemy) -> None:
        """Patlama radyal - yonlu degil (docs/derinlestirme.md 1.2)."""
        self.juice.explosion(enemy.body.center_x, enemy.body.center_y,
                             ImpactWeight.KILL)
        self.particles.burst(enemy.body.center_x, enemy.body.center_y, 22,
                             path="spark", speed=(1.2, 3.6))
        self.decals.scorch(enemy.body.center_x, enemy.body.feet[1])

    def on_combo_threshold(self, player, threshold: int) -> None:
        # Saldirgan oynayan kademesini geri kazanir (GOREVLER Gorev 3.1).
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

    def on_player_attack(self, player, index: int) -> None: ...

    def on_attack_swing(self, player, box) -> None:
        """Vurus kirilabilir duvara degdi mi?

        Hitbox sistemi yalnizca **varliklara** bakiyor; duvar bir tile.
        Burada ayrica sorulmasi gerekiyor - yoksa oyuncu duvara vurur ve
        hicbir sey olmaz.
        """
        broken = False
        for rect in self.tilemap.breakable_rects():
            if not box.rect.colliderect(rect):
                continue
            tx = rect.x // TILE_SIZE
            ty = rect.y // TILE_SIZE
            if self.tilemap.break_at(tx, ty):
                broken = True
                self.particles.burst(rect.centerx, rect.centery, 8,
                                     path="dust", speed=(0.5, 1.8))
                self.decals.splatter(rect.centerx, rect.bottom, amount=4,
                                     path="soot", spread=7.0)
        if broken:
            self.juice.explosion(player.body.center_x, player.body.center_y,
                                 ImpactWeight.NORMAL)
            self.on_wall_broken()

    def on_wall_broken(self) -> None:
        """Gizli gecit acildi. Alt sinif ozel tepki verebilir."""
        self.show_toast(t("echo.wall_broken"), frames=120)

    def on_player_jump(self, player) -> None:
        self.particles.burst(player.body.feet[0], player.body.feet[1], 4,
                             direction=(0.0, -1.0), path="dust",
                             speed=(0.3, 0.9), life=(8, 16), gravity=0.04)

    def on_player_land(self, player, air_frames: int) -> None:
        self.particles.burst(player.body.feet[0], player.body.feet[1], 6,
                             direction=(0.0, -1.0), path="dust",
                             speed=(0.4, 1.2), life=(10, 20), gravity=0.05)

    def on_player_dodge(self, player) -> None:
        self.particles.burst(player.body.center_x, player.body.feet[1], 8,
                             direction=(-player.facing, 0.0), path="dust",
                             speed=(0.5, 1.6), life=(10, 22), gravity=0.03)

    def on_dodge_trail(self, player) -> None:
        if player.dodge.frames_left % 3 == 0:
            self.particles.burst(player.body.center_x, player.body.center_y, 1,
                                 direction=(-player.facing, 0.0), path="echo",
                                 speed=(0.1, 0.4), life=(8, 14), gravity=0.0)

    def on_player_hurt(self, player, result) -> None:
        self.show_toast(t("combat.hurt"))

    def on_echo_tier_changed(self, tier: int, gained: bool) -> None:
        """Kademe degisti. Asamali aciga cikarma: yalnizca **degisince**
        gosteriliyor (CLAUDE.md 9)."""
        # Anahtarlar **acikca** yazili: f-string ile kurulan anahtari
        # tests/test_lang.py kaynak taramasinda goremiyor ve "olu anahtar"
        # sayiyor. Bu tuzaga ikinci kez dusuldu.
        self.show_toast(t("echo.tier_up" if gained else "echo.tier_down"),
                        frames=120)

    def on_player_died(self, player) -> None:
        # Olunce Yanki bir kademe zayiflar. Dip SESSIZ - daha asagi inmez,
        # olum sarmali boyle engelleniyor (docs/gdd.md 4).
        if self.echo is not None and self.echo.weaken():
            self.on_echo_tier_changed(self.echo.tier, gained=False)
        self.show_toast(t("combat.died"))

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
