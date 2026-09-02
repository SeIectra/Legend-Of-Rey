"""Bolum 15 - "Sessizlik". Oynanabilir sahne.

Oda verisi `src/world/rooms/chapter15.py`, gurultu
`src/systems/noise.py`, uyaniklik `src/entities/enemy.py`
(`alert_level`, `hear`, `_investigate`).

`docs/yapi.md` B15: *"Yanki'yi kapali oynamak zorundasin. Uyuyan
suru. Kosarsan uyanirlar. Gurultu kaynaklarini kullanarak dikkat
dagitma. **Tamamen dovussuz gecilebilir - ve daha iyi odul verir.**"*

## Bolumun olcusu DOVUSMEMEK

Oteki bolumlerde sayac combo, altin, sir. Burada iki sayi var ve
ikisi de **yapmadigin sey**: kac dusman uyandirdin, kac dusman
oldurdun. Ikisi de sifirsa bolum sonu farkli.

`docs/ekonomi-uretim.md` zorlugu 4 veriyor - B14 zirvesinden sonraki
dusus. O yuzden ceza yok: uyandirmak bolumu kaybettirmiyor, yalnizca
odulu kucultuyor. Ceza koysaydik gizlilik bir kaydet-yukle oyununa
donerdi.

## Yanki zaten kapali

B14'ten sonra `sense_betrayed` acik ve duyuyu acmak menzildeki
herkesi uyandiriyor (`PlayScene._update_betrayal`). Bu bolum o kurali
**oynatiyor**, yeniden kurmuyor - tek satir bile yazmiyor.

## Gurultu kaynagi UC tane, ucu de ayni alandan geciyor

    oyuncunun kendisi   adim, inis, kacinma, vurus, rezonans
    can                 rezonansla calinan - SEN tetikliyorsun
    damla               kendi calan - RITME uyuyorsun

Ucu de `NoiseField.emit()` cagiriyor, yani "kim duydu" sorusu tek
yerde cevaplaniyor ve ekrandaki halka her zaman gercegi gosteriyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import (
    NOISE_ATTACK, NOISE_CHIME, NOISE_DODGE, NOISE_LAND, NOISE_RESONATE,
    NOISE_RUN, NOISE_WALK, PLAYER_RUN_SPEED, TILE_SIZE,
)
from src.scenes.play import PlayScene
from src.systems.noise import Chime, NoiseField
from src.systems.resonance import ResonanceState
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.rooms.chapter15 import (
    CHEST_GOLD, DRIP_INTERVAL, FLOOR_TOP, GHOST_BONUS, LEVEL, ROOM_STARTS,
    SECRETS_TOTAL,
)
from src.world.tilemap import TileMap

ENEMY_CLASSES = {
    "shambler": "src.entities.enemies.shambler:Shambler",
    "silent": "src.entities.enemies.silent:Silent",
}

# Yurumek mi kosmak mi: hizin bu orani ustunde "kosuyor" sayiliyor.
# Tam `PLAYER_RUN_SPEED`e bakmak yanlis olurdu - hizlanma sirasinda
# oyuncu bir kare bile tam hiza ulasmadan once ceza yerdi.
RUN_THRESHOLD = 0.55


def _load(path: str):
    module_name, class_name = path.split(":")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


class Chapter15Scene(PlayScene):
    """Sessizlik: alti oda, uyuyan suru, tek kural."""

    chapter_number = 15
    chapter_name_key = "chapter.silence"
    postfx_grade = "descent"
    ambience_preset = "dust"
    # Gizlilik bolumu kendi havasini istiyor: dovus parcasi burada
    # yanlis soz soylerdi. `docs/ekonomi-uretim.md` zorlugu 4 veriyor.
    music_context = "sad"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        self.companion = None           # Bolum 10'dan beri yalniz

        self.noise = NoiseField()
        self.chimes = [Chime(spot.tile_x, spot.tile_y)
                       for spot in LEVEL.of("chime")]
        drip = LEVEL.first("drip")
        self.drip = Chime(drip.tile_x, drip.tile_y) if drip else None
        self.drip_frames = 0

        # Rezonans B8'de ogrenildi. Bayrak yoksa yine de acik: bu
        # bolume gelen oyuncu onu almis olmali, ve kapali kalsaydi
        # bulmaca cozulemezdi (yumusak kilit).
        self.resonance = ResonanceState(unlocked=True)

        self.chests = [Chest(spot.x, spot.feet_y, gold=CHEST_GOLD, secret=True)
                       for spot in LEVEL.of("chest")]

        self.room = ""
        self.room_frames = 0
        self.frames = 0
        self.entered_rooms: set[str] = set()
        self.fired_triggers: set[str] = set()
        self.earned_gold = 0
        self.secret_found = False
        self.finished = False
        # **Bolumun iki olcusu.** Ikisi de "yapmadigin sey".
        self.kills = 0
        self.chime_hinted = False
        self.walk_hinted = False

        self._enter_room(self._room_at(self.player.body.center_x))

    @property
    def wakes(self) -> int:
        return self.noise.wakes

    @property
    def ghost(self) -> bool:
        """Hic uyandirmadan ve hic oldurmeden geldi mi.

        `docs/yapi.md`: *"Tamamen dovussuz gecilebilir - ve daha iyi
        odul verir."* Bolumun tek basari olcutu bu.

        Sayaca degil **duruma** bakiyor. Ilk surum yalnizca
        `noise.wakes`i sayiyordu ve o yalnizca **gurultuyle** uyanani
        goruyor - bir dusman baska bir yoldan uyanirsa (vurus,
        `sense_betrayed`, bir sahne kancasi) sayac sifir kalir ve
        oyuncu hak etmedigi odulu alirdi. Ekranda uyanik bir dusman
        varken "hic uyandirmadin" demek yalan olurdu.
        """
        if self.kills:
            return False
        return not any(e.aware and not e.dead for e in self.enemies)

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
        """Bu odanin dusmanlari - **hepsi uyuyor.**

        Uyku haritada bir isaret degil, burada veriliyor: dusman ayni
        dusman, degisen sey durumu. Ayri bir "uyuyan Suruklenen"
        sinifi ya da harfi ortak sozlugu sisirirdi ve `Silent` gibi
        kendi mantigi olanlari ikiye bolerdi.
        """
        start, end = self._room_span(name)
        for kind, path in ENEMY_CLASSES.items():
            for spot in LEVEL.of(kind):
                if not (start <= spot.tile_x < end):
                    continue
                enemy = _load(path)(self, spot.x, spot.feet_y)
                enemy.asleep = True
                enemy.aware = False
                self.enemies.append(enemy)

    def _narrate_room(self, name: str) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        if name == "uyku":
            self.say_player("line.ch15_rey_sleep", "line.ch15_ardo_sleep")
        elif name == "damla":
            self.say_player("line.ch15_rey_drip", "line.ch15_ardo_drip")
        elif name == "dar":
            self.say_player("line.ch15_rey_narrow", "line.ch15_ardo_narrow")

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.room_frames += 1
        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        self._update_footsteps()
        self._update_resonance()
        self._update_drip()
        self._update_chimes()
        self.noise.update()
        self._update_hints()
        self._update_triggers()
        self._update_chests()
        self._check_exit()

    def _update_footsteps(self) -> None:
        """Yurumek sessiz, kosmak degil.

        `docs/yapi.md`: *"Kosarsan uyanirlar."* Ses her adimda degil,
        `on_player_step` kancasindan geliyor - yani ayak sesinin
        ritmine bagli ve hizlandikca **siklasan** bir sey. Her karede
        ses cikarsaydi durmak ile yurumek arasindaki fark kaybolurdu.
        """

    def on_player_step(self, player) -> None:
        super().on_player_step(player)
        speed = abs(player.body.vx) / max(0.1, PLAYER_RUN_SPEED)
        loud = NOISE_RUN if speed > RUN_THRESHOLD else NOISE_WALK
        self._emit(player.body.center_x, player.body.center_y, loud)

    def on_player_land(self, player, air_frames: int) -> None:
        super().on_player_land(player, air_frames)
        # Kisa bir dususun sesi yok - platformdan inmek ceza olmamali.
        if air_frames > 12:
            self._emit(player.body.center_x, player.body.center_y, NOISE_LAND)

    def on_player_dodge(self, player) -> None:
        super().on_player_dodge(player)
        self._emit(player.body.center_x, player.body.center_y, NOISE_DODGE)

    def on_player_attack(self, player, index: int) -> None:
        super().on_player_attack(player, index)
        # **Tek vurus yeter.** Dovus bu bolumde cozum degil.
        self._emit(player.body.center_x, player.body.center_y, NOISE_ATTACK)

    def on_enemy_died(self, enemy) -> None:
        super().on_enemy_died(enemy)
        self.kills += 1

    def _emit(self, x: float, y: float, strength: float) -> None:
        self.noise.emit(self.enemies, x, y, strength)

    def _update_resonance(self) -> None:
        """Darbe **kendi sesini de** cikariyor.

        Bulmacayi kuran sey bu: yeterince uzak dur ki kendi darbeni
        duymasinlar, yeterince yakin dur ki cana ulassin. Bedava
        olsaydi dikkat dagitmak risksiz bir dugme olurdu.
        """
        from src.core.input import Action
        self.resonance.update()
        if self.game.input.pressed(Action.RESONATE):
            body = self.player.body
            if self.resonance.pulse(body.center_x, body.center_y):
                self._emit(body.center_x, body.center_y, NOISE_RESONATE)

        for chime in self.chimes:
            if self.resonance.reaches(chime) and chime.ring():
                self._ring(chime)

    def _ring(self, chime: Chime) -> None:
        """Can caldi - ses **onun** yerinde, oyuncunun degil."""
        self._emit(chime.x, chime.y, NOISE_CHIME)
        self.game.play_sound("echo_wall")
        self.particles.burst(chime.x, chime.y, 12,
                             path="spark", speed=(0.4, 1.6))

    def _update_drip(self) -> None:
        """Su damlasi - kendi caliyor, oyuncu ritmine uyuyor."""
        if self.drip is None:
            return
        self.drip.update()
        self.drip_frames += 1
        if self.drip_frames < DRIP_INTERVAL:
            return
        self.drip_frames = 0
        self.drip.cooldown = 0
        self.drip.ring()
        self._emit(self.drip.x, self.drip.y, NOISE_CHIME)
        self.game.play_sound("step_water")
        self.particles.burst(self.drip.x, self.drip.y, 6,
                             path="echo", speed=(0.2, 0.9))

    def _update_chimes(self) -> None:
        for chime in self.chimes:
            chime.update()

    def _update_hints(self) -> None:
        """Iki kural, iki ipucu, **her biri bir kez**."""
        if not self.walk_hinted and self.room == "uyku":
            near = any(e.asleep and e.distance_to(self.player) < 140
                       for e in self.enemies if not e.dead)
            if near:
                self.walk_hinted = True
                self.show_toast(t("chapter15.walk"), frames=240)
        if not self.chime_hinted and self.room == "can":
            self.chime_hinted = True
            from src.core.input import Action
            self.hint_once("hint_chime", "hint.chime", Action.RESONATE)

    # --- Tetikleyiciler ------------------------------------------------------
    def _update_triggers(self) -> None:
        for spot in LEVEL.of("trigger"):
            key = f"trigger{spot.tile_x}"
            if key in self.fired_triggers:
                continue
            if abs(self.player.body.center_x - spot.x) > TILE_SIZE:
                continue
            self.fired_triggers.add(key)
            from src.scenes import chapter15_cinematics as cine
            self.scenes.push(cine.PassedCinematic, character=self.character,
                             ghost=self.ghost)

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
        if self.finished or exit_at is None:
            return
        if self.player.body.center_x < exit_at.x - 8:
            return
        self.finished = True
        self._end_chapter()

    def _end_chapter(self) -> None:
        """Odul **yapmadigin seye** gore.

        `docs/yapi.md`: *"Tamamen dovussuz gecilebilir - ve daha iyi
        odul verir."* Ek altin bir sayidan fazlasi: bolumun sana ne
        sorduğunun cevabi.
        """
        self.game.play_sound("chapter_end")
        ghost = self.ghost
        gold = self.earned_gold
        if ghost:
            gold += GHOST_BONUS
            self.show_toast(t("chapter15.ghost"), frames=260)
        # `ghost`/`ghost_bonus` ozet ekranina da gidiyor: odul yalnizca
        # altin sayisina eklenseydi kazanan neden kazandigini,
        # kazanamayan boyle bir sey oldugunu ogrenemezdi. Kacirilan
        # satir da odulun buyuklugunu yaziyor.
        result = ChapterResult(
            chapter_key="chapter.silence",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
            ghost=ghost,
            ghost_bonus=GHOST_BONUS,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 15
            data.chapter_name = "chapter.silence"
            data.playtime_frames += self.frames
            data.secrets_found += result.secrets_found
            if ghost:
                data.flags["ch15_ghost"] = True
        # Bolum 16 henuz yok - ozet ekrani kapaninca ana menuye donuluyor.
        self.scenes.push(ChapterEndScene, result=result)

    # --- Cizim ---------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        for chime in self.chimes:
            chime.draw(surface, offset, self.game.frame)
        if self.drip is not None:
            self._draw_drip(surface, offset)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)
        self._draw_sleepers(surface, offset)
        # Halkalar en uste: duyulan sey **gorulen sey** olmali.
        self.noise.draw(surface, offset)
        self._draw_pulse(surface, offset)

    def _draw_drip(self, surface: pygame.Surface, offset) -> None:
        """Damlanin **ne zaman** dusecegi gorunuyor.

        Ritme uymak ancak ritim okunabiliyorsa mumkun. Damla
        buyudukce dusme ani yaklasiyor - bir sayac degil, bir
        damla.
        """
        ox, oy = offset
        x = int(self.drip.x) - ox
        y = int(self.drip.y) - oy
        ratio = self.drip_frames / DRIP_INTERVAL
        size = 1 + int(3 * ratio)
        surface.fill(palette.color("stone_dark"), (x - 3, y - 2, 7, 2))
        surface.fill(palette.color("echo_bright"),
                     (x - size // 2, y, max(1, size), max(1, size)))

    def _draw_sleepers(self, surface: pygame.Surface, offset) -> None:
        """Uyku ve **kimildanma** gorunur.

        Gizlilikte en sik hata sessiz bir sayac: oyuncu ne kadar
        yaklastigini bilmeden yakalanir. Uyuyanin ustunde uc nokta
        var; uyaniklik artinca once titriyor, sonra kirmiziya
        donuyor. `CLAUDE.md` 10: renk tek basina yeterli degil, o
        yuzden **hareket** de degisiyor.
        """
        ox, oy = offset
        for enemy in self.enemies:
            if enemy.dead or not enemy.asleep:
                continue
            x = int(enemy.body.center_x) - ox
            y = int(enemy.body.top) - oy - 8
            stirring = enemy.stirring
            wobble = int(math.sin(self.frames * 0.4) * 2) if stirring else 0
            tone = "danger_bright" if stirring else "stone_light"
            for index in range(3):
                lit = enemy.alert_level > index * 0.33
                colour = palette.color(tone if lit else "stone_darkest")
                surface.fill(colour,
                             (x - 4 + index * 4, y + (wobble if lit else 0),
                              2, 2))

    def _draw_pulse(self, surface: pygame.Surface, offset) -> None:
        if not self.resonance.active:
            return
        ox, oy = offset
        cx = int(self.resonance.x) - ox
        cy = int(self.resonance.y) - oy
        radius = int(self.resonance.radius)
        if radius < 2:
            return
        fade = max(0.0, 1.0 - self.resonance.progress)
        base = palette.color("echo_bright" if self.character != "ardo"
                             else "ember_light")
        colour = tuple(int(c * (0.35 + 0.65 * fade)) for c in base)
        pygame.draw.circle(surface, colour, (cx, cy), radius, 1)

    def debug_lines(self) -> list[str]:
        alerts = " ".join(f"{e.alert_level:.2f}" for e in self.enemies
                          if e.asleep and not e.dead)
        return [f"oda {self.room}  uyandirilan {self.wakes}  oldurulen "
                f"{self.kills}  hayalet={self.ghost}  [{alerts}]"]
