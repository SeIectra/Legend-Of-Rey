"""Bolum 5 - "Sular". Oynanabilir sahne.

Oda verisi `src/world/rooms/chapter05.py` icinde; burasi onu oynatiyor.

Bulmaca dort adim (`docs/yapi.md` B5): vana suyu yukseltir -> oyuncu
yuzerek ust kata cikar -> oradaki ikinci vana suyu indirir -> alttaki
savak acilir. Ucuncu adimda oyuncu **kendisi de asagi iniyor** - cozumun
bedeli konumunu kaybetmek, ve bulmacayi bir karar yapan sey bu.

## Vana etkilesimle, savak KENDILIGINDEN

Vana tusla ceviriliyor (bir KARAR), savak su seviyesini izleyip
kendiliginden aciliyor/kapaniyor (bir SONUC). Ayrim bilincli: oyuncunun
verdigi karar ile onun dogurdugu sonuc farkli kanallardan gelmeli, yoksa
"ben mi yaptim, oyun mu yapti" belirsizligi olusuyor.

## Savak tilemap'e yaziliyor

`keydoor.LockedDoor` ile ayni yol: gorsel bir kapak degil, gercek `SOLID`
tile'lar. Carpisma zaten tilemap'ten geliyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_WIDTH, TILE_SIZE
from src.core.input import Action
from src.core.juice import ImpactWeight
from src.scenes.play import PlayScene
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.dialogue import Line
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.rooms.chapter05 import (
    CHEST_GOLD, LEVEL, ROOM_STARTS, SECRETS_TOTAL, SLUICE_CLOSE_LEVEL,
    SLUICE_ROWS, SLUICE_TILE_COLUMN, VALVE_HIGH_TILE, VALVE_LOW_TILE,
    WATER_HIGH, WATER_LOW,
)
from src.world.tilemap import EMPTY, SOLID, TileMap
from src.world.water import WaterState

# Oyuncu vanaya bu kadar yaklasinca cevirebilir (piksel).
VALVE_REACH = 20.0
# Vana cevrildikten sonra tekrar cevrilemeyecegi kare sayisi. Su yavas
# hareket ettigi icin arka arkaya basmak seviyeyi titretirdi.
VALVE_COOLDOWN = 45

ENEMY_CLASSES = {
    "shambler": "src.entities.enemies.shambler:Shambler",
    # Katman 2'nin ilk uyesi, tek ornek (DEVIR 3 madde 8). Yerlesim
    # gerekcesi `src/world/rooms/chapter05.py` Oda 3'te yazili.
    "shieldbearer": "src.entities.enemies.shieldbearer:Shieldbearer",
}


def _load(path: str):
    module_name, class_name = path.split(":")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


class Chapter05Scene(PlayScene):
    """Sular: uc oda, bir su bulmacasi, bir gizli sandik."""

    chapter_number = 5
    chapter_name_key = "chapter.waters"
    # **Kesif muzigi burada.** `docs/ekonomi-uretim.md` bu bolumu
    # "bulmaca agirlikli" diye etiketliyor - dovus seyrek, yani
    # muzigin degismesi nadir ve anlamli oluyor. Oteki bolumlerde
    # varsayilan "combat" (gerekce `PlayScene.music_context`).
    music_context = "explore"
    postfx_grade = "descent"
    ambience_preset = "dust"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)

        # Su bastan ALCAK: oyuncu once kuru hali goruyor.
        self.water = WaterState(level=WATER_LOW, min_level=WATER_HIGH,
                                max_level=WATER_LOW)
        self.sluice_open = True
        self._apply_sluice(opened=True)

        self.valve_frames = 0
        self.valves_turned = 0
        self.room = ""
        self.room_frames = 0
        self.frames = 0
        self.entered_rooms: set[str] = set()
        self.earned_gold = 0
        self.secret_found = False
        self.finished = False
        self.shield_hinted = False

        self.chests = [Chest(spot.x, spot.feet_y, gold=CHEST_GOLD,
                             secret=True)
                       for spot in LEVEL.of("chest")]

        self._enter_room(self._room_at(self.player.body.center_x))

    # --- Odalar -------------------------------------------------------------
    def _room_at(self, x: float) -> str:
        tile_x = int(x) // TILE_SIZE
        name = ROOM_STARTS[0][0]
        for room_name, start in ROOM_STARTS:
            if tile_x >= start:
                name = room_name
        return name

    def _room_span(self, name: str) -> tuple[int, int]:
        for index, (room_name, start) in enumerate(ROOM_STARTS):
            if room_name != name:
                continue
            end = (ROOM_STARTS[index + 1][1] if index + 1 < len(ROOM_STARTS)
                   else 10_000)
            return start, end
        return 0, 0

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
        if name == "esik":
            self._voice("line.ch05_echo_enter", "line.ch05_ardo_enter")
        elif name == "vana_odasi":
            self._voice("line.ch05_echo_valve", "line.ch05_ardo_valve")
        elif name == "alt_gecit":
            # Kalkanli'yi **gormeden once** tanitiyoruz: yeni bir siluet
            # bir de aciklamasiz gelirse oyuncu once olur, sonra anlar.
            self._voice("line.ch05_echo_guard", "line.ch05_ardo_guard")

    def _voice(self, echo_key: str, ardo_key: str) -> None:
        """Yanki konusur, Yanki yoksa oynanan karakter (Bolum 3/4 deseni)."""
        if self.has_echo:
            self.say(Line("echo", echo_key))
        else:
            self.say(Line(self.character, ardo_key))

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.room_frames += 1
        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        if self.valve_frames > 0:
            self.valve_frames -= 1
        self._update_valves()
        self._update_sluice()
        self._update_chests()
        self._check_exit()

    # --- Kalkanli -----------------------------------------------------------
    def on_shield_block(self, enemy) -> None:
        """Kalkan ilk kez blokladi - **ipucu tam burada** veriliyor.

        Odaya girerken degil, oyuncu **kendi elleriyle** duvara toslayinca:
        onceden soylenen bir ipucu bilgi, tam o anda soylenen bir ipucu
        cevaptir. Yankı'nin ucuncu goz rolu de bu - oyuncunun goremedigini
        gosteriyor (Arda, 24.08.2026).

        Bir kez. Tekrarlanan ipucu ogut olur.
        """
        super().on_shield_block(enemy)
        if self.shield_hinted:
            return
        self.shield_hinted = True
        self._voice("line.ch05_echo_block", "line.ch05_ardo_block")

    # --- Vana ---------------------------------------------------------------
    def _valve_positions(self) -> tuple[tuple[float, float], ...]:
        return tuple(
            (tile[0] * TILE_SIZE + TILE_SIZE * 0.5,
             (tile[1] + 1) * TILE_SIZE)
            for tile in (VALVE_LOW_TILE, VALVE_HIGH_TILE))

    def _valve_near(self) -> int:
        """Oyuncunun yanindaki vananin indeksi, yoksa -1."""
        for index, (vx, vy) in enumerate(self._valve_positions()):
            if (abs(self.player.body.center_x - vx) <= VALVE_REACH
                    and abs(self.player.body.bottom - vy) <= TILE_SIZE * 2):
                return index
        return -1

    def _update_valves(self) -> None:
        if self.valve_frames > 0:
            return
        index = self._valve_near()
        if index < 0 or not self.game.input.pressed(Action.INTERACT):
            return
        self.water.toggle()
        self.valve_frames = VALVE_COOLDOWN
        self.valves_turned += 1
        vx, vy = self._valve_positions()[index]
        self.juice.explosion(vx, vy - 8, ImpactWeight.NORMAL)
        self.particles.burst(vx, vy - 8, 10, path="echo", speed=(0.4, 1.4))
        self.game.play_sound("rift_open")
        if self.valves_turned == 1:
            self.show_toast(t("chapter05.valve_turned"), frames=170)

    # --- Savak --------------------------------------------------------------
    def _update_sluice(self) -> None:
        """Su yuksekken kapak KAPALI, cekilince ACIK.

        Samandirali savak: mekanik bir sebep. "Kapi suyun altinda kaliyor"
        demek bogulma sistemi gerektirirdi - oyunda yok.
        """
        should_open = self.water.level > SLUICE_CLOSE_LEVEL
        if should_open == self.sluice_open:
            return
        self.sluice_open = should_open
        self._apply_sluice(should_open)
        self.game.play_sound("rift_close" if not should_open else "rift_open")
        x = SLUICE_TILE_COLUMN * TILE_SIZE
        self.juice.explosion(x, self.player.body.center_y, ImpactWeight.NORMAL)

    def _apply_sluice(self, opened: bool) -> None:
        tile = EMPTY if opened else SOLID
        for row in SLUICE_ROWS:
            self.tilemap.set_tile(SLUICE_TILE_COLUMN, row, tile)

    # --- Sandik ve cikis ----------------------------------------------------
    def _update_chests(self) -> None:
        for chest in self.chests:
            chest.update()
            if chest.opened or not chest.rect.colliderect(self.player.body.rect):
                continue
            chest.open()
            self.earned_gold += chest.gold
            if self.save_data is not None:
                self.save_data.gold += chest.gold
            self.secret_found = True
            self.show_toast(t("chapter05.chest_found", count=chest.gold),
                            frames=180)

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
            chapter_key="chapter.waters",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 5
            data.chapter_name = "chapter.waters"
            data.playtime_frames += self.frames
            data.best_combo = max(data.best_combo, self.player.combo.best)
            data.secrets_found += result.secrets_found
        # Bolum 6'ya baglaniyor: ozet ekrani kapaninca oradan devam.
        character = self.character

        def _continue() -> None:
            from src.scenes.chapter06 import Chapter06Scene
            self.scenes.set_root(Chapter06Scene, character=character)

        self.scenes.push(ChapterEndScene, result=result,
                         on_continue=_continue)

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        self._draw_valves(surface, offset)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)

    def _draw_valves(self, surface: pygame.Surface, offset) -> None:
        """Vana: duvara gomulu bir carkin dort kolu.

        Yakindayken parliyor - "burada bir sey var" bilgisi ipucu
        metninden ONCE gelmeli.
        """
        ox, oy = offset
        near = self._valve_near()
        for index, (vx, vy) in enumerate(self._valve_positions()):
            x = int(vx) - ox
            y = int(vy) - oy - 9
            if x < -16 or x > INTERNAL_WIDTH + 16:
                continue
            active = index == near
            spin = self.frames * (0.09 if self.water.moving else 0.02)
            # "brass" bir ZINCIR adi, palet rengi degil - dogru renk adi
            # "gold". (Zincir adi != renk adi; DEVIR 6'daki tuzak.)
            tone = palette.color("gold" if active else "earth")
            surface.fill(palette.color("stone_darkest"), (x - 4, y - 4, 9, 9))
            for arm in range(4):
                angle = spin + arm * math.pi / 2
                ex = x + int(round(math.cos(angle) * 4))
                ey = y + int(round(math.sin(angle) * 4))
                pygame.draw.line(surface, tone, (x, y), (ex, ey))
            surface.fill(tone, (x, y, 1, 1))
