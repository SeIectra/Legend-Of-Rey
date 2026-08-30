"""Bolum 6 - "ARDO". Oynanabilir sahne. Katman 1'in finali.

Oda verisi `src/world/rooms/chapter06.py` icinde; burasi onu oynatiyor.

`docs/yapi.md` B6: *"Rey kosede sikisir, uc yaratik. Golge yukaridan
duser, ucunu bicer. Bakisma, soru isareti balonu. Mekanik: ilk team-up
dovusu + agirlik plakalari."*
`docs/gdd.md` 10: *"Havali giris, ilk team-up, **BOSS 1**"*.

## Uc yeni sistem burada bulusuyor

    src/entities/companion.py   yaninda dovusen oteki karakter
    src/world/plate.py          beraberligi mekanige sokan plakalar
    src/entities/bosses/        BOSS 1 - Katman 1'in sinavi

## Konusma yok - **soru isareti**

`docs/gdd.md` 11 romantik yay: *"B6 | Ilk karsilasma | Bakisma, soru
isareti"*. Iki yabanci karsilasiyor ve **konusmuyorlar**. Bolum boyunca
yoldas tek kelime etmiyor; iletisimin tamami konum ve zamanlama.

Yanki bu boslugu doldurmuyor da: Rey oynanirken bile Yanki yoldas
hakkinda **B8'e kadar konusmuyor** (`docs/gdd.md` 10: *"8 | Ates Basi |
Yanki ilk kez Ardo hakkinda konusur"*). Burada sessiz kalmasi bir eksik
degil, o satirin korunmasi.

## Plaka: once ogret, sonra sina

Oda 3 sakin (dusman yok), Oda 4 dovusun ortasi. `docs/gdd.md` 9: *"yeni
mekanik + eski mekanik = yeni bulmaca"*. Ikisini ayni odada yapmak
mekanigi ogretmeden sinamak olurdu.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_WIDTH, TILE_SIZE
from src.core.input import Action
from src.core.juice import ImpactWeight
from src.entities.companion import Companion, other_character
from src.scenes.play import PlayScene
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.dialogue import Line
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.plate import PlateGate, WeightPlate
from src.world.rooms.chapter06 import (
    ARENA_DOOR_ROWS, ARENA_DOOR_TILE, ARENA_PLATE_A_TILE, ARENA_PLATE_B_TILE,
    BOSS_GOLD, BOSS_SPAWN, CHEST_GOLD, CORNER_WALL_ROWS, CORNER_WALL_TILE,
    LEVEL, ROOM_STARTS, SECRETS_TOTAL, TEACH_GATE_ROWS, TEACH_GATE_TILE,
    TEACH_PLATE_A_TILE, TEACH_PLATE_B_TILE,
)
from src.world.tilemap import EMPTY, SOLID, TileMap

ENEMY_CLASSES = {
    "shambler": "src.entities.enemies.shambler:Shambler",
    "climber": "src.entities.enemies.climber:Climber",
    "bloated": "src.entities.enemies.bloated:Bloated",
}

# Oyuncu kosede bu kadar kare kalinca yoldas geliyor. Sifir olsaydi
# "sikismak" hic yasanmazdi; cok uzun olsaydi bir olum tuzagi olurdu.
RESCUE_DELAY = 90
# Kurtarma parcasi (Ardo.mp3) bu kadar kare kilitli kaliyor - an
# gecene kadar dovus muzigi devralmasin. ~10 saniye.
RESCUE_MUSIC_FRAMES = 600
# Kapi kapanmadan once yoldasin arenaya girmesi icin taninan sure.
# ~1.3 saniye: kosarak yetismesine yeter, oyuncuyu bekletmez.
SEAL_GRACE_FRAMES = 80

# Yoldasa "su plakaya bas" emri bu tusla veriliyor. Etkilesim tusu -
# oyuncu zaten vana/sandik icin onu kullaniyor, yeni bir tus ogrenmiyor.
ORDER_KEY = Action.INTERACT
# Emir menzili: yoldas yakinsa emri duyar. Sinirsiz olsaydi oyuncu
# yoldasi hic gormeden odanin obur ucundan yonetirdi.
ORDER_RANGE = 90.0


def _load(path: str):
    module_name, class_name = path.split(":")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


class Chapter06Scene(PlayScene):
    """ARDO: dort oda, bir yoldas, iki plaka takimi, BOSS 1."""

    chapter_number = 6
    chapter_name_key = "chapter.ardo"
    postfx_grade = "descent"
    ambience_preset = "dust"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)

        # --- Yoldas: kanon geregi SECMEDIGIN karakter -------------------
        self.companion_key = other_character(self.character)
        self.companion: Companion | None = None
        self.rescued = False
        self.corner_frames = 0

        # Kose duvari - sinematik bitince aciliyor.
        for row in CORNER_WALL_ROWS:
            self.tilemap.set_tile(CORNER_WALL_TILE, row, SOLID)

        # --- Plakalar: ogretme takimi + arena takimi --------------------
        self.teach_plates = [WeightPlate(*TEACH_PLATE_A_TILE),
                             WeightPlate(*TEACH_PLATE_B_TILE)]
        self.teach_gate = PlateGate(TEACH_GATE_TILE, TEACH_GATE_ROWS,
                                    self.teach_plates)
        self.teach_gate.close(self.tilemap)

        self.arena_plates = [WeightPlate(*ARENA_PLATE_A_TILE),
                             WeightPlate(*ARENA_PLATE_B_TILE)]

        # --- Arena ------------------------------------------------------
        self.boss = None
        self.boss_defeated = False
        self.arena_sealed = False
        self.plate_hinted = False
        self.seal_hinted = False
        self.seal_wait = 0        # yoldas arenaya girsin diye beklenen kare

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
        if name == "arena":
            self._spawn_boss()

    def _narrate_room(self, name: str) -> None:
        """Yalnizca oyuncunun ICI konusuyor - yoldas sessiz.

        `docs/gdd.md` 11: B6'nin dili "bakisma, soru isareti". Yoldasa tek
        replik vermek o satiri bozardi. Yanki da yoldas hakkinda
        konusmuyor: o an B8'e ait.
        """
        # `say_player(key, ardo_key)` - Ardo oynanirken ikinci anahtar.
        # Anahtarlar **duz dize**: f-string ile kurulani `test_lang.py`
        # goremiyor (bu tuzaga proje bes kereden fazla dustu).
        if name == "plaka_odasi":
            self.say_player("line.ch06_rey_plates", "line.ch06_ardo_plates")
        elif name == "arena":
            self.say_player("line.ch06_rey_arena", "line.ch06_ardo_arena")

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.room_frames += 1
        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        self._update_rescue()
        if self.companion is not None:
            self.companion.update()
        self._update_orders()
        self._update_plates()
        self._update_arena()
        self._update_chests()
        self._check_exit()


    # --- Kurtarma ani -------------------------------------------------------
    def _update_rescue(self) -> None:
        """Oyuncu kosede bir sure kalinca yoldas yukaridan duser.

        `docs/yapi.md`: *"Golge yukaridan duser, ucunu bicer."* Ucunu
        birden bicmesi onemli - yoldasin ilk izlenimi "yardimci" degil
        **guclu** olmali; oyuncu onu bir yuk degil bir ortak sansin.
        """
        if self.rescued or self.room != "kose":
            return
        self.corner_frames += 1
        if self.corner_frames < RESCUE_DELAY:
            return
        self._rescue()

    def _rescue(self) -> None:
        self.rescued = True
        x = self.player.body.center_x + 26.0
        # Yoldas yukaridan duserken doguyor - `free_spot_near` yatayda
        # bos bir sutun ariyor, dikeyde 40 piksel yukarida kaliyor.
        spawn_x, _ = self.free_spot_near(x, self.player.body.feet[1],
                                         self.player.body)
        self.companion = Companion(self, spawn_x,
                                   self.player.body.bottom - 40,
                                   self.companion_key)
        self.companion.body.vy = 6.0          # yukaridan duser

        # Odadaki yaratiklari **bicer** - sahne bir hediye degil bir guc
        # gosterisi.
        for enemy in list(self.enemies):
            if not enemy.dead:
                enemy.health = 0
                enemy.die()
        # **Ardo.mp3** - Arda: "Rey oynarken Ardo'nun girislerinde, Ardo
        # oynarken de Rey'in girislerinde Ardo'yu cal". Parca oteki
        # karakterin GIRISI'ne ait, karaktere degil; o yuzden hangisi
        # geliyorsa ayni parca caliyor.
        # `hold`, `play` degil: bir sonraki karede `_update_music`
        # dovus baglamina donup bu ani sessizce ezerdi.
        self.game.music.hold("companion", RESCUE_MUSIC_FRAMES,
                             fade_ms=200)
        self.juice.explosion(x, self.player.body.center_y, ImpactWeight.KILL)
        self.particles.burst(x, self.player.body.center_y, 22, path="blood",
                             speed=(1.2, 3.4))
        self.game.play_sound("hit_kill")

        self.player.facing = 1
        self.companion.facing = -1

        # Kose duvari aciliyor - kurtarilmanin somut karsiligi.
        self._open_corner()

        # **Havali giris sahnesi.** `docs/gdd.md` 10 bunu bastan
        # istiyordu ama kodda yoktu: kurtaris tek karede oluyor, oyuncu
        # hicbir seyi goremiyordu. Sahne `push` ile aciliyor, yani bu
        # sahne altta dondurulmus halde bekliyor ve kapaninca oyun
        # kaldigi yerden suruyor.
        #
        # Soru isareti balonu artik SAHNENIN icinde ciziliyor
        # (`chapter06_cinematics.draw_stage_foreground`); buradaki
        # `question_frames` yolu kaldirildi - ayni seyi iki yerde
        # cizmek ikisinin ayrisması demekti.
        from src.scenes.chapter06_cinematics import ArdoEntranceCinematic
        self.scenes.push(ArdoEntranceCinematic, character=self.character)

    def _open_corner(self) -> None:
        for row in CORNER_WALL_ROWS:
            self.tilemap.set_tile(CORNER_WALL_TILE, row, EMPTY)

    # --- Emirler ------------------------------------------------------------
    def _update_orders(self) -> None:
        """Etkilesim tusu: yakindaki plakaya "bas" emri.

        Ayni tus ikinci kez basilinca yoldas serbest kaliyor. Iki ayri tus
        (emret/birak) ogrenilecek ikinci bir sey olurdu; tek tus yeterli
        cunku durum zaten gorunur (yoldas plakada mi degil mi).
        """
        if self.companion is None:
            return
        if not self.game.input.pressed(ORDER_KEY):
            return
        if self.companion.hold_x is not None:
            self.companion.release()
            self.game.play_sound("ui_tick")
            return
        plate = self._nearest_plate()
        if plate is None:
            return
        self.companion.hold(plate.centre_x)
        self.game.play_sound("ui_confirm")

    def _nearest_plate(self):
        """Oyuncuya en yakin plaka - ama **oyuncunun bastigi degil**.

        Oyuncunun ustunde durdugu plakayi yoldasa emretmek bulmacayi
        cozmez ve oyuncuya "calismadi" dedirtir; o plaka bilerek
        eleniyor.
        """
        plates = (self.arena_plates if self.room == "arena"
                  else self.teach_plates)
        best, best_distance = None, ORDER_RANGE
        for plate in plates:
            if plate.rect.collidepoint(int(self.player.body.center_x),
                                       int(self.player.body.bottom)):
                continue
            distance = abs(plate.centre_x - self.player.body.center_x)
            if distance < best_distance:
                best, best_distance = plate, distance
        return best

    # --- Plakalar -----------------------------------------------------------
    def _plate_actors(self) -> list:
        actors = [self.player]
        if self.companion is not None:
            actors.append(self.companion)
        return actors

    def _update_plates(self) -> None:
        actors = self._plate_actors()
        for plate in self.teach_plates + self.arena_plates:
            if plate.update(actors) and not self.plate_hinted:
                self.plate_hinted = True
                self.show_toast(t("chapter06.plate_hint"), frames=200)

        if self.teach_gate.update(self.tilemap):
            self.game.play_sound("rift_open")
            self.juice.explosion(TEACH_GATE_TILE * TILE_SIZE,
                                 self.player.body.center_y,
                                 ImpactWeight.FINISHER)
            self.show_toast(t("chapter06.gate_open"), frames=180)

        # Arena plakalari kapi acmiyor - **boss'un muhrunu** kiriyor.
        if (self.boss is not None and not self.boss.dead
                and self.boss.sealed and self.boss.stun_frames <= 0
                and all(p.held for p in self.arena_plates)):
            self.boss.break_seal()

    # --- Arena --------------------------------------------------------------
    def _spawn_boss(self) -> None:
        from src.entities.bosses.rotted_one import RottedOne
        x = BOSS_SPAWN[0] * TILE_SIZE + TILE_SIZE * 0.5
        y = (BOSS_SPAWN[1] + 1) * TILE_SIZE
        self.boss = RottedOne(self, x, y)
        self.enemies.append(self.boss)

    def _update_arena(self) -> None:
        if self.room != "arena" or self.boss is None:
            return
        if not self.arena_sealed and not self.boss_defeated:
            # Giris kapaniyor - Bolum 2/3'un dersi: boss atlanamamali.
            if self.player.body.x > (ARENA_DOOR_TILE + 1) * TILE_SIZE:
                self._seal_arena()
        if self.boss_defeated or not self.boss.dead:
            return
        self._finish_boss()

    def _seal_arena(self) -> None:
        """Arena kapisi kapaniyor - **yoldas da iceride.**

        Arda (30.08.2026): *"Boss fight'a Ardo giremiyor, duvarin
        arkasinda kaliyor."* Sebep: muhur yalnizca OYUNCUNUN konumuna
        bakiyordu. Yoldas takip ettigi icin her zaman biraz geride ve
        kapi tam onunde kapaniyordu - yani bolumun butun anlamini
        tasiyan "birlikte dovusme" sahnesi yalniz oynaniyordu.

        Cozum ısınlamak degil **iceri almak**: kapi kapanmadan once
        yoldasa arena icinde bir nokta emrediliyor ve gercekten
        varmasi bekleniyor (`SEAL_GRACE_FRAMES`). Bekleme bitmisse ve
        hala disaridaysa o zaman konuluyor - dovussuz bir boss odasi,
        goze batan bir isinlanmadan daha kotu.
        """
        inside_x = (ARENA_DOOR_TILE + 4) * TILE_SIZE
        if self.companion is not None:
            if self.companion.body.x < (ARENA_DOOR_TILE + 1) * TILE_SIZE:
                self.companion.hold(float(inside_x))
                self.seal_wait += 1
                if self.seal_wait < SEAL_GRACE_FRAMES:
                    return                  # Henuz kapatma, geliyor
                ix, iy = self.free_spot_near(float(inside_x),
                                             self.player.body.feet[1],
                                             self.companion.body)
                self.companion.body.set_feet(ix, iy)
            self.companion.release()

        self.arena_sealed = True
        for row in ARENA_DOOR_ROWS:
            self.tilemap.set_tile(ARENA_DOOR_TILE, row, SOLID)
        self.game.play_sound("rift_close")

    def after_restart(self, room: str) -> None:
        """Olumden sonra yoldas geri geliyor.

        `setup()` `self.companion = None` yapiyor ve yoldas yalnizca
        "kose" odasindaki kurtarma sahnesinde doguyor. Arenada olen
        oyuncu icin o sahne bir daha hic gerceklesmiyordu: boss yalniz
        doguluyordu ve bolum aslinda gecilemez hale geliyordu (Arda:
        *"oldukten sonra o boss fight ta hic dogmuyor"*).

        Kurtarma sahnesi TEKRARLANMIYOR - o bir kez yasanan bir andir.
        Yalnizca yoldas, oyuncunun yaninda, sessizce geri kuruluyor.
        """
        if room == "kose" or self.companion is not None:
            return
        x, y = self.free_spot_near(self.player.body.center_x - 24,
                                   self.player.body.feet[1],
                                   self.player.body)
        self.companion = Companion(self, x, y, self.companion_key)
        self.rescued = True

    def _finish_boss(self) -> None:
        self.boss_defeated = True
        self.arena_sealed = False
        for row in ARENA_DOOR_ROWS:
            self.tilemap.set_tile(ARENA_DOOR_TILE, row, EMPTY)
        self.earned_gold += BOSS_GOLD
        if self.save_data is not None:
            self.save_data.gold += BOSS_GOLD
        self.show_toast(t("chapter06.boss_down", count=BOSS_GOLD), frames=200)

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
            self.show_toast(t("chapter06.chest_found", count=chest.gold),
                            frames=180)

    def _check_exit(self) -> None:
        exit_at = LEVEL.first("exit")
        if self.finished or exit_at is None or not self.boss_defeated:
            return
        if self.player.body.center_x < exit_at.x - 8:
            return
        self.finished = True
        self._end_chapter()

    def _end_chapter(self) -> None:
        self.game.play_sound("chapter_end")
        result = ChapterResult(
            chapter_key="chapter.ardo",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 6
            data.chapter_name = "chapter.ardo"
            data.playtime_frames += self.frames
            data.best_combo = max(data.best_combo, self.player.combo.best)
            data.secrets_found += result.secrets_found
        # Bolum 7'ye baglaniyor. Ara sahne UZERINDEN: "Muhur" bolumun
        # acilisi ve Katman 2'nin ilk goruntusu - oynanisa dogrudan
        # dusmek o gecisi yok ederdi.
        character = self.character

        def _continue() -> None:
            from src.scenes.chapter07_cinematics import SealCinematic
            self.scenes.set_root(SealCinematic, character=character)

        self.scenes.push(ChapterEndScene, result=result,
                         on_continue=_continue)

    # --- Kancalar -----------------------------------------------------------
    def on_boss_sealed(self, boss) -> None:
        """Muhurlu boss'a vuruldu - **sebebi bir kez** soyle.

        Oyuncu vurusun neden islemedigini bilmiyor. Bir kez soyleniyor;
        tekrarlanan ipucu ogut olur.
        """
        self.game.play_sound("enemy_blocked")
        self.particles.burst(boss.body.center_x, boss.body.center_y, 6,
                             path="spark", speed=(0.6, 1.8))
        if self.seal_hinted:
            return
        self.seal_hinted = True
        self.show_toast(t("chapter06.seal_hint"), frames=240)

    def on_seal_broken(self, boss) -> None:
        self.juice.explosion(boss.body.center_x, boss.body.center_y,
                             ImpactWeight.FINISHER)
        self.particles.burst(boss.body.center_x, boss.body.center_y, 18,
                             path="spark", speed=(1.0, 3.0))
        self.game.play_sound("rift_open")
        self.show_toast(t("chapter06.seal_broken"), frames=150)

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
        for plate in self.teach_plates + self.arena_plates:
            plate.draw(surface, offset)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)
        if self.companion is not None:
            self.companion.draw(surface, offset)
        self._draw_seal(surface, offset)

    def _draw_seal(self, surface: pygame.Surface, offset) -> None:
        """Muhur halkasi - "simdi vurulmaz" bilgisinin SEKIL kanali.

        Renk tek basina yeterli degil (`CLAUDE.md` 10). Boss muhurluyken
        etrafinda kemik renginde bir halka doner; muhur kirilinca kaybolur.
        """
        boss = self.boss
        if boss is None or boss.dead or not boss.sealed:
            return
        if boss.stun_frames > 0:
            return
        ox, oy = offset
        cx = int(boss.body.center_x) - ox
        cy = int(boss.body.center_y) - oy
        radius = 26
        for index in range(8):
            angle = self.frames * 0.05 + index * math.pi / 4
            x = cx + int(round(math.cos(angle) * radius))
            y = cy + int(round(math.sin(angle) * radius * 0.7))
            surface.fill(palette.color("bone"), (x, y, 2, 2))

