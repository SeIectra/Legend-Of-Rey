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
from src.systems import abilities
from src.world.rooms.chapter01 import (
    ECHO_TUTORIAL_TILE, LEVEL, PROLOGUE, RIFT_TILE, SCENERY,
    TUTORIAL_ATTACK_AFTER, TUTORIAL_MOVE_AFTER,
)
from src.world.tilemap import TileMap

# Yarik **Cemo'nun oldugu yerde** aciliyor, sabit bir tile'da degil.
# Sabit konum denendi ve kirildi: oyuncu prolog boyunca gezinebiliyor, uzaga
# giderse sahne ekran disinda oluyor; yakinsa Rey yariga Cemo'dan once
# variyor ve "yetisemezsin" ani hic olusmuyordu. RIFT_TILE artik yalnizca
# bolum tasariminda nerede olacaginin notu.
CEMO_SINK_SPEED = 0.42
HINT_Y = INTERNAL_HEIGHT - 26
SHOCK_LOCK_FRAMES = 46   # Rey yerden kalkana kadar


class Chapter01Scene(PlayScene):
    """Koy. Kolye verilir, Cemo kacirilir."""

    def setup(self) -> None:
        self.tilemap = TileMap(LEVEL.terrain_rows)

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

        # Yaratiklar prologdan **sonra** cikar: koy once sakin olmali,
        # yoksa Cemo'nun kacirilisi bir dovusun icinde kayboluyor.
        self.creatures_released = False

        # Kilic: yaratiklardan once duruyor. Rey silahsiz basliyor ve ilk
        # yaratigi gorunce kacacak yeri yok - kilici alma ani bir rahatlama
        # oluyor. Once ihtiyaci hissettiriyoruz, sonra veriyoruz.
        sword_at = LEVEL.first("pickup_sword")
        self.sword_pos = ((sword_at.x, sword_at.feet_y - 10)
                          if sword_at else None)

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
        self._watch_player()

    def _update_rift(self) -> None:
        """Yarigin acilip kapanmasi Cemo'dan **bagimsiz**.

        Bir donem `_update_cemo` icindeydi; Cemo cekilince o fonksiyon erken
        donuyor ve yarik sonsuza kadar acik kaliyordu.
        """
        if self.beat in ("taken", "chase"):
            self.rift = min(1.0, self.rift + 0.02)
        else:
            self.rift = max(0.0, self.rift - 0.03)

    def _advance_prologue(self) -> None:
        if self.beat_index >= len(PROLOGUE):
            return
        self.beat_frames += 1
        length = PROLOGUE[self.beat_index][0]
        if self.beat_frames >= length:
            self.beat_index += 1
            self.beat_frames = 0
            self._on_beat_start()

    def _on_beat_start(self) -> None:
        # Replikler jestin **yerine** degil yanina geliyor. Cemo'nun yariga
        # cekildigi an ("chase") hala kelimesiz - orada bir replik ani
        # ucuzlatirdi.
        if self.beat == "wake":
            # Sesin ilk kelimesi. Tek kelime - Rey uyanirken.
            self.say(Line("echo", "line.ch01_echo_first"))
        elif self.beat == "gift":
            self.say(Line("cemo", "line.ch01_cemo_gift"),
                     Line("rey", "line.ch01_rey_thanks"))
        elif self.beat == "alone":
            self.say(Line("echo", "line.ch01_echo_alone"))

        if self.beat == "taken":
            # Yer sarsilir. Radyal - yarilmanin yonu yok.
            # Yarik Cemo'nun ayaginin dibinde acilir.
            self.rift_x = self.cemo_x
            self.rift_y = self.cemo_y
            self.juice.explosion(self.rift_x, self.rift_y,
                                 ImpactWeight.FINISHER)
            # Sarsinti Rey'i yere serer. **Yetisememesinin sebebi bu.**
            # Yoksa Rey 2.0 piksel/kare kosuyor ve Cemo'dan once yariga
            # varirdi; "kurtaramadin" ani hic olusmazdi.
            self.player.control_locked = SHOCK_LOCK_FRAMES
            self.player.body.vx = -1.8
            self.player.body.vy = -1.2
            # Ses ilk kez burada duyuluyor: yarik acilirken. Iki kelime.
            self.say(Line("echo", "line.ch01_echo_rift"))
        elif self.beat == "alone":
            self.necklace = True
            self.cemo_gone = True
        elif self.beat == "play":
            self._release_creatures()

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

    def on_ability_gained(self, ability: str) -> None:
        """Yetenek kazanildi. Bir sey **kazanmis** olmali - sessiz gecmesin."""
        self.show_toast(t(abilities.label_key(ability)), frames=180)
        self.juice.explosion(self.player.body.center_x,
                             self.player.body.center_y, ImpactWeight.NORMAL)
        self.particles.burst(self.player.body.center_x,
                             self.player.body.center_y, 14,
                             path="spark", speed=(0.6, 2.2))

    def on_chapter_end(self) -> None:
        """Bolum 1 bitti - Rey zindana iner.

        Gecis **kesme degil**: yarik yukarida kaldi, Rey asagi iniyor.
        Bolum 2 dogrudan aciliyor; ara sahne icin dogru an bu degil,
        inisin kendisi zaten Bolum 2'nin ilk odasi (docs/bolum-02.md).
        """
        from src.scenes.chapter02 import Chapter02Scene
        self.scenes.replace(Chapter02Scene, character=self.character)

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
        ox, _oy = offset
        # Gece gokyuzu - yildizlar parallax ile yavas kayar.
        surface.fill(palette.color("abyss_dark"))
        for i in range(60):
            x = (i * 97 - int(ox * 0.25)) % INTERNAL_WIDTH
            y = (i * 53) % 120
            tone = "bone" if i % 5 == 0 else "stone_dark"
            surface.fill(palette.color(tone), (x, y, 1, 1))
        self._draw_scenery(surface, offset)

    def _draw_scenery(self, surface: pygame.Surface, offset) -> None:
        """Evler, kuyu, cit. Carpisma yok - yalnizca dekor.

        Koyun koye benzemesi icin sart: duz zemin uzerinde iki platform
        "koy" degil "test odasi" gibi okunuyordu.
        """
        ox, oy = offset
        for tx, ty, tw, th, kind in SCENERY:
            x = tx * TILE_SIZE - ox
            base = (ty + 1) * TILE_SIZE - oy
            width = tw * TILE_SIZE
            height = th * TILE_SIZE
            if x + width < 0 or x > INTERNAL_WIDTH:
                continue                     # Gorunmeyeni cizme

            if kind == "house":
                surface.fill(palette.color("ink_soft"),
                             (x, base - height, width, height))
                # Cati: ustte ucgen.
                for i in range(height // 3):
                    inset = int(width * 0.5 * i / max(1, height // 3))
                    surface.fill(palette.color("earth_dark"),
                                 (x + inset, base - height - i,
                                  width - inset * 2, 1))
                # Isikli pencere - koyde hayat var.
                surface.fill(palette.color("ember"),
                             (x + width // 2 - 1, base - height // 2, 3, 3))
                pygame.draw.rect(surface, palette.color("void"),
                                 pygame.Rect(x, base - height, width, height), 1)
            elif kind == "well":
                surface.fill(palette.color("stone_darkest"),
                             (x, base - height, width, height))
                surface.fill(palette.color("stone_dark"),
                             (x - 2, base - height, width + 4, 2))
            else:                            # cit
                for i in range(0, width, 5):
                    surface.fill(palette.color("earth_dark"),
                                 (x + i, base - height, 1, height))
                surface.fill(palette.color("earth_dark"),
                             (x, base - height + 2, width, 1))

    def _draw_sword(self, surface: pygame.Surface, offset) -> None:
        """Yerde duran kilic - hafif suzulur ve parildar.

        Toplanabilir bir seyin **toplanabilir gorunmesi** gerekiyor: durgun
        bir sprite dekor sanilir.
        """
        if self.sword_pos is None:
            return
        ox, oy = offset
        bob = int(round(math.sin(self.game.frame * 0.06) * 2))
        x = int(self.sword_pos[0]) - ox
        y = int(self.sword_pos[1]) - oy + bob

        glow = radial_glow(14, palette.color("gold"), peak=0.30)
        surface.blit(glow, (x - 14, y - 14),
                     special_flags=pygame.BLEND_RGB_ADD)
        # Kilic: dikey namlu + capraz balcak.
        surface.fill(palette.color("stone_light"), (x, y - 9, 1, 14))
        surface.fill(palette.color("bone"), (x, y - 9, 1, 3))
        surface.fill(palette.color("brass" if False else "gold"),
                     (x - 3, y + 2, 7, 1))
        surface.fill(palette.color("earth_dark"), (x, y + 3, 1, 3))

    def draw_foreground(self, surface: pygame.Surface, offset) -> None:
        self._draw_sword(surface, offset)
        self._draw_rift(surface, offset)
        if not self.cemo_gone:
            self._draw_cemo(surface, offset)

    def _draw_rift(self, surface: pygame.Surface, offset) -> None:
        if self.rift <= 0.0:
            return
        ox, oy = offset
        x = int(self.rift_x) - ox
        y = int(self.rift_y) - oy
        width = int(26 * self.rift)
        height = int(40 * self.rift)

        glow = radial_glow(max(4, height), palette.color("violet"),
                           peak=0.5 * self.rift)
        surface.blit(glow, (x - height, y - height),
                     special_flags=pygame.BLEND_RGB_ADD)
        # Yarik: zeminde acilan dikey bir gedik.
        for i in range(height):
            t_value = i / max(1, height)
            span = max(1, int(width * (1.0 - t_value) * 0.5))
            surface.fill(palette.color("void"), (x - span, y - i, span * 2, 1))
            if t_value < 0.5:
                surface.fill(palette.color("violet_dark"),
                             (x - span // 2, y - i, max(1, span), 1))

    def _draw_cemo(self, surface: pygame.Surface, offset) -> None:
        ox, oy = offset
        facing = 1 if self.beat in ("taken", "chase") else -1
        image = self.cemo.render(facing)
        if image is None:
            return
        foot = 27          # CEMO_SPEC.foot_y
        # Gomuldukce sprite'in alti kirpilir: yarigin icinde kaybolur.
        visible = max(1, image.get_height() - int(self.cemo_sink))
        image = image.subsurface((0, 0, image.get_width(), visible))
        surface.blit(image, (int(self.cemo_x - image.get_width() * 0.5) - ox,
                             int(self.cemo_y - foot) - oy))

        icon = self._cemo_balloon()
        if icon:
            balloon.draw(surface, icon,
                         int(self.cemo_x) - ox,
                         int(self.cemo_y - foot) - oy,
                         frame=self.game.frame,
                         colour=palette.color("violet_bright")
                         if icon == "alert" else palette.role("ui_text"))

    def _cemo_balloon(self) -> str:
        return {
            "wake": "necklace",
            "gift": "necklace",
            "taken": "alert",
            "chase": "alert",
        }.get(self.beat, "")

    def draw_overlay(self, surface: pygame.Surface) -> None:
        self._draw_tutorial(surface)

    def _draw_tutorial(self, surface: pygame.Surface) -> None:
        """Ogreti metni **son care**. Once oyuncuya deneme sansi verilir."""
        hint = ""
        if self.beat != "play":
            return
        if not self.moved and self.game.frame > TUTORIAL_MOVE_AFTER:
            hint = t("chapter01.hint_move",
                     left=self.game.input.binding_label(Action.LEFT),
                     right=self.game.input.binding_label(Action.RIGHT))
        elif (self.moved and not self.attacked and self.enemies
                and self.player.has(abilities.SWORD)
                and self.game.frame > TUTORIAL_ATTACK_AFTER):
            hint = t("chapter01.hint_attack",
                     key=self.game.input.binding_label(Action.ATTACK))
        if not hint:
            return
        text.draw(surface, hint, INTERNAL_WIDTH // 2, HINT_Y,
                  color=palette.role("ui_text_dim"), align="center")

    def debug_lines(self) -> list[str]:
        return super().debug_lines() + [
            f"prolog: {self.beat} ({self.beat_frames})  "
            f"yarik {self.rift:.2f}  kolye {self.necklace}"]
