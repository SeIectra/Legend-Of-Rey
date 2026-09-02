"""Bolum 18 - "Son". Oyunun son bolumu.

Boss `src/entities/bosses/caller.py`, susturma
`src/systems/silence.py`, ara sahneler
`src/scenes/chapter18_cinematics.py`, kapanis `src/scenes/ending.py`.

`docs/yapi.md` B18: *"Yaratik, Yanki'yi kullanarak Cemo'nun sesiyle
konusur. Rey sesi susturmayi secer - sessizlikte, yardimsiz savasir."*
`docs/ekonomi-uretim.md`: zorluk **9/10**.

## Finalin tek kurali

    Yanki acikken Cagiran olmuyor.

On sekiz bolumdur Yanki oyuncunun araciydi. Burada onun **dusmani
ayakta tuttugu** ortaya cikiyor: can bitiyor, yaratik diz cokuyor,
sonra kalkiyor. Oyuncu bunu bir kez gorunce sorunun ne oldugunu
anliyor; iki kez gorunce ne yapmasi gerektigini.

Susturmak (`[K]` basili tut) gorusu, hasari ve soru sormayi
goturuyor. Belgenin "yardimsiz" kelimesi bir anlatim degil bir
**oynanis**.

## Bolum sonu, bolum sonu EKRANI degil

Oteki on yedi bolum `ChapterEndScene` acip sayilari gosteriyordu.
Burada acmiyoruz: oyunun son dovusunden cikip bir istatistik paneli
gormek anin butun agirligini alirdi. Sayilar jenerige tasindi
(`ending.py` `credits.path_*`) - orada bir puan degil bir
**hatirlatma** oluyorlar.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE
from src.core.input import Action
from src.entities.bosses.caller import Caller
from src.scenes.play import PlayScene
from src.systems.echo import EchoState
from src.systems.silence import SilenceState
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.rooms.chapter18 import (
    ARENA_SEAL_COLUMN, ARENA_SEAL_ROWS, CALLER_TILE, CEMO_TILE, CLEAN_BONUS,
    CLEAN_RISES, FALSE_CEMO_TILE, LEVEL, ZONE_STARTS,
)
from src.world.tilemap import SOLID, TileMap

# Susturma halkasinin yaricapi (piksel) - oyuncunun ustunde.
RING_RADIUS = 13


class Chapter18Scene(PlayScene):
    """Son: uc bolge, bir yaratik, bir karar."""

    chapter_number = 18
    chapter_name_key = "chapter.end"
    postfx_grade = "descent"
    ambience_preset = "dust"
    music_context = "boss"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        self.companion = None       # Yalniz. Belgenin "yardimsiz"i.

        # Yanki bolum basinda **acik** - ve bu bilincli. Oyuncunun
        # birakacagi seyi once elinde tutmasi lazim.
        self.echo = EchoState()
        self.silence = SilenceState(unlocked=False)

        self.boss: Caller | None = None
        self.arena_sealed = False
        self.boss_defeated = False

        self.zone = ""
        self.frames = 0
        self.entered_zones: set[str] = set()
        self.fired_triggers: set[str] = set()
        self.finished = False
        self.silence_hinted = False
        self.calls = 0

        self._enter_zone(self._zone_at(self.player.body.center_x))

    # --- Bolgeler -----------------------------------------------------------
    def _zone_at(self, x: float) -> str:
        tile = int(x) // TILE_SIZE
        name = ZONE_STARTS[0][0]
        for zone_name, start in ZONE_STARTS:
            if tile >= start:
                name = zone_name
        return name

    def _enter_zone(self, name: str) -> None:
        self.zone = name
        if name in self.entered_zones:
            return
        self.entered_zones.add(name)
        self._narrate_zone(name)

    def _narrate_zone(self, name: str) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        if name == "dip":
            self.say_player("line.ch18_rey_bottom", "line.ch18_ardo_bottom")
        elif name == "ses":
            self.say_player("line.ch18_rey_voice", "line.ch18_ardo_voice")

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        zone = self._zone_at(self.player.body.center_x)
        if zone != self.zone:
            self._enter_zone(zone)

        self._update_silence()
        self._update_triggers()
        self._update_hints()
        self._check_exit()

    def _update_silence(self) -> None:
        """Basili tut, ses gitsin.

        Tus `ECHO`: on sekiz bolumdur Yanki'yi **acan** tus. Onu
        kapatmak icin de ayni tusun kullanilmasi bilincli - oyuncu
        yeni bir sey ogrenmiyor, hep yaptigi seyi son kez yapiyor.
        """
        holding = self.game.input.held(Action.ECHO)
        hurt = self.player.hurt_frames > 0
        if not self.silence.update(self.echo, holding, hurt):
            return
        self.game.play_sound("echo_tier_down")
        self.game.hitstop(10)
        self.particles.burst(self.player.body.center_x,
                             self.player.body.center_y, 24, path="echo")
        self.show_toast(t("chapter18.silenced"), frames=200)

    def _update_hints(self) -> None:
        if self.silence_hinted or not self.silence.unlocked:
            return
        self.silence_hinted = True
        self.hint_once("hint_silence", "hint.silence", Action.ECHO)

    def _update_triggers(self) -> None:
        for spot in LEVEL.of("trigger"):
            key = f"trigger{spot.tile_x}"
            if key in self.fired_triggers:
                continue
            if abs(self.player.body.center_x - spot.x) > TILE_SIZE:
                continue
            self.fired_triggers.add(key)
            self._fire_trigger(spot.tile_x)

    def _fire_trigger(self, tile_x: int) -> None:
        from src.scenes import chapter18_cinematics as cine
        zone = self._zone_at(tile_x * TILE_SIZE)
        if zone == "dip":
            self.scenes.push(cine.DescentCinematic, character=self.character)
        elif zone == "ses":
            self.scenes.push(cine.VoiceCinematic, character=self.character)
        elif zone == "arena":
            self._spawn_boss()
            self._seal_arena()
            self.scenes.push(cine.NameCinematic, character=self.character)

    # --- Boss ---------------------------------------------------------------
    def _spawn_boss(self) -> None:
        if self.boss is not None:
            return
        x = CALLER_TILE[0] * TILE_SIZE + TILE_SIZE * 0.5
        y = (CALLER_TILE[1] + 1) * TILE_SIZE
        self.boss = Caller(self, x, y)
        self.enemies.append(self.boss)

    def _seal_arena(self) -> None:
        """Arena muhurleniyor - B6'dan beri ayni desen."""
        if self.arena_sealed:
            return
        for row in ARENA_SEAL_ROWS:
            self.tilemap.set_tile(ARENA_SEAL_COLUMN, row, SOLID)
        self.arena_sealed = True

    def on_caller_kneel(self, boss) -> None:
        """Diz cokup **kalkacak**. Bu bir hata degil, bolumun tezi.

        Ilk dizde susturma aciliyor: oyuncu sorunu gordu, artik
        cozumu de gorebilir. Daha erken acmak karari anlamsizlastirir
        (neyi biraktigini bilmez), daha gec acmak oyuncuyu bir dongude
        birakirdi.
        """
        self.game.hitstop(12)
        self.game.play_sound("echo_tier_up")
        if not self.silence.unlocked:
            self.silence.unlocked = True
            from src.scenes import chapter18_cinematics as cine
            self.scenes.push(cine.SilenceCinematic, character=self.character)

    def on_caller_rise(self, boss) -> None:
        self.game.play_sound("echo_open")
        self.particles.burst(boss.body.center_x, boss.body.center_y, 18,
                             path="echo")

    def on_caller_call(self, boss) -> None:
        self.calls += 1
        self.camera.linger(20)

    def on_caller_empty_call(self, boss) -> None:
        """Cagiriyor ama kimse duymuyor.

        Sustuktan sonra `call` bos donuyor ve bu **goruluyor**: hamle
        oynuyor, yem cikmiyor. Oyuncunun kazandigi seyin resmi.
        """
        self.particles.burst(boss.body.center_x, boss.body.center_y, 6,
                             path="dust")

    def on_enemy_died(self, enemy) -> None:
        super().on_enemy_died(enemy)
        if enemy is self.boss and not self.boss_defeated:
            self.boss_defeated = True
            self._open_arena()

    def _open_arena(self) -> None:
        from src.world.tilemap import EMPTY
        for row in ARENA_SEAL_ROWS:
            self.tilemap.set_tile(ARENA_SEAL_COLUMN, row, EMPTY)
        self.arena_sealed = False

    # --- Cikis --------------------------------------------------------------
    def _check_exit(self) -> None:
        exit_at = LEVEL.first("exit")
        if self.finished or exit_at is None or not self.boss_defeated:
            return
        if self.player.body.center_x < exit_at.x - 8:
            return
        self.finished = True
        self._end_game()

    def _end_game(self) -> None:
        """Bolum sonu ekrani YOK - dogrudan kapanis.

        Oyunun son dovusunden cikip bir istatistik paneli gormek anin
        agirligini alirdi. Dort bayrak jenerige gidiyor ve orada bir
        puan degil bir hatirlatma oluyor.
        """
        data = self.save_data
        flags = data.flags if data is not None else {}
        if data is not None:
            data.chapter = 18
            data.chapter_name = "chapter.end"
            data.playtime_frames += self.frames
            data.flags["finished"] = True
            if self.silence.done:
                data.flags["ch18_silenced"] = True

        from src.scenes.ending import DawnCinematic
        self.scenes.set_root(
            DawnCinematic,
            character=self.character,
            ghost=bool(flags.get("ch15_ghost")),
            lifted=bool(flags.get("ch16_lifted")),
            gesture_key=str(flags.get("ch16_gesture") or "nod"),
            tidy=bool(flags.get("ch17_tidy")),
            clean=self.boss is not None and self.boss.rises <= CLEAN_RISES,
        )

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.frames)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        self._draw_false_cemo(surface, offset)
        self._draw_cemo(surface, offset)
        self._draw_silence_ring(surface, offset)

    def _draw_false_cemo(self, surface: pygame.Surface, offset) -> None:
        """Bolge 2'deki yalan - **Yanki sustuktan sonra yok.**

        Oyuncu geri donerse orada bir sey olmadigini goruyor. Sahne
        yalan soylemiyor: gosterdigi sey aracin gosterdigi seydi.
        """
        if "ses" not in self.entered_zones or self.silence.done:
            return
        if "trigger44" in self.fired_triggers:
            return
        ox, oy = offset
        x = FALSE_CEMO_TILE[0] * TILE_SIZE - ox
        y = (FALSE_CEMO_TILE[1] + 1) * TILE_SIZE - 30 - oy
        wobble = int(math.sin(self.frames * 0.17) * 1.5)
        body = pygame.Surface((14, 30), pygame.SRCALPHA)
        body.fill((*palette.color("echo"), 150))
        body.fill((*palette.color("echo_bright"), 200), (4, 0, 6, 7))
        surface.blit(body, (x + wobble, y))

    def _draw_cemo(self, surface: pygame.Surface, offset) -> None:
        """**Gercek** Cemo - boss olunce goruluyor.

        Yem gibi titremiyor, yari saydam degil. Fark ilk bakista
        okunuyor ve bu bilincli: oyuncu on sekiz bolumdur bu ani
        bekliyor, "acaba bu da mi yalan" diye sormamali.
        """
        if not self.boss_defeated:
            return
        ox, oy = offset
        x = CEMO_TILE[0] * TILE_SIZE - ox
        y = (CEMO_TILE[1] + 1) * TILE_SIZE - 26 - oy
        surface.fill(palette.color("flesh"), (x + 3, y, 8, 8))
        surface.fill(palette.color("violet_dark"), (x + 2, y + 8, 10, 18))

    def _draw_silence_ring(self, surface: pygame.Surface, offset) -> None:
        """Susturma ilerlemesi - oyuncunun ustunde bir halka.

        `CLAUDE.md` 9: durum HUD cubuguyla degil dunyanin icinde
        anlatilir. B16'nin kaldirma halkasiyla ayni dil - ve bilerek:
        oyuncu bu sekli tanıyor, "basili tut" demek icin ikinci bir
        gorsel dil gerekmiyor.
        """
        if self.silence.done or not self.silence.unlocked:
            return
        progress = self.silence.progress
        if progress <= 0.0:
            return
        ox, oy = offset
        cx = int(self.player.body.center_x) - ox
        cy = int(self.player.body.top) - oy - 12
        filled = max(1, int(round(progress * 20)))
        for step in range(20):
            angle = step / 20 * math.tau - math.tau / 4
            x = cx + int(round(math.cos(angle) * RING_RADIUS))
            y = cy + int(round(math.sin(angle) * RING_RADIUS))
            if step < filled:
                surface.fill(palette.color("violet_bright"),
                             (x - 1, y - 1, 2, 2))
            else:
                surface.fill(palette.role("ui_text_dim"), (x, y, 1, 1))
