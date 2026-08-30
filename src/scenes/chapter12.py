"""Bolum 12 - "Mektup". Oynanabilir sahne.

Oda verisi `src/world/rooms/chapter12.py`, ara sahneler
`src/scenes/chapter12_cinematics.py`, mekanik `src/world/rig.py`.

`docs/yapi.md` B12: *"Ardo'nun gectigi yoldan gidiyorsun. (...)
Yoklugunda anlatilan yakinlik. **Tek bir dovus yok**, sadece iz
surme."*

## Bolumde tek bir dusman YOK - ve bu bir kisit degil, tasarim

`docs/ekonomi-uretim.md`: *"Nefes bolumleri zorluk egrisinin
parcasidir. Surekli tirmanan gerilim yorar; dususler zirveleri
yukseltir."* B13 boss'tan sonra, B14 twist'inden once duruyor.

O yuzden bu dosyada `enemies` listesi hic dolmuyor, `hitboxes`
hicbir sey uretmiyor. `PlayScene`'in dovus altyapisi calisiyor ama
**kullanilmiyor** - ayri bir "nefes sahnesi" sinifi yazmadik, cunku
kayit, kamera, HUD, duraklatma ve olum ekrani aynen gerekiyor.

## Ayni bolum, iki zit mahremiyet

Bolumun asil bulusu burada ve **var olan sistemlerden dustu**:

    Rey oynuyor   -> Ardo'nun BILEREK biraktiklarini goruyor
                     (cizdigi ok, birakugi erzak, kazidigi figur)
    Ardo oynuyor  -> Rey'in ISTEMEDEN biraktiklarini goruyor
                     (`src/systems/tracking.py` - ayak izi, kan)

Ikisi de "onun izini surmek" ama biri bir **mektup**, oteki bir
**takip**. Bolumun adi ikisini birden kesiyor. Tek satir ozel kod
yazilmadi: Iz Surme zaten Ardo'da acik, isaretler zaten bolum
icerigi.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import TILE_SIZE
from src.core.input import Action
from src.entities.candle_keeper import CandleKeeper
from src.scenes.play import PlayScene
from src.ui.chapter_end import ChapterEndScene, ChapterResult
from src.ui.i18n import t
from src.world.rig import Mark, Rig
from src.world.rooms.chapter12 import (
    WIDTH as LEVEL_WIDTH,
    BOTTOM_FLOOR, CACHE_GOLD, LEVEL, MARKS, MARKS_TOTAL, RIG_CENTER_TILE,
    SHAFT_BOTTOM, SHAFT_TOP, TOP_FLOOR,
)
from src.world.tilemap import TileMap

# Kafese binmek icin bu kadar yakin olmak gerek (piksel).
BOARD_RANGE = 26.0


class Chapter12Scene(PlayScene):
    """Mektup: bir kuyu, bir kafes, alti iz."""

    chapter_number = 12
    chapter_name_key = "chapter.letter"
    postfx_grade = "descent"
    ambience_preset = "dust"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)
        self.companion = None           # Bolum 10'dan beri yalniz

        self.rig = Rig(
            center_x=RIG_CENTER_TILE * TILE_SIZE + TILE_SIZE * 0.5,
            top_y=SHAFT_TOP * TILE_SIZE,
            bottom_y=SHAFT_BOTTOM * TILE_SIZE,
        )
        self.marks = [Mark(tile_y=y, side=side, key=key, ardo_key=ardo,
                           kind=kind)
                      for y, side, key, ardo, kind in MARKS]
        self.riding = False
        self.landed = False

        keeper = LEVEL.first("candle_keeper")
        self.candle_keeper = (CandleKeeper(keeper.x, keeper.feet_y)
                              if keeper is not None else None)
        self._keeper_seen = False

        self.frames = 0
        self.fired_triggers: set[str] = set()
        self.earned_gold = 0
        self.finished = False
        self.board_hinted = False
        self.brake_hinted = False

    @property
    def marks_found(self) -> int:
        return sum(1 for mark in self.marks if mark.found)

    # --- Dongu ---------------------------------------------------------------
    def update_scene(self) -> None:
        self.frames += 1
        self._update_rig()
        self._update_marks()
        self._update_keeper()
        self._update_triggers()
        self._check_exit()

    def _update_rig(self) -> None:
        body = self.player.body
        if not self.riding:
            # Kafese binmek: uzerine gelmek yetiyor. Ayri bir tus
            # ogretmek nefes bolumunun tonuna aykiri olurdu.
            near = (abs(body.center_x - self.rig.center_x) < BOARD_RANGE
                    and abs(body.feet[1] - self.rig.y) < BOARD_RANGE)
            if near and not self.landed:
                self._board()
            return

        braking = self.game.input.held(Action.DOWN)
        self.rig.update(braking)
        self.rig.carry(body)

        if not self.brake_hinted and self.rig.y > (SHAFT_TOP + 3) * TILE_SIZE:
            self.brake_hinted = True
            self.hint_once("hint_rig_brake", "hint.rig_brake", Action.DOWN)

        if self.rig.landed and not self.landed:
            self._land()

    def _board(self) -> None:
        self.riding = True
        self.rig.start()
        self.game.play_sound("ledge_grab")
        self.show_toast(t("chapter12.descend"), frames=180)

    def _land(self) -> None:
        """Dip. Kafesten iniliyor, yercekimi geri geliyor."""
        self.landed = True
        self.riding = False
        self.rig.release(self.player.body)
        self.player.body.set_feet(self.rig.center_x,
                                  (BOTTOM_FLOOR) * TILE_SIZE)
        self.game.play_sound("land_soft")

    def _update_marks(self) -> None:
        """Yavasken ve dogru tarafta olan isaret **okunuyor**.

        Okumak bir tusa basmak degil: yavaslamak zaten karar. Ustune
        bir de "E'ye bas" koymak ayni karari iki kez sormak olurdu.
        """
        if not self.riding:
            return
        body = self.player.body
        for mark in self.marks:
            if not self.rig.reads(mark, body):
                continue
            mark.found = True
            self._read(mark)

    def _read(self, mark: Mark) -> None:
        self.say(self._voice(mark.key, mark.ardo_key))
        self.game.play_sound("necklace_warm")
        self.particles.burst(
            self.rig.center_x + mark.side * TILE_SIZE * 3, mark.y, 10,
            path="dust", speed=(0.2, 0.9))
        if mark.kind == "cache":
            # Erzak: `docs/yapi.md` *"senin icin birakilmis erzak"*.
            # Kucuk - bu bir odul degil bir jest.
            self.earned_gold += CACHE_GOLD
            self.pickup_juice(gold=True)
        if mark.kind == "figure":
            # ★ Bolumun tepesi. Kolye burada isiniyor - ayni ses
            # Bolum 13'un kafes sahnesinde de var, ikisi akraba anlar.
            self.game.play_sound("necklace_beat")

    def _voice(self, rey_key: str, ardo_key: str):
        """Ayni isaret, iki karakterde iki farkli sey.

        Rey icin bunlar **onun icin birakilmis** seyler; Ardo icin
        Rey'in farkinda olmadan biraktigi izler.

        Iki anahtar da **cagirandan duz dize** geliyor. Ilk surum
        `key + "_ardo"` uretiyordu ve `tests/test_lang.py` on iki
        Ardo repligini "olu anahtar" diye raporladi - hepsi
        kullaniliyordu ama tarayici hesaplanmis adi goremiyor.
        `CLAUDE.md` 9 bunu yaziyor; proje bu tuzaga ucuncu kez dustu.
        """
        from src.ui.dialogue import Line
        if self.character == "ardo":
            return Line("ardo", ardo_key)
        return Line("rey", rey_key)

    def _update_keeper(self) -> None:
        """Mum Bekcisi ucuncu kez - `docs/bolum-03.md` 122.

        *"Mum Bekcisi B7, B12 ve B16'da tekrar cikar. Her seferinde
        biraz daha derinde, biraz daha az mumla."* Burada ticaret
        **yok**: nefes bolumunde bir dukkan acmak tonu kirardi. Yalniz
        duruyor, ve mumu bir oncekinden az.
        """
        if self.candle_keeper is None:
            return
        self.candle_keeper.update()
        near = (abs(self.candle_keeper.x - self.player.body.center_x) < 22
                and abs(self.candle_keeper.feet_y
                        - self.player.body.feet[1]) < 26)
        if near and not self._keeper_seen:
            self._keeper_seen = True
            self.say(self._voice("line.ch12_keeper",
                             "line.ch12_keeper_ardo"))

    def _update_triggers(self) -> None:
        for spot in LEVEL.of("trigger"):
            key = f"trigger{spot.tile_x}_{spot.tile_y}"
            if key in self.fired_triggers:
                continue
            body = self.player.body
            if (abs(body.center_x - spot.x) > TILE_SIZE
                    or abs(body.feet[1] - spot.feet_y) > TILE_SIZE * 2):
                continue
            self.fired_triggers.add(key)
            self._fire_trigger(spot.tile_y)

    def _fire_trigger(self, tile_y: int) -> None:
        from src.scenes import chapter12_cinematics as cine
        if tile_y < TOP_FLOOR:
            self.scenes.push(cine.CampCinematic, character=self.character)
        else:
            self.scenes.push(cine.LetterCinematic, character=self.character,
                             found=self.marks_found, total=MARKS_TOTAL)

    def _check_exit(self) -> None:
        exit_at = LEVEL.first("exit")
        if self.finished or exit_at is None or not self.landed:
            return
        body = self.player.body
        if abs(body.center_x - exit_at.x) > 10:
            return
        self.finished = True
        self._end_chapter()

    def _end_chapter(self) -> None:
        self.game.play_sound("chapter_end")
        result = ChapterResult(
            chapter_key="chapter.letter",
            frames=self.frames,
            best_combo=self.player.combo.best,
            gold=self.earned_gold,
            # **Sirlar degil, IZLER.** Ayni sayac alani ama anlami
            # baska: bir nefes bolumunun olcusu beceri degil yakinlik.
            secrets_found=self.marks_found,
            secrets_total=MARKS_TOTAL,
        )
        data = self.save_data
        if data is not None:
            data.chapter = 12
            data.chapter_name = "chapter.letter"
            data.playtime_frames += self.frames
            data.secrets_found += self.marks_found

        from src.scenes.chapter13 import Chapter13Scene
        self.scenes.push(
            ChapterEndScene, result=result,
            on_continue=lambda: self.scenes.set_root(
                Chapter13Scene, character=self.character))

    # --- Cizim ---------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        """Kuyunun ici - **`cave_backdrop` KULLANILMIYOR.**

        Ilk surum onu cagiriyordu ve ekran goruntusu sorunu tek
        bakista gosterdi: o arka plan yatay magara icin yazilmis, uzak
        tepeler ve gece gogu ciziyor. Bir kuyunun **icinde** gokyuzu
        gorunmesi mekani tamamen yanlis okutuyordu - "asagi iniyorum"
        yerine "disarida kosuyorum".

        Burasi kapali bir sey: iki yanda tas, ortada dipsiz karanlik.
        """
        surface.fill(palette.color("void"))
        ox, oy = offset
        height = surface.get_height()

        # Kuyunun boslugu - asagi indikce koyulasan bir kolon.
        shaft_left = 2 * TILE_SIZE - ox
        shaft_width = (LEVEL_WIDTH - 4) * TILE_SIZE
        surface.fill(palette.color("abyss_dark"),
                     (shaft_left, 0, shaft_width, height))

        # Yatay tas siralari - **hiz hissi buradan geliyor.**
        # Duz bir duvarda kamera kaysa da hicbir sey degismiyordu;
        # gecen siralari saymak inisi olculebilir yapiyor.
        band = TILE_SIZE * 2
        first = (int(oy) // band) * band - oy
        for y in range(int(first), height + band, band):
            surface.fill(palette.color("stone_darkest"),
                         (shaft_left, y, shaft_width, 1))

        # Yan duvarlarin dokusu: duzenli, insan yapimi. Bir kuyu
        # kazilmis bir seydir, magara degil.
        for wall_x in (shaft_left - TILE_SIZE, shaft_left + shaft_width):
            surface.fill(palette.color("stone_dark"),
                         (wall_x, 0, TILE_SIZE, height))
            for y in range(int(first), height + band, band):
                surface.fill(palette.color("stone"), (wall_x, y, TILE_SIZE, 1))
                surface.fill(palette.color("ink"),
                             (wall_x + TILE_SIZE // 2, y, 1, band))

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        for mark in self.marks:
            self._draw_mark(surface, offset, mark)
        self._draw_rig(surface, offset)
        if self.candle_keeper is not None:
            self.candle_keeper.draw(surface, offset)

    def _draw_rig(self, surface: pygame.Surface, offset) -> None:
        """Kafes: tahta zemin, iki yandan zincir, tavana kadar.

        Zincir **yukari dogru** ciziliyor ve ekranin ustune tasiyor -
        inerken tek gorunen sey o. Kafesin nereden asili oldugu
        gorunmezse "duser gibi" hissettiriyordu; zincir onu bir
        **duzenek** yapiyor.
        """
        ox, oy = offset
        left = int(self.rig.left) - ox
        top = int(self.rig.y) - oy
        width = int(self.rig.width)

        for side in (left + 1, left + width - 3):
            surface.fill(palette.color("stone_dark"), (side, top - 400, 2, 400))
            # Halkalar - zincirin hareket ettigi buradan okunuyor.
            phase = int(self.rig.y) % 8
            for link in range(top - 400 + phase, top, 8):
                surface.fill(palette.color("stone_light"), (side, link, 2, 3))

        surface.fill(palette.color("earth_dark"), (left, top, width, 5))
        surface.fill(palette.color("earth"), (left, top, width, 1))
        for post in (left, left + width - 2):
            surface.fill(palette.color("stone_dark"), (post, top - 10, 2, 12))

        # Fren basiliyken kivilcim - girdi GORUNUR olmali.
        if self.rig.braking and self.rig.speed > 0.05:
            spark = 0.5 + 0.5 * math.sin(self.frames * 0.7)
            colour = tuple(int(c * spark) for c in palette.color("ember_light"))
            surface.fill(colour, (left - 2, top + 2, 2, 2))
            surface.fill(colour, (left + width, top + 2, 2, 2))

    def _draw_mark(self, surface: pygame.Surface, offset, mark: Mark) -> None:
        """Ardo'nun biraktigi sey.

        Okunmadan once **soluk** - orada bir sey oldugu belli ama ne
        oldugu degil. Okununca renkleniyor. Yani oyuncu "orada bir sey
        var" diye yavasliyor, karsiligini gorunce yavaslamayi
        ogreniyor. Ikinci isaretten sonra frene basmak refleks oluyor.
        """
        ox, oy = offset
        x = int(self.rig.center_x + mark.side * TILE_SIZE * 3.2) - ox
        y = int(mark.y) - oy
        if mark.found:
            tone = palette.color("gold" if mark.kind == "figure"
                                 else "ember_light")
        else:
            # Okunmadan once soluk ama **gorulebilir**. Ilk degerler
            # (0.35 tabanli) ekranda neredeyse yoktu - oyuncu
            # yavaslamak icin once orada bir sey oldugunu gormeli.
            # Taban genligin ustunde: nabzin dibinde negatife dusen
            # bir carpan `surface.fill`i patlatiyor (Yankilayan'da
            # tam bu oldu).
            pulse = 0.62 + 0.38 * math.sin(self.frames * 0.05 + mark.tile_y)
            tone = tuple(int(c * pulse) for c in palette.color("bone"))

        # Duvarda kazinmis bir oyuk - isaretin ARKASI. Tek basina
        # ince cizgiler tas dokusunda kayboluyordu.
        surface.fill(palette.color("stone_darkest"), (x - 7, y - 8, 15, 17))

        if mark.kind == "cache":
            surface.fill(tone, (x - 4, y - 3, 9, 7))
            surface.fill(palette.color("stone_darkest"), (x - 2, y - 1, 5, 1))
        elif mark.kind == "camp":
            for index in range(3):
                surface.fill(tone, (x - 4 + index * 4, y + index, 3, 2))
        elif mark.kind == "figure":
            # Kucuk bir insan figuru - **bes piksel**. Fazlasi
            # karikatur olurdu; bu kadari "biri cizmis" okunuyor.
            surface.fill(tone, (x, y - 5, 2, 2))
            surface.fill(tone, (x, y - 2, 2, 4))
            surface.fill(tone, (x - 2, y - 1, 6, 1))
            surface.fill(tone, (x - 1, y + 2, 1, 2))
            surface.fill(tone, (x + 2, y + 2, 1, 2))
        else:
            arrow = -mark.side
            for index in range(4):
                surface.fill(tone, (x + arrow * index, y - index, 2, 2))
                surface.fill(tone, (x + arrow * index, y + index, 2, 2))

    def debug_lines(self) -> list[str]:
        return [f"kafes y={self.rig.y:.0f} hiz={self.rig.speed:.2f} "
                f"fren={self.rig.braking}  iz {self.marks_found}/"
                f"{MARKS_TOTAL}  bindi={self.riding} indi={self.landed}"]
