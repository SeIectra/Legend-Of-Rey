"""Bolum 17 - "Ikili Kule". Oynanabilir sahne.

Oda verisi `src/world/rooms/chapter17.py`, gecis `src/systems/duo.py`,
plaka/kapi `src/world/plate.py`, ara sahneler
`src/scenes/chapter17_cinematics.py`.

`docs/yapi.md` B17: *"Ayri yollardan tirmanis, karakter arasi gecis.
Bulmaca: Biri kolu tutar, digeri gecer. Sonra tersi. Camdan/
parmakliktan birbirini gorursunuz ama dokunamazsiniz."*

## Iki `Player`, bir isaretci

`docs/yapi.md` 119 mimariyi zaten soyluyor ve olculdu: dogru.
`self.player`i cevirmek kamerayi, HUD'u, dusman hedeflemesini ve
kaydi birlikte ceviriyor - ikinci bir "aktif oyuncu" kavrami
gerekmedi.

Sahnenin ekledigi tek sey **otekini de surmek**: `PlayScene.update`
yalnizca `self.player`i guncelliyor ve `draw` yalnizca onu ciziyor
(B6/B9/B16 yoldas icin ayni satiri kendi yaziyor).

## Ikisi de ekranda, hep

Kule 26 tile genisliginde = 416 piksel, ic ekran 480. Yani **iki
saft da ayni anda goruluyor** ve kamera yalnizca dikey kayiyor.
Belgenin "birbirinizi gorursunuz ama dokunamazsiniz" cumlesi bir
efektle degil **olculerle** karsilaniyor: bolme gercek duvar, ama
ikisi de kadrajda.

## Pasif olan zarar gormuyor

Dusmanlar `scene.player`i hedefliyor - yani hep aktif olani. Bu bir
eksiklik degil kural: kontrol edemedigin karakter dovulemez. Zaten
bu bolumde dusman yok denecek kadar az (`docs/gdd.md` 11: oyun kendi
dovus dongusunu dort kez bilerek kiriyor ve B17 onlardan biri).
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE
from src.core.input import Action
from src.entities.companion import other_character
from src.entities.player import Player
from src.scenes.play import PlayScene
from src.entities.character_stats import ARDO, REY
from src.systems.duo import DuoState
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.plate import PlateGate, WeightPlate
from src.world.rooms.chapter17 import (
    ALL_STAGES, CHEST_GOLD, DIVIDER, FLOOR_NAMES, FLOOR_ROWS, LEVEL,
    SECRETS_TOTAL, SPAWN_RIGHT, SUMMIT_ROW, TIDY_BONUS, TIDY_SWITCHES,
)
from src.world.tilemap import TileMap

# Aktif karakterin ustundeki isaret - kac gecise kadar gosterilecek.
# `CLAUDE.md` 9 "asamali aciga cikarma": ilk gecislerde yardim,
# sonra ekran temizleniyor.
MARKER_UNTIL_SWITCHES = 6


class Chapter17Scene(PlayScene):
    """Ikili Kule: iki saft, bes kapi, bir isaretci."""

    chapter_number = 17
    chapter_name_key = "chapter.twintower"
    postfx_grade = "descent"
    ambience_preset = "dust"
    music_context = "sad"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")

        # **Iki oynanabilir karakter.** Soldaki oyuncunun sectigi,
        # sagdaki oteki - `docs/gdd.md` 3'un kanonu ("secmedigin taraf")
        # burada da geciyor, ama bu sefer ikisi de oynaniyor.
        self.left = self.make_player(spawn.x, spawn.feet_y)
        self.right_key = other_character(self.character)
        self.right = Player(self, SPAWN_RIGHT[0] * TILE_SIZE + TILE_SIZE * 0.5,
                            (SPAWN_RIGHT[1] + 1) * TILE_SIZE,
                            ARDO if self.right_key == "ardo" else REY)
        self.duo = DuoState(self.left, self.right)
        self.player = self.duo.active
        self.companion = None           # yapay zeka yoldas YOK - ikisi de sen

        # Plakalar ve kapilar. `latching=False`: plakadan inince kapi
        # kapaniyor (Arda 02.09.2026) - "biri kolu TUTAR".
        self.plates: list[WeightPlate] = []
        self.gates: list[PlateGate] = []
        for stage in ALL_STAGES:
            plates = [WeightPlate(tx, ty) for tx, ty in stage["plates"]]
            self.plates.extend(plates)
            self.gates.append(PlateGate(stage["gate_column"],
                                        stage["gate_rows"], plates,
                                        latching=False))

        self.chests = [Chest(spot.x, spot.feet_y, gold=CHEST_GOLD, secret=True)
                       for spot in LEVEL.of("chest")]

        self.floor = ""
        self.frames = 0
        self.entered_floors: set[str] = set()
        self.fired_triggers: set[str] = set()
        self.earned_gold = 0
        self.secret_found = False
        self.finished = False
        self.switch_hinted = False

        self._enter_floor(self._floor_at(self.player.body.center_y))

    # --- Katlar -------------------------------------------------------------
    def _floor_at(self, y: float) -> str:
        """Hangi kattayiz - **satira** bakiyor. B9'un deseni, dondurulmus.

        Yatay bolumlerde oda sutundan turuyor; kulede kat satirdan.
        """
        tile = int(y) // TILE_SIZE
        name = FLOOR_NAMES[0]
        for index, row in enumerate(FLOOR_ROWS):
            if tile <= row:
                name = FLOOR_NAMES[index]
        return name

    def _enter_floor(self, name: str) -> None:
        self.floor = name
        if name in self.entered_floors:
            return
        self.entered_floors.add(name)
        self._narrate_floor(name)

    def _narrate_floor(self, name: str) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        if name == "taban":
            self.say_player("line.ch17_rey_split", "line.ch17_ardo_split")
        elif name == "ucuncu":
            self.say_player("line.ch17_rey_glass", "line.ch17_ardo_glass")
        elif name == "zirve":
            self.say_player("line.ch17_rey_top", "line.ch17_ardo_top")

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1

        # **Otekini de sur.** `PlayScene.update` yalnizca `self.player`i
        # guncelliyor; pasif karakterin yer cekimi, animasyonu ve
        # plakanin ustunde durmasi buna bagli.
        self.duo.other.update()
        self.duo.update()
        self._update_switch()

        floor = self._floor_at(self.player.body.center_y)
        if floor != self.floor:
            self._enter_floor(floor)

        self._update_plates()
        self._update_hints()
        self._update_triggers()
        self._update_chests()
        self._check_exit()

    def _update_switch(self) -> None:
        if not self.game.input.pressed(Action.SWITCH):
            return
        if not self.duo.switch():
            return
        # **Isaretci cevrildi.** `PlayScene`in tamami buradan besleniyor.
        self.player = self.duo.active
        self.game.play_sound("ui_tab")
        # Kamera kesmiyor, kayiyor: mevcut yumusatma 0,45-0,58 saniyede
        # oturtuyor (olculdu) ve kayma iki karakterin AYNI kulede
        # oldugunu gosteriyor. Sert kesme onlari iki ayri yer gibi
        # gosterirdi.

    def _update_plates(self) -> None:
        """Plakalar **iki oyuncuyu da** goruyor, kapilar da.

        `actors` listesi ikisini birden tasiyor - pasif olani disarida
        birakmak bulmacayi imkansiz yapardi: plakada birakilan karakter
        tam olarak pasif olan.
        """
        actors = self.duo.players
        for plate in self.plates:
            plate.update(actors)
        for gate in self.gates:
            gate.update(self.tilemap, actors)

    def _update_hints(self) -> None:
        if self.switch_hinted or self.duo.switches > 0:
            return
        self.switch_hinted = True
        self.hint_once("hint_switch", "hint.switch", Action.SWITCH)

    def _update_triggers(self) -> None:
        for spot in LEVEL.of("trigger"):
            key = f"trigger{spot.tile_x}_{spot.tile_y}"
            if key in self.fired_triggers:
                continue
            if abs(self.player.body.center_x - spot.x) > TILE_SIZE:
                continue
            if abs(self.player.body.center_y - spot.feet_y) > TILE_SIZE * 2:
                continue
            self.fired_triggers.add(key)
            from src.scenes import chapter17_cinematics as cine
            self.scenes.push(cine.HeldDoorCinematic, character=self.character)

    def _update_chests(self) -> None:
        for chest in self.chests:
            chest.update()
            if chest.opened:
                continue
            # **Ikisi de acabiliyor** - sandik sagdaki saftin icinde ve
            # oraya yalnizca sagdaki karakter varabiliyor.
            if not any(chest.rect.colliderect(p.body.rect)
                       for p in self.duo.players):
                continue
            chest.open()
            self.earned_gold += chest.gold
            self.secret_found = True
            self.pickup_juice(gold=True)

    def _check_exit(self) -> None:
        exit_at = LEVEL.first("exit")
        if self.finished or exit_at is None:
            return
        body = self.player.body
        if abs(body.center_x - exit_at.x) > TILE_SIZE:
            return
        if abs(body.feet[1] - exit_at.feet_y) > TILE_SIZE:
            return
        self.finished = True
        self._end_chapter()

    def _end_chapter(self) -> None:
        """Odul **verimlilik**: bulmacayi anlayan az gecisle cikiyor.

        B15 "hic uyandirmadan", B16 "kaldirarak" olcuyordu. Burada
        olcu kac kez karakter degistirdigin - anlayan oyuncu planliyor,
        anlamayan deneme-yanilma yapiyor. Ceza yok, yalnizca odul
        (`docs/ekonomi-uretim.md` zorluk 5).
        """
        self.game.play_sound("chapter_end")
        tidy = self.duo.switches <= TIDY_SWITCHES
        gold = self.earned_gold + (TIDY_BONUS if tidy else 0)
        if tidy:
            self.show_toast(t("chapter17.tidy"), frames=260)
        result = ChapterResult(
            chapter_key="chapter.twintower",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
            ghost=tidy,
            ghost_bonus=TIDY_BONUS,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 17
            data.chapter_name = "chapter.twintower"
            data.playtime_frames += self.frames
            data.secrets_found += result.secrets_found
            if tidy:
                data.flags["ch17_tidy"] = True
        # Bolum 18 henuz yok - ozet ekrani kapaninca ana menuye donuluyor.
        self.scenes.push(ChapterEndScene, result=result)

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.frames)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        self._draw_divider(surface, offset)
        for plate in self.plates:
            plate.draw(surface, offset)
        for chest in self.chests:
            chest.draw(surface, offset)
        # Pasif karakteri de sahne ciziyor - `PlayScene.draw` yalnizca
        # `self.player`i biliyor.
        self.duo.other.draw(surface, offset)
        self._draw_marker(surface, offset)

    def _draw_divider(self, surface: pygame.Surface, offset) -> None:
        """Bolme bir duvar degil bir **parmaklik** gibi okunuyor.

        Tilemap tarafinda gercek `SOLID`: dokunulamiyor. Ama cizimde
        dikey cubuklar ve aralarindan gorunen bosluk var - belgenin
        *"camdan/parmakliktan birbirini gorursunuz ama
        dokunamazsiniz"* cumlesi.

        Zemin karolarinin **ustune** ciziliyor: tilemap orayi tas
        olarak boyuyor, burasi onu parmakliga ceviriyor.
        """
        ox, oy = offset
        top = SUMMIT_ROW - 8
        for column in DIVIDER:
            x = column * TILE_SIZE - ox
            surface.fill(palette.color("ink"),
                         (x, -oy, TILE_SIZE, len(LEVEL.terrain_rows) * TILE_SIZE))
        # Dikey cubuklar - aralarindan arka plan goruluyor.
        for index in range(4):
            x = DIVIDER[0] * TILE_SIZE + 2 + index * 8 - ox
            surface.fill(palette.color("stone_dark"),
                         (x, -oy, 2, len(LEVEL.terrain_rows) * TILE_SIZE))
        # Yatay kusaklar - parmakligi "yapilmis" gosteriyor.
        for row in range(top, len(LEVEL.terrain_rows), 6):
            surface.fill(palette.color("stone"),
                         (DIVIDER[0] * TILE_SIZE - ox,
                          row * TILE_SIZE - oy, TILE_SIZE * 2, 1))

    def _draw_marker(self, surface: pygame.Surface, offset) -> None:
        """Aktif karakterin ustunde kucuk bir isaret.

        Kamera zaten aktif olani takip ediyor ama ilk gecislerde iki
        ayni boyda figur arasinda "hangisi benim" sorusu gercek.
        Birkac gecisten sonra kayboluyor - `CLAUDE.md` 9 asamali aciga
        cikarma.
        """
        if self.duo.switches > MARKER_UNTIL_SWITCHES:
            return
        ox, oy = offset
        body = self.player.body
        x = int(body.center_x) - ox
        y = int(body.top) - oy - 6 + int(math.sin(self.frames * 0.12))
        colour = palette.color("violet_bright")
        for step in range(3):
            surface.fill(colour, (x - step, y + step, 1, 1))
            surface.fill(colour, (x + step, y + step, 1, 1))
