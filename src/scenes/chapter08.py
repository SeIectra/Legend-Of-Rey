"""Bolum 8 - "Ates Basi". Oynanabilir sahne. **Nefes bolumu.**

Oda verisi `src/world/rooms/chapter08.py`, ara sahneler
`src/scenes/chapter08_cinematics.py`.

`docs/yapi.md` B8: *"Dovus yok. Ates, iki siluet. Rey kolyeyi cevirir,
Ardo omzundaki yarayi sarar, Rey uzanir. Mekanik: Yanki Rezonansi
burada ogrenilir - Ardo ona sesi silah olarak kullanmayi gosterir.
Yanki ilk kez Ardo hakkinda fisildar, Rey rahatsiz olur."*

## Sifir dovus

`docs/yapi.md` 114: *"Nefes bolumleri (B4, B8, B12) sifir dovus kodu
ister."* Bu dosyada `ENEMY_CLASSES` yok, `_spawn_room` yok, saldiri
hakki yok. Yedi bolumdur dovusen oyuncu burada duruyor.

`docs/gdd.md` 41: nefes bolumleri **Yanki kademesini geri veriyor**.
Olumle kaybedilen kademe burada tamir ediliyor - ceza kalici degil.

## Rezonans burada ogreniliyor

Oda 2 ogretiyor (kristali kirmasan da gecersin), Oda 3 siniyor
(kirmadan gecemezsin). `docs/gdd.md` 9: once ogret, sonra sina.

Odanin ikinci yarisi mekanigin asil noktasi: mandal duvarin ardinda,
oraya **yuruyemiyorsun**. Elle yapilabilen bir sey icin sese gerek
olmazdi.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE
from src.core.input import Action
from src.core.juice import ImpactWeight
from src.entities.companion import Companion, other_character
from src.scenes.play import PlayScene
from src.systems import resonance
from src.systems.resonance import ResonanceState
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.resonant import Crystal, Latch
from src.world.rooms.chapter08 import (
    CHEST_GOLD, FIRE_TILE, GATE_CRYSTAL_HEIGHT, GATE_CRYSTAL_TILE,
    LATCH_DOOR_ROWS, LATCH_DOOR_TILE, LATCH_TILE_ABS, LEVEL, ROOM_STARTS,
    SECRETS_TOTAL, TEACH_CRYSTAL_TILE,
)
from src.world.tilemap import EMPTY, SOLID, TileMap

# Ates isiginin yaricapi ve nabzi.
FIRE_RADIUS = 46


class Chapter08Scene(PlayScene):
    """Ates Basi: dort oda, sifir dusman, bir yeni mekanik."""

    chapter_number = 8
    chapter_name_key = "chapter.fireside"
    postfx_grade = "descent"
    ambience_preset = "dust"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)

        self.companion_key = other_character(self.character)
        self.companion = Companion(self, spawn.x + 30, spawn.feet_y,
                                   self.companion_key)
        # Ates basinda oturuyorlar - yoldas oyuncuyu takip etmiyor,
        # atesin yaninda bekliyor. Sahne bitince birakiliyor.
        self.companion.hold(float(FIRE_TILE[0] * TILE_SIZE))

        # --- Rezonans ---------------------------------------------------
        # Kilitli basliyor: ara sahne acıyor. Oyuncu mekanigi
        # ogrenmeden once tusa basarsa hicbir sey olmamali - "bozuk mu?"
        # sorusu yerine "henuz yok" cevabi.
        self.resonance = ResonanceState(unlocked=False)
        self.taught = False

        self.crystals = [
            Crystal(*TEACH_CRYSTAL_TILE, height=2),
            Crystal(GATE_CRYSTAL_TILE[0], GATE_CRYSTAL_TILE[1],
                    height=GATE_CRYSTAL_HEIGHT),
        ]
        self.teach_crystal, self.gate_crystal = self.crystals
        self.latch = Latch(*LATCH_TILE_ABS)

        # Gecidi kapatan kristal tilemap'te de KATI - yoksa oyuncu
        # icinden gecerdi ve engel bir resim olurdu.
        self._set_crystal_solid(self.gate_crystal, True)
        for row in LATCH_DOOR_ROWS:
            self.tilemap.set_tile(LATCH_DOOR_TILE, row, SOLID)
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
        self.fireside_played = False
        self.whisper_played = False
        self.hinted = False

        self._enter_room(self._room_at(self.player.body.center_x))

    def _set_crystal_solid(self, crystal: Crystal, solid: bool) -> None:
        column = crystal.rect.x // TILE_SIZE
        state = SOLID if solid else EMPTY
        for row in range(crystal.rect.y // TILE_SIZE,
                         crystal.rect.bottom // TILE_SIZE):
            self.tilemap.set_tile(column, row, state)

    # --- Odalar -------------------------------------------------------------
    def _room_at(self, x: float) -> str:
        tile = int(x) // TILE_SIZE
        name = ROOM_STARTS[0][0]
        for room_name, start in ROOM_STARTS:
            if tile >= start:
                name = room_name
        return name

    def _enter_room(self, name: str) -> None:
        self.room = name
        self.room_frames = 0
        if name in self.entered_rooms:
            return
        self.entered_rooms.add(name)
        self._narrate_room(name)

    def _narrate_room(self, name: str) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        if name == "ogrenme":
            self.say_player("line.ch08_rey_learn", "line.ch08_ardo_learn")
        elif name == "gecit":
            self.say_player("line.ch08_rey_gate", "line.ch08_ardo_gate")

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.room_frames += 1
        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        self._update_fireside()
        self._update_resonance()
        self._update_crystals()
        self._update_chests()
        self._update_whisper()
        self._check_exit()

        if self.companion is not None:
            self.companion.update()

    # --- Ara sahne 1: Ates Basi ---------------------------------------------
    def _update_fireside(self) -> None:
        """Oyuncu atesin yanina varinca ★ sahne aciliyor."""
        if self.fireside_played:
            return
        fire_x = FIRE_TILE[0] * TILE_SIZE
        if abs(self.player.body.center_x - fire_x) > TILE_SIZE * 2:
            return
        self.fireside_played = True
        from src.scenes.chapter08_cinematics import FiresideCinematic
        self.scenes.push(FiresideCinematic, character=self.character)
        self._learn_resonance()

    def _learn_resonance(self) -> None:
        """Rezonans aciliyor + Yanki kademesi geri geliyor.

        `docs/gdd.md` 41: *"Kademe kazanimi: kontrol noktalari ve nefes
        bolumleri (B4, B8, B12)."* Olumle kaybedilen kademe burada
        tamir ediliyor - ceza kalici degil, bir sarmal degil.
        """
        self.resonance.unlocked = True
        self.taught = True
        if self.echo is not None:
            self.echo.restore()
        if self.save_data is not None:
            self.save_data.flags["resonance"] = True
        # Yoldas artik takip ediyor - ates basi bitti.
        if self.companion is not None:
            self.companion.release()

    # --- Rezonans -----------------------------------------------------------
    def _update_resonance(self) -> None:
        self.resonance.update()
        if not self.resonance.unlocked:
            return
        if self.game.input.pressed(Action.RESONATE):
            if self.resonance.pulse(self.player.body.center_x,
                                    self.player.body.center_y):
                self._on_pulse()

        if (not self.hinted and self.taught
                and self.resonance.pulses == 0
                and self.room_frames > resonance.HINT_FRAMES):
            self.hinted = True
            self.hint_once("hint_resonance", "hint.resonance",
                           Action.RESONATE)

    def _on_pulse(self) -> None:
        """Darbe cikti - ses **oyuncudan** cikiyor, gorulsun ve duyulsun.

        Rey sesiyle, Ardo kiliciyla taşa vurarak: ayni mekanik, iki
        gerekce (`resonance.py` modul basligi). Fark burada sese ve
        renge yansiyor.
        """
        rey = self.character != "ardo"
        self.game.play_sound("echo_open" if rey else "swing_light")
        self.particles.burst(self.player.body.center_x,
                             self.player.body.center_y, 8,
                             path="echo" if rey else "spark",
                             speed=(0.3, 1.1))

    def _update_crystals(self) -> None:
        for crystal in self.crystals:
            crystal.update()
            if crystal.triggered:
                continue
            if self.resonance.reaches(crystal):
                self._shatter(crystal)

        self.latch.update()
        if not self.latch.triggered and self.resonance.reaches(self.latch):
            self._open_latch()

    def _shatter(self, crystal: Crystal) -> None:
        crystal.strike()
        self._set_crystal_solid(crystal, False)
        self.juice.explosion(crystal.rect.centerx, crystal.rect.centery,
                             ImpactWeight.FINISHER)
        self.particles.burst(crystal.rect.centerx, crystal.rect.centery,
                             18, path="echo", speed=(0.8, 2.6))
        self.game.play_sound("wall_break")
        if crystal is self.teach_crystal:
            self.show_toast(t("chapter08.first_crystal"), frames=190)

    def _open_latch(self) -> None:
        self.latch.strike()
        self.door_open = True
        for row in LATCH_DOOR_ROWS:
            self.tilemap.set_tile(LATCH_DOOR_TILE, row, EMPTY)
        self.game.play_sound("rift_open")
        self.show_toast(t("chapter08.latch"), frames=190)

    # --- Ara sahne 3: Yanki'nin fisiltisi ------------------------------------
    def _update_whisper(self) -> None:
        """Bolum sonunda Yanki **ilk kez Ardo hakkinda** konusuyor.

        `docs/gdd.md` 134: *"Yanki ilk kez Ardo hakkinda konusur."*
        Bolum 6'nin sessizligi (o modulde korunan satir) tam olarak
        buraya kadardi.
        """
        if self.whisper_played or self.room != "cikis":
            return
        self.whisper_played = True
        from src.scenes.chapter08_cinematics import WhisperCinematic
        self.scenes.push(WhisperCinematic, character=self.character)

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
            self.pickup_juice()

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
            chapter_key="chapter.fireside",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 8
            data.chapter_name = "chapter.fireside"
            data.playtime_frames += self.frames
            data.secrets_found += result.secrets_found
        # Bolum 9 henuz yok - ozet ekrani kapaninca ana menuye donuluyor.
        self.scenes.push(ChapterEndScene, result=result)

    # --- Kancalar -----------------------------------------------------------
    def after_restart(self, room: str) -> None:
        """Nefes bolumunde olmek neredeyse imkansiz (dusman yok) ama
        cukura dusmek mumkun. Rezonans ogrenildiyse **kayitli** kaliyor."""
        if self.save_data is not None and self.save_data.flags.get("resonance"):
            self.resonance.unlocked = True
            self.taught = True
            self.fireside_played = True
        if self.companion is not None and room != "ates":
            x, y = self.free_spot_near(self.player.body.center_x - 22,
                                       self.player.body.feet[1],
                                       self.companion.body)
            self.companion.body.set_feet(x, y)
            self.companion.release()

    def on_companion_attack(self, companion) -> None:
        self.game.play_sound("swing_light")

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        self._draw_fire(surface, offset)
        for crystal in self.crystals:
            crystal.draw(surface, offset)
        self.latch.draw(surface, offset)
        self._draw_door(surface, offset)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)
        if self.companion is not None:
            self.companion.draw(surface, offset)
        self._draw_pulse(surface, offset)

    def _draw_fire(self, surface: pygame.Surface, offset) -> None:
        """Kamp atesi - bolumun adi ve tek isik kaynagi."""
        ox, oy = offset
        x = FIRE_TILE[0] * TILE_SIZE - ox
        y = FIRE_TILE[1] * TILE_SIZE - oy
        surface.fill(palette.color("earth_dark"), (x - 4, y + 10, 16, 3))
        flicker = 0.7 + 0.3 * math.sin(self.game.frame * 0.21)
        for index in range(5):
            height = int((5 - abs(index - 2)) * 2 * flicker)
            tone = "gold" if index == 2 else "ember_light"
            surface.fill(palette.color(tone),
                         (x + index * 2, y + 10 - height, 2, height))

    def _draw_door(self, surface: pygame.Surface, offset) -> None:
        if self.door_open:
            return
        ox, oy = offset
        x = LATCH_DOOR_TILE * TILE_SIZE - ox
        top = LATCH_DOOR_ROWS.start * TILE_SIZE - oy
        height = len(LATCH_DOOR_ROWS) * TILE_SIZE
        surface.fill(palette.color("stone_dark"), (x, top, TILE_SIZE, height))
        surface.fill(palette.color("stone_darkest"), (x, top, 1, height))

    def _draw_pulse(self, surface: pygame.Surface, offset) -> None:
        """Genisleyen ses halkasi.

        Dolu bir daire degil **halka**: sesin bir cephesi var ve
        ilerliyor. Dolu cizilseydi bir patlama gibi okunurdu ve
        gecikmenin (nesne ses varinca kiriliyor) sebebi gorunmezdi.
        """
        if not self.resonance.active:
            return
        ox, oy = offset
        cx = int(self.resonance.x) - ox
        cy = int(self.resonance.y) - oy
        radius = self.resonance.radius
        # Sonuna dogru soluyor - ses uzaklastikca zayifliyor.
        fade = max(0.0, 1.0 - self.resonance.progress)
        base = palette.color("echo_bright" if self.character != "ardo"
                             else "ember_light")
        colour = tuple(int(c * (0.35 + 0.65 * fade)) for c in base)
        steps = max(12, int(radius * 0.5))
        for index in range(steps):
            angle = index * math.tau / steps
            x = cx + int(round(math.cos(angle) * radius))
            y = cy + int(round(math.sin(angle) * radius * 0.82))
            surface.fill(colour, (x, y, 2, 2))

    def debug_lines(self) -> list[str]:
        return [f"oda {self.room}  rezonans={self.resonance.unlocked}"
                f" darbe={self.resonance.pulses}"
                f"  kapi={'acik' if self.door_open else 'kapali'}"]
