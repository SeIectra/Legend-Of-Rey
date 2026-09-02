"""Bolum 7 - "Dar Gecit". Oynanabilir sahne.

Oda verisi `src/world/rooms/chapter07.py`, ara sahneler
`src/scenes/chapter07_cinematics.py`.

`docs/yapi.md` B7: *"Tek kisilik bir aralik. Ardo gecemez, Rey gecer.
Rey obur taraftan kapiyi acar. Romantik an: Ardo elini uzatir, Rey
tutar, aralıktan ceker."*

## Iki oynanis, tek kod

Kanon `girth`'e bagli, oynanan karaktere degil: catlaktan **her zaman**
Rey geciyor.

    Rey oynanirken   sen geciyorsun, carki sen ceviriyorsun,
                     yoldas kapiyi bekliyor
    Ardo oynanirken  sen gecemiyorsun. Yoldasi (Rey) catlaga
                     **gonderiyorsun**; carki o ceviriyor, kapiyi sana
                     o aciyor.

Ikinci yol bir yedek degil, oyunun kendi diliyle tutarli bir cozum:
`Companion.hold(x)` Bolum 6'da plakalar icin yazilmisti ve emir tusu
(INTERACT) oyuncunun zaten bildigi tus. Yeni bir sey ogretmeden yeni bir
sey soyluyor.

Ve tematik olarak daha da dogru: Ardo oynayan oyuncu **beklemeyi**
yasiyor. Bolum 6'da kurtaran taraftı; burada bekleyen taraf.

## Dorduncu isaret

Bolum 3 "Ucuncu Isaret" ile bitiyordu; bu da dordunculeyle. Kolye
titresimi + uzakta bir isik: her bolumun sonunda ayni dil, sayisi bir
artiyor - oyuncu ilerledigini bir sayacla degil bir **ritimle** biliyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE
from src.core.input import Action
from src.core.juice import ImpactWeight
from src.entities.character_stats import ARDO, REY
from src.entities.companion import Companion, other_character
from src.scenes.play import PlayScene
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.gap import NarrowGap
from src.world.pickups import Chest
from src.world.rooms.chapter07 import (
    CHEST_GOLD, DOOR_ROWS, DOOR_TILES, GAP_CLEARANCE, GAP_ROWS, GAP_TILE,
    HAND_TILE, LEVEL, LEDGE_TILE, ROOM_STARTS, SECRETS_TOTAL, WINCH_TILE,
)
from src.world.tilemap import EMPTY, SOLID, TileMap

ENEMY_CLASSES = {
    "shambler": "src.entities.enemies.shambler:Shambler",
    "climber": "src.entities.enemies.climber:Climber",
    "shieldbearer": "src.entities.enemies.shieldbearer:Shieldbearer",
}

# Carki cevirmek icin bu kadar yakin olmak gerek (piksel).
WINCH_REACH = 22.0
# Kapi acildiktan sonra yoldas bu kadar karede kosarak geliyor.
COMPANION_ARRIVAL_FRAMES = 90
# Yoldasa "catlaga git" emri bu menzilde veriliyor - Bolum 6'daki
# `ORDER_RANGE` ile ayni sayi, ayni tus. Oyuncu yeni bir sey ogrenmiyor.
ORDER_RANGE = 90.0
# Sigmayan karakter bu kadar kez zorlayinca "Sigmiyor" sahnesi aciliyor.
# Bir kere degil: ilk carpma kaza olabilir, ikincisi bir deneme.
REFUSALS_BEFORE_SCENE = 2


def _load(path: str):
    module_name, class_name = path.split(":")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


class Chapter07Scene(PlayScene):
    """Dar Gecit: bes oda, bir catlak, bir cark, bir el."""

    chapter_number = 7
    chapter_name_key = "chapter.narrow_pass"
    postfx_grade = "descent"
    ambience_preset = "dust"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)

        # --- Yoldas: kanon geregi SECMEDIGIN karakter -------------------
        self.companion_key = other_character(self.character)
        self.companion = Companion(self, spawn.x - 26, spawn.feet_y,
                                   self.companion_key)

        # --- Catlak ve kapi ---------------------------------------------
        self.gap = NarrowGap(GAP_TILE, GAP_ROWS, GAP_CLEARANCE)
        for column in DOOR_TILES:
            for row in DOOR_ROWS:
                self.tilemap.set_tile(column, row, SOLID)
        self.door_open = False
        self.winch_turned = False
        self.arrival_frames = 0

        # --- Sahne bayraklari -------------------------------------------
        self.gap_scene_played = False
        self.alone_scene_played = False
        self.hand_scene_played = False
        self.reunited = False
        self.order_hinted = False
        self.gap_hinted = False

        self.chests = [Chest(spot.x, spot.feet_y, gold=CHEST_GOLD, secret=True)
                       for spot in LEVEL.of("chest")]

        self.room = ""
        self.room_frames = 0
        self.frames = 0
        self.entered_rooms: set[str] = set()
        self.earned_gold = 0
        self.secret_found = False
        self.finished = False

        self._enter_room(self._room_at(self.player.body.center_x))

    # --- Kim ince, kim genis ------------------------------------------------
    @property
    def player_is_slim(self) -> bool:
        """Oyuncu catlaktan geciyor mu? Kanon: yalnizca Rey."""
        return self.character != "ardo"

    def _girth(self, character: str) -> int:
        return ARDO.girth if character == "ardo" else REY.girth

    # --- Odalar -------------------------------------------------------------
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
                if start <= spot.tile_x < end:
                    self.enemies.append(_load(path)(self, spot.x, spot.feet_y))

    def _narrate_room(self, name: str) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        if name == "kapi_onu":
            self.say_player("line.ch07_rey_door", "line.ch07_ardo_door")
        elif name == "gecit":
            self.say_player("line.ch07_rey_together",
                            "line.ch07_ardo_together")

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.room_frames += 1
        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        self._update_gap()
        self._update_orders()
        self._update_winch()
        self._update_arrival()
        self._update_hand()
        self._update_chests()
        self._check_exit()

        if self.companion is not None:
            self.companion.update()

    # --- Catlak -------------------------------------------------------------
    def _update_gap(self) -> None:
        """Sigmayani geri iter, sigani isaretler.

        **Yoldas da sorgulaniyor**: Rey oynanirken Ardo catlaga girmeye
        calisip takiliyor ve "Sigmiyor" sahnesi oradan tetikleniyor.
        Yalnizca oyuncu sorgulansaydi yoldas duvarin icinden gecerdi.
        """
        pushed = self.gap.enforce(self.player.body,
                                  self._girth(self.character))
        self.gap.note_passage(self.player.body, self._girth(self.character))
        if pushed and not self.gap_hinted:
            # **Bir kez** soyleniyor. Oyuncu neden gecemedigini bilmiyor;
            # tekrarlanan ipucu ogut olur (ayni gerekce `chapter06`
            # `seal_hint`'te de yazili).
            self.gap_hinted = True
            self.show_toast(t("chapter07.gap_blocked"), frames=200)
        if self.companion is not None:
            girth = self._girth(self.companion_key)
            self.gap.enforce(self.companion.body, girth)
            self.gap.note_passage(self.companion.body, girth)

        if (not self.gap_scene_played
                and self.gap.refusals >= REFUSALS_BEFORE_SCENE):
            self.gap_scene_played = True
            self._play_gap_scene()

        if not self.alone_scene_played and self.gap.passed:
            self.alone_scene_played = True
            self._play_alone_scene()

    def _play_gap_scene(self) -> None:
        from src.scenes.chapter07_cinematics import GapCinematic
        self.game.play_sound("enemy_blocked")
        self.scenes.push(GapCinematic, character=self.character)

    def _play_alone_scene(self) -> None:
        from src.scenes.chapter07_cinematics import AloneCinematic
        # Yoldas catlagin bu tarafinda kaliyor - gecemez.
        if self.companion is not None:
            self.companion.hold(self.gap.rect.left - 24)
        self.scenes.push(AloneCinematic, character=self.character)

    # --- Yoldasa emir (yalnizca Ardo oynanirken gerekiyor) -------------------
    def _update_orders(self) -> None:
        """Ardo oynanirken catlaktan yoldas geciyor - oyuncu onu gonderiyor.

        Rey oynanirken bu yol hic calismiyor: oyuncu zaten kendisi
        geciyor ve emir vermesine gerek yok.
        """
        if self.player_is_slim or self.companion is None or self.door_open:
            return
        near_gap = abs(self.player.body.center_x
                       - self.gap.rect.centerx) <= ORDER_RANGE
        if near_gap and not self.order_hinted:
            self.order_hinted = True
            self.show_toast(t("chapter07.order_hint"), frames=240)
        if not near_gap or not self.game.input.pressed(Action.INTERACT):
            return
        # Yoldasi catlagin OTESINE gonderiyoruz; `hold` oraya yuruyor ve
        # sigdigi icin catlak onu durdurmuyor.
        self.companion.hold(float(WINCH_TILE[0] * TILE_SIZE))
        self.game.play_sound("ui_tick")

    # --- Cark ---------------------------------------------------------------
    def _winch_position(self) -> tuple[float, float]:
        return (WINCH_TILE[0] * TILE_SIZE + TILE_SIZE * 0.5,
                WINCH_TILE[1] * TILE_SIZE + TILE_SIZE)

    def _turner_at_winch(self):
        """Cark basinda kim var - oyuncu ya da gonderilen yoldas."""
        wx, wy = self._winch_position()
        for actor in (self.player, self.companion):
            if actor is None:
                continue
            if (abs(actor.body.center_x - wx) <= WINCH_REACH
                    and abs(actor.body.bottom - wy) <= TILE_SIZE * 2):
                return actor
        return None

    def _update_winch(self) -> None:
        if self.winch_turned:
            return
        turner = self._turner_at_winch()
        if turner is None:
            return
        # Oyuncu carktaysa tusa basmasi gerekiyor; yoldas carka vardiysa
        # kendiliginden ceviriyor - ona "bas" diyemeyiz.
        if turner is self.player and not self.game.input.pressed(Action.INTERACT):
            return
        self._turn_winch()

    def _turn_winch(self) -> None:
        self.winch_turned = True
        self.door_open = True
        for column in DOOR_TILES:
            for row in DOOR_ROWS:
                self.tilemap.set_tile(column, row, EMPTY)
        wx, wy = self._winch_position()
        self.juice.explosion(wx, wy - 10, ImpactWeight.FINISHER)
        self.particles.burst(wx, wy - 10, 16, path="dust", speed=(0.5, 2.0))
        self.game.play_sound("rift_open")
        self.show_toast(t("chapter07.door_open"), frames=200)
        self.arrival_frames = COMPANION_ARRIVAL_FRAMES
        # Yoldasin girisi - Arda'nin talimati: oteki karakterin
        # girislerinde `Ardo.mp3`.
        self.game.music.hold("companion", 420)

    def _update_arrival(self) -> None:
        """Kapi acilinca yoldas kosarak geliyor."""
        if self.arrival_frames <= 0 or self.companion is None:
            return
        self.arrival_frames -= 1
        self.companion.hold(self.player.body.center_x - 20)
        if self.arrival_frames == 0:
            self.companion.release()
            self.reunited = True

    # --- El -----------------------------------------------------------------
    def _update_hand(self) -> None:
        """Oyuncu cukurun kenarina varinca ★ sahne.

        Sahne bittikten sonra oyuncu ucurumun **otesine** birakiliyor:
        anlatilan sey tam olarak buydu, oyuncunun ayrica ziplamasi
        gerekseydi sahne bir sus payi olurdu.
        """
        if self.hand_scene_played or not self.reunited:
            return
        ledge_x = LEDGE_TILE[0] * TILE_SIZE
        if abs(self.player.body.center_x - ledge_x) > TILE_SIZE * 1.5:
            return
        self.hand_scene_played = True
        from src.scenes.chapter07_cinematics import HandCinematic
        self.scenes.push(HandCinematic, character=self.character)
        self._place_after_hand()

    def _place_after_hand(self) -> None:
        hand_x = HAND_TILE[0] * TILE_SIZE
        self.player.body.x = float(hand_x)
        self.player.body.y = float(HAND_TILE[1] * TILE_SIZE
                                   - self.player.body.height)
        self.player.body.vx = 0.0
        self.player.body.vy = 0.0
        if self.companion is not None:
            # **Bos yer aranarak.** Arda (30.08.2026): *"Bolum 7'de
            # 'Ardo yine yanimda' kisminda Ardo duvarin icinde
            # kaliyor."* Sabit `hand_x + 22` bazen karsi kenarin
            # kaya blogunun icine dusuyordu ve `Companion` kendi
            # kendini kurtarmiyor.
            cx, cy = self.free_spot_near(hand_x + 22,
                                         HAND_TILE[1] * TILE_SIZE,
                                         self.companion.body)
            self.companion.body.set_feet(cx, cy)
            self.companion.release()

    # --- Sandik ve cikis ----------------------------------------------------
    def _update_chests(self) -> None:
        for chest in self.chests:
            if chest.opened:
                continue
            if not chest.rect.colliderect(self.player.body.rect):
                continue
            chest.open()
            self.earned_gold += chest.gold
            self.secret_found = True
            self.pickup_juice(gold=True)

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
            chapter_key="chapter.narrow_pass",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 7
            data.chapter_name = "chapter.narrow_pass"
            data.playtime_frames += self.frames
            data.best_combo = max(data.best_combo, self.player.combo.best)
            data.secrets_found += result.secrets_found
        # Bolum 8'e baglaniyor.
        character = self.character

        def _continue() -> None:
            from src.scenes.chapter08 import Chapter08Scene
            self.scenes.set_root(Chapter08Scene, character=character)

        self.scenes.push(ChapterEndScene, result=result,
                         on_continue=_continue)

    # --- Kancalar -----------------------------------------------------------
    def after_restart(self, room: str) -> None:
        """Olumden sonra yoldas oyuncunun YANINDA basliyor.

        Bolum 6'daki kadar agir bir sorun degil (buradaki yoldas
        `setup()`'ta doguyor, yani kaybolmuyor) ama yeri yanlis
        olabiliyordu: `setup()` onu bolumun BASINA koyuyor ve oyuncu
        catlagin otesindeki bir odada olduyse yoldas duvarin ardinda,
        ulasilamaz bir yerde kaliyordu.

        Catlaktan sonraki odalarda kapi zaten aciliyor, yani yoldasin
        oraya yurumesinin bir engeli yok - onu oyuncunun yanina koymak
        yalnizca uzun ve sikici bir yuruyusu atliyor.
        """
        if self.companion is None or room in ("kapi_onu", "carkhane"):
            return
        x, y = self.free_spot_near(self.player.body.center_x - 22,
                                   self.player.body.feet[1],
                                   self.companion.body)
        self.companion.body.set_feet(x, y)
        self.companion.release()

    def on_companion_down(self, companion) -> None:
        self.particles.burst(companion.body.center_x, companion.body.center_y,
                             10, path="blood", speed=(0.8, 2.2))
        self.game.play_sound("player_hurt")
        self.show_toast(t("chapter06.companion_down"), frames=150)

    def on_companion_up(self, companion) -> None:
        self.pickup_juice()

    def on_companion_attack(self, companion) -> None:
        self.game.play_sound("swing_light")

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        self.gap.draw(surface, offset)
        self._draw_door(surface, offset)
        self._draw_winch(surface, offset)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)
        if self.companion is not None:
            self.companion.draw(surface, offset)

    def _draw_door(self, surface: pygame.Surface, offset) -> None:
        """Muhurlu kapi. Acilinca yalnizca cercevesi kaliyor."""
        ox, oy = offset
        x = DOOR_TILES.start * TILE_SIZE - ox
        top = DOOR_ROWS.start * TILE_SIZE - oy
        height = len(DOOR_ROWS) * TILE_SIZE
        width = len(DOOR_TILES) * TILE_SIZE
        if self.door_open:
            surface.fill(palette.color("stone_darkest"), (x, top, 1, height))
            surface.fill(palette.color("stone_darkest"),
                         (x + width - 1, top, 1, height))
            return
        surface.fill(palette.color("stone_dark"), (x, top, width, height))
        # Muhur: mor, nefes aliyor. Bolum 3'un renk ailesi.
        breath = 0.6 + 0.4 * math.sin(self.frames * 0.05)
        colour = tuple(int(c * breath) for c in palette.color("violet_bright"))
        cy = top + height // 2
        surface.fill(colour, (x + width // 2 - 1, cy - 1, 3, 3))

    def _draw_winch(self, surface: pygame.Surface, offset) -> None:
        ox, oy = offset
        wx, wy = self._winch_position()
        x = int(wx) - ox
        y = int(wy) - oy - 12
        surface.fill(palette.color("earth_dark"), (x - 5, y, 10, 12))
        # Kollar: cevrilince donmus kaliyor.
        angle = 0.0 if not self.winch_turned else 0.8
        for index in range(4):
            theta = angle + index * math.pi / 2
            px = x + int(round(math.cos(theta) * 6))
            py = y + 4 + int(round(math.sin(theta) * 4))
            # "ember" bir RENK; "brass" bir golge ZINCIRI ve
            # `palette.color()` onu tanimaz. Bu tuzaga projede iki kez
            # dusuldu (`steel`, `brass`) - zincir adi renk adi degil.
            surface.fill(palette.color("ember"), (px - 1, py - 1, 2, 2))

    def debug_lines(self) -> list[str]:
        return [f"oda {self.room}  catlak gecildi={self.gap.passed}"
                f"  kapi={'acik' if self.door_open else 'kapali'}"
                f"  el={self.hand_scene_played}"]
