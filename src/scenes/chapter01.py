"""Bolum 1 - Koy. Oynanabilir sahne.

Oda verisi ve prolog sirasi `src/world/rooms/chapter01.py` icinde; burasi
onu oynatiyor. Ayrim bilincli: bir bolumu yeniden dengelemek motoru
degistirmemeli.

## Prolog kontrolu geri veriyor, elinden almiyor

Ilk yetmis kare Rey uyanirken oyuncu **zaten oynayabilir**. Ara sahne
degil, sahnenin kendisi. Tek istisna Cemo'nun cekildigi an: orada oyuncu
kosar ama yetismez - bu bir kisitlama degil, bir **deneyim**. Cemo'yu
kurtaramayacagini izleyerek degil deneyerek ogrenirsin.

## Ogretiler diegetik

"Sag/sol ile yuru" yazan bir kutu yok. Oyuncu hareket etmezse yerdeki
tozda bir yon isareti belirir; saldiri gerekince Rey'in eli kabzaya gider.
Metin son care olarak, ekranin altinda, sonuk.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.animation import CHARACTERS
from src.art.animator import Animator
from src.art.glow import radial_glow
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH, TILE_SIZE
from src.core.input import Action
from src.core.juice import ImpactWeight
from src.scenes.play import PlayScene
from src.ui import balloon, text
from src.ui.dialogue import Line
from src.ui.i18n import t
from src.entities.enemies.shambler import Shambler
from src.entities.villager import Villager
from src.systems import abilities
from src.world.rooms.chapter01 import (
    ECHO_TUTORIAL_TILE, LEVEL, PROLOGUE, RIFT_TILE, SCENERY,
    TUTORIAL_ATTACK_AFTER, TUTORIAL_MOVE_AFTER,
)
from src.scenes import chapter01_render
from src.world import village_backdrop
from src.world.tilemap import TileMap

# Yarik **Cemo'nun oldugu yerde** aciliyor, sabit bir tile'da degil.
# Sabit konum denendi ve kirildi: oyuncu prolog boyunca gezinebiliyor, uzaga
# giderse sahne ekran disinda oluyor; yakinsa Rey yariga Cemo'dan once
# variyor ve "yetisemezsin" ani hic olusmuyordu. RIFT_TILE artik yalnizca
# bolum tasariminda nerede olacaginin notu.
CEMO_SINK_SPEED = 0.42
HINT_Y = INTERNAL_HEIGHT - 26
SHOCK_LOCK_FRAMES = 46   # Rey yerden kalkana kadar

# Bir beat'in repligi suresi icinde bitmezse (oyuncu onaylamadi, diyalog
# kendi otomatik-ilerleme suresini bekliyor) beat en fazla bu kadar uzar.
# Yoksa bir sonraki beat'in `_on_beat_start()`'i kuyrugu **aninda** degistirir
# ve okunmamis bir replik (orn. "gift" beatindeki Rey'in tesekkuru) sessizce
# kaybolur - Arda'nin "bunlar cok anlamsiz cumleler" geri bildiriminin
# kaynagi buydu. Azami: sonsuza dek beklemez, sahne kilitlenmez.
DIALOGUE_GRACE_FRAMES = 100

# --- Kolyenin verilisi ------------------------------------------------------
# Kolye bir donem hic EL DEGISTIRMIYORDU: Cemo'nun basinda bir ikon
# beliriyor, sonra "alone" adiminda sessizce `necklace = True` oluyordu.
# Oyunun butun hikayesi o kolyeye asili (docs/yapi.md B1: "Elde sadece
# kolye") ama oyuncu onun kendisine gectigi ani hic gormuyordu.
#
# Artik "gift" adiminin bu oranindan sonra kolye Cemo'dan ayrilip
# oyuncuya dogru bir yay cizerek gidiyor; vardigi karede parlama +
# parcacik + ses tetikleniyor. Bir jest, bir replikten daha iyi anlatir.
GIFT_RELEASE_AT = 0.55       # "gift" adiminin ne kadari gecince firlar
GIFT_FLIGHT_FRAMES = 34      # Ucus suresi
GIFT_ARC_HEIGHT = 14.0       # Yayin tepe yuksekligi (piksel)
NECKLACE_CHEST_OFFSET = 5.0  # Oyuncunun merkezinden gogse kadar


class Chapter01Scene(PlayScene):
    """Koy. Kolye verilir, Cemo kacirilir."""

    footstep_sound = "step_earth"    # Koy toprak zemini - zindan tasi degil

    # Bolum basi karti (src/ui/chapter_card.py) - oynanisi durdurmaz.
    chapter_number = 1
    chapter_name_key = "chapter.village"
    postfx_grade = "village"   # src/art/postfx.py
    ambience_preset = "night"

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)
        # `amb_village_night` donguluk sesi kaldirildi (Arda'nin canli
        # oynanis geri bildirimi: sentezlenmis surekli sesler "cizirti
        # gibi, rahatsiz edici"). Kisa/tek seferlik efektler kaliyor.

        spawn = LEVEL.first("player")
        self.player = self.make_player(spawn.x, spawn.feet_y)

        cemo_at = LEVEL.first("cemo")
        self.cemo = Animator("cemo")
        self.cemo.play("idle")
        self.cemo_x = cemo_at.x
        self.cemo_y = cemo_at.feet_y
        self.cemo_sink = 0.0         # Yariga ne kadar gomuldu
        self.cemo_gone = False
        self.rift_x = RIFT_TILE[0] * TILE_SIZE + TILE_SIZE // 2
        self.rift_y = (RIFT_TILE[1] + 1) * TILE_SIZE

        # Prolog durumu
        self.beat_index = 0
        self.beat_frames = 0
        self.necklace = False        # Rey kolyeyi aldi mi
        self.rift = 0.0              # Yarigin acilma orani 0..1
        self.echo_taught = False

        # Kolyenin ucusu: -1 = henuz firlamadi, 0..GIFT_FLIGHT_FRAMES = havada.
        self.gift_frames = -1
        self.gift_from = (0.0, 0.0)  # Firladigi nokta (dunya koordinati)

        # Yaratiklar prologdan **sonra** cikar: koy once sakin olmali,
        # yoksa Cemo'nun kacirilisi bir dovusun icinde kayboluyor.
        self.creatures_released = False

        # Kilic: yaratiklardan once duruyor. Rey silahsiz basliyor ve ilk
        # yaratigi gorunce kacacak yeri yok - kilici alma ani bir rahatlama
        # oluyor. Once ihtiyaci hissettiriyoruz, sonra veriyoruz.
        #
        # **Ardo icin YOK** - o zaten kilicla basliyor (egitimli yabanci,
        # weapons.starting_weapon). Prop yine de cizilseydi Ardo, elinde
        # zaten kilic varken yerde "al beni" diyen ikinci bir kilica
        # bakardi - Arda'nin bildirdigi tam bu celiskiydi ("karakter
        # kilici almadan once de kilici oluyor").
        sword_at = LEVEL.first("pickup_sword")
        self.sword_pos = ((sword_at.x, sword_at.feet_y - 10)
                          if sword_at and self.character != "ardo" else None)

        # Koyluler: her evin onunde bir tane, kapisi kendi evi.
        # Arda'nin istegi - "olaylar patlak verdiginde koyluler evlerine
        # kacsin". Kayip boylece Cemo'yla sinirli kalmiyor, koyun kendisi
        # bosaliyor. `seed` her koyluye kendi ritmini veriyor; `random`
        # yok, ayni sahne her acilista ayni sekilde yasiyor.
        ground_y = LEVEL.first("player").feet_y
        self.villagers = []
        for index, (tx, ty, tw, th, kind) in enumerate(SCENERY):
            if kind != "house":
                continue
            door_x = (tx + tw * 0.5) * TILE_SIZE
            # Kapinin biraz yanindan basliyor - hepsi kapida durmasin.
            start_x = door_x + (12 if index % 2 else -12)
            self.villagers.append(
                Villager(start_x, ground_y, door_x, seed=index))
        self.villagers_fled = False

        # Ogreti durumu
        self.moved = False
        self.attacked = False
        self.finished = False

        # Ilk adimin kendisi de tetiklenmeli. `_on_beat_start` yalnizca
        # adim **degisince** cagriliyor; ilk adim ("wake") icin hic
        # calismiyordu ve o repligi kimse duymuyordu.
        self._on_beat_start()

    @property
    def beat(self) -> str:
        if self.beat_index >= len(PROLOGUE):
            return "play"
        return PROLOGUE[self.beat_index][1]

    # --- Dongu --------------------------------------------------------------
    def update_scene(self) -> None:
        self._advance_prologue()
        self._update_rift()
        self._update_cemo()
        self._update_gift()
        self._update_villagers()
        self._watch_player()

    # --- Kolyenin verilisi --------------------------------------------------
    @property
    def gift_flying(self) -> bool:
        return 0 <= self.gift_frames < GIFT_FLIGHT_FRAMES

    @property
    def gift_progress(self) -> float:
        if not self.gift_flying:
            return 0.0
        return self.gift_frames / GIFT_FLIGHT_FRAMES

    def _necklace_target(self) -> tuple[float, float]:
        """Kolyenin varacagi nokta - oyuncunun gogsu."""
        body = self.player.body
        return (body.center_x, body.center_y - NECKLACE_CHEST_OFFSET)

    def gift_position(self) -> tuple[float, float]:
        """Ucus sirasindaki dunya konumu. Duz cizgi + parabolik yay.

        Duz gitseydi "isinlandi" gibi okunurdu; yay onu ATILMIS bir nesne
        yapiyor - kucuk bir detay ama jesti fiziksel kiliyor.
        """
        t_value = self.gift_progress
        fx, fy = self.gift_from
        tx, ty = self._necklace_target()
        x = fx + (tx - fx) * t_value
        y = fy + (ty - fy) * t_value
        y -= math.sin(t_value * math.pi) * GIFT_ARC_HEIGHT
        return (x, y)

    def _update_gift(self) -> None:
        # Firlatma ani: "gift" adiminin belli bir orani gecince.
        if self.gift_frames < 0 and self.beat == "gift":
            length = PROLOGUE[self.beat_index][0]
            if self.beat_frames >= length * GIFT_RELEASE_AT:
                foot = CHARACTERS["cemo"].foot_y
                self.gift_from = (self.cemo_x,
                                  self.cemo_y - foot - balloon.height_of())
                self.gift_frames = 0
            return

        if not self.gift_flying:
            return

        self.gift_frames += 1
        if self.gift_frames < GIFT_FLIGHT_FRAMES:
            return

        # Vardi. Kazanim ani: parlama + parcacik + ses **ayni karede**
        # (CLAUDE.md 7'nin uclu senkron kurali - ayri cagrilirsa kare
        # kaymasi olur ve his bozulur).
        self.necklace = True
        tx, ty = self._necklace_target()
        self.juice.explosion(tx, ty, ImpactWeight.NORMAL)
        self.particles.burst(tx, ty, count=12, path="spark")
        self.game.play_sound("item_pickup")

    def _update_rift(self) -> None:
        """Yarigin acilip kapanmasi Cemo'dan **bagimsiz**.

        Bir donem `_update_cemo` icindeydi; Cemo cekilince o fonksiyon erken
        donuyor ve yarik sonsuza kadar acik kaliyordu.
        """
        was_open = self.rift > 0.0
        if self.beat in ("taken", "chase"):
            self.rift = min(1.0, self.rift + 0.02)
        else:
            self.rift = max(0.0, self.rift - 0.03)
        if was_open and self.rift <= 0.0:
            self.game.play_sound("rift_close")

    def _advance_prologue(self) -> None:
        if self.beat_index >= len(PROLOGUE):
            return
        self.beat_frames += 1
        length = PROLOGUE[self.beat_index][0]
        if self.beat_frames < length:
            return
        # Sure doldu ama repligi (varsa) henuz bitmediyse DIALOGUE_GRACE_
        # FRAMES kadar daha bekle - `self.dialogue.done` cok-replikli bir
        # beat'te ikinci satirin da (onaylanarak ya da kendiliginden)
        # gosterilmis olmasini garanti eder.
        if (not self.dialogue.done
                and self.beat_frames < length + DIALOGUE_GRACE_FRAMES):
            return
        self.beat_index += 1
        self.beat_frames = 0
        self._on_beat_start()

    def _on_beat_start(self) -> None:
        # Replikler jestin **yerine** degil yanina geliyor. Cemo'nun yariga
        # cekildigi an ("chase") hala kelimesiz - orada bir replik ani
        # ucuzlatirdi.
        # `auto_advance=True`: bu repliklerin hepsi `_advance_prologue()`'un
        # beat-zamanlayicisiyla yarisiyor (bkz. DIALOGUE_GRACE_FRAMES) -
        # oyuncu onaylamasa bile dizinin tamami gosterilmeli. Asagidaki
        # `sword`/`wall` replikleri (etkilesimle tetiklenir, zamanlayici
        # yok) bilerek varsayilanda kaliyor.
        if self.beat == "wake":
            # Sesin ilk kelimesi. Tek kelime - Rey uyanirken.
            self.say(Line("echo", "line.ch01_echo_first"), auto_advance=True)
        elif self.beat == "gift":
            self.say(Line("cemo", "line.ch01_cemo_gift"),
                     Line("rey", "line.ch01_rey_thanks"), auto_advance=True)
        elif self.beat == "alone":
            self.say(Line("echo", "line.ch01_echo_alone"), auto_advance=True)

        if self.beat == "taken":
            # Yer sarsilir. Radyal - yarilmanin yonu yok.
            # Yarik Cemo'nun ayaginin dibinde acilir.
            self.rift_x = self.cemo_x
            self.rift_y = self.cemo_y
            self.juice.explosion(self.rift_x, self.rift_y,
                                 ImpactWeight.FINISHER)
            self.game.play_sound("rift_open")
            # Sarsinti Rey'i yere serer. **Yetisememesinin sebebi bu.**
            # Yoksa Rey 2.0 piksel/kare kosuyor ve Cemo'dan once yariga
            # varirdi; "kurtaramadin" ani hic olusmazdi.
            self.player.control_locked = SHOCK_LOCK_FRAMES
            self.player.body.vx = -1.8
            self.player.body.vy = -1.2
            # Ses ilk kez burada duyuluyor: yarik acilirken. Iki kelime.
            self.say(Line("echo", "line.ch01_echo_rift"), auto_advance=True)
        elif self.beat == "alone":
            # `self.necklace` burada DEGIL, kolye ucusu varinca ayarlaniyor
            # (bkz. _update_gift). Eskiden burada sessizce True oluyordu ve
            # oyuncu kolyenin kendisine gectigi ani hic gormuyordu.
            self.cemo_gone = True
        elif self.beat == "play":
            self._release_creatures()

    def _update_villagers(self) -> None:
        """Koyluler gezinir; yarik acilinca evlerine kacar.

        Tetikleyici "taken" adimi - yarigin acildigi an. Daha once
        (kolye verilirken) kacsalardi neye tepki verdikleri belirsiz
        kalirdi; daha sonra kacsalardi tepki gecikmis gorunurdu.
        """
        if not self.villagers_fled and self.beat in ("taken", "chase"):
            self.villagers_fled = True
            for villager in self.villagers:
                villager.flee()
        for villager in self.villagers:
            villager.update()
        # Eve giren listeden dusuyor - her karede `gone` kontrolu yerine
        # liste kisaliyor.
        self.villagers = [v for v in self.villagers if not v.gone]

    def _update_cemo(self) -> None:
        if self.cemo_gone:
            return
        self.cemo.update()

        if self.beat == "gift":
            # Cemo Rey'e dogru yurur.
            target = self.player.body.center_x + 12
            if abs(self.cemo_x - target) > 1.0:
                self.cemo_x += math.copysign(0.5, target - self.cemo_x)
                self.cemo.play("run")
            else:
                self.cemo.play("idle")
        elif self.beat in ("taken", "chase"):
            # Yariga **cekilir**: asagi gomulur, bir yandan direnir.
            # Direnc sinusle salinir - duzgun bir inis "asansor" gibi
            # okunurdu; kesintili inis tutunmaya calisan bir cocuk gibi.
            resist = 0.55 + 0.45 * math.sin(self.beat_frames * 0.22)
            self.cemo_sink = min(20.0, self.cemo_sink
                                 + CEMO_SINK_SPEED * resist)
            self.cemo_x += math.sin(self.beat_frames * 0.31) * 0.5
            self.cemo.play("hurt")

    def _release_creatures(self) -> None:
        """Yarik kapandi; icerideki seyler disari sizmis."""
        if self.creatures_released:
            return
        self.creatures_released = True
        for spot in LEVEL.of("shambler"):
            self.enemies.append(Shambler(self, spot.x, spot.feet_y))

    def _watch_player(self) -> None:
        if abs(self.player.body.vx) > 0.2:
            self.moved = True

        if (self.sword_pos is not None
                and abs(self.player.body.center_x - self.sword_pos[0]) < 12
                and abs(self.player.body.center_y - self.sword_pos[1]) < 20):
            self.sword_pos = None
            if self.player.grant(abilities.SWORD):
                self.on_ability_gained(abilities.SWORD)
                self.say(Line("echo", "line.ch01_echo_sword"))
        if self.player.chain.busy:
            self.attacked = True

        exit_at = LEVEL.first("exit")
        if (not self.finished and exit_at is not None
                and self.player.body.center_x >= exit_at.x - 8):
            self.finished = True
            self.on_chapter_end()

        # Yanki Gorusu ogretisi - sistem Gorev 3'te gelecek.
        trigger = ECHO_TUTORIAL_TILE
        if (not self.echo_taught and trigger is not None
                and abs(self.player.body.center_x - trigger.x) < TILE_SIZE):
            self.echo_taught = True
            self.on_echo_tutorial()

    def on_chapter_end(self) -> None:
        """Bolum 1 bitti - Rey zindana iner.

        Gecis **kesme degil**: yarik yukarida kaldi, Rey asagi iniyor.
        `docs/bolum-02.md` Oda 1 bunu acikca tarif ediyor ("Rey yariktan
        asagi duser, yuvarlanarak iner") - o dusus artik bir ara sahne
        (`chapter02_cinematics.DescentCinematic`). Eskiden Bolum 2
        dogrudan aciliyordu ve oyuncu kendini bir anda baska bir yerde
        buluyordu.
        """
        from src.scenes.chapter02_cinematics import DescentCinematic
        self.scenes.replace(DescentCinematic, character=self.character)

    def on_echo_tutorial(self) -> None:
        """Yanki Gorusu burada ogreniliyor.

        Ogretinin hemen **saginda** kirilabilir bir duvar var: oyuncu
        yetenegi ogrenir ogrenmez kullanacagi bir sey buluyor. Once
        ogretip sonra kullandirmak, ogretiyi hatirlanabilir yapan sey.

        **Ardo'da bu tetiklenmemeli.** Ardo'nun Yanki'si yok (`self.echo`
        `None` - play.py::on_enter); eskiden bu kontrol hic yoktu ve Ardo
        da "Yanki Gorusu kazandin" bildirimini goruyordu - kazanmadigi,
        hicbir mekanik karsiligi olmayan bir gucu acmasi isteniyordu. Ardo
        duvari sezgiyle degil, sozun kendisiyle: kilici zaten elinde,
        vurup kirar.
        """
        if self.echo is None:
            return
        if self.player.grant(abilities.ECHO_SIGHT):
            self.on_ability_gained(abilities.ECHO_SIGHT)
            self.say(Line("echo", "line.ch01_echo_wall"))

    # --- Cizim --------------------------------------------------------------
    def draw_background(self, surface: pygame.Surface, offset) -> None:
        """Gece gokyuzu -> ay -> uzak tepeler -> koy. Dort parallax katmani.

        Ilk halinde yalnizca yildizlar ve evler vardi; aradaki bosluk
        "gokyuzu" degil "hiclik" gibi okunuyordu (ayni tuzak magara arka
        planinda da yasanmisti - DEVIR.md 4 madde 19). Ay ve uzak tepe
        siluetleri o boslugu **mesafeye** ceviriyor.

        Katman hizlari bilerek farkli: yildiz 0.10, ay 0.04 (neredeyse
        sabit - cok uzak), tepeler 0.35, koy 1.0.
        """
        ox, _oy = offset
        surface.fill(palette.color("abyss_dark"))
        village_backdrop.draw_sky(surface, ox, self.game.frame)
        village_backdrop.draw(surface, offset, self.game.frame)

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        chapter01_render.draw_sword(self, surface, offset)
        chapter01_render.draw_rift(self, surface, offset)
        for villager in self.villagers:
            villager.draw(surface, offset)
        if not self.cemo_gone:
            chapter01_render.draw_cemo(self, surface, offset)
        chapter01_render.draw_necklace(self, surface, offset)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        chapter01_render.draw_tutorial(self, surface)

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"prolog: {self.beat} ({self.beat_frames})  "
            f"yarik {self.rift:.2f}  kolye {self.necklace}"]
