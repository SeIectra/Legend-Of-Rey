"""Bolum 13 - "Cemo". Oynanabilir sahne.

Oda verisi `src/world/rooms/chapter13.py`, ara sahneler
`src/scenes/chapter13_cinematics.py`, mekanik
`src/systems/timegate.py`, BOSS 2 `src/entities/bosses/gaoler.py`.

`docs/yapi.md` B13: *"Cemo. Kafeste, canli, sana bakiyor - **ulasamadan
tasinir.** Mekanik: Zaman kapilari - kovalamaca bolumu."*

## Bolumun tek cumlesi: DURMA

On iki bolum boyunca "odayi temizle, sonra gec" dogru cevapti. Burada
kol cevriliyor, surgu inmeye basliyor ve yoldaki her dusman **zaman**
demek. Odalara konan iki dusman bu yuzden Okcu ve Komutan: ikisi de
"once beni hallet" diye bagiran dusmanlar, ve ikisinin de dogru cevabi
burada hayir.

Katman 2 (B7-B13) bu bolumde bitiyor. Dort muhafizin dordu de burada:
Okcu ve Komutan odalarda, Mizrakli Oda 6'da, Kalkanli ise Zindanci'nin
ilk fazinda bir hamle olarak.

## Karanlik yalnizca ARENADA

`art/lighting.render` her karede tam ekran bir maske uretiyor. Butun
bolume uygulamak hem pahali hem yanlis olurdu: kovalamaca odalarinin
sorusu gorunurluk degil **zaman**. Karanlik boss arenasina ait, cunku
orada bir sorusu var (fener).
"""
from __future__ import annotations

import math

import pygame

from src.art import lighting, palette
from src.config import (
    LEVER_REACH, NECKLACE_LIGHT_RADIUS, TILE_SIZE,
    TIMEGATE_EJECT_PUSH, TIMEGATE_FRAMES,
    TIMEGATE_CHAIN_FRAMES, TIMEGATE_TEACH_FRAMES,
)
from src.core.input import Action
from src.core.juice import ImpactWeight
from src.entities.enemies.extinguished_one import Brazier
from src.scenes.play import PlayScene
from src.systems.light import LightState
from src.systems.timegate import GateBank, Lever, TimeGate
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.rooms.chapter13 import (
    CHEST_GOLD, FLOOR_TOP, GATE_TOP, LEVEL, ROOM_STARTS, SECRETS_TOTAL,
)
from src.world.tilemap import EMPTY, SOLID, TileMap

ENEMY_CLASSES = {
    "shambler": "src.entities.enemies.shambler:Shambler",
    "archer": "src.entities.enemies.archer:Archer",
    "commander": "src.entities.enemies.commander:Commander",
    "spearman": "src.entities.enemies.spearman:Spearman",
}

# Oda basina surgu suresi. Ogretme comert, zirve dar.
GATE_FRAMES = {
    "kol": TIMEGATE_TEACH_FRAMES,
    "okcu": TIMEGATE_FRAMES,
    "komutan": TIMEGATE_FRAMES,
    "cifte": TIMEGATE_CHAIN_FRAMES,
}

# Arena muhru - boss odasinin girisi.
ARENA_SEAL_ROWS = range(3, FLOOR_TOP)


def _load(path: str):
    module_name, class_name = path.split(":")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


class Chapter13Scene(PlayScene):
    """Cemo: yedi oda, bes surgu, bir boss."""

    chapter_number = 13
    chapter_name_key = "chapter.cemo"
    postfx_grade = "descent"
    ambience_preset = "dust"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        self.companion = None           # Bolum 10'dan beri yalniz

        # Isik: yalnizca arenada anlami var ama sahne basina tek nesne
        # (Zindanci'nin feneri buraya yaziyor).
        self.light = LightState()

        self._build_gates()
        self.braziers = [Brazier(spot.x, spot.feet_y)
                         for spot in LEVEL.of("brazier")]

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
        self.gate_hinted = False
        self.run_hinted = False
        # Kac kez surgunun altinda kalindi - anlatim icin degil,
        # `debug_lines` ve test icin.
        self.ejections = 0

        self._enter_room(self._room_at(self.player.body.center_x))

    # --- Kapilar ------------------------------------------------------------
    def _build_gates(self) -> None:
        """Haritadaki `T` ve `L` isaretlerinden kapi/kol kuruyor.

        Esleme **konuma gore**: her kol, kendi odasindaki butun
        kapilari aciyor. Bu Oda 6'yi bedavaya dogru yapiyor (tek kol,
        iki kapi, tek sayac) ve bir eslestirme tablosu yazmayi
        gereksiz kiliyor - harita zaten tek kaynak (`level.py`).
        """
        self.gates = GateBank()
        for index, spot in enumerate(LEVEL.of("timegate")):
            room = self._room_at(spot.x)
            self.gates.add_gate(TimeGate(
                tile_x=spot.tile_x, top_row=GATE_TOP, floor_row=FLOOR_TOP,
                frames=GATE_FRAMES.get(room, TIMEGATE_FRAMES),
                name=f"{room}_{index}",
            ))
        for spot in LEVEL.of("lever"):
            room = self._room_at(spot.x)
            names = tuple(name for name, gate in self.gates.gates.items()
                          if self._room_at(gate.center_x) == room)
            self.gates.add_lever(Lever(spot.tile_x, spot.tile_y, gates=names))
        self.gates.seal_all(self.tilemap)

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
        if name == "zindan" and self.boss is None:
            self._spawn_boss()

    def _narrate_room(self, name: str) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        if name == "kol":
            self.say_player("line.ch13_rey_lever", "line.ch13_ardo_lever")
        elif name == "okcu":
            self.say_player("line.ch13_rey_run", "line.ch13_ardo_run")
        elif name == "isaret":
            self.say_player("line.ch13_rey_mark", "line.ch13_ardo_mark")

    def _spawn_boss(self) -> None:
        from src.entities.bosses.gaoler import Gaoler
        spot = LEVEL.first("gaoler")
        if spot is None:
            return
        self.boss = Gaoler(self, spot.x, spot.feet_y)
        self.enemies.append(self.boss)

    def after_restart(self, room: str) -> None:
        """Olumden sonra: arenada olduysak boss ve muhur geri gelmeli.

        `setup()` her seyi sifirliyor, `_enter_room` ise odayi
        `entered_rooms`'a bakarak bir kez kuruyor - yani arenada olen
        oyuncu bos bir arenada uyanirdi. Bolum 6'da tam olarak bu
        olmustu (`DEVIR.md`).
        """
        if room != "zindan":
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

        self._update_gates()
        self._update_levers()
        self._update_braziers()
        self._update_lights()
        self._update_triggers()
        self._update_arena()
        self._update_chests()
        self._check_exit()

    def _update_gates(self) -> None:
        closed = self.gates.update(self.tilemap)
        for gate in closed:
            self._on_gate_closed(gate)
        # Surgu inerken uyari: son dilimde ses de degisiyor, cunku
        # renk tek basina yeterli degil (`CLAUDE.md` 10).
        for gate in self.gates.gates.values():
            if gate.urgency and gate.remaining % 12 == 0:
                self.game.play_sound("ui_tick", volume=0.5)

    def _on_gate_closed(self, gate: TimeGate) -> None:
        """Surgu kapandi. Altinda kalan oyuncu **eziliyor degil itiliyor.**

        Bir zaman bulmacasinin cezasi zaman olmali. Olum ya da
        kilitlenme yasak (`DEVIR.md`, "yumusak kilit").
        """
        self.game.play_sound("enemy_blocked", volume=0.7)
        self.particles.burst(gate.center_x, gate.mouth_y, 10,
                             path="dust", speed=(0.4, 1.6))
        body = self.player.body
        if not gate.blocks(body.center_x):
            return
        if not self.tilemap.solid_overlap(body.rect):
            return
        self.ejections += 1
        # Geldigi tarafa itiyor - "az kalmisti" duygusu korunsun.
        side = -1.0 if body.center_x < gate.center_x else 1.0
        spot = self.free_spot_near(body.center_x + side * TILE_SIZE * 1.5,
                                   body.feet[1], body)
        body.set_feet(spot[0], spot[1])
        body.vx = side * TIMEGATE_EJECT_PUSH
        # Uclusu tek cagridan (`CLAUDE.md` 7): hitstop + sarsinti +
        # parcacik. Ayri cagrilsa kare kaymasi olur.
        self.juice.explosion(gate.center_x, gate.mouth_y,
                             ImpactWeight.NORMAL)

    def _update_levers(self) -> None:
        for lever in self.gates.levers:
            lever.update()
        lever = self.gates.lever_near(self.player.body.center_x,
                                      self.player.body.center_y, LEVER_REACH)
        if lever is None:
            return
        if not self.gate_hinted:
            self.gate_hinted = True
            self.hint_once("hint_lever", "hint.lever", Action.INTERACT)
        if not self.game.input.pressed(Action.INTERACT):
            return
        opened = self.gates.pull(lever)
        if not opened:
            return
        self.game.play_sound("rift_open")
        self.particles.burst(lever.center_x, lever.center_y, 10,
                             path="spark", speed=(0.4, 1.6))
        for gate in opened:
            self.particles.burst(gate.center_x, gate.mouth_y, 8,
                                 path="dust", speed=(0.3, 1.2))
        if not self.run_hinted:
            self.run_hinted = True
            self.show_toast(t("chapter13.run"), frames=150)

    def _update_lights(self) -> None:
        """Oyuncunun kendi isigi - **kolye.**

        Arena karanlik ve oyuncunun mesalesi yok. Ilk surumde bu
        demek oluyordu ki Zindanci'nin fenerinden uzaktaki oyuncu
        **kendini bile goremiyordu** - ekran goruntusu tek bakista
        gosterdi.

        Cozum bir parlaklik ayari degil: kolye zaten oyunun dilinde
        (`CLAUDE.md` 9, *"kolye pusulasi boyundaki sprite
        parildamasiyla anlatilir"*). Yaricap kasitli olarak KUCUK -
        kendini ve kilic menzilini goruyorsun, boss'u degil. Karanlik
        hala bir soru; yalnizca haksiz degil.
        """
        if self.room != "zindan":
            self.light.remove_static("necklace")
            return
        body = self.player.body
        self.light.set_static("necklace", body.center_x, body.center_y,
                              NECKLACE_LIGHT_RADIUS)

    def _update_braziers(self) -> None:
        for brazier in self.braziers:
            brazier.update()
            key = f"brazier{id(brazier)}"
            if brazier.lit:
                self.light.set_static(key, brazier.x, brazier.y - 6,
                                      brazier.radius)
            else:
                self.light.remove_static(key)

    def on_attack_swing(self, player, box) -> None:
        """Kilic mangala degdi mi - **ayri bir tusa gerek yok.**

        Bolum 3'te mangali yakan sey elde tasinan mesaleydi. Burada
        mesale yok, ve bir "yak" tusu eklemek boss dovusunun ortasinda
        yeni bir kontrol ogretmek olurdu. Celik demire vurunca kivilcim
        cikar - hem diegetik hem bedava.
        """
        super().on_attack_swing(player, box)
        for brazier in self.braziers:
            if brazier.lit:
                continue
            rect = pygame.Rect(int(brazier.x) - 8, int(brazier.y) - 12, 16, 14)
            if not box.rect.colliderect(rect):
                continue
            brazier.light()
            self.particles.burst(brazier.x, brazier.y - 6, 14,
                                 path="spark", speed=(0.6, 2.2))
            self.game.play_sound("torch_light")

    # --- Arena ---------------------------------------------------------------
    def _update_arena(self) -> None:
        if self.boss is None or self.boss_defeated:
            return
        if not self.arena_sealed and self.room == "zindan":
            start, _ = self._room_span("zindan")
            if self.player.body.center_x > (start + 4) * TILE_SIZE:
                self._seal_arena()
        if self.boss.dead:
            self._on_boss_defeated()

    def _seal_arena(self) -> None:
        start, _ = self._room_span("zindan")
        for row in ARENA_SEAL_ROWS:
            self.tilemap.set_tile(start + 3, row, SOLID)
        self.arena_sealed = True
        self.game.play_sound("rift_close")

    def _on_boss_defeated(self) -> None:
        self.boss_defeated = True
        start, _ = self._room_span("zindan")
        for row in ARENA_SEAL_ROWS:
            self.tilemap.set_tile(start + 3, row, EMPTY)
        self.exit_open = True
        # Fener kirikti; boss olunce arena tamamen kararmasin - cikisi
        # gorebilmeli. Mangallar sonmusse birini yakiyoruz.
        if not any(b.lit for b in self.braziers) and self.braziers:
            self.braziers[-1].light()
        self.juice.explosion(self.boss.body.center_x, self.boss.body.center_y,
                             ImpactWeight.FINISHER)
        self.show_toast(t("chapter13.gate_open"), frames=210)
        # Son ara sahne: kapi acildi ve **arkasi bos**. Bolumun asil
        # darbesi bu - boss'u yenmek yetmedi.
        from src.scenes import chapter13_cinematics as cine
        self.scenes.push(cine.GateCinematic, character=self.character)

    def on_lantern_broken(self, boss) -> None:
        """Faz 2 - fener kirildi, arena karardi."""
        self.juice.explosion(boss.body.center_x, boss.body.center_y,
                             ImpactWeight.BOSS)
        self.show_toast(t("chapter13.dark"), frames=180)

    def on_gaoler_guard(self, boss) -> None:
        self.game.play_sound("enemy_blocked")

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
        from src.scenes import chapter13_cinematics as cine
        if room == "kafes":
            self.scenes.push(cine.CageCinematic, character=self.character)
        elif room == "isaret":
            self.scenes.push(cine.MarkCinematic, character=self.character)
        elif room == "zindan":
            self.scenes.push(cine.GaolerCinematic, character=self.character)

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
            chapter_key="chapter.cemo",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 13
            data.chapter_name = "chapter.cemo"
            data.playtime_frames += self.frames
            data.best_combo = max(data.best_combo, self.player.combo.best)
            data.secrets_found += result.secrets_found
        # Bolum 14 henuz yok - ozet ekrani kapaninca ana menuye donuluyor.
        self.scenes.push(ChapterEndScene, result=result)

    # --- Cizim ---------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame)
        if self.room == "kafes":
            self._draw_cage(surface, offset)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        for gate in self.gates.gates.values():
            self._draw_gate(surface, offset, gate)
        for lever in self.gates.levers:
            self._draw_lever(surface, offset, lever)
        for brazier in self.braziers:
            brazier.draw(surface, offset, self.game.frame)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)
        if self.room == "isaret":
            self._draw_mark(surface, offset)
        # Karanlik **yalnizca arenada**: kovalamaca odalarinin sorusu
        # gorunurluk degil zaman. Gerekce modul basliginda.
        if self.room == "zindan":
            lighting.render(surface, offset, self.light)

    def _draw_gate(self, surface: pygame.Surface, offset,
                   gate: TimeGate) -> None:
        """Surgu - **sayacin kendisi.**

        Inen demir bir kafes. Kalan sure = kalan bosluk.

        Kafes **acikken de ciziliyor**, tavan yuvasina cekilmis halde.
        Ilk surumde acik kapi tamamen gorunmezdi ve ekran goruntusu
        sorunu gosterdi: oyuncu kolu ceviriyor ama nereye kosacagini
        bilmiyor. Oysa bu mekanigin tamami "su kapiya yetis" - kapinin
        nerede oldugu her an gorunur olmali.

        Cekilmis kafesi yukarida gostermek ayrica **fiziksel olarak
        dogru**: kapi yok olmuyor, yukari kayiyor. Ne kadari yukarida
        duruyorsa o kadar sure kalmis demek - yani ayni bilgi iki kez,
        iki ayri yerde.
        """
        ox, oy = offset
        x = gate.tile_x * TILE_SIZE - ox
        ceiling_y = (gate.top_row - gate.height) * TILE_SIZE - oy
        top = gate.top_row * TILE_SIZE - oy
        filled = gate.filled_rows
        urgent = gate.urgency

        # Kizaklar: kapinin sutunu her zaman okunuyor.
        rail = palette.color("stone_darkest")
        surface.fill(rail, (x - 1, ceiling_y, 1, gate.height * 2 * TILE_SIZE))
        surface.fill(rail, (x + TILE_SIZE, ceiling_y,
                            1, gate.height * 2 * TILE_SIZE))

        # Yukarida bekleyen kisim + asagi inmis kisim.
        raised = gate.height - filled
        if raised > 0:
            self._draw_grille(surface, x, top - raised * TILE_SIZE,
                              raised * TILE_SIZE, urgent, dim=True)
        if filled > 0:
            self._draw_grille(surface, x, top, filled * TILE_SIZE, urgent)
        self._draw_gate_teeth(surface, x, top + filled * TILE_SIZE, urgent)

    def _draw_grille(self, surface: pygame.Surface, x: int, y: int,
                     height: int, urgent: bool, dim: bool = False) -> None:
        """Demir kafes govdesi - dikey cubuklar.

        `dim` yukarida bekleyen kisim: ayni sey, daha koyu. Ayni renkte
        olsaydi "kapi zaten kapali" okunurdu.
        """
        if height <= 0:
            return
        body = "danger" if urgent and not dim else (
            "stone_darkest" if dim else "stone_dark")
        bar = "danger_bright" if urgent and not dim else (
            "stone_dark" if dim else "stone")
        surface.fill(palette.color(body), (x, y, TILE_SIZE, height))
        for step in (2, 7, 12):
            surface.fill(palette.color(bar), (x + step, y, 2, height))
        # Yatay kusaklar - "kafes" okunsun, "duvar" degil.
        for band in range(0, height, TILE_SIZE):
            surface.fill(palette.color(bar), (x, y + band, TILE_SIZE, 1))

    def _draw_gate_teeth(self, surface: pygame.Surface, x: int, y: int,
                         urgent: bool = False) -> None:
        """Surgunun alt kenari - sivri. Inen sey bir kapi degil bir tehdit.

        Renk korlugu icin sekil kanali: son uyaride disler yalnizca
        kirmiziya donmuyor, **uzuyor** da (`CLAUDE.md` 10).
        """
        length = 4 if urgent else 2
        tone = "danger_bright" if urgent else "stone_light"
        for index in range(0, TILE_SIZE, 4):
            surface.fill(palette.color(tone), (x + index, y, 2, length))

    def _draw_lever(self, surface: pygame.Surface, offset,
                    lever: Lever) -> None:
        ox, oy = offset
        x = int(lever.center_x) - ox
        y = int(lever.center_y) - oy
        surface.fill(palette.color("stone_dark"), (x - 3, y + 2, 6, 6))
        # Kol cevrilince yatiyor - durum GORULUYOR, sayilmiyor.
        pulled = lever.cooldown > 0
        angle = -1 if not pulled else 1
        for step in range(6):
            surface.fill(palette.color("gold" if not pulled else "ember"),
                         (x + angle * step, y + 2 - step, 2, 2))

    def _draw_cage(self, surface: pygame.Surface, offset) -> None:
        """Cemo'nun kafesi - ust ledge'in kenarindaki parmakliklar.

        Ara sahne Cemo'yu goturdukten sonra bile kafes duruyor: bos bir
        kafes, dolu bir kafesten daha cok sey soyluyor.
        """
        spot = LEVEL.first("cemo")
        if spot is None:
            return
        ox, oy = offset
        x = int(spot.x) - ox
        y = int(spot.feet_y) - oy
        for index in range(-3, 4):
            surface.fill(palette.color("stone_light"),
                         (x + index * 5, y - 26, 1, 26))
        surface.fill(palette.color("stone_dark"), (x - 18, y - 28, 37, 2))

    def _draw_mark(self, surface: pygame.Surface, offset) -> None:
        """Cemo'nun duvara kazidigi isaret.

        `docs/yapi.md` B13: *"Kacmayi denemis, muhafizi yaralamis,
        duvara isaret kazimis."* Uc cumle, sifir diyalog: kazinmis
        cizgi, kurumus kan, kirik zincir. `docs/gdd.md` 11 - anlatim
        jestle.
        """
        start, _ = self._room_span("isaret")
        ox, oy = offset
        x = (start + 8) * TILE_SIZE - ox
        y = (FLOOR_TOP - 3) * TILE_SIZE - oy
        pulse = 0.55 + 0.45 * math.sin(self.frames * 0.05)
        mark = tuple(int(c * pulse) for c in palette.color("bone"))
        # Bolum 2'de gorulen isaretin ayni - "baska birinin sembolu"
        # oradaydi, burada kimin oldugu anlasiliyor.
        for index in range(5):
            surface.fill(mark, (x + index * 2, y + abs(2 - index) * 2, 2, 2))
        surface.fill(palette.color("blood_dark"), (x + 12, y + 8, 3, 2))
        surface.fill(palette.color("blood_dark"), (x + 16, y + 10, 2, 2))
        # Kirik zincir - muhafizi yaralarken kopmus.
        # NOT: `steel` bir golge ZINCIRI, renk degil - `palette.color()`
        # onu tanimaz. Projede bu tuzaga uc kez dusuldu.
        for index in range(3):
            surface.fill(palette.color("stone_light"),
                         (x - 10 - index * 3, y + 14 + index, 2, 2))

    def debug_lines(self) -> list[str]:
        gates = " ".join(f"{g.name}:{g.remaining}"
                         for g in self.gates.gates.values() if g.is_open)
        return [f"oda {self.room}  kapilar[{gates}]  itilme {self.ejections}"
                f"  muhur={self.arena_sealed}"]
