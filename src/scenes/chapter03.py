"""Bolum 3 - "Mesale Mahzeni". Oynanabilir sahne.

Oda geometrisi `src/world/rooms/chapter03.py` icinde; burasi onu oynatiyor
(chapter02.py'nin *aynı* iskeleti: `_room_at`/`_enter_room`/`_spawn_room`).

## Bu bolumun kalbi: `self.light`

`docs/bolum-03.md`'nin uc yeni mekaniginin (meşale ekonomisi, ses haritasi,
Mor Alev) ucu de "bu nokta aydinlik mi?" sorusuna dayaniyor
(`src/systems/light.py`). Her kare `_update_light()` bu soruyu yeniden
kurar: yanan yuvalar + tasinan mesale/Mor Alev + mangal (yaniyorsa).

## Mesale tek nesne, uc hal

`self.torch` (`Torch | None`): `held` (oyuncuyu takip eder, 2'li combo
kisitlar - `ChainState.max_index`), `thrown`/`landed` (yerde yanar,
tekrar alinabilir), ya da bir yuvaya socketed olup kaybolur (alev artik
o yuva). Mor Alev alinca `self.torch` tamamen devre disi kalir - Mor Alev
kisitlamasiz, sonmez (docs: "iki elin serbest" degil ama "iki elin dolu"
kurali da yok, cunku dogaustu bir alev, sıradan bir esya degil - bu
varsayimi plan dosyasinda acikca isaretledim).
"""
from __future__ import annotations

import math

import pygame

from src.art import lighting, palette
from src.combat.hitbox import Hitbox, Team, melee_rect
from src.config import (
    CANDLE_KEEPER_PRICE_DEATH_CANDLE, CANDLE_KEEPER_PRICE_ETERNAL_WICK,
    CANDLE_KEEPER_PRICE_TORCH, CHAPTER3_BOSS_GOLD, CHAPTER3_CHEST_GOLD_ROOM2,
    CHAPTER3_CHEST_GOLD_SECRET, DARK_WAVE_BLACKOUT_FRAMES, INTERNAL_WIDTH,
    PURPLE_FLAME_LIGHT_RADIUS, TILE_SIZE, TORCH_LIGHT_RADIUS,
)
from src.core.input import Action
from src.core.juice import ImpactWeight
from src.entities.candle_keeper import CandleKeeper
from src.entities.enemies.extinguished_one import Brazier, ExtinguishedOne
from src.scenes.play import PlayScene
from src.systems import abilities, charms, economy
from src.systems.economy import TradeOffer
from src.systems.light import LightState
from src.ui import text as text_ui
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.dialogue import Line
from src.ui.i18n import t
from src.ui.widgets import panel
from src.world import cave_backdrop
from src.world.keydoor import BossKey, LockedDoor
from src.world.pickups import Chest
from src.world.rooms.chapter03 import (
    ARENA_DOOR_COLUMN, ARENA_EXIT_COLUMN, ARENA_EXIT_ROWS,
    BRAZIER_TILE, LEVEL, PURPLE_FLAME_TILE,
    ROOM3_SOCKET_INDICES, ROOM_STARTS, SECRET_POCKET_ABS_COLUMNS,
    SECRET_WALL_MIN_COLUMN, TORCHES, WIND_ZONES,
)
from src.world.tilemap import TileMap
from src.world.torch import HELD, LANDED, SOCKETED, THROWN, Torch

ENEMY_CLASSES: dict[str, str] = {
    "shambler": "src.entities.enemies.shambler:Shambler",
    "climber": "src.entities.enemies.climber:Climber",
    "shadow_shambler": "src.entities.enemies.shadow_shambler:ShadowShambler",
}

# Firlatilan mesale bir yuvaya bu kadar yakin duserse onu yakar.
SOCKET_CATCH_RANGE = TILE_SIZE * 1.4

# Mum Bekcisi'nin uc sabit teklifi (docs/bolum-03.md Oda 3-A).
TRADE_OFFERS = (
    TradeOffer("candle_keeper_torch", CANDLE_KEEPER_PRICE_TORCH, "trade.torch"),
    TradeOffer("eternal_wick", CANDLE_KEEPER_PRICE_ETERNAL_WICK, "trade.wick"),
    TradeOffer("death_candle", CANDLE_KEEPER_PRICE_DEATH_CANDLE, "trade.candle"),
)


def _load(path: str):
    module_name, class_name = path.split(":")
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)


class Chapter03Scene(PlayScene):
    """Mesale Mahzeni: 7 oda, gizli Mum Bekcisi cebi, mini-boss."""

    # Bolum basi karti (src/ui/chapter_card.py) - oynanisi durdurmaz.
    chapter_number = 3
    chapter_name_key = "chapter.torch_crypt"
    postfx_grade = "crypt"   # src/art/postfx.py
    ambience_preset = "ember"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)

        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        # Bolum 2'den geliyoruz: kilic ve kacinma elde.
        self.player.grant(abilities.SWORD)
        self.player.grant(abilities.DODGE)
        # `amb_torch` donguluk sesi kaldirildi - bkz. chapter01.py ayni
        # tarihli not (Arda: sentezlenmis surekli sesler rahatsiz edici).

        self.light = LightState()
        self.sconces = [list(entry) for entry in TORCHES]      # kendi kopyasi
        self.brazier = Brazier(BRAZIER_TILE[0] * TILE_SIZE + TILE_SIZE // 2,
                               (BRAZIER_TILE[1] + 1) * TILE_SIZE)

        # Bolum 2'den kalan mesale elimizde basliyor (Ara Sahne 1: "elinde
        # B2'den kalan mesale").
        self.torch: Torch | None = Torch(self.player.body.center_x,
                                          self.player.body.feet[1])
        self.has_purple_flame = False
        self.blackout_frames = 0        # Karanlik Dalgasi (Oda 7)

        self.chests = [
            Chest(spot.x, spot.feet_y,
                  gold=(CHAPTER3_CHEST_GOLD_SECRET if self._is_secret(spot.tile_x)
                        else CHAPTER3_CHEST_GOLD_ROOM2),
                  secret=self._is_secret(spot.tile_x))
            for spot in LEVEL.of("chest")
        ]

        keeper_spot = LEVEL.first("candle_keeper")
        self.candle_keeper = (CandleKeeper(keeper_spot.x, keeper_spot.feet_y)
                              if keeper_spot is not None else None)
        self.trading = False
        self.trade_index = 0
        self._keeper_seen = False

        self.room = ""
        self.entered_rooms: set[str] = set()
        self.room_frames = 0
        self.puzzle_solved = False

        self.boss = None
        self.arena_sealed = False
        self.boss_defeated = False
        # Bolum 2 ile ayni kacak buradaydi da: giris muhurlense de arka
        # taraf acikti. Kilitli cikis + boss'un dusurdugu anahtar.
        self.exit_door = LockedDoor(ARENA_EXIT_COLUMN, ARENA_EXIT_ROWS)
        self.exit_door.close(self.tilemap)
        self.boss_key: BossKey | None = None
        self.has_key = False
        self._door_hinted = False
        self.secret_found = False

        self.earned_gold = 0
        self.frames = 0
        self.finished = False

        self._enter_room(self._room_at(self.player.body.center_x))

    def _is_secret(self, tile_x: int) -> bool:
        lo, hi = SECRET_POCKET_ABS_COLUMNS
        return lo <= tile_x < hi

    # --- Odalar ---------------------------------------------------------------
    def _room_at(self, x: float) -> str:
        tile = int(x) // TILE_SIZE
        name = ROOM_STARTS[0][0]
        for room_name, start in ROOM_STARTS:
            if tile >= start:
                name = room_name
        return name

    def _room_span(self, name: str) -> tuple[int, int]:
        for index, (room_name, start) in enumerate(ROOM_STARTS):
            if room_name != name:
                continue
            end = (ROOM_STARTS[index + 1][1] if index + 1 < len(ROOM_STARTS)
                   else self.tilemap.width)
            return start, end
        return 0, self.tilemap.width

    def _enter_room(self, name: str) -> None:
        self.room = name
        self.room_frames = 0
        if name in self.entered_rooms:
            return
        self.entered_rooms.add(name)
        self._spawn_room(name)
        self._narrate_room(name)

    def _spawn_room(self, name: str) -> None:
        start, end = self._room_span(name)
        for kind, path in ENEMY_CLASSES.items():
            for spot in LEVEL.of(kind):
                if not (start <= spot.tile_x < end):
                    continue
                enemy = _load(path)(self, spot.x, spot.feet_y)
                self.enemies.append(enemy)

        for spot in LEVEL.of("miniboss"):
            if start <= spot.tile_x < end:
                self.boss = ExtinguishedOne(self, spot.x, spot.feet_y)
                self.enemies.append(self.boss)

    def _narrate_room(self, name: str) -> None:
        # Kapi **burada** kapatilmiyor - `_update_arena()` oyuncu gercekten
        # kapi sutununu gecince kapatiyor (Bolum 2'de yasanan ayni hata:
        # oda sinirina girer girmez kapatilinca kapi neredeyse oyuncunun
        # yuzune kapaniyordu - bkz. ARENA_DOOR_COLUMN).
        # Yanki replikleri `has_echo` ardinda (Yanki Rey'in laneti,
        # docs/gdd.md 4). Ardo ayni anlari kendi gozlemiyle karsiliyor -
        # Bolum 1 ve 2'de kurulan ayni desen.
        if name == "isigin_kurali":
            self._voice("line.ch03_echo_enter", "line.ch03_ardo_enter")
        elif name == "sonmus_olan":
            self._voice("line.ch03_echo_boss", "line.ch03_ardo_boss")
        elif name == "mor_alev":
            from src.scenes.chapter03_cinematics import PurpleCinematic
            self.scenes.push(PurpleCinematic)

    def _voice(self, echo_key: str, ardo_key: str) -> None:
        """Yanki konusur, Yanki yoksa oynanan karakter konusur.

        Bolum 3 bastan sona SESSIZDI - Mum Bekcisi, Mor Alev karari ve
        mini-boss dahil hicbir anda replik yoktu. Arda'nin "hikaye
        sunumlarini gelistir" istegi icin en buyuk bosluk burasiydi.
        """
        if self.has_echo:
            self.say(Line("echo", echo_key))
        else:
            self.say(Line(self.character, ardo_key))

    # --- Dongu ------------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.room_frames += 1

        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        if self.trading:
            self._update_trade()
        self._update_torch_input()
        self._update_torch_physics()
        self._update_combo_restriction()
        self._update_light()
        self._update_chests()
        self._update_candle_keeper()
        self._update_puzzle()
        self._update_purple_flame()
        self._update_brazier_input()
        self._update_arena()
        self._update_key()
        self._update_blackout()
        self._check_exit()

    def _update_combo_restriction(self) -> None:
        """Mesale elde iken tek elle dovus: 2'li zincir, bitirici yok.

        Mor Alev muaf (dogaustu, sonmez - sıradan elde tutulan bir esya
        degil; bu tasarim kararini onay icin plan dosyasinda isaretledim).
        """
        carrying = (not self.has_purple_flame and self.torch is not None
                   and self.torch.state == HELD)
        self.player.chain.max_index = 1 if carrying else None

    # --- Isik --------------------------------------------------------------------
    def _update_light(self) -> None:
        self.light = LightState()
        if self.blackout_frames > 0:
            return                       # Karanlik Dalgasi: hicbir isik yok
        for entry in self.sconces:
            tile_x, tile_y, lit = entry
            if lit:
                x = tile_x * TILE_SIZE + TILE_SIZE // 2
                y = (tile_y + 1) * TILE_SIZE
                self.light.set_static(f"sconce{id(entry)}", x, y, TORCH_LIGHT_RADIUS)
        if self.brazier.lit:
            self.light.set_static("brazier", self.brazier.x, self.brazier.y,
                                  self.brazier.radius)
        if self.has_purple_flame:
            scale = charms.light_scale(self.player.charms, self.player)
            self.light.set_carried(self.player.body.center_x,
                                   self.player.body.feet[1],
                                   PURPLE_FLAME_LIGHT_RADIUS * scale)
        elif self.torch is not None and self.torch.state in (HELD, THROWN):
            radius = TORCH_LIGHT_RADIUS
            if self.torch.state == HELD and self._in_wind_zone(self.torch.x):
                radius = 0.0             # Ruzgar sonduruyor (Oda 6)
            if radius > 0.0:
                scale = charms.light_scale(self.player.charms, self.player)
                self.light.set_carried(self.torch.x, self.torch.y, radius * scale)
        elif self.torch is not None and self.torch.state == LANDED:
            self.light.set_static("dropped_torch", self.torch.x, self.torch.y,
                                  TORCH_LIGHT_RADIUS)

    def _in_wind_zone(self, x: float) -> bool:
        tile_x = int(x) // TILE_SIZE
        return any(lo <= tile_x < hi for lo, hi in WIND_ZONES)

    # --- Mesale --------------------------------------------------------------------
    def _update_torch_input(self) -> None:
        if self.has_purple_flame or self.trading:
            return
        if not self.game.input.pressed(Action.INTERACT):
            return

        if self.torch is not None and self.torch.state == HELD:
            # Yakinda sonuk bir yuva varsa oraya kon (iki el serbest kalir);
            # yoksa firlat.
            socket = self._nearest_dark_socket()
            if socket is not None:
                self._socket_torch(socket)
            else:
                self.torch.throw(self.player.facing)
        elif self.torch is None:
            # Elde mesale yok - yakindaki yanan bir yuvadan yeniden yak.
            socket = self._nearest_lit_socket()
            if socket is not None:
                self.torch = Torch(self.player.body.center_x,
                                   self.player.body.feet[1])
                self.game.play_sound("torch_light")

    def _nearest_dark_socket(self, range_px: float = TILE_SIZE * 2.5):
        best, best_d = None, range_px
        for entry in self.sconces:
            if entry[2]:
                continue
            x = entry[0] * TILE_SIZE + TILE_SIZE // 2
            d = abs(x - self.player.body.center_x)
            if d < best_d:
                best, best_d = entry, d
        return best

    def _nearest_lit_socket(self, range_px: float = TILE_SIZE * 2.5):
        best, best_d = None, range_px
        for entry in self.sconces:
            if not entry[2]:
                continue
            x = entry[0] * TILE_SIZE + TILE_SIZE // 2
            d = abs(x - self.player.body.center_x)
            if d < best_d:
                best, best_d = entry, d
        return best

    def _socket_torch(self, entry: list) -> None:
        entry[2] = True
        self.torch = None
        self.game.play_sound("torch_light")

    def _update_torch_physics(self) -> None:
        if self.torch is None:
            return
        if self.torch.state == HELD:
            self.torch.follow(self.player.body.center_x, self.player.body.feet[1] - 2)
        self.torch.update(self.tilemap)

        if self.torch.state == LANDED:
            # Ustune basarak geri alinabilir.
            if abs(self.torch.x - self.player.body.center_x) < 8 \
                    and abs(self.torch.y - self.player.body.feet[1]) < 10:
                self.torch.state = HELD
                return
            # Bir yuvaya yeterince yakin dustuyse onu yakar ve kendisi kaybolur.
            for entry in self.sconces:
                if entry[2]:
                    continue
                x = entry[0] * TILE_SIZE + TILE_SIZE // 2
                y = (entry[1] + 1) * TILE_SIZE
                if abs(self.torch.x - x) < SOCKET_CATCH_RANGE \
                        and abs(self.torch.y - y) < SOCKET_CATCH_RANGE:
                    entry[2] = True
                    self.torch = None
                    return

    # --- Bulmaca (Oda 3) -----------------------------------------------------------
    def _update_puzzle(self) -> None:
        if self.puzzle_solved:
            return
        if all(self.sconces[i][2] for i in ROOM3_SOCKET_INDICES
               if i < len(self.sconces)):
            self.puzzle_solved = True
            self.show_toast(t("chapter03.puzzle_solved"), frames=180)
            self.particles.burst(self.player.body.center_x,
                                 self.player.body.center_y, 16,
                                 path="spark", speed=(0.6, 2.0))

    # --- Mor Alev (Oda 5) --------------------------------------------------------------
    def _update_purple_flame(self) -> None:
        """Alinabilir ya da birakilabilir - oyun bunu hic soylemez (docs).

        Karar `has_purple_flame`'e yaziliyor; bolum sonu ekraninda
        gorunecek tek yer burasi (docs: "alindi/birakildi" satiri).
        """
        if self.has_purple_flame or self.room != "mor_alev":
            return
        px = PURPLE_FLAME_TILE[0] * TILE_SIZE + TILE_SIZE // 2
        py = (PURPLE_FLAME_TILE[1] + 1) * TILE_SIZE
        near = abs(px - self.player.body.center_x) < 16
        if not near or not self.game.input.pressed(Action.INTERACT):
            return
        self.has_purple_flame = True
        self.torch = None
        if self.echo is not None:
            self.echo.restore()          # Bir kademe yukselir ve orada kalir
        self.juice.explosion(px, py, ImpactWeight.NORMAL)
        self.particles.burst(px, py, 14, path="echo", speed=(0.4, 1.6))
        self.show_toast(t("chapter03.purple_taken"), frames=200)
        # Alev Yanki'nin kademesini YUKSELTIYOR (yukarida `restore()`).
        # Yani ses bu isten KAZANCLI cikiyor - ve bunu soyluyor.
        # docs/yapi.md B14: "Yanki lanet degil, asagidaki seyin sesi. Hep
        # yardim ediyordu cunku onu cekiyordu." Bu replik o donusun
        # tohumu: oyuncu simdi anlamiyor, B14'te hatirliyor.
        self._voice("line.ch03_echo_purple", "line.ch03_ardo_purple")

    # --- Sandiklar -------------------------------------------------------------------
    def _update_chests(self) -> None:
        for chest in self.chests:
            chest.update()
            if chest.opened or not chest.rect.colliderect(self.player.hurtbox):
                continue
            self._open_chest(chest)

    def _open_chest(self, chest: Chest) -> None:
        if not chest.open():
            return
        self.earned_gold += chest.gold
        if self.save_data is not None:
            self.save_data.gold += chest.gold
        self.particles.burst(chest.x, chest.feet_y - 8, 14, path="spark",
                             speed=(0.5, 2.0), life=(18, 34))
        self.juice.explosion(chest.x, chest.feet_y - 6, ImpactWeight.NORMAL)
        self.game.play_sound("chest_open")
        if chest.secret and not self.secret_found:
            self.secret_found = True
            self.show_toast(t("chapter03.secret_found"), frames=200)
        else:
            self.show_toast(t("chapter03.gold_found", count=chest.gold))

    # --- Mum Bekcisi -----------------------------------------------------------------
    def _update_candle_keeper(self) -> None:
        if self.candle_keeper is None:
            return
        self.candle_keeper.update()
        if self.has_purple_flame:
            return                       # "Mor alev tasiyani tanimiyor"
        near = (abs(self.candle_keeper.x - self.player.body.center_x) < 20
                and abs(self.candle_keeper.feet_y - self.player.body.feet[1]) < 24)
        # Bekci'nin KENDISI konusmuyor (candle_keeper.py: "konusmayan,
        # savasmayan"). Tepki oyuncunun - dusmanca bir dunyada dusman
        # olmayan bir varlikla karsilasmak bir an olmali.
        if near and not self._keeper_seen:
            self._keeper_seen = True
            self._voice("line.ch03_echo_keeper", "line.ch03_ardo_keeper")
        if near and not self.trading and self.game.input.pressed(Action.INTERACT):
            self.trading = True
            self.trade_index = 0

    @property
    def modal_active(self) -> bool:
        """Ticaret ekrani aciksa ESC once ONU kapatiyor - duraklatmayi
        degil. Gerekce `PlayScene.handle_event`'te."""
        return self.trading

    def _update_trade(self) -> None:
        inp = self.game.input
        if inp.pressed(Action.UP):
            self.trade_index = (self.trade_index - 1) % len(TRADE_OFFERS)
        elif inp.pressed(Action.DOWN):
            self.trade_index = (self.trade_index + 1) % len(TRADE_OFFERS)
        elif inp.pressed(Action.CANCEL) or inp.pressed(Action.PAUSE):
            self.trading = False
        elif inp.pressed(Action.CONFIRM):
            self._buy(TRADE_OFFERS[self.trade_index])

    def _buy(self, offer: TradeOffer) -> None:
        if economy.already_bought(self.save_data, offer):
            self.show_toast(t("chapter03.already_bought"))
            return
        if not economy.spend(self.save_data, offer.cost):
            self.show_toast(t("chapter03.not_enough_gold"))
            return
        economy.mark_bought(self.save_data, offer)
        if offer.key == "candle_keeper_torch" and self.torch is None:
            self.torch = Torch(self.player.body.center_x, self.player.body.feet[1])
        self.show_toast(t(offer.label_key), frames=160)
        self.game.play_sound("chest_open")
        self.trading = False

    # --- Arena / mangal ---------------------------------------------------------------
    def _update_arena(self) -> None:
        self.brazier.update()
        if (self.room == "sonmus_olan" and not self.arena_sealed
                and not self.boss_defeated and self.boss is not None):
            # `body.x` (SOL kenar), `center_x` DEGIL - bkz. chapter02.py
            # ayni kontrol: merkez esigi gecince govdenin sol yarisi hala
            # esigi kapliyor olabiliyordu, o an muhurlenirse oyuncu yeni
            # kati tile'in icinde kalip cikamiyordu.
            if self.player.body.x > (ARENA_DOOR_COLUMN + 1) * TILE_SIZE:
                self._seal_arena()
            return
        if not self.arena_sealed or self.boss_defeated:
            return
        if self.boss is not None and not self.boss.dead:
            return
        self._open_arena()

    def _seal_arena(self) -> None:
        if self.arena_sealed:
            return
        self.arena_sealed = True

    def _open_arena(self) -> None:
        self.boss_defeated = True
        self.arena_sealed = False
        self.earned_gold += CHAPTER3_BOSS_GOLD
        if self.save_data is not None:
            self.save_data.gold += CHAPTER3_BOSS_GOLD
        if self.player.equip(charms.FENER):
            if (self.save_data is not None
                    and charms.FENER not in self.save_data.charms):
                self.save_data.charms.append(charms.FENER)
        self.show_toast(t("chapter03.boss_gold", count=CHAPTER3_BOSS_GOLD), frames=200)
        self._drop_key()

    def _drop_key(self) -> None:
        """Sonmus Olan oldu - cikis anahtari duser (src/world/keydoor.py)."""
        if self.boss_key is not None:
            return
        if self.boss is not None:
            x, y = self.boss.body.center_x, self.boss.body.bottom
        else:
            x = (ARENA_EXIT_COLUMN - 3) * TILE_SIZE
            y = self.player.body.bottom
        self.boss_key = BossKey(x, y)

    def _update_key(self) -> None:
        self.exit_door.update()
        # Kilitli kapiya dayanan oyuncuya sebebini bir kez soyle - yoksa
        # onu siradan bir duvar sanip geri doner.
        if (self.exit_door.bumped_by(self.player) and not self._door_hinted):
            self._door_hinted = True
            self.show_toast(t("chapter02.door_locked"), frames=150)
        if self.boss_key is None or self.has_key:
            return
        self.boss_key.update()
        if self.boss_key.try_take(self.player):
            self.has_key = True
            self.exit_door.unlock(self.tilemap)
            self.pickup_juice()
            self.show_toast(t("chapter02.key_taken"), frames=180)

    def _update_blackout(self) -> None:
        if self.blackout_frames > 0:
            self.blackout_frames -= 1

    def _update_brazier_input(self) -> None:
        if self.brazier.lit or self.room != "sonmus_olan":
            return
        has_fire = self.has_purple_flame or (
            self.torch is not None and self.torch.state == HELD)
        if not has_fire:
            return
        near = (abs(self.brazier.x - self.player.body.center_x) < 18
                and abs(self.brazier.y - self.player.body.feet[1]) < 20)
        if near and self.game.input.pressed(Action.INTERACT):
            self.light_brazier()

    def light_brazier(self) -> None:
        """Oyuncu mangali yakti - boss sersemler, Karanlik Dalgasi iptal."""
        if not self.brazier.light():
            return
        if self.boss is not None and hasattr(self.boss, "on_brazier_lit"):
            self.boss.on_brazier_lit()
        self.particles.burst(self.brazier.x, self.brazier.y, 12, path="spark",
                             speed=(0.6, 2.2))

    # --- Boss kancalari ----------------------------------------------------------------
    def on_boss_move(self, boss, move: str) -> None:
        if move == "dark_wave":
            self.blackout_frames = DARK_WAVE_BLACKOUT_FRAMES
            self.camera.linger(6)
        elif move == "snuff":
            self.show_toast(t("chapter03.brazier_snuffed"))

    # --- Cikis -------------------------------------------------------------------------
    def _check_exit(self) -> None:
        exit_at = LEVEL.first("exit")
        if self.finished or exit_at is None:
            return
        if self.player.body.center_x < exit_at.x - 8:
            return
        self.finished = True
        self._end_chapter()

    def _end_chapter(self) -> None:
        self.game.play_sound("chapter_end")
        if self.save_data is not None:
            self.save_data.purple_flame_taken = self.has_purple_flame
        result = ChapterResult(
            chapter_key="chapter.torch_crypt",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=1,
            purple_flame_taken=self.has_purple_flame,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 3
            data.chapter_name = "chapter.torch_crypt"
            data.playtime_frames += self.frames
            data.best_combo = max(data.best_combo, self.player.combo.best)
            data.secrets_found += result.secrets_found
            data.secrets_total += 1
            if "chapter.torch_crypt" not in data.chapters_cleared:
                data.chapters_cleared.append("chapter.torch_crypt")
        # Bolum 4 artik var - ozet ekrani kapaninca dogrudan ona geciliyor.
        # (Onceden `on_continue` verilmiyordu ve ana menuye donuluyordu;
        # Bolum 2'nin B3'e baglanmasiyla ayni desen.)
        character = self.character

        def _continue() -> None:
            from src.scenes.chapter04 import Chapter04Scene
            self.scenes.set_root(Chapter04Scene, character=character)

        self.scenes.push(ChapterEndScene, result=result, on_continue=_continue)

    # --- Yanki: sonar --------------------------------------------------------------------
    def update(self) -> None:
        if self.echo is not None and not self.trading:
            if self.game.input.pressed(Action.ECHO) and self.echo.pulse():
                self._on_sonar_pulse()
        super().update()

    def _on_sonar_pulse(self) -> None:
        px = self.player.body.center_x
        py = self.player.body.center_y
        for enemy in self.enemies:
            if math.hypot(enemy.body.center_x - px,
                         enemy.body.center_y - py) <= 200.0:
                enemy.aware = True

    def on_wall_broken(self, rects: list[pygame.Rect]) -> None:
        for rect in rects:
            if rect.x // TILE_SIZE >= SECRET_WALL_MIN_COLUMN:
                self.show_toast(t("chapter03.pocket_open"), frames=140)
                return
        super().on_wall_broken(rects)

    def on_player_died(self, player) -> None:
        if self.arena_sealed:
            self._open_arena()
        super().on_player_died(player)

    # --- Cizim --------------------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        lit_sconces = [tuple(entry) for entry in self.sconces]
        cave_backdrop.draw_torches(surface, offset, lit_sconces, self.game.frame)
        self.brazier.draw(surface, offset, self.game.frame)
        self.exit_door.draw(surface, offset, self.game.frame)
        if self.boss_key is not None:
            self.boss_key.draw(surface, offset)
        if self.candle_keeper is not None:
            self.candle_keeper.draw(surface, offset)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)
        if self.torch is not None and self.torch.state != SOCKETED:
            self.torch.draw(surface, offset)
        if not self.has_purple_flame:
            self._draw_purple_pedestal(surface, offset)
        if self.blackout_frames > 0:
            # Karanlik Dalgasi: hicbir isik kaynagi yok demek "normal
            # aydinlik oda" degil, **tam karanlik** demek - `lighting.render`
            # kaynak yoksa hicbir sey cizmiyor (Bolum 1/2'nin maliyeti
            # odememesi icin), o yuzden burada ayrica tam karartma cizilir.
            blackout = pygame.Surface(surface.get_size())
            blackout.fill(palette.color(palette.darkest_names(1)[0]))
            surface.blit(blackout, (0, 0))
        else:
            lighting.render(surface, offset, self.light)

    def _draw_purple_pedestal(self, surface: pygame.Surface, offset) -> None:
        if self.room != "mor_alev":
            return
        ox, oy = offset
        px = PURPLE_FLAME_TILE[0] * TILE_SIZE + TILE_SIZE // 2 - ox
        py = (PURPLE_FLAME_TILE[1] + 1) * TILE_SIZE - oy
        surface.fill(palette.color("stone_dark"), (px - 6, py - 4, 12, 5))
        surface.fill(palette.color("stone"), (px - 6, py - 4, 12, 1))
        flicker = (self.game.frame // 8) % 3
        surface.fill(palette.color("violet"), (px - 2, py - 12 + flicker, 4, 8 - flicker))
        surface.fill(palette.color("violet_bright"), (px - 1, py - 8, 2, 4))
        from src.art.glow import radial_glow
        glow = radial_glow(28, palette.color("violet"),
                           peak=0.4 + 0.05 * math.sin(self.game.frame * 0.05))
        surface.blit(glow, (px - 28, py - 28), special_flags=pygame.BLEND_RGB_ADD)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        if self.boss is not None and not self.boss.dead and self.arena_sealed:
            self.boss.draw_health_bar(surface)
        if self.trading:
            self._draw_trade(surface)

    def _draw_trade(self, surface: pygame.Surface) -> None:
        # Yukseklik bir satir fazla: en altta **cikis ipucu** var.
        # Olmadigi surumde oyuncu ekranin nasil kapandigini bilmiyordu -
        # ve ESC de calismadigi icin gercekten sikismis oluyordu.
        width, height = 180, 34 + len(TRADE_OFFERS) * 14
        rect = pygame.Rect(INTERNAL_WIDTH // 2 - width // 2, 60, width, height)
        panel(surface, rect)
        text_ui.draw(surface, t("chapter03.trade_title"), rect.centerx, rect.y + 6,
                    color=palette.color("violet_bright"), align="center")
        for i, offer in enumerate(TRADE_OFFERS):
            y = rect.y + 20 + i * 14
            bought = economy.already_bought(self.save_data, offer)
            colour = (palette.role("ui_text_dim") if i != self.trade_index
                     else palette.color("violet_bright"))
            if bought:
                colour = palette.role("ui_text_dim")
            label = t(offer.label_key)
            value = t("chapter03.trade_owned") if bought else str(offer.cost)
            if i == self.trade_index and not bought:
                text_ui.draw(surface, "▸", rect.x + 4, y,
                             color=palette.color("violet_bright"))
            text_ui.draw(surface, label, rect.x + 10, y, color=colour)
            text_ui.draw(surface, value, rect.right - 10, y, color=colour, align="right")
        text_ui.draw(surface, t("chapter03.trade_exit"), rect.centerx,
                     rect.bottom - 11, color=palette.role("ui_text_dim"),
                     align="center")

    def debug_lines(self) -> list[str]:
        torch_state = self.torch.state if self.torch else "yok"
        return super().debug_lines() + [
            f"oda {self.room} ({self.room_frames})  mesale {torch_state}  "
            f"mor alev {self.has_purple_flame}  arena {self.arena_sealed}"]
