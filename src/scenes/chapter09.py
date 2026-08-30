"""Bolum 9 - "Can Kulesi". Oynanabilir sahne. **Ilk dikey bolum.**

Oda verisi `src/world/rooms/chapter09.py`, ara sahne
`src/scenes/chapter09_cinematics.py`.

`docs/yapi.md` B9: *"Dikey bolum. Bulmaca: Rezonans ile uc cani dogru
sirada calmak, sira ipucu duvardaki freskte. Mekanik: Team-up
firlatma - Ardo seni platformlara firlatir."*

## Odalar y'ye gore

Sekiz bolumdur `_room_at(x)` sutuna bakiyordu; burada `_floor_at(y)`
satira bakiyor. Ayni fikir doksan derece donmus - ve donduren sey
bolumun kendisi, bir soyutlama degil.

## Firlatma **etkilesim** tusunda

Yeni bir tus ogretilmiyor: `Action.INTERACT` zaten "dunyayla bir sey
yap" tusu ve Bolum 6/7'de yoldas emri de o. Yoldasin yaninda basinca
firlatiyor, sandigin yaninda basinca sandigi aciyor - ikisi ayni anda
mumkun degil cunku firlatma **ikisinin de yerde ve yakin** olmasini
istiyor.

Ayrica `Action` listesi dolu: standart bir kolun sekiz dugmesi de
kullaniliyor ve ayarlar ekranindaki tus sekmesi 14/14. Yeni bir
aksiyon eklemek oradan bir seyi cikarmak demekti.

## Yoldas kuleyi tirmaniyor

Firlatilan taraf yukari cikiyor, atan taraf asagida kaliyor - ve
`Companion`'in yol bulmasi yok. Bir kat fark olusunca yoldas kisa bir
gecikmeyle oyuncunun yanina geliyor (`CATCHUP_FRAMES`). Alternatifi
yoldasi kalici olarak kaybetmekti; bu bir cozum degil bir hataydi.
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
from src.systems import boost, resonance
from src.systems.boost import BoostState
from src.systems.resonance import ResonanceState
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.resonant import Bell
from src.world.rooms.chapter09 import (
    BELL_ORDER, BELL_TILES, CHEST_GOLD, EXIT_DOOR_COLUMN, EXIT_DOOR_ROWS,
    FLOOR_NAMES, FLOOR_ROWS, FRESCO_TILE, LEVEL, SECRETS_TOTAL,
)
from src.world.tilemap import EMPTY, SOLID, TileMap

# Yoldas oyuncudan bu kadar tile asagida kalirsa yetismesi bekleniyor.
CATCHUP_DISTANCE = TILE_SIZE * 7
# Yetisme gecikmesi - aninda olsaydi isinlanma goze batardi.
CATCHUP_FRAMES = 70


class Chapter09Scene(PlayScene):
    """Can Kulesi: bes kat, uc can, bir firlatma."""

    chapter_number = 9
    chapter_name_key = "chapter.bell_tower"
    postfx_grade = "descent"
    ambience_preset = "dust"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)

        self.companion_key = other_character(self.character)
        self.companion = Companion(self, spawn.x + 26, spawn.feet_y,
                                   self.companion_key)
        self.catchup = 0

        # Rezonans Bolum 8'de ogrenildi - kayittan geliyor.
        self.resonance = ResonanceState(
            unlocked=bool(self.save_data
                          and self.save_data.flags.get("resonance", True)))
        # Firlatma **burada** ogreniliyor.
        self.boost = BoostState(unlocked=False)
        self.taught = False

        self.bells = [Bell(x, y, index=i)
                      for i, (x, y) in enumerate(BELL_TILES)]
        self.rung: list[int] = []       # calinan canlarin sirasi
        self.solved = False

        for row in EXIT_DOOR_ROWS:
            self.tilemap.set_tile(EXIT_DOOR_COLUMN, row, SOLID)
        self.door_open = False

        self.chests = [Chest(spot.x, spot.feet_y, gold=CHEST_GOLD, secret=True)
                       for spot in LEVEL.of("chest")]

        self.floor = ""
        self.floor_frames = 0
        self.frames = 0
        self.entered: set[str] = set()
        self.earned_gold = 0
        self.secret_found = False
        self.finished = False
        self.trust_played = False
        self.wrong_hinted = False

        self._enter_floor(self._floor_at(self.player.body.feet[1]))

    # --- Katlar (y'ye gore) -------------------------------------------------
    def _floor_at(self, y: float) -> str:
        """Verilen yukseklik hangi kat?

        `FLOOR_ROWS` asagidan yukari sirali; oyuncu bir katin zemininin
        **uzerindeyse** o kattadir.
        """
        row = int(y) // TILE_SIZE
        name = FLOOR_NAMES[0]
        for index, floor_row in enumerate(FLOOR_ROWS):
            if row <= floor_row:
                name = FLOOR_NAMES[index]
        return name

    def _enter_floor(self, name: str) -> None:
        self.floor = name
        self.floor_frames = 0
        if name in self.entered:
            return
        self.entered.add(name)
        self._narrate(name)

    def _narrate(self, name: str) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        if name == "taban":
            self.say_player("line.ch09_rey_tower", "line.ch09_ardo_tower")
        elif name == "tepe":
            self.say_player("line.ch09_rey_top", "line.ch09_ardo_top")

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.floor_frames += 1
        floor = self._floor_at(self.player.body.feet[1])
        if floor != self.floor:
            self._enter_floor(floor)

        self._update_boost()
        self._update_catchup()
        self._update_resonance()
        self._update_bells()
        self._update_chests()
        self._check_exit()

        if self.companion is not None:
            self.companion.update()

    # --- Firlatma -----------------------------------------------------------
    def _update_boost(self) -> None:
        self.boost.update()
        if not self.taught and self.floor_frames > 90:
            # Kule goruldu; firlatma aciliyor ve guven sahnesi oynuyor.
            self._teach_boost()
        if not self.boost.unlocked or self.companion is None:
            return
        if not self.game.input.pressed(Action.INTERACT):
            return
        # **Guclu olan Ardo.** Roller karakterden turuyor, sabit degil
        # (`docs/yapi.md` 18: "sen ona basamak olursun").
        strong = self.companion_key == "ardo"
        if self.boost.launch(self.companion, self.player, strong):
            self._on_boost()

    def _teach_boost(self) -> None:
        self.taught = True
        self.boost.unlocked = True
        if not self.trust_played:
            self.trust_played = True
            from src.scenes.chapter09_cinematics import TrustCinematic
            self.scenes.push(TrustCinematic, character=self.character)
        self.hint_once("hint_boost", "hint.boost", Action.INTERACT)

    def _on_boost(self) -> None:
        """Firlatmanin **hissi** - `CLAUDE.md` 7'nin uclu senkronu."""
        x = self.player.body.center_x
        y = self.player.body.feet[1]
        self.juice.explosion(x, y, ImpactWeight.FINISHER)
        self.particles.burst(x, y, 14, path="dust", speed=(0.6, 2.2))
        self.game.play_sound("swing_heavy")
        if self.boost.count == 1:
            self.show_toast(t("chapter09.first_boost"), frames=170)

    def _update_catchup(self) -> None:
        """Yoldas kuleyi tirmaniyor - gerekce modul basliginda."""
        if self.companion is None:
            return
        drop = self.companion.body.feet[1] - self.player.body.feet[1]
        if drop < CATCHUP_DISTANCE or not self.player.body.grounded:
            self.catchup = 0
            return
        self.catchup += 1
        if self.catchup < CATCHUP_FRAMES:
            return
        self.catchup = 0
        x, y = self.free_spot_near(self.player.body.center_x - 22,
                                   self.player.body.feet[1],
                                   self.companion.body)
        self.companion.body.set_feet(x, y)
        self.companion.release()
        self.particles.burst(x, y - 8, 8, path="dust", speed=(0.3, 1.2))

    # --- Rezonans ve canlar -------------------------------------------------
    def _update_resonance(self) -> None:
        self.resonance.update()
        if not self.resonance.unlocked:
            return
        if self.game.input.pressed(Action.RESONATE):
            if self.resonance.pulse(self.player.body.center_x,
                                    self.player.body.center_y):
                rey = self.character != "ardo"
                self.game.play_sound("echo_open" if rey else "swing_light")

    def _update_bells(self) -> None:
        for bell in self.bells:
            bell.update()
            if bell.triggered or self.solved:
                continue
            if self.resonance.reaches(bell):
                self._ring(bell)

    def _ring(self, bell: Bell) -> None:
        bell.strike()
        self.game.play_sound("echo_wall")
        self.particles.burst(bell.rect.centerx, bell.rect.centery, 14,
                             path="spark", speed=(0.5, 2.0))
        self.rung.append(bell.index)

        expected = BELL_ORDER[:len(self.rung)]
        if tuple(self.rung) != expected:
            self._wrong_order()
            return
        if len(self.rung) == len(BELL_ORDER):
            self._solve()

    def _wrong_order(self) -> None:
        """Yanlis sira - **hepsi sifirlaniyor, ceza yok.**

        Bir bulmaca geri alinabilir olmali. Ceza (can, altin, geri
        gonderme) koymak oyuncuyu denemekten alikoyar ve bu bulmacanin
        cozumu zaten denemekten geciyor: fresk sirayi soyluyor ama
        canlar farkli katlarda, yani oyuncu once haritayi ogreniyor.
        """
        self.rung.clear()
        for bell in self.bells:
            bell.reset()
        self.game.play_sound("ui_deny")
        if not self.wrong_hinted:
            self.wrong_hinted = True
            self.show_toast(t("chapter09.wrong_order"), frames=200)

    def _solve(self) -> None:
        self.solved = True
        self.door_open = True
        for row in EXIT_DOOR_ROWS:
            self.tilemap.set_tile(EXIT_DOOR_COLUMN, row, EMPTY)
        self.game.play_sound("rift_open")
        self.show_toast(t("chapter09.solved"), frames=220)
        self.game.music.hold("echo", 420)

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
        if self.finished or exit_at is None or not self.solved:
            return
        if self.player.body.center_x < exit_at.x - 8:
            return
        if abs(self.player.body.feet[1] - exit_at.feet_y) > TILE_SIZE * 2:
            return
        self.finished = True
        self._end_chapter()

    def _end_chapter(self) -> None:
        self.game.play_sound("chapter_end")
        result = ChapterResult(
            chapter_key="chapter.bell_tower",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 9
            data.chapter_name = "chapter.bell_tower"
            data.playtime_frames += self.frames
            data.secrets_found += result.secrets_found
            data.flags["boost"] = True
        # Bolum 10'a baglaniyor.
        character = self.character

        def _continue() -> None:
            from src.scenes.chapter10 import Chapter10Scene
            self.scenes.set_root(Chapter10Scene, character=character)

        self.scenes.push(ChapterEndScene, result=result,
                         on_continue=_continue)

    # --- Kancalar -----------------------------------------------------------
    def after_restart(self, room: str) -> None:
        if self.save_data is not None and self.save_data.flags.get("boost"):
            self.boost.unlocked = True
            self.taught = True
            self.trust_played = True
        if self.companion is not None:
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
        self._draw_fresco(surface, offset)
        for bell in self.bells:
            bell.draw(surface, offset)
        self._draw_door(surface, offset)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)
        if self.companion is not None:
            self.companion.draw(surface, offset)
        self._draw_pulse(surface, offset)
        self._draw_boost_prompt(surface, offset)

    def _draw_fresco(self, surface: pygame.Surface, offset) -> None:
        """Duvardaki fresk - **sira burada yaziyor.**

        Rakam degil **sekil**: canlarin konumu (sol/sag) ve sirasi
        uc kucuk figurle anlatiliyor. `CLAUDE.md` 10: bilgi yalnizca
        renkle degil sekille de verilmeli, ve bir rakam okumak icin
        oyuncunun dili bilmesi gerekirdi.
        """
        ox, oy = offset
        x = FRESCO_TILE[0] * TILE_SIZE - ox
        y = FRESCO_TILE[1] * TILE_SIZE - oy
        surface.fill(palette.color("stone_darkest"), (x - 2, y - 2, 30, 24))
        surface.fill(palette.color("stone_dark"), (x - 1, y - 1, 28, 22))
        for step, bell_index in enumerate(BELL_ORDER):
            bell_x, _ = BELL_TILES[bell_index]
            # Sol taraftaki can sola, sagdaki saga ciziliyor - fresk
            # kulenin haritasi.
            side = 3 if bell_x < 13 else 17
            top = y + 2 + step * 6
            done = step < len(self.rung)
            tone = "gold" if done else "ember"
            surface.fill(palette.color(tone), (x + side, top, 6, 4))
            surface.fill(palette.color("ink"), (x + side + 2, top + 4, 2, 1))

    def _draw_door(self, surface: pygame.Surface, offset) -> None:
        if self.door_open:
            return
        ox, oy = offset
        x = EXIT_DOOR_COLUMN * TILE_SIZE - ox
        top = EXIT_DOOR_ROWS.start * TILE_SIZE - oy
        height = len(EXIT_DOOR_ROWS) * TILE_SIZE
        surface.fill(palette.color("stone_dark"), (x, top, TILE_SIZE, height))
        breath = 0.6 + 0.4 * math.sin(self.frames * 0.05)
        colour = tuple(int(c * breath) for c in palette.color("gold"))
        cy = top + height // 2
        for index, _ in enumerate(BELL_ORDER):
            lit = index < len(self.rung)
            surface.fill(colour if lit else palette.color("stone_darkest"),
                         (x + 5, cy - 6 + index * 5, 6, 3))

    def _draw_pulse(self, surface: pygame.Surface, offset) -> None:
        if not self.resonance.active:
            return
        ox, oy = offset
        cx = int(self.resonance.x) - ox
        cy = int(self.resonance.y) - oy
        radius = self.resonance.radius
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

    def _draw_boost_prompt(self, surface: pygame.Surface, offset) -> None:
        """Firlatma hazirken iki figurun arasinda yukari ok.

        Diegetik: bir tus adi degil bir **yon**. Oyuncu neyin
        olacagini goruyor.
        """
        if self.companion is None or not self.boost.ready(self.companion,
                                                          self.player):
            return
        ox, oy = offset
        mid = int((self.player.body.center_x
                   + self.companion.body.center_x) * 0.5) - ox
        top = int(min(self.player.body.y, self.companion.body.y)) - oy - 12
        lift = int(math.sin(self.frames * 0.14) * 2)
        colour = palette.color("gold")
        surface.fill(colour, (mid - 1, top + lift, 3, 6))
        surface.fill(colour, (mid - 3, top + lift + 2, 7, 1))
        surface.fill(colour, (mid - 2, top + lift + 1, 5, 1))

    def debug_lines(self) -> list[str]:
        return [f"kat {self.floor}  can {self.rung}/{list(BELL_ORDER)}"
                f"  firlatma={self.boost.unlocked} ({self.boost.count})"]
