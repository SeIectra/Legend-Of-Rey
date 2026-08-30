"""Bolum 11 - "Ayna Salonu". Oynanabilir sahne.

Oda verisi `src/world/rooms/chapter11.py`, ara sahne
`src/scenes/chapter11_cinematics.py`.

`docs/yapi.md` B11: *"Yalnizsin. Golge yaratiklar sadece isikta olur.
Aynalari cevirerek isini yaratiklara yonlendir. **Yanki sana yalan
soyluyor olabilir** - hangi aynanin dogru oldugunu kendin bulmalisin."*

## Bolum 3'un isik sistemi hicbir degisiklik istemedi

`ShadowShambler` orada yazilmisti ve `scene.light.in_light()` soruyor.
Isin `LightState`'e kaynak dizisi yaziyor (`beam.apply_light`), yani
golge yaratigi **bedavaya** calisiyor. Sekiz bolum onceki bir sinir
dogru yerdeymis.

## Yalan artik SUREKLI

Bolum 10'da yalan tek bir secimdi. Burada Yanki bulmaca boyunca
konusuyor ve isaretledigi ayna **zaten dogru** olani - yani dogru
olani bozmaya davet ediyor. Oyuncu ona uyarsa zincir bozuluyor ve
butun zinciri yeniden dusunmek zorunda kaliyor.

Bolum 10'da Yanki'yi dinlememis oyuncu (`loyalty` negatif) burada
kendi icinden bir supheyle uyariliyor - sayacin ilk gorunur karsiligi.
Ama sayi hala **gosterilmiyor**: degisen sey yalnizca bir replik.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE
from src.core.input import Action
from src.core.juice import ImpactWeight
from src.scenes.play import PlayScene
from src.systems import beam, loyalty
from src.systems.beam import Mirror
from src.systems.light import LightState
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.rooms.chapter11 import (
    BEAM_DIRECTION, CHEST_GOLD, HALL_DOOR_ROWS, HALL_DOOR_TILE,
    HALL_EMITTER_TILE, HALL_MIRROR_TILES, HALL_RECEIVER_TILE, LEVEL,
    LIE_INDEX, ROOM_STARTS, SECRETS_TOTAL, TEACH_EMITTER_TILE,
    TEACH_MIRROR_TILE,
)
from src.world.tilemap import EMPTY, SOLID, TileMap

ENEMY_CLASSES = {
    "shadow_shambler": "src.entities.enemies.shadow_shambler:ShadowShambler",
    "spearman": "src.entities.enemies.spearman:Spearman",
}

# Aynayi cevirmek icin bu kadar yakin olmak gerek (piksel).
MIRROR_REACH = 26.0


def _load(path: str):
    module_name, class_name = path.split(":")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


class Chapter11Scene(PlayScene):
    """Ayna Salonu: dort oda, uc ayna, bir yalan."""

    chapter_number = 11
    chapter_name_key = "chapter.mirror_hall"
    postfx_grade = "descent"
    ambience_preset = "dust"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        self.companion = None           # Bolum 10'dan beri yalniz

        # **Isik sistemi Bolum 3'ten.** Golge yaratiklari bunu soruyor.
        self.light = LightState()

        # Iki bulmaca: ogretme odasi ve salon.
        self.teach_mirror = Mirror(*TEACH_MIRROR_TILE, kind=beam.SLASH)
        self.hall_mirrors = [Mirror(x, y, kind=start)
                             for x, y, start, _correct in HALL_MIRROR_TILES]
        self.mirrors = [self.teach_mirror] + self.hall_mirrors
        self.paths: list[beam.BeamPath] = []
        self.solved = False

        for row in HALL_DOOR_ROWS:
            self.tilemap.set_tile(HALL_DOOR_TILE, row, SOLID)
        self.door_open = False

        self.chests = [Chest(spot.x, spot.feet_y, gold=CHEST_GOLD, secret=True)
                       for spot in LEVEL.of("chest")]

        self.room = ""
        self.room_frames = 0
        self.frames = 0
        self.entered_rooms: set[str] = set()
        self.earned_gold = 0
        self.secret_found = False
        self.finished = False
        self.lie_told = False
        self.doubt_told = False
        self.rule_hinted = False

        self._enter_room(self._room_at(self.player.body.center_x))
        self._trace_beams()

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
        if name == "giris":
            self.say_player("line.ch11_rey_hall", "line.ch11_ardo_hall")
        elif name == "ogrenme":
            self.say_player("line.ch11_rey_mirror", "line.ch11_ardo_mirror")

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.room_frames += 1
        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        for mirror in self.mirrors:
            mirror.update()
        self._update_rotate()
        self._trace_beams()
        self._update_lie()
        self._update_rule_hint()
        self._update_chests()
        self._check_exit()

    # --- Isin ---------------------------------------------------------------
    def _trace_beams(self) -> None:
        """Iki isini her karede yeniden iziyor ve isiga yaziyor.

        Her karede yeniden: ayna cevrilince yol aninda degismeli.
        Onbelleklemek "ne zaman bayat" sorusunu getirirdi ve tile
        bazli izleme zaten ucuz (en fazla 200 adim, iki isin).
        """
        teach = beam.trace(self.tilemap, [self.teach_mirror],
                           TEACH_EMITTER_TILE, BEAM_DIRECTION)
        hall = beam.trace(self.tilemap, self.hall_mirrors,
                          HALL_EMITTER_TILE, BEAM_DIRECTION)
        self.paths = [teach, hall]
        beam.apply_light(self.light, teach, "beamA")
        beam.apply_light(self.light, hall, "beamB")

        if not self.solved and HALL_RECEIVER_TILE in hall.tiles:
            self._solve()

    def _update_rotate(self) -> None:
        mirror = self._mirror_near()
        if mirror is None or not self.game.input.pressed(Action.INTERACT):
            return
        if not mirror.rotate():
            return
        self.game.play_sound("ui_tick")
        self.particles.burst(mirror.tile_x * TILE_SIZE + 8,
                             mirror.tile_y * TILE_SIZE + 8, 8,
                             path="spark", speed=(0.3, 1.2))

    def _mirror_near(self) -> Mirror | None:
        for mirror in self.mirrors:
            dx = abs(mirror.tile_x * TILE_SIZE + 8 - self.player.body.center_x)
            dy = abs(mirror.tile_y * TILE_SIZE + 8 - self.player.body.center_y)
            if dx <= MIRROR_REACH and dy <= MIRROR_REACH:
                return mirror
        return None

    def _solve(self) -> None:
        self.solved = True
        self.door_open = True
        for row in HALL_DOOR_ROWS:
            self.tilemap.set_tile(HALL_DOOR_TILE, row, EMPTY)
        x, y = HALL_RECEIVER_TILE
        self.juice.explosion(x * TILE_SIZE, y * TILE_SIZE,
                             ImpactWeight.FINISHER)
        self.particles.burst(x * TILE_SIZE, y * TILE_SIZE, 20,
                             path="spark", speed=(0.8, 2.6))
        self.game.play_sound("rift_open")
        self.show_toast(t("chapter11.solved"), frames=210)

    # --- Yalan ---------------------------------------------------------------
    def _update_lie(self) -> None:
        """Salona girince Yanki **zaten dogru olan** aynayi isaretliyor.

        Yalanin bicimi onemli: "sunu cevir" demek, "sunu cevirme"
        demekten cok daha zararli - cunku oyuncu cevirdiginde zincir
        bozuluyor ve hangi adimin yanlis gittigini bilemiyor.
        """
        if self.lie_told or self.room != "salon":
            return
        self.lie_told = True
        self.say(self._voice("line.ch11_echo_lie", "line.ch11_trace_lie"))
        self.game.play_sound("echo_reveal")

        # Bolum 10'da Yanki'yi dinlememis oyuncu supheli - **sayac
        # gosterilmiyor**, yalnizca bir replik degisiyor.
        if loyalty.read(self.save_data) < 0 and not self.doubt_told:
            self.doubt_told = True
            self.say_player("line.ch11_rey_doubt", "line.ch11_ardo_doubt")

    def _voice(self, echo_key: str, ardo_key: str):
        from src.ui.dialogue import Line
        if self.character == "ardo":
            return Line("ardo", ardo_key)
        return Line("echo", echo_key)

    def _update_rule_hint(self) -> None:
        """Golge yaratigina vurup hicbir sey olmayinca kurali soyle.

        **Bir kez.** Ders zaten kilicin bosa gitmesiyle veriliyor;
        yazi yalnizca oyuncunun "oyun mu bozuk" diye dusunmesini
        onluyor.
        """
        if self.rule_hinted:
            return
        for enemy in self.enemies:
            if getattr(enemy, "shrugged_off", 0) > 0:
                self.rule_hinted = True
                self.show_toast(t("chapter11.rule"), frames=220)
                return

    # --- Sandik ve cikis ----------------------------------------------------
    def _update_chests(self) -> None:
        for chest in self.chests:
            chest.update()
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
            chapter_key="chapter.mirror_hall",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 11
            data.chapter_name = "chapter.mirror_hall"
            data.playtime_frames += self.frames
            data.best_combo = max(data.best_combo, self.player.combo.best)
            data.secrets_found += result.secrets_found
        # Bolum 12 henuz yok - ozet ekrani kapaninca ana menuye donuluyor.
        self.scenes.push(ChapterEndScene, result=result)

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        self._draw_beams(surface, offset)
        self._draw_emitters(surface, offset)
        for mirror in self.mirrors:
            self._draw_mirror(surface, offset, mirror)
        self._draw_receiver(surface, offset)
        self._draw_door(surface, offset)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)

    def _draw_beams(self, surface: pygame.Surface, offset) -> None:
        """Isinin kendisi.

        `art/lighting.render` isigi zaten deliyor; bu **cizgi**, yani
        isinin nereden gectigi. Ikisi ayri: biri aydinlatma, oteki
        bilgi. Yalnizca isik olsaydi oyuncu isinin yolunu izleyemez ve
        bulmacayi cozemezdi.
        """
        ox, oy = offset
        for path in self.paths:
            for x, y in path.tiles:
                px = x * TILE_SIZE + TILE_SIZE // 2 - ox
                py = y * TILE_SIZE + TILE_SIZE // 2 - oy
                flicker = 0.75 + 0.25 * math.sin(self.frames * 0.3 + x + y)
                colour = tuple(int(c * flicker)
                               for c in palette.color("bone"))
                surface.fill(colour, (px - 1, py - 1, 3, 3))
            for x, y in path.bounces:
                px = x * TILE_SIZE + TILE_SIZE // 2 - ox
                py = y * TILE_SIZE + TILE_SIZE // 2 - oy
                surface.fill(palette.color("white_flash"), (px - 2, py - 2, 4, 4))

    def _draw_emitters(self, surface: pygame.Surface, offset) -> None:
        ox, oy = offset
        for tile in (TEACH_EMITTER_TILE, HALL_EMITTER_TILE):
            x = tile[0] * TILE_SIZE - ox
            y = tile[1] * TILE_SIZE - oy
            surface.fill(palette.color("stone_dark"), (x, y + 2, TILE_SIZE, 12))
            pulse = 0.6 + 0.4 * math.sin(self.frames * 0.11)
            colour = tuple(int(c * pulse) for c in palette.color("bone"))
            surface.fill(colour, (x + TILE_SIZE - 4, y + 6, 4, 4))

    def _draw_mirror(self, surface: pygame.Surface, offset,
                     mirror: Mirror) -> None:
        """Ayna - **egimi okunur olmali.**

        Bir kare cizip icine cizgi koymak yetmiyordu: 16 pikselde
        egimin yonu ancak kosegen bir serit olarak okunuyor. Cerceve
        ince, serit kalin.
        """
        ox, oy = offset
        x = mirror.tile_x * TILE_SIZE - ox
        y = mirror.tile_y * TILE_SIZE - oy
        frame_tone = "stone" if not mirror.fixed else "stone_dark"
        surface.fill(palette.color(frame_tone), (x + 1, y + 1, 14, 14))
        surface.fill(palette.color("ink"), (x + 2, y + 2, 12, 12))

        spinning = mirror.spin > 0
        tone = "white_flash" if spinning else "bone"
        for step in range(12):
            if mirror.kind == beam.SLASH:
                px, py = x + 13 - step, y + 2 + step
            else:
                px, py = x + 2 + step, y + 2 + step
            surface.fill(palette.color(tone), (px, py, 2, 2))

        # Yanki'nin isaretledigi ayna - yalan gorunur olmali ki secim
        # gercek olsun.
        if (self.lie_told and not self.solved
                and mirror is self.hall_mirrors[LIE_INDEX]):
            pulse = 0.5 + 0.5 * math.sin(self.frames * 0.09)
            base = palette.color("echo_bright" if self.character != "ardo"
                                 else "bone")
            colour = tuple(int(c * pulse) for c in base)
            surface.fill(colour, (x, y - 4, 16, 2))

    def _draw_receiver(self, surface: pygame.Surface, offset) -> None:
        ox, oy = offset
        x = HALL_RECEIVER_TILE[0] * TILE_SIZE - ox
        y = HALL_RECEIVER_TILE[1] * TILE_SIZE - oy
        surface.fill(palette.color("stone_dark"), (x + 1, y + 1, 14, 14))
        tone = "gold" if self.solved else "stone_darkest"
        surface.fill(palette.color(tone), (x + 4, y + 4, 8, 8))

    def _draw_door(self, surface: pygame.Surface, offset) -> None:
        if self.door_open:
            return
        ox, oy = offset
        x = HALL_DOOR_TILE * TILE_SIZE - ox
        top = HALL_DOOR_ROWS.start * TILE_SIZE - oy
        height = len(HALL_DOOR_ROWS) * TILE_SIZE
        surface.fill(palette.color("stone_dark"), (x, top, TILE_SIZE, height))
        surface.fill(palette.color("stone_darkest"), (x, top, 1, height))

    def debug_lines(self) -> list[str]:
        kinds = "".join(m.kind for m in self.hall_mirrors)
        return [f"oda {self.room}  aynalar {kinds}  cozuldu={self.solved}"
                f"  sadakat={loyalty.read(self.save_data)}"]
