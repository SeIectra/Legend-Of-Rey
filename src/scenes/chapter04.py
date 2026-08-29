"""Bolum 4 - "Kayit Odasi". Oynanabilir sahne.

Oda geometrisi `src/world/rooms/chapter04.py` icinde; burasi onu oynatiyor
(chapter02/03 ile *ayni* iskelet: `_room_at`/`_enter_room`/`_narrate_room`).

## Bu bolum bir **nefes**

`docs/yapi.md` B4: *"Dovus yok. Onceki maceracinin kampi: iskelet, gunluk
(resimli, kelimesiz), yarim harita. Ilerleme: ilk yetenek agaci ekrani.
Rey burada kolyeyi ilk kez cevirir - sessiz karakter ani."*
`docs/gdd.md` ★nefes diye isaretliyor.

Bunun kod tarafindaki karsiligi **eksiltmek**: dusman yok, arena yok,
kapi/anahtar yok, isik maskesi yok, mesale ekonomisi yok. Bolum 3'un
`Chapter03Scene`'i 700 satirdi cunku uc mekanigi ayni anda tasiyordu;
burada tasinacak mekanik yok. Kalan dort sey - kamp, gunluk, harita,
kolye - hepsi ayni sekilde calisiyor: **yaklas, bir sey olsun.**

## Uc jest, uc farkli giris bicimi

    kamp      tusa basilir   (bir karar: dinlenmek istiyor musun)
    gunluk    yaklasilir     (kelimesiz - tus istemek celiski olurdu)
    harita    dokunulur      (odul; odulle oyuncu arasina tus konmaz)
    kolye     kendiliginden  (karakterin ani, oyuncunun degil)

Bu dagilim keyfi degil: her biri **kimin** eylemi oldugunu anlatiyor.

## Yetenek agaci ekrani burada degil

`open_skill_tree()` bilerek bos. Ekran ayri bir iste yaziliyor; bu sahne
yalnizca **ne zaman** acilmasi gerektigini biliyor (kampta dinlenince).
Boylece iki is birbirini beklemeden ilerliyor ve baglanti tek satir.
"""
from __future__ import annotations

import pygame

from src.config import (
    REST_SKILL_POINTS,
    CAMP_NEAR_RANGE, HALF_MAP_PICKUP_RANGE, JOURNAL_FADE_FRAMES,
    JOURNAL_NEAR_RANGE, JOURNAL_PAGE_FRAMES, NECKLACE_MOMENT_FRAMES,
    NECKLACE_MOMENT_RANGE, NECKLACE_RESTORE_AT, TILE_SIZE,
)
from src.core.input import Action
from src.core.juice import ImpactWeight
from src.scenes import chapter04_render as render
from src.scenes.play import PlayScene
from src.systems import abilities
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.dialogue import Line
from src.ui.i18n import t
from src.world import cave_backdrop
from src.world.pickups import Chest
from src.world.rooms.chapter04 import (
    CHAPTER4_CHEST_GOLD, FIRE_TILE, HALF_MAP_TILE, JOURNAL_TILE, LEVEL,
    NECKLACE_TILE, ROOM_STARTS, SECRETS_TOTAL, TORCHES,
)
from src.world.tilemap import TileMap

# Kayit bayraklari. Bolum 4'un butun kalici izi bu uc anahtar - hepsi
# `SaveData.flags` icinde, cunku bunlar ilerleme degil **yasanmis an**:
# ileride (B12 "Mektup", B14 twist) "bu oyuncu kampi gordu mu" diye
# sorulabilsin diye duruyorlar.
FLAG_RESTED = "ch04_rested"
FLAG_HALF_MAP = "ch04_half_map"
FLAG_NECKLACE = "ch04_necklace_turned"


class Chapter04Scene(PlayScene):
    """Kayit Odasi: dort oda, sifir dusman, uc buluntu ve bir sessiz an."""

    # Bolum basi karti (src/ui/chapter_card.py) - oynanisi durdurmaz.
    chapter_number = 4
    chapter_name_key = "chapter.record_room"
    postfx_grade = "record"     # src/art/postfx.py
    ambience_preset = "dust"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)

        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        # Bolum 3'ten geliyoruz: kilic ve kacinma elde. Burada dovus yok
        # ama yetenekler kaybolmus gibi gorunmesin - oyuncu tuslara
        # basarsa karsiligini bulmali.
        self.player.grant(abilities.SWORD)
        self.player.grant(abilities.DODGE)

        self.chests = [Chest(spot.x, spot.feet_y, gold=CHAPTER4_CHEST_GOLD)
                       for spot in LEVEL.of("chest")]

        self.room = ""
        self.entered_rooms: set[str] = set()
        self.room_frames = 0

        # Kamp
        self.fire_lit = False
        self.rested = False
        self._rest_hinted = False

        # Kelimesiz gunluk - `journal_alpha` 0..1 arasi suzulerek gidip
        # geliyor. Ani acilip kapanan bir panel "arayuz" gibi carpiyor;
        # suzulen panel bir nesneye **yaklasmis** olmak gibi hissettiriyor.
        self.journal_alpha = 0.0
        self.journal_page = 0
        self.journal_frames = 0
        self.journal_seen = False

        # Yarim harita
        self.map_taken = False

        # Kolye ani
        self.necklace_frames = 0
        self.necklace_ready = False      # Noktadan gecildi, an sirasini bekliyor
        self.necklace_active = False
        self.necklace_done = False
        self._necklace_restored = False

        self.earned_gold = 0
        self.frames = 0
        self.finished = False

        self._enter_room(self._room_at(self.player.body.center_x))

    # --- Odalar ---------------------------------------------------------------
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
        self._narrate_room(name)

    def _narrate_room(self, name: str) -> None:
        """Odaya ilk girisin repligi. Kirik merdiven **sessiz** - jest yeter.

        Kolye anina hicbir replik dusmuyor: `docs/yapi.md` onu "sessiz
        karakter ani" diye tanimliyor. Esik odasinin repligi oyuncu odaya
        **girerken** soyleniyor, an ise odanin ortasinda basliyor - araya
        mesafe koymak bilincli, yoksa ses jestin uzerine binerdi.
        """
        if name == "inis":
            self._voice("line.ch04_echo_enter", "line.ch04_ardo_enter")
        elif name == "kamp":
            self._voice("line.ch04_echo_camp", "line.ch04_ardo_camp")
        elif name == "esik":
            self._voice("line.ch04_echo_exit", "line.ch04_ardo_exit")

    def _voice(self, echo_key: str, ardo_key: str) -> None:
        """Yanki konusur, Yanki yoksa oynanan karakter konusur.

        Bolum 1/2/3 ile ayni desen (`has_echo`, DEVIR.md 3.7): Yanki
        Rey'in laneti, Ardo onu duymaz. Ardo ayni anlari kendi gozlemiyle
        karsiliyor - odalar onun icin sessiz kalmasin ama sahip olmadigi
        bir gucun sesini de duymasin.
        """
        if self.has_echo:
            self.say(Line("echo", echo_key))
        else:
            self.say(Line(self.character, ardo_key))

    # --- Dongu ------------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self.room_frames += 1

        room = self._room_at(self.player.body.center_x)
        if room != self.room:
            self._enter_room(room)

        self._update_camp()
        self._update_journal()
        self._update_half_map()
        self._update_necklace()
        self._update_chests()
        self._check_exit()

    # --- Kamp -------------------------------------------------------------------
    def _tile_center(self, tile: tuple[int, int]) -> tuple[float, float]:
        return (tile[0] * TILE_SIZE + TILE_SIZE * 0.5,
                (tile[1] + 1) * TILE_SIZE)

    def _near(self, tile: tuple[int, int], range_px: float) -> bool:
        """Oyuncu bu tile'a yakin mi? Yatayda **ve** dikeyde.

        Yalniz yatay bakmak Oda 3'te yanlis sonuc verirdi: sahanligin
        ustundeki oyuncu, altindaki bir nesneye "yakin" sayilirdi.
        """
        x, feet_y = self._tile_center(tile)
        return (abs(self.player.body.center_x - x) < range_px
                and abs(self.player.body.feet[1] - feet_y) < TILE_SIZE * 2.0)

    def _update_camp(self) -> None:
        if self.rested:
            return
        if not self._near(FIRE_TILE, CAMP_NEAR_RANGE):
            return
        if not self._rest_hinted:
            self._rest_hinted = True
            # Ogreti metni son care ama burada **sart**: dinlenme bu
            # bolumun tek tusla yapilan isi ve baska hicbir yerde
            # ogretilmiyor. Tus adi baglantidan okunuyor - oyuncu tusu
            # yeniden atadiysa ekranda kendi tusunu gormeli.
            self.show_toast(t("chapter04.hint_rest",
                              key=self.game.input.binding_label(Action.INTERACT)),
                            frames=180)
        if self.game.input.pressed(Action.INTERACT):
            self._rest()

    def _rest(self) -> None:
        """Sonmus ates yeniden yanar. Iyilesme + yetenek agaci ani.

        Atesin **yanmasi** onemli: dinlenmenin gorunur karsiligi bu.
        Yalnizca can dolsaydi oyuncu bir sey oldugunu ancak HUD'a bakarak
        anlardi; oda isinirsa bakmasi gerekmiyor.
        """
        self.rested = True
        self.fire_lit = True
        self.player.heal(self.player.max_health)
        if self.save_data is not None:
            self.save_data.flags[FLAG_RESTED] = True
            # Ilk yetenek puani BURADA veriliyor. Bos bir agac acmak
            # "kazanim" degil "menu" hissi verirdi; oyuncu agaci ilk kez
            # gorurken harcayacak bir seyi olmali. `docs/gdd.md` 4 puan
            # kazanimini nefes bolumlerine (B4, B8, B12) bagliyor.
            from src.systems import skilltree
            skilltree.grant_points(self.save_data, REST_SKILL_POINTS)
        x, y = self._tile_center(FIRE_TILE)
        self.juice.explosion(x, y - 8, ImpactWeight.NORMAL)
        self.particles.burst(x, y - 8, 16, path="spark", speed=(0.4, 1.8),
                             life=(20, 40))
        self.game.play_sound("torch_light")
        self.show_toast(t("chapter04.rested"), frames=200)
        self.open_skill_tree()

    def open_skill_tree(self) -> None:
        """Yetenek agaci ekranini acar (`src/ui/skill_tree.py`).

        Bindirme olarak aciliyor: alttaki sahne donuyor ama gorunur
        kaliyor, arkasi bulaniklastiriliyor. Oyuncu agaci acinca oyundan
        cikmiyor - kamp orada duruyor, ates yanmaya devam ediyor.
        """
        from src.systems import skilltree
        from src.ui.skill_tree import SkillTreeScene
        self.scenes.push(SkillTreeScene, save_data=self.save_data,
                         tree=skilltree)

    # --- Kelimesiz gunluk ---------------------------------------------------------
    def _update_journal(self) -> None:
        """Yaklasinca acilir, sayfalar kendi cevrilir, uzaklasinca kapanir.

        Tus **yok**: gunlukte tek kelime yok, o yuzden "cevirmek icin X"
        diyen bir yazi da olamazdi (docs/yapi.md B4: kelimesiz). Panel
        oynanisi durdurmuyor - oyuncu okurken yuruyebilir, yuruyunce
        kapanir. Kalmak bir **secim**.
        """
        near = self._near(JOURNAL_TILE, JOURNAL_NEAR_RANGE)
        step = 1.0 / max(1, JOURNAL_FADE_FRAMES)
        if near:
            self.journal_alpha = min(1.0, self.journal_alpha + step)
            self.journal_frames += 1
            if self.journal_frames % JOURNAL_PAGE_FRAMES == 0:
                self.journal_page = (self.journal_page + 1) % render.page_count()
            if not self.journal_seen:
                self.journal_seen = True
                self.camera.linger(24)
            return
        self.journal_alpha = max(0.0, self.journal_alpha - step)
        if self.journal_alpha <= 0.0:
            # Bastan basliyor: geri donen oyuncu ilk sayfayi gorsun,
            # birakip gittigi yeri degil - gunluk bir kayit degil bir
            # **hikaye**, ortasindan baslamamali.
            self.journal_frames = 0
            self.journal_page = 0

    # --- Yarim harita -------------------------------------------------------------
    def _update_half_map(self) -> None:
        if self.map_taken or not self._near(HALF_MAP_TILE,
                                            HALF_MAP_PICKUP_RANGE):
            return
        self.map_taken = True
        if self.save_data is not None:
            self.save_data.flags[FLAG_HALF_MAP] = True
        self.pickup_juice()
        self.show_toast(t("chapter04.map_found"), frames=200)
        self._voice("line.ch04_echo_map", "line.ch04_ardo_map")

    # --- Kolye ani ------------------------------------------------------------------
    def _update_necklace(self) -> None:
        """Rey kolyeyi ilk kez cevirir. Kelimesiz, kesintisiz.

        Oynanis **durmuyor**: oyuncu yurumeye devam edebilir, an onun
        etrafinda olup bitiyor. Kesme yapsaydik bu bir ara sahne olurdu;
        `docs/yapi.md` bunu "sessiz karakter ani" diye tanimliyor -
        sahnenin degil karakterin ani.
        """
        if self.necklace_active:
            self.necklace_frames += 1
            # Kamera hafifce oyalaniyor: goz oyuncuya donsun.
            self.camera.linger(4)
            if (self.necklace_frames >= NECKLACE_RESTORE_AT
                    and not self._necklace_restored):
                self._necklace_restored = True
                self._necklace_reward()
            if self.necklace_frames >= NECKLACE_MOMENT_FRAMES:
                self.necklace_active = False
                self.necklace_done = True
                self.necklace_frames = 0
            return
        if self.necklace_done or self.room != "esik":
            return
        # Tetik bir kez **kuruluyor**, sonra bekliyor. Sadece "yakinsa ve
        # replik bittiyse basla" deseydik, esige girerken soylenen cumleyi
        # onaylamadan yuruyen oyuncu noktanin uzerinden gecer ve ani hic
        # yasamazdi. Kurulan tetik oyuncuyu birakmiyor: replik biter
        # bitmez an basliyor, oyuncu nerede olursa olsun (an zaten
        # oyuncunun etrafinda geciyor).
        if not self.necklace_ready:
            if not self._near(NECKLACE_TILE, NECKLACE_MOMENT_RANGE):
                return
            self.necklace_ready = True
        # Replik surerken baslamiyor: "sessiz karakter ani" bir repligin
        # uzerine binerse sessiz kalmaz.
        if not self.dialogue.done:
            return
        self.necklace_active = True
        self.necklace_frames = 1
        self.particles.burst(self.player.body.center_x,
                             self.player.body.center_y - 5, 8, path="echo",
                             speed=(0.15, 0.6), life=(24, 48), gravity=0.0)

    def _necklace_reward(self) -> None:
        """Anin karsiligi: Yanki bir kademe berraklasiyor.

        `docs/gdd.md` 4: *"Kademe kazanimi: kontrol noktalari ve nefes
        bolumleri (B4, B8, B12)."* Ardo'da Yanki yok - onda an ayni
        sekilde yasaniyor ama kademe verilmiyor; ona verilecek bir sey
        olmadigi icin **eksik** degil, farkli (DEVIR.md 3.7).
        """
        if self.save_data is not None:
            self.save_data.flags[FLAG_NECKLACE] = True
        x, y = self.player.body.center_x, self.player.body.center_y - 5
        self.particles.burst(x, y, 14, path="echo", speed=(0.3, 1.2),
                             life=(24, 52), gravity=0.0)
        self.game.play_sound("necklace_beat")
        if self.echo is not None and self.echo.restore():
            self.on_echo_tier_changed(self.echo.tier, gained=True)

    # --- Sandiklar --------------------------------------------------------------------
    def _update_chests(self) -> None:
        for chest in self.chests:
            chest.update()
            if chest.opened or not chest.rect.colliderect(self.player.hurtbox):
                continue
            if not chest.open():
                continue
            self.earned_gold += chest.gold
            if self.save_data is not None:
                self.save_data.gold += chest.gold
            self.particles.burst(chest.x, chest.feet_y - 8, 14, path="spark",
                                 speed=(0.5, 2.0), life=(18, 34))
            self.juice.explosion(chest.x, chest.feet_y - 6, ImpactWeight.NORMAL)
            self.game.play_sound("chest_open")
            self.show_toast(t("chapter04.gold_found", count=chest.gold))

    # --- Cikis ---------------------------------------------------------------------------
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
            chapter_key="chapter.record_room",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            secrets_found=0,
            secrets_total=SECRETS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 4
            data.chapter_name = "chapter.record_room"
            data.playtime_frames += self.frames
            data.best_combo = max(data.best_combo, self.player.combo.best)
            data.secrets_total += SECRETS_TOTAL
            if "chapter.record_room" not in data.chapters_cleared:
                data.chapters_cleared.append("chapter.record_room")
        # Bolum 5 ("Sular") henuz yok - ozet ekrani kapaninca ana menuye
        # donuluyor. Bilincli bir uc: Bolum 3'un sonu Bolum 4 yazilana
        # kadar aynen boyleydi.
        self.scenes.push(ChapterEndScene, result=result)

    # --- Cizim ------------------------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw(surface, offset, self.game.frame)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        cave_backdrop.draw_torches(surface, offset, TORCHES, self.game.frame)
        for chest in self.chests:
            chest.draw(surface, offset, self.game.frame)
        render.draw_camp(self, surface, offset)
        render.draw_half_map(self, surface, offset)
        render.draw_necklace(self, surface, offset)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        render.draw_journal_panel(self, surface)

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"oda {self.room} ({self.room_frames})  ates {self.fire_lit}  "
            f"gunluk {self.journal_page}/{self.journal_alpha:.2f}  "
            f"harita {self.map_taken}  kolye {self.necklace_done}"]
