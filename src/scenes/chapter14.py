"""Bolum 14 - "Yanki'nin Kaynagi". Oynanabilir sahne.

Oda verisi `src/world/rooms/chapter14.py`, ara sahneler
`src/scenes/chapter14_cinematics.py`, BOSS 3
`src/entities/bosses/source.py`.

`docs/yapi.md` B14: *"Rey anlar: Yanki lanet degil, asagidaki seyin
sesi. Hep yardim ediyordu cunku onu cagiriyordu."*
*Mekanik:* **Yanki tersine doner - actiginda dusmanlar da seni gorur.**

## Bolumun isi bir REFLEKSI kirmak

On uc bolumdur oyuncunun eli bu tusa gidiyor: emin degilsen Yanki'yi
ac. Oda 1-2 bunu **son kez** dogruluyor. Ara sahneden sonra ayni tus
odanin tamamini uyandiriyor.

Once son kez ogretip sonra kirmak, bastan kirmaktan cok daha etkili:
refleksin taze olmasi gerek ki ihanet hissedilsin.

## Ihanet burada YASAMIYOR

Bayrak `SaveData.flags["sense_betrayed"]`e yaziliyor ve mekanizma
`PlayScene._update_betrayal`de. Yani B15-B18 hicbir sey yazmadan
devraliyor - ve bu bolum de kendi kurdugu seyi kendi tasimiyor.
"Her bolum bir satir eklemek zorunda" bu projede uc kez hatanin
sekli oldu (kilic verme, boss bari, yetenek geri yukleme).
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE
from src.core.juice import ImpactWeight
from src.scenes.play import PlayScene
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.rooms.chapter14 import (
    BETRAYAL_ROOM, CHEST_GOLD, FLOOR_TOP, LEVEL, ROOM_STARTS, SECRETS_TOTAL,
)
from src.world.tilemap import EMPTY, SOLID, TileMap

ENEMY_CLASSES = {
    "shambler": "src.entities.enemies.shambler:Shambler",
    "silent": "src.entities.enemies.silent:Silent",
    "echoing": "src.entities.enemies.echoing:Echoing",
    "splitter": "src.entities.enemies.splitter:Splitter",
}

ARENA_SEAL_ROWS = range(3, FLOOR_TOP)


def _load(path: str):
    module_name, class_name = path.split(":")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


class Chapter14Scene(PlayScene):
    """Kaynak: alti oda, uc ihanet, bir donus."""

    chapter_number = 14
    chapter_name_key = "chapter.source"
    postfx_grade = "descent"
    ambience_preset = "dust"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        self.companion = None           # Bolum 10'dan beri yalniz

        self.chests = [Chest(spot.x, spot.feet_y, gold=CHEST_GOLD, secret=True)
                       for spot in LEVEL.of("chest")]

        self.boss = None
        self.arena_sealed = False
        self.boss_defeated = False
        self.exit_open = False

        self.room = ""
        self.room_frames = 0
        self.frames = 0
        self.entered_rooms: set[str] = set()
        self.fired_triggers: set[str] = set()
        self.earned_gold = 0
        self.secret_found = False
        self.finished = False
        self.silent_hinted = False
        self.betrayal_shown = False
        # Kac kez duyu yuzunden ele verildi - anlatim degil, olcum.
        self.betrayal_wakes = 0

        self._enter_room(self._room_at(self.player.body.center_x))

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
        if name == "arena" and self.boss is None:
            self._spawn_boss()

    def _narrate_room(self, name: str) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        if name == "sessiz":
            self.say_player("line.ch14_rey_empty", "line.ch14_ardo_empty")
        elif name == "ters":
            self.say_player("line.ch14_rey_turned", "line.ch14_ardo_turned")
        elif name == "bolunen":
            self.say_player("line.ch14_rey_split", "line.ch14_ardo_split")

    def _spawn_boss(self) -> None:
        from src.entities.bosses.source import Source
        spot = LEVEL.first("source")
        if spot is None:
            return
        self.boss = Source(self, spot.x, spot.feet_y)
        self.enemies.append(self.boss)

    def after_restart(self, room: str) -> None:
        """Arenada olduysak boss ve muhur geri gelmeli (`DEVIR.md` B6)."""
        if room != "arena":
            return
        if self.boss is None:
            self._spawn_boss()
        self._seal_arena()

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.room_frames += 1
        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        self._update_silent_hint()
        self._update_triggers()
        self._update_arena()
        self._update_chests()
        self._check_exit()

    def _update_silent_hint(self) -> None:
        """Sessiz'e vurulunca kurali **bir kez** soyle.

        Ders zaten "gormedigin bir sey seni vurdu" ile veriliyor; yazi
        yalnizca oyuncunun "oyun mu bozuk" diye dusunmesini onluyor.
        Ayni gerekce Bolum 11'in golge yaratigi ipucunda da yazili.
        """
        if self.silent_hinted or not self.has_echo:
            return
        for enemy in self.enemies:
            if type(enemy).__name__ != "Silent" or not enemy.aware:
                continue
            self.silent_hinted = True
            self.show_toast(t("chapter14.silent"), frames=220)
            return

    # --- Donus noktasi ------------------------------------------------------
    def _begin_betrayal(self) -> None:
        """Ara sahne bitti - **sozlesme degisti.**

        Bayrak kayda yaziliyor, mekanizma `PlayScene`de. Bu satir
        bolumun tek isi; gerisi zaten hazir ve B15-B18 bedavaya
        devraliyor.
        """
        self.sense_betrayed = True
        data = self.save_data
        if data is not None:
            data.flags["sense_betrayed"] = True
        self.show_toast(t("chapter14.betrayed"), frames=260)

    def on_betrayal_wake(self, enemy) -> None:
        """Duyu yuzunden bir dusman uyandi - **gorunur olmali.**

        Yeni kural sessizce isleseydi oyuncu neden aniden kalabalik
        oldugunu anlamazdi; kurallar ogretilir. Ilk seferde bir de
        yazi cikiyor, sonrasinda yalnizca parcacik ve ses - ogut
        tekrarlanmaz.
        """
        self.betrayal_wakes += 1
        self.particles.burst(enemy.body.center_x, enemy.body.center_y - 8, 10,
                             path="echo", speed=(0.4, 1.6))
        if not self.betrayal_shown:
            self.betrayal_shown = True
            self.show_toast(t("chapter14.heard"), frames=200)
            self.game.play_sound("echo_reveal")

    # --- Arena ---------------------------------------------------------------
    def _update_arena(self) -> None:
        if self.boss is None or self.boss_defeated:
            return
        if not self.arena_sealed and self.room == "arena":
            start, _ = self._room_span("arena")
            if self.player.body.center_x > (start + 4) * TILE_SIZE:
                self._seal_arena()
        if self.boss.dead:
            self._on_boss_defeated()

    def _seal_arena(self) -> None:
        start, _ = self._room_span("arena")
        for row in ARENA_SEAL_ROWS:
            self.tilemap.set_tile(start + 3, row, SOLID)
        self.arena_sealed = True
        self.game.play_sound("rift_close")

    def _on_boss_defeated(self) -> None:
        """Boss dustu - ama **olmedi.**

        `docs/yapi.md` B18: *"Yaratik, Yanki'yi kullanarak Cemo'nun
        sesiyle konusur."* Yani bu sey final bolumunde geri geliyor.
        Burada yenilen bir suret; kaynak asagida.

        Bu ayrim bolumun sonunu bir zafer degil bir **bilgi** yapiyor,
        ve B15'in ("Yanki'yi kapali oyna") sebebi oluyor.
        """
        self.boss_defeated = True
        start, _ = self._room_span("arena")
        for row in ARENA_SEAL_ROWS:
            self.tilemap.set_tile(start + 3, row, EMPTY)
        self.exit_open = True
        self.juice.explosion(self.boss.body.center_x, self.boss.body.center_y,
                             ImpactWeight.FINISHER)
        self.show_toast(t("chapter14.not_dead"), frames=240)
        from src.scenes import chapter14_cinematics as cine
        self.scenes.push(cine.AfterCinematic, character=self.character)

    # --- Tetikleyiciler ------------------------------------------------------
    def _update_triggers(self) -> None:
        for spot in LEVEL.of("trigger"):
            key = f"trigger{spot.tile_x}"
            if key in self.fired_triggers:
                continue
            if abs(self.player.body.center_x - spot.x) > TILE_SIZE:
                continue
            self.fired_triggers.add(key)
            self._fire_trigger(self._room_at(spot.x))

    def _fire_trigger(self, room: str) -> None:
        from src.scenes import chapter14_cinematics as cine
        if room == "sessiz":
            # ★ Donus noktasi. Sahne kapaninca sozlesme degisiyor.
            self.scenes.push(cine.SourceCinematic, character=self.character,
                             on_done=self._begin_betrayal)
        elif room == "bolunen":
            self.scenes.push(cine.ArenaCinematic, character=self.character)

    # --- Sandik ve cikis -----------------------------------------------------
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
        if self.finished or exit_at is None or not self.exit_open:
            return
        if self.player.body.center_x < exit_at.x - 8:
            return
        self.finished = True
        self._end_chapter()

    def _end_chapter(self) -> None:
        self.game.play_sound("chapter_end")
        result = ChapterResult(
            chapter_key="chapter.source",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 14
            data.chapter_name = "chapter.source"
            data.playtime_frames += self.frames
            data.best_combo = max(data.best_combo, self.player.combo.best)
            data.secrets_found += result.secrets_found
        # Bolum 15 henuz yok - ozet ekrani kapaninca ana menuye donuluyor.
        self.scenes.push(ChapterEndScene, result=result)

    # --- Cizim ---------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        """Cerceve **en uste** ciziliyor - `draw_foreground`a degil.

        Ilk surumde on planda ciziliyordu ve Yanki'nin kendi
        karartmasi (`echo_view.draw_dim`) onu yutuyordu: ekran
        goruntusunde cerceve zar zor secilebiliyordu. Oysa anlatmak
        istedigi sey karartmanin **tersi** - o "sen goruyorsun"
        diyor, bu "sen goruluyorsun".

        Iki bedelin ust uste binmemesi icin sira da onemli: karartma
        once (dunyaya ait), cerceve sonra (oyuncuya ait).
        """
        if self.sense_betrayed and self.sense_open():
            self._draw_listening(surface)

    def _draw_listening(self, surface: pygame.Surface) -> None:
        """Duyu acikken ekranin kenarindan iceri **dinleyen** bir nabiz.

        Rengi Yanki'nin camgobegi degil **tehlike**: on uc bolumdur
        mor/camgobegi "yardim" demekti. Ayni renkte cizseydik yeni
        kural eski dilin icinde kaybolurdu.
        """
        width, height = surface.get_size()
        pulse = 0.5 + 0.5 * math.sin(self.frames * 0.12)
        thickness = 2 + int(3 * pulse)
        colour = tuple(int(c * (0.55 + 0.45 * pulse))
                       for c in palette.color("danger_bright"))
        surface.fill(colour, (0, 0, width, thickness))
        surface.fill(colour, (0, height - thickness, width, thickness))
        surface.fill(colour, (0, 0, thickness, height))
        surface.fill(colour, (width - thickness, 0, thickness, height))

    def debug_lines(self) -> list[str]:
        return [f"oda {self.room}  ihanet={self.sense_betrayed}"
                f"  uyanan {self.betrayal_wakes}  muhur={self.arena_sealed}"]
