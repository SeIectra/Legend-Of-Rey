"""Bolum 2 - "Ilk Inis". Oynanabilir sahne.

Oda geometrisi `src/world/rooms/chapter02.py` icinde; burasi onu oynatiyor.
`docs/bolum-02.md`: *"Oyunun normal dokusunu tam kalitede kanitlamak. Bu
bolum iyiyse oyun iyidir."*

## Dusmanlar odaya girilince doguyor

Hepsi bastan dogsaydi on dort dusman ayni anda dusunurdu ve - daha kotusu -
Oda 6'daki Suruklenenler oyuncu Oda 2'deyken duvara dogru yurumeye
baslardi. Odaya girince dogmalari hem kare butcesi hem **kompozisyon**
meselesi: bir odanin dovusu o odada basliyor.

## Yanki odasi bolumun kalbi

Belge onu "ogretim zirvesi" diye anlatiyor: oyuncu takilir, ses
**kendiliginden** yukselir, catlak parlar, ayni uc saniyede ekran kararir.
Kazanc ve bedelin ayni anda hissedilmesi sart - ayri anlara dagilirsa
oyuncu ikisi arasinda bag kurmaz.

## Ikinci catlak sinav

Oda 4'un catlagi ogretiyor: kirmadan ilerlenemez. Gizli odanin catlagi
sinav - hicbir ipucu yok, ana yol alt koridordan duz gecip gidiyor.
Bolum sonu ekranindaki "0/1 gizli alan" ancak boyle anlamli oluyor.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_WIDTH, TILE_SIZE
from src.core.juice import ImpactWeight
from src.scenes.play import PlayScene
from src.systems import abilities, charms
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.dialogue import Line
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.rooms.chapter02 import (
    ARENA_DOOR_COLUMN, ARENA_DOOR_ROWS, BOSS_GOLD, CHEST_GOLD_MAIN,
    CHEST_GOLD_SECRET, CLAW_LINGER_FRAMES, CLAW_MARKS, ECHO_RISE_DELAY,
    ECHO_RISE_FRAMES, LEVEL, ROOM_STARTS, SECRETS_TOTAL,
    SECRET_CHAMBER_FLOOR_ROW, SECRET_WALL_MIN_COLUMN, TORCHES,
)
from src.world.tilemap import EMPTY, SOLID, TileMap

# Tirmik izi bu kadar piksel yakinda fark edilir.
CLAW_NOTICE_RANGE = 30
# Gizli odada sessizlik bu hizda giriyor/cikiyor (kare basina oran).
HUSH_RISE = 0.04
HUSH_FALL = 0.06

# Dusman siniflari gec yukleniyor: sahne modulu import edilirken dort
# dusman modulunu de cekmek gereksiz, hepsi sahne kurulurken lazim oluyor.
ENEMY_CLASSES: dict[str, str] = {
    "shambler": "src.entities.enemies.shambler:Shambler",
    "climber": "src.entities.enemies.climber:Climber",
    "bloated": "src.entities.enemies.bloated:Bloated",
    "miniboss": "src.entities.enemies.bloated_one:BloatedOne",
}


def _load(path: str):
    module_name, class_name = path.split(":")
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)


class Chapter02Scene(PlayScene):
    """Ilk Inis: sekiz oda, bir gizli oda, bir mini-boss."""

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)

        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        # Bolum 1'den sonra geliyoruz: kilic ve kacinma elde. Bolum tek
        # basina da oynanabilmeli (test, bolum secimi), o yuzden burada
        # acikca veriliyor - kayittan gelmesini beklemiyoruz.
        self.player.grant(abilities.SWORD)
        self.player.grant(abilities.DODGE)
        self.game.play_loop("amb", "amb_cellar", volume=0.7)

        self.chests = [
            Chest(spot.x, spot.feet_y,
                  gold=(CHEST_GOLD_SECRET if self._is_secret(spot.tile_x)
                        else CHEST_GOLD_MAIN),
                  charm=(charms.BLOODY_WHET if self._is_secret(spot.tile_x)
                         else ""),
                  secret=self._is_secret(spot.tile_x))
            for spot in LEVEL.of("chest")
        ]

        self.room = ""
        self.entered_rooms: set[str] = set()
        self.room_frames = 0
        self.seen_claw: set[int] = set()

        # Yanki odasi durumu
        self.echo_forced = 0
        self.crack_revealed = False      # Ardo'nun izi surdugu an

        # Gizli oda
        self.secret_found = False
        self.hush = 0.0                  # 0..1 sessizlik orani

        # Arena
        self.arena_sealed = False
        self.boss = None
        self.boss_defeated = False

        self.earned_gold = 0
        self.frames = 0
        self.finished = False

        self._enter_room(self._room_at(self.player.body.center_x))

    def on_exit(self) -> None:
        self.game.stop_loop("amb")

    def _is_secret(self, tile_x: int) -> bool:
        """Gizli oda sutun araligi. Ana yoldaki sandiktan boyle ayriliyor."""
        return SECRET_WALL_MIN_COLUMN <= tile_x < ARENA_DOOR_COLUMN

    # --- Odalar -------------------------------------------------------------
    def _room_at(self, x: float) -> str:
        tile = int(x) // TILE_SIZE
        name = ROOM_STARTS[0][0]
        for room_name, start in ROOM_STARTS:
            if tile >= start:
                name = room_name
        return name

    def _room_span(self, name: str) -> tuple[int, int]:
        """Odanin tile araligi [baslangic, bitis)."""
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
        """Odanin dusmanlarini dogurur. Her oda **bir kez**."""
        start, end = self._room_span(name)
        for kind, path in ENEMY_CLASSES.items():
            for spot in LEVEL.of(kind):
                if not (start <= spot.tile_x < end):
                    continue
                enemy = _load(path)(self, spot.x, spot.feet_y)
                self.enemies.append(enemy)
                if kind == "miniboss":
                    self.boss = enemy

    def _narrate_room(self, name: str) -> None:
        """Odaya ilk girisin repligi. Cogu oda **sessiz** - jest yeter.

        Kapi **burada** kapatilmiyor - `_update_arena()` oyuncu gercekten
        kapi sutununu gecince kapatiyor (Arda'nin bildirdigi hata: oda
        sinirina girer girmez kapatilinca, sinir kapi sutununa cok yakin
        oldugu icin kapi neredeyse oyuncunun yuzune kapaniyordu).
        """
        if name == "miniboss":
            self.say(Line("echo", "line.ch02_echo_boss"))
        elif name == "cikis":
            self.say(Line("rey", "line.ch02_rey_claw2"),
                     Line("echo", "line.ch02_echo_exit"))

    # --- Dongu --------------------------------------------------------------
    def echo_held(self) -> bool:
        # Yanki odasinda ses **kendiliginden** yukselir; oyuncu tusa
        # basmadan da acilir. Kanca `PlayScene`'de: bedel muhasebesi tek
        # yerde kaliyor.
        return super().echo_held() or self.echo_forced > 0

    def update_scene(self) -> None:
        self.frames += 1
        self.room_frames += 1

        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        self._update_echo_room()
        self._update_claw_marks()
        self._update_chests()
        self._update_hush()
        self._update_arena()
        self._check_exit()

    def _update_echo_room(self) -> None:
        """Belgenin "ogretim zirvesi" ani.

        Oyuncu takilir; birkac saniye sonra ses kendiliginden yukselir ve
        catlak parlar. Ayni anda ekran kararir - kazanc ve bedel tek
        saniyede.
        """
        if self.echo_forced > 0:
            self.echo_forced -= 1
            return
        if self.room != "yanki_odasi" or self.crack_revealed:
            return
        if self.room_frames < ECHO_RISE_DELAY:
            return

        self.crack_revealed = True
        if self.echo is not None:
            self.player.grant(abilities.ECHO_SIGHT)
            self.echo_forced = ECHO_RISE_FRAMES
            self.say(Line("echo", "line.ch02_echo_wall"))
        else:
            # Ardo'nun Yanki'si yok. Ayni bilgiyi iz surerek buluyor:
            # catlak kalici olarak gorunur hale geliyor. Yoksa bu oda
            # Ardo icin gecilemez bir cikmaz olurdu.
            self.show_toast(t("chapter02.ardo_tracks"), frames=150)
        self.juice.explosion(self.player.body.center_x,
                             self.player.body.center_y, ImpactWeight.NORMAL)

    def _update_claw_marks(self) -> None:
        """Tirmik izinin yaninda kamera oyalanir - oyuncu fark etsin."""
        for index, (tile_x, tile_y) in enumerate(CLAW_MARKS):
            if index in self.seen_claw:
                continue
            mark_x = tile_x * TILE_SIZE + TILE_SIZE // 2
            if abs(self.player.body.center_x - mark_x) > CLAW_NOTICE_RANGE:
                continue
            self.seen_claw.add(index)
            self.camera.linger(CLAW_LINGER_FRAMES)
            self.particles.burst(mark_x, tile_y * TILE_SIZE + TILE_SIZE, 5,
                                 path="dust", speed=(0.1, 0.5), life=(20, 40),
                                 gravity=0.02)

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

        if chest.charm and self.player.equip(chest.charm):
            if (self.save_data is not None
                    and chest.charm not in self.save_data.charms):
                self.save_data.charms.append(chest.charm)
            self.show_toast(t(charms.label_key(chest.charm)), frames=200)
        else:
            self.show_toast(t("chapter02.gold_found", count=chest.gold))

    def _update_hush(self) -> None:
        """Gizli odada dunya susar.

        Ses sistemi Gorev 10'da geliyor; `hush` simdiden dogru degeri
        tutuyor ve **gorsel** yarisi bugun calisiyor: kenarlardan karanlik
        iceri cekiliyor. Muzigi kesecek olan taraf bu degeri okuyacak.
        """
        target = 1.0 if self._in_secret_chamber() else 0.0
        if self.hush < target:
            self.hush = min(target, self.hush + HUSH_RISE)
        else:
            self.hush = max(target, self.hush - HUSH_FALL)
        self.game.music_hush = self.hush

    def _in_secret_chamber(self) -> bool:
        """Oyuncu gizli **odacigin** icinde mi?

        Sutuna bakmak yetmiyor: ana koridor odacigin tam altindan geciyor
        ve ayni sutunlari paylasiyor. Yukseklik de sart, yoksa gizli odayi
        hic bulmamis oyuncu da sessizligi yasardi.
        """
        if not self.secret_found or self.room != "gizli_oda":
            return False
        floor = (SECRET_CHAMBER_FLOOR_ROW + 1) * TILE_SIZE
        return self.player.body.bottom <= floor

    def _update_arena(self) -> None:
        if (self.room == "miniboss" and not self.arena_sealed
                and not self.boss_defeated):
            # Oyuncu kapi sutununu **gercekten gecince** kapanir - oda
            # sinirina girer girmez degil (bkz. _narrate_room). `boss_defeated`
            # kontrolu sart: yoksa kapi acildiktan sonra oyuncu hala sutunun
            # otesindeyse bir sonraki karede kendini hemen yeniden kilitliyordu.
            if self.player.body.center_x > (ARENA_DOOR_COLUMN + 1) * TILE_SIZE:
                self._seal_arena()
            return
        if not self.arena_sealed or self.boss_defeated:
            return
        if self.boss is not None and not self.boss.dead:
            return
        self._open_arena()

    def _seal_arena(self) -> None:
        """Girise kapi iner. Belge: kapali arena."""
        if self.arena_sealed:
            return
        self.arena_sealed = True
        for row in ARENA_DOOR_ROWS:
            self.tilemap.set_tile(ARENA_DOOR_COLUMN, row, SOLID)
        self.juice.explosion(ARENA_DOOR_COLUMN * TILE_SIZE,
                             self.player.body.center_y, ImpactWeight.FINISHER)

    def _open_arena(self) -> None:
        """Boss oldu: kapi kalkar, odul verilir.

        Kapinin **acilmasi** kritik: oyuncu olurse de aciliyor, yoksa
        arenada kilitli kalirdi.
        """
        self.boss_defeated = True
        self.arena_sealed = False
        for row in ARENA_DOOR_ROWS:
            self.tilemap.set_tile(ARENA_DOOR_COLUMN, row, EMPTY)
        self.earned_gold += BOSS_GOLD
        if self.save_data is not None:
            self.save_data.gold += BOSS_GOLD
        self.show_toast(t("chapter02.boss_gold", count=BOSS_GOLD), frames=180)

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
        result = ChapterResult(
            chapter_key="chapter.first_descent",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 2
            data.chapter_name = "chapter.first_descent"
            data.playtime_frames += self.frames
            data.best_combo = max(data.best_combo, self.player.combo.best)
            data.secrets_found += result.secrets_found
            data.secrets_total += SECRETS_TOTAL
            if "chapter.first_descent" not in data.chapters_cleared:
                data.chapters_cleared.append("chapter.first_descent")

        # Bolum 3 artik var - ozet ekrani kapaninca dogrudan ona gecilir.
        # (Onceden buraya `on_continue=None` verilip ana menuye donuluyordu;
        # DEVIR.md'nin "Bolum 3 henuz yok" notu bu satirla kapaniyor.)
        character = self.character

        def _continue() -> None:
            from src.scenes.chapter03_cinematics import DescentCinematic
            self.scenes.set_root(DescentCinematic, character=character)

        self.scenes.push(ChapterEndScene, result=result, on_continue=_continue)

    # --- Kancalar -----------------------------------------------------------
    def on_player_died(self, player) -> None:
        # Arenada olen oyuncu kilitli kalmasin.
        if self.arena_sealed:
            self._open_arena()
        super().on_player_died(player)

    def on_wall_broken(self, rects: list[pygame.Rect]) -> None:
        """Iki catlagin anlami farkli - hangisi yikildi?"""
        secret = any(rect.x // TILE_SIZE >= SECRET_WALL_MIN_COLUMN
                     for rect in rects)
        if secret and not self.secret_found:
            self.secret_found = True
            self.show_toast(t("chapter02.secret_found"), frames=200)
            self.say(Line("echo", "line.ch02_echo_secret"))
            return
        super().on_wall_broken(rects)

    def on_boss_move(self, boss, move: str) -> None:
        """Mini-boss hamle yapti. Cokus aninda kamera bir an takiliyor."""
        if move == "slam":
            self.camera.linger(6)

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw_torches(surface, offset, TORCHES, self.game.frame)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)
        self._draw_claw_marks(surface, offset)
        if self.crack_revealed and self.echo is None:
            self._draw_crack(surface, offset)

    def _draw_claw_marks(self, surface: pygame.Surface, offset) -> None:
        """Duvarda uc cizik. Cemo'nun boyunda - **alcakta**.

        Ikincisi daha derin: belge "daha caresiz" diyor, bunun gorsel
        karsiligi daha uzun ve daha dagilmis cizikler.
        """
        ox, oy = offset
        for index, (tile_x, tile_y) in enumerate(CLAW_MARKS):
            x = tile_x * TILE_SIZE - ox
            y = tile_y * TILE_SIZE - oy
            if x < -32 or x > INTERNAL_WIDTH + 32:
                continue
            length = 7 if index == 0 else 11
            spread = 3 if index == 0 else 5
            for stroke in range(3):
                surface.fill(palette.color("blood_dark"),
                             (x + stroke * spread, y + stroke, 1, length))

    def _draw_crack(self, surface: pygame.Surface, offset) -> None:
        """Ardo'nun izini surdugu catlak - kalici olarak gorunur."""
        ox, oy = offset
        for rect in self.tilemap.breakable_rects():
            surface.fill(palette.color("violet_dark"),
                         (rect.centerx - ox, rect.y - oy, 1, rect.height))

    def draw_overlay(self, surface: pygame.Surface) -> None:
        # Boss bari **sahne** ciziyor, dusman kendi cizmiyor: bar ekranin
        # ustunde sabit duruyor, dunyada degil. `Boss.draw_health_bar`
        # bunu bekliyordu ama hicbir sahne cagirmiyordu - arena kapaniyor,
        # bar hic gorunmuyordu. Normal dusmanlarda bar **yok** (CLAUDE.md
        # 7): durum sendeleme ve renkle okunuyor, yalnizca boss'ta bar var.
        if self.boss is not None and not self.boss.dead and self.arena_sealed:
            self.boss.draw_health_bar(surface)
        if self.hush > 0.02:
            self._draw_hush(surface)

    def _draw_hush(self, surface: pygame.Surface) -> None:
        """Sessizligin gorsel karsiligi: kenarlardan iceri cekilen karanlik."""
        depth = int(28 * self.hush)
        if depth <= 0:
            return
        row = pygame.Surface((INTERNAL_WIDTH, 1))
        row.fill(palette.color("void"))
        bottom = surface.get_height() - 1
        for i in range(depth):
            row.set_alpha(int(200 * (1.0 - i / depth)))
            surface.blit(row, (0, i))
            surface.blit(row, (0, bottom - i))

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"oda {self.room} ({self.room_frames})  "
            f"gizli {self.secret_found}  sessizlik {self.hush:.2f}  "
            f"arena {self.arena_sealed}"]
