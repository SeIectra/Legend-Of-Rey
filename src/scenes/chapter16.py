"""Bolum 16 - "Sirt Sirta". Oynanabilir sahne.

Oda verisi `src/world/rooms/chapter16.py`, kaldirma
`src/systems/rescue.py`, jest secimi `src/ui/gesture.py`, ara sahneler
`src/scenes/chapter16_cinematics.py`.

`docs/yapi.md` B16: *"Ardo geri doner, havali giris. Ama bu sefer **Rey
de onu kurtarir.** Karsilikli. Mekanik: En uzun team-up. Asist
kombolar zirvede. Bolum sonu: kalp balonu."*

## Bolumun olcusu KALDIRMAK

B15'in iki sayaci "yapmadigin sey"di (kac uyandirdin, kac oldurdun).
Burada sayac tersine donuyor: **kac kez onu kaldirdin.** On bes bolum
boyunca tasinan taraftin; bu bolum bunu olcuyor.

## Yoldas burada kendi kendine kalkmiyor

Tek satir - `self.companion.self_recovers = False` - ama bolumun
butun tezi o. B6'dan beri yoldas diz cokup kendi kalkiyordu ve oyuncu
onun icin hicbir sey yapmiyordu.

Karar **ornekte** veriliyor, sinifta degil: `Companion.self_recovers`
sinif duzeyinde True kaliyor, cunku oteki bolumlerde kaldirma
mekanigi yok ve orada yoldas yerde kalsaydi agirlik plakasi bulmacasi
cozulemezdi.

## Uc ara sahne, ucu de bir isi olan

    kapi     DONUS   - yalnizligi bitiriyor
    dusus    KALDIR  - mekanigi OGRETIYOR
    cikis    KALP    - jest secimi ve kapanis

Ortadaki pazarlik konusu degil: yoldas kendi kalkmadigi icin
ogretilmemis bir mekanik oyuncuyu bolumun yarisinda yoldassiz
birakirdi. Sahne yoldasi senaryolu olarak dusuruyor, oyuncu ilk
kaldirmayi **guvenli** bir anda yapiyor, sinav bir sonraki odada.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE
from src.core.input import Action
from src.entities.companion import Companion, other_character
from src.scenes.play import PlayScene
from src.systems.boost import BoostState
from src.systems.rescue import HINT_AFTER, RescueState
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.rooms.chapter16 import (
    CHEST_GOLD, LEVEL, LIFT_BONUS, ROOM_STARTS, SECRETS_TOTAL,
)
from src.world.tilemap import TileMap

ENEMY_CLASSES = {
    "shambler": "src.entities.enemies.shambler:Shambler",
    "spearman": "src.entities.enemies.spearman:Spearman",
    "shieldbearer": "src.entities.enemies.shieldbearer:Shieldbearer",
    "archer": "src.entities.enemies.archer:Archer",
    "commander": "src.entities.enemies.commander:Commander",
    "silent": "src.entities.enemies.silent:Silent",
    "echoing": "src.entities.enemies.echoing:Echoing",
    "splitter": "src.entities.enemies.splitter:Splitter",
}

# Kaldirma halkasinin yaricapi (piksel) - yoldasin ustunde.
RING_RADIUS = 11


def _load(path: str):
    module_name, class_name = path.split(":")
    return getattr(__import__(module_name, fromlist=[class_name]), class_name)


class Chapter16Scene(PlayScene):
    """Sirt Sirta: yedi oda, bir yoldas, bir kaldirma."""

    chapter_number = 16
    chapter_name_key = "chapter.backtoback"
    postfx_grade = "descent"
    ambience_preset = "dust"
    music_context = "combat"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)

        # **Ilk odada yoldas YOK.** Bolumun ilk perdesi yalnizlik;
        # yoldas "Donus" ara sahnesiyle geliyor. Bastan yaninda
        # olsaydi havali giris bir tekrar olurdu.
        self.companion_key = other_character(self.character)
        self.companion: Companion | None = None

        self.rescue = RescueState(unlocked=False)   # "Kaldir" sahnesi aciyor
        self.boost = BoostState(unlocked=True)      # B9'da ogrenildi

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
        # **Bolumun olcusu.** B15 "yapmadigin seyi" sayiyordu; burada
        # yaptigin sey sayiliyor.
        self.lifts = 0
        self.assists = 0
        self.downs = 0
        self.rescue_hinted = False
        self.gesture_key = ""       # kapanista secilen jest

        self._enter_room(self._room_at(self.player.body.center_x))

    # --- Yoldas -------------------------------------------------------------
    def summon_companion(self) -> Companion:
        """Yoldasi sahneye koyar - "Donus" ara sahnesinden sonra.

        `free_spot_near` ile bos yer araniyor: dogrudan koordinat
        vermek onu bir yukseltinin icine dogurabiliyordu (bu tuzaga
        iki bolumde dusuldu, `Companion._unstick` onun calisma zamani
        karsiligi).
        """
        if self.companion is not None:
            return self.companion
        body = self.player.body
        companion = Companion(self, body.center_x + 26, body.feet[1],
                              self.companion_key)
        x, y = self.free_spot_near(body.center_x + 26, body.feet[1],
                                   companion.body)
        companion.body.set_feet(x, y)
        # **Bolumun tezi tek satirda.** Gerekce modul basliginda.
        companion.self_recovers = False
        self.companion = companion
        return companion

    def on_companion_down(self, companion) -> None:
        self.downs += 1
        self.rescue.cancel()

    def on_companion_attack(self, companion) -> None:
        """Asist vurusu normalden **daha agir** okunuyor.

        Bayrak `last_swing_assisted`dan geliyor; kanca imzasi
        degismedi (gerekce `companion.py`).
        """
        if not companion.last_swing_assisted:
            return
        self.assists += 1
        self.game.hitstop(3)
        self.particles.burst(companion.body.center_x + companion.facing * 12,
                             companion.body.center_y, 8, path="spark")

    def on_player_attack(self, player, index: int) -> None:
        """Bitirici yoldasi da tetikliyor - **asist kombo**.

        `docs/yapi.md` B16: *"Asist kombolar zirvede."* Sart bitirici
        olmasi: her vurusta tetiklenseydi yoldas oyunu oyuncunun
        yerine oynardi (`companion.py` basligindaki en buyuk risk).
        """
        super().on_player_attack(player, index)
        if self.companion is None or not player.chain.is_finisher:
            return
        self.companion.assist()

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
                if not (start <= spot.tile_x < end):
                    continue
                self.enemies.append(_load(path)(self, spot.x, spot.feet_y))

    def _narrate_room(self, name: str) -> None:
        """Anahtarlar **duz dize** - f-string ile kurulani test goremiyor."""
        if name == "yalniz":
            self.say_player("line.ch16_rey_many", "line.ch16_ardo_many")
        elif name == "koridor":
            self.say_player("line.ch16_rey_corridor", "line.ch16_ardo_corridor")
        elif name == "sirt":
            self.say_player("line.ch16_rey_back", "line.ch16_ardo_back")

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.room_frames += 1
        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        # **Yoldasi sahne guncelliyor.** `PlayScene` bunu yapmiyor ve
        # B6/B9 da ayni satiri kendi yaziyor. Bu satir bir sure
        # UNUTULMUSTU: yoldas donmus duruyordu, yer cekimi bile
        # islemiyordu (`body.grounded` False kaliyordu) ve bu yuzden
        # kaldirma hicbir zaman mumkun olmuyordu - `RescueState.reach`
        # ikisinin de yerde olmasini ariyor. Testler yakaladi.
        if self.companion is not None:
            self.companion.update()

        self._update_rescue()
        self.boost.update()
        self._update_hints()
        self._update_triggers()
        self._update_chests()
        self._check_exit()

    def _update_rescue(self) -> None:
        """Basili tut, kalksin.

        Tus INTERACT: sandik/plaka ile ayni tus ve bu bilincli - ikisi
        de "elini uzat" demek ve bu bolumde yoldasin yaninda sandik
        yok. Ayri bir tus, yalnizca bir bolumde kullanilan bir tusa
        yer acmak olurdu.
        """
        holding = self.game.input.held(Action.INTERACT)
        lifted = self.rescue.update(self.player, self.companion, holding)
        if not lifted:
            return
        self.lifts += 1
        self.game.play_sound("ledge_grab")
        self.game.hitstop(4)
        if self.companion is not None:
            self.particles.burst(self.companion.body.center_x,
                                 self.companion.body.center_y, 12,
                                 path="echo")

    def on_player_hurt(self, player, result) -> None:
        """Vurulunca kaldirma ilerlemesi **sifirlaniyor**.

        Riskin gercek olmasi icin: yoksa oyuncu dusmanlarin ortasinda
        dayak yiyerek de kaldirabilirdi ve "once ortaligi temizle"
        karari anlamsizlasirdi.
        """
        super().on_player_hurt(player, result)
        self.rescue.cancel()

    def _update_hints(self) -> None:
        if (self.rescue.unlocked and self.companion is not None
                and self.companion.downed
                and self.rescue.count < HINT_AFTER
                and not self.rescue_hinted):
            self.rescue_hinted = True
            self.hint_once("hint_rescue", "hint.rescue", Action.INTERACT)

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
        from src.scenes import chapter16_cinematics as cine
        room = self._room_at(tile_x * TILE_SIZE)
        if room == "kapi":
            # Havali giris. Yoldas ara sahneden **once** sahaya
            # konuyor: `ScenesManager.push` kwarg'lari dogrudan
            # `on_enter`a geciriyor, yani "bitince sunu cagir" diye bir
            # kanca yok. Oyuncu zaten ara sahnede oldugu icin
            # yerlestirmeyi gormuyor ve dondugunde yoldasi tam ara
            # sahnenin gosterdigi yerde buluyor.
            self.summon_companion()
            self.scenes.push(cine.ReturnCinematic, character=self.character)
            return
        if room == "dusus":
            # Mekanigi OGRETEN sahne. Yoldas senaryolu olarak dusuyor -
            # sahneden once, ki oyuncu kontrolu geri aldiginda onu
            # yerde bulsun ve ogrendigi seyi hemen yapsin.
            self.rescue.unlocked = True
            companion = self.summon_companion()
            companion.die()          # diz coker, olmez
            self.scenes.push(cine.LiftCinematic, character=self.character)
            return
        if room == "cikis":
            # Secilen jest geri geliyor: `on_picked` `HeartCinematic`in
            # kendi parametresi (B15'in `ghost=` kalibinin tersi -
            # orada veri sahneye giriyordu, burada cikiyor).
            self.scenes.push(cine.HeartCinematic, character=self.character,
                             on_picked=self._remember_gesture)

    def _remember_gesture(self, picked) -> None:
        """Secilen jesti kayda tasir - `SaveData.flags`.

        Puan degil **ton**: sonraki sahneler (B18) buna bakabilir.
        """
        self.gesture_key = picked.key if picked is not None else ""
        data = self.save_data
        if data is not None and self.gesture_key:
            data.flags["ch16_gesture"] = self.gesture_key

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
        """Odul **kaldirdigin** kadar.

        B15'in hayalet odulunun ayni kalibi: satir kazanilsa da
        kazanilmasa da ozet ekraninda gorunuyor, cunku kazanamayan da
        boyle bir sey oldugunu ogrenmeli
        (`src/ui/chapter_end.py` gerekcesi).
        """
        self.game.play_sound("chapter_end")
        lifted = self.lifts > 0
        gold = self.earned_gold + (LIFT_BONUS if lifted else 0)
        if lifted:
            self.show_toast(t("chapter16.lifted"), frames=260)
        result = ChapterResult(
            chapter_key="chapter.backtoback",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=gold,
            secrets_found=1 if self.secret_found else 0,
            secrets_total=SECRETS_TOTAL,
            ghost=lifted,
            ghost_bonus=LIFT_BONUS,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 16
            data.chapter_name = "chapter.backtoback"
            data.playtime_frames += self.frames
            data.secrets_found += result.secrets_found
            if lifted:
                data.flags["ch16_lifted"] = True
        from src.scenes.chapter17 import Chapter17Scene
        self.scenes.push(
            ChapterEndScene, result=result,
            on_continue=lambda: self.scenes.set_root(
                Chapter17Scene, character=self.character))

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.frames)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        for chest in self.chests:
            chest.draw(surface, offset)
        # Yoldasi da sahne ciziyor (B9 ile ayni satir) - `PlayScene`
        # yalnizca oyuncuyu ve dusmanlari biliyor.
        if self.companion is not None:
            self.companion.draw(surface, offset)
        self._draw_rescue_ring(surface, offset)

    def _draw_rescue_ring(self, surface: pygame.Surface, offset) -> None:
        """Diz cokmus yoldasin ustunde bir halka - **diegetik sayac**.

        `CLAUDE.md` 9: durum HUD cubuguyla degil dunyanin icinde
        anlatilir. Halka yoldasin ustunde duruyor, tutuldukca doluyor.

        Menzil disindayken sonuk bir daire, menzildeyken parlak: oyuncu
        yeterince yakin olup olmadigini **gorerek** anliyor, deneyerek
        degil.
        """
        companion = self.companion
        if companion is None or not companion.downed:
            return
        ox, oy = offset
        cx = int(companion.body.center_x) - ox
        cy = int(companion.body.top) - oy - 10
        near = self.rescue.reach(self.player, companion)
        base = (palette.color("violet_bright") if near
                else palette.role("ui_text_dim"))

        # Bos halka - noktalarla, cunku 11 piksellik bir cember
        # `draw.circle` ile pikselli ve titrek cikiyor.
        for step in range(16):
            angle = step / 16 * math.tau - math.tau / 4
            x = cx + int(round(math.cos(angle) * RING_RADIUS))
            y = cy + int(round(math.sin(angle) * RING_RADIUS))
            surface.fill(base, (x, y, 1, 1))

        progress = self.rescue.progress
        if progress <= 0.0:
            return
        # Dolan kisim - saat yonunde, tepeden basliyor.
        filled = max(1, int(round(progress * 16)))
        for step in range(filled):
            angle = step / 16 * math.tau - math.tau / 4
            x = cx + int(round(math.cos(angle) * RING_RADIUS))
            y = cy + int(round(math.sin(angle) * RING_RADIUS))
            surface.fill(palette.color("gold"), (x - 1, y - 1, 2, 2))