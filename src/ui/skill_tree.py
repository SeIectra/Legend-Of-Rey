"""Yetenek agaci ekrani - uc dal, dort seviye.

`docs/gdd.md` 6: *"Yetenek agaci (3 dal x 4 seviye)"*. `docs/yapi.md` B4:
ilk kez **Kayit Odasi**'nda aciliyor - dovussuz bir nefes bolumunde,
onceki maceracinin kampinda.

## Ekran degil, BINDIRME

`ChapterEndScene` ile ayni desen: alttaki sahne donuyor ama gorunur
kaliyor (`blocks_update=True`, `blocks_draw=False`) ve arkasi bu sahne
tarafindan bulaniklastiriliyor.

Oyuncu agaci acinca oyundan **cikmiyor**, oyunun uzerine bakiyor - kamp
orada duruyor.

Not: `transparent_bg` ozniteligi `chapter_end.py` ve `pause.py`'de yazili
ama `scene.py` ONA HIC BAKMIYOR - olu bir oznitelik. Gorunuru saglayan
sey yalnizca `blocks_draw=False`. Burada bilincli olarak yazilmadi;
ucuncu kez kopyalamak onu "gercek" gibi gosterirdi.

## Uc dal yan yana, dort seviye yukaridan asagi

Dallar sutun, seviyeler satir. Baglanti cizgileri **onkosulu** anlatiyor:
bir dugum ancak ustundeki acikken acilabilir, ve cizgi o iliskiyi
gosteriyor. Cizgi olmasaydi oyuncu dort ayri dugum gorurdu, bir yol
degil.

## Durum RENKLE DEGIL, uc kanalla anlatiliyor

Renk korlugu icin (CLAUDE.md 10) her durum **renk + sekil + parlaklik**
birlikte tasiyor:

    ACIK      dolu daire, parlak, baglanti cizgisi kalin
    ALINABILIR  halka + nabiz, orta parlaklik
    KILITLI   ince halka, sonuk, cizgi noktali

## Yazi yok demiyoruz

Secili dugumun adi ve aciklamasi altta duruyor. Agacin kendisi ikonik,
ama "bu ne ise yarar" sorusu metinle cevaplaniyor - `docs/menu-ui.md`
diegetik tercih ediyor ama bir ILERLEME ekraninda belirsizlik ceza olur.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.ui import text, widgets
from src.ui.font_data import GLYPH_HEIGHT
from src.ui.i18n import t

# Yerlesim. Uc sutun ekrana esit bolunuyor, dort satir yukaridan asagi.
# TREE_TOP 52 iken dal adlari (TREE_TOP-16 = 36) baslik altindaki puan
# sayacinin (~26-33) uzerine biniyordu - ekran goruntusunde "YANKI" ile
# "Yetenek puani" ust uste cikmisti. 62'ye indirilince adlar 46'ya
# geciyor, aralik temiz. ROW_STEP de 31'e cekildi ki dort satir yine
# ayrinti paneline degmeden sigsin.
TREE_TOP = 62
ROW_STEP = 31
NODE_RADIUS = 6
# Secili dugumun adi/aciklamasi icin altta ayrilan serit.
DETAIL_Y = INTERNAL_HEIGHT - 52
# Baslik ve puan sayaci.
HEADER_Y = 16


class SkillTreeScene(Scene):
    """Yetenek agaci bindirmesi. Alttaki sahne donar, gorunur kalir."""

    blocks_update = True
    blocks_draw = False

    def on_enter(self, save_data=None, tree=None, **kwargs: object) -> None:
        """`tree` `src/systems/skilltree.py` modulu, `save_data` kayit.

        Modul olarak gecirmek (ornek degil) bilincli: agacin durumu
        kayitta tutuluyor, modulun kendisi durumsuz. Ayni desen
        `charms.py` ve `abilities.py`'de de var.
        """
        self.save_data = save_data
        self.tree = tree
        self.branch_index = 0
        self.level_index = 0
        self.frames = 0
        self._blurred: pygame.Surface | None = None

    # --- Gezinme ------------------------------------------------------------
    @property
    def branches(self) -> tuple:
        return getattr(self.tree, "BRANCHES", ()) if self.tree else ()

    @property
    def current_branch(self):
        if not self.branches:
            return None
        return self.branches[self.branch_index % len(self.branches)]

    @property
    def current_node(self):
        branch = self.current_branch
        if branch is None or not branch.nodes:
            return None
        return branch.nodes[self.level_index % len(branch.nodes)]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        inp = self.game.input
        if inp.pressed(Action.CANCEL) or inp.pressed(Action.PAUSE):
            self.game.play_sound("ui_back")
            self.scenes.pop()
            return
        if inp.pressed(Action.LEFT):
            self._move_branch(-1)
        elif inp.pressed(Action.RIGHT):
            self._move_branch(1)
        elif inp.pressed(Action.UP):
            self._move_level(-1)
        elif inp.pressed(Action.DOWN):
            self._move_level(1)
        elif inp.pressed(Action.CONFIRM):
            self._try_unlock()

    def _move_branch(self, direction: int) -> None:
        if not self.branches:
            return
        self.branch_index = (self.branch_index + direction) % len(self.branches)
        # Seviye imleci yeni dalin sinirlari icinde kalmali - dallar ayni
        # uzunlukta olmayabilir.
        branch = self.current_branch
        if branch is not None and branch.nodes:
            self.level_index = min(self.level_index, len(branch.nodes) - 1)
        self.game.play_sound("ui_tick")

    def _move_level(self, direction: int) -> None:
        branch = self.current_branch
        if branch is None or not branch.nodes:
            return
        self.level_index = (self.level_index + direction) % len(branch.nodes)
        self.game.play_sound("ui_tick")

    def _try_unlock(self) -> None:
        node = self.current_node
        if node is None or self.tree is None or self.save_data is None:
            return
        if self._node_state(node) == "kullanilamaz":
            self.game.play_sound("ui_deny")
            return
        if self.tree.unlock(self.save_data, node.key):
            self.game.play_sound("ui_confirm")
        else:
            # Reddedilen giris SESSIZ kalmamali - oyuncu tusun calismadigini
            # mi yoksa kosulun saglanmadigini mi bilmiyor.
            self.game.play_sound("ui_deny")

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        self.frames += 1

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        self._draw_backdrop(surface)
        self._draw_header(surface)
        for index, branch in enumerate(self.branches):
            self._draw_branch(surface, index, branch)
        self._draw_detail(surface)

    def _draw_backdrop(self, surface: pygame.Surface) -> None:
        """Alttaki sahne bulanik ve koyu - oyun duruyor ama kaybolmuyor."""
        if self._blurred is None:
            self._blurred = widgets.blur(surface.copy())
        surface.blit(self._blurred, (0, 0))
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 170))
        surface.blit(veil, (0, 0))

    def _draw_header(self, surface: pygame.Surface) -> None:
        text.draw(surface, text.tr_upper(t("skilltree.title")),
                  INTERNAL_WIDTH // 2, HEADER_Y, align="center",
                  color=palette.role("ui_text_bright"), outline=True)
        points = 0
        if self.tree is not None and self.save_data is not None:
            points = self.tree.available_points(self.save_data)
        text.draw(surface, t("skilltree.points", count=points),
                  INTERNAL_WIDTH // 2, HEADER_Y + GLYPH_HEIGHT + 3,
                  align="center", color=palette.color("gold"))

    def _branch_usable(self, branch) -> bool:
        """Bu dal bu karakter icin anlamli mi?

        YANKI dali Ardo'da etkisiz - Yanki Rey'in laneti (DEVIR §3.7).
        `can_unlock` bunu bilerek sormuyor (sozlesme "puan + onkosul"),
        ayrimi burada yapiyoruz: kullanilamaz dal SOLUK ciziliyor ve
        acilmaya calisilinca reddediliyor. Ekran bunu gostermeseydi Ardo
        oyuncusu puanini oraya harcamaya calisip neden olmadigini
        anlamazdi.
        """
        if self.tree is None or self.save_data is None:
            return True
        checker = getattr(self.tree, "branch_usable", None)
        if checker is None:
            return True
        return bool(checker(self.save_data, branch.key))

    def _column_x(self, index: int) -> int:
        span = INTERNAL_WIDTH // max(1, len(self.branches))
        return span * index + span // 2

    def _draw_branch(self, surface: pygame.Surface, index: int,
                     branch) -> None:
        x = self._column_x(index)
        usable = self._branch_usable(branch)
        label_colour = (palette.role("ui_text_dim") if usable
                        else palette.color("stone_darkest"))
        text.draw(surface, text.tr_upper(t(branch.label_key)), x, TREE_TOP - 16,
                  align="center", color=label_colour)

        for level, node in enumerate(branch.nodes):
            y = TREE_TOP + level * ROW_STEP
            if level > 0:
                self._draw_link(surface, x, y - ROW_STEP, y, node)
            selected = (index == self.branch_index
                        and level == self.level_index)
            self._draw_node(surface, x, y, node, selected)

    def _node_state(self, node) -> str:
        """acik | alinabilir | kilitli"""
        if self.tree is None or self.save_data is None:
            return "kilitli"
        branch = self.tree.branch_of(node.key) if hasattr(
            self.tree, "branch_of") else None
        if branch is not None and not self._branch_usable(branch):
            return "kullanilamaz"
        if self.tree.unlocked(self.save_data, node.key):
            return "acik"
        if self.tree.can_unlock(self.save_data, node.key):
            return "alinabilir"
        return "kilitli"

    def _draw_link(self, surface: pygame.Surface, x: int, top: int,
                   bottom: int, node) -> None:
        """Onkosul cizgisi. Acik yol KALIN, kapali yol NOKTALI.

        Cizgi olmasaydi oyuncu dort ayri dugum gorurdu, bir YOL degil.
        """
        state = self._node_state(node)
        if state == "acik":
            surface.fill(palette.color("gold"),
                         (x - 1, top + NODE_RADIUS, 2, ROW_STEP - NODE_RADIUS * 2))
            return
        tone = (palette.color("stone_light") if state == "alinabilir"
                else palette.color("stone_dark"))
        for offset in range(NODE_RADIUS, ROW_STEP - NODE_RADIUS, 3):
            surface.fill(tone, (x, top + offset, 1, 1))

    def _draw_node(self, surface: pygame.Surface, x: int, y: int,
                   node, selected: bool) -> None:
        """Durum uc kanalla: sekil + parlaklik + renk (CLAUDE.md 10).

        Renk gormeyen oyuncu SEKLI goruyor: dolu daire acik, halka
        alinabilir, ince halka kilitli.
        """
        state = self._node_state(node)
        if state == "acik":
            pygame.draw.circle(surface, palette.color("gold"), (x, y),
                               NODE_RADIUS)
            surface.fill(palette.color("white_flash"), (x - 1, y - 3, 1, 1))
        elif state == "alinabilir":
            pulse = 0.5 + 0.5 * math.sin(self.frames * 0.08)
            tone = (palette.color("gold") if pulse > 0.5
                    else palette.color("ember_light"))
            pygame.draw.circle(surface, tone, (x, y), NODE_RADIUS, 2)
        elif state == "kullanilamaz":
            # Kilitli DEGIL, ERISILEMEZ. Farki sekille anlatiyoruz: kilitli
            # bir halka, erisilemez capraz. Renk gormeyen oyuncu da ayirt
            # etsin (CLAUDE.md 10).
            tone = palette.color("stone_darkest")
            pygame.draw.circle(surface, tone, (x, y), NODE_RADIUS, 1)
            r = NODE_RADIUS - 2
            pygame.draw.line(surface, tone, (x - r, y - r), (x + r, y + r))
            pygame.draw.line(surface, tone, (x - r, y + r), (x + r, y - r))
        else:
            pygame.draw.circle(surface, palette.color("stone_dark"),
                               (x, y), NODE_RADIUS, 1)

        if selected:
            # Secim cercevesi dugumun DISINDA - uzerine binerse durum
            # okunmaz hale geliyor.
            rect = pygame.Rect(x - NODE_RADIUS - 4, y - NODE_RADIUS - 4,
                               (NODE_RADIUS + 4) * 2, (NODE_RADIUS + 4) * 2)
            pygame.draw.rect(surface, palette.color("violet_bright"), rect, 1)

    def _draw_detail(self, surface: pygame.Surface) -> None:
        """Secili dugumun adi, aciklamasi ve bedeli.

        Agac ikonik ama bir ILERLEME ekraninda "bu ne ise yarar"
        belirsizligi ceza olur - metin sart.
        """
        node = self.current_node
        if node is None:
            return
        panel_rect = pygame.Rect(20, DETAIL_Y - 6, INTERNAL_WIDTH - 40, 46)
        widgets.panel(surface, panel_rect)

        state = self._node_state(node)
        name_colour = (palette.color("gold") if state == "acik"
                       else palette.role("ui_text_bright"))
        text.draw(surface, text.tr_upper(t(node.label_key)),
                  INTERNAL_WIDTH // 2, DETAIL_Y, align="center",
                  color=name_colour)
        text.draw(surface, t(node.desc_key), INTERNAL_WIDTH // 2,
                  DETAIL_Y + GLYPH_HEIGHT + 2, align="center",
                  color=palette.role("ui_text_dim"))

        if state == "kullanilamaz":
            footer = t("skilltree.unavailable")
        elif state == "acik":
            footer = t("skilltree.owned")
        elif state == "alinabilir":
            footer = t("skilltree.cost", count=node.cost)
        else:
            footer = t("skilltree.locked")
        text.draw(surface, footer, INTERNAL_WIDTH // 2,
                  DETAIL_Y + (GLYPH_HEIGHT + 2) * 2, align="center",
                  color=palette.color("gold") if state == "alinabilir"
                  else palette.role("ui_text_dim"))
