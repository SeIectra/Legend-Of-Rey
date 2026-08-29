"""Silah secimi - Bolum 2 mini-boss odulu.

`docs/bolum-02.md`: *"Odul: 55 altin + **ilk silah secimi**: Hancer (hizli,
kisa) veya Balta (yavas, zirh deler). Kilic zaten elinde."* ve gerekcesi:
*"Oyuncu artik dovusu anladi, tercih yapabilecek bilgiye sahip. Daha erken
verirsen anlamsiz secim olur."*

## Sayilar UYDURULMUYOR

Panellerdeki hasar/kare degerleri metin olarak yazilmiyor, `config.py`'nin
zincir tablolarindan (`DAGGER_CHAIN` / `AXE_CHAIN`) **okunuyor**. Denge
degisirse ekran kendiliginden dogru kalir. Elle yazilmis bir "13 hasar"
ilk denge geciside yalan olurdu ve kimse fark etmezdi.

## Karsilastirma, aciklama degil

Iki panel yan yana ve **ayni satirlar** karsilikli duruyor: vurus sayisi,
bitirici hasari, bitirici kare butcesi. Oyuncu "hizli" ve "yavas"
kelimelerine degil sayilara bakip karar veriyor. Kelimeler de var ama
ikinci sirada.

Silah **sprite'i** de gosteriliyor (`rey_dagger` / `rey_axe`, karaktere
gore) - secilen sey elde nasil gorunecekse ekranda o gorunuyor.

## Iptal YOK

`Action.CANCEL` bu ekranda calismiyor: bu bir menu degil bir **odul**.
Kacisi olan bir secim ekrani oyuncuyu "yanlisini sonra duzeltirim" moduna
sokar ve kararin agirligini alir. Ayrica geri donulse odul havada kalirdi
- mini-boss oldu, kapi acildi, ekran kapandi ve oyuncunun elinde bir sey
yok. Bunun yerine iki secenek de gecerli ve ikisi de iyi.

Kilic **kaybolmuyor**: secilen silah kusaniliyor ama `SaveData.weapon`
degisiyor, yani ileride bir donanim ekrani gelirse geri takilabilir
(`docs/menu-ui.md` EKIPMAN, henuz kapali).
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.animator import Animator
from src.combat import weapons
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.ui import text, widgets
from src.ui.font_data import GLYPH_HEIGHT
from src.ui.i18n import t

# Yerlesim: iki panel yan yana, ortada bosluk.
PANEL_WIDTH = 168
PANEL_HEIGHT = 150
PANEL_GAP = 16
PANEL_TOP = 56
HEADER_Y = 20
ROW_STEP = GLYPH_HEIGHT + 4

# Secilen panelin nabzi (kare). Sabit hiz - okunur, dikkat dagitmaz.
PULSE_PERIOD = 48

CHOICES = (weapons.DAGGER, weapons.AXE)

# Anahtarlar **duz dize** olarak yaziliyor, f-string ile kurulmuyor.
# `tests/test_lang.py` kodu tarayarak `t("...")` cagrilarini buluyor;
# f-string ile kurulan bir anahtar ona GORUNMEZ ve eksik ceviri sessizce
# yayina cikar. Bu projede ayni tuzaga bes kereden fazla dusuldu.
NOTE_KEYS = {
    weapons.DAGGER: "weapon.dagger_note",
    weapons.AXE: "weapon.axe_note",
}
LABEL_KEYS = {
    weapons.DAGGER: "weapon.dagger",
    weapons.AXE: "weapon.axe",
}


def _chain_summary(key: str) -> tuple[tuple[str, str], ...]:
    """(etiket, deger) satirlari - hepsi zincir tablosundan okunuyor.

    Elle yazilmis sayilar ilk denge gecisinde yalan olurdu.
    """
    chain = weapons.get(key).chain
    last = chain[-1]
    # Bitiricinin toplam kare butcesi: hazirlik + aktif + toparlanma.
    # Oyuncunun gercekten hissettigi sey bu - tek basina "hasar" yanilticidir.
    budget = last.windup + last.active + last.recovery
    return (
        (t("weapon.stat_hits"), str(len(chain))),
        (t("weapon.stat_finisher"), str(last.damage)),
        (t("weapon.stat_frames"), f"{budget}"),
        (t("weapon.stat_knockback"), f"{last.knockback:.1f}"),
    )


class WeaponChoiceScene(Scene):
    """Iki silah, bir karar. Bindirme - alttaki sahne gorunur kalir."""

    blocks_update = True
    blocks_draw = False

    def on_enter(self, save_data=None, player=None, character: str = "rey",
                 on_chosen=None, **kwargs: object) -> None:
        self.save_data = save_data
        self.player = player
        self.character = character
        self.on_chosen = on_chosen
        self.index = 0
        self.frames = 0
        self.chosen: str | None = None
        self._blurred: pygame.Surface | None = None
        # Onizleme sprite'lari bir kez uretiliyor - her karede Animator
        # kurmak bos yere atlas uretir (CLAUDE.md 4).
        self._previews = {key: self._preview(key) for key in CHOICES}

    def _preview(self, key: str) -> pygame.Surface | None:
        """Secenegin sprite'i - hangi karakter oynuyorsa onunki.

        Poz **duruş degil savurma**: `idle`'da silah govdenin onunde
        duruyor ve kucuk bir cizgiye iniyor; `attack3`'un son karesinde
        tam uzanmis halde, yani sekli okunuyor. Secim ekraninda gorulmesi
        gereken sey silahin kendisi.

        Buyutmedik: 2x olceklenmis bir sprite'in pikselleri ekranin geri
        kalanindan buyuk olur ve iki cozunurluk yan yana gelir (pixel art
        icin en belirgin hatalardan biri).
        """
        name = f"{self.character}{weapons.get(key).sprite_suffix}"
        from src.art.animation import CHARACTERS
        if name not in CHARACTERS:
            return None
        animator = Animator(name)
        animator.play("attack3")
        animator.set_progress(0.75)      # silah uzanmis, henuz toparlanmamis
        return animator.render(1)

    # --- Girdi --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN or self.chosen is not None:
            return
        inp = self.game.input
        # CANCEL bilerek yok - modul basligindaki gerekce.
        if inp.pressed(Action.LEFT):
            self._move(-1)
        elif inp.pressed(Action.RIGHT):
            self._move(1)
        elif inp.pressed(Action.CONFIRM):
            self._choose()

    def _move(self, direction: int) -> None:
        self.index = (self.index + direction) % len(CHOICES)
        self.game.play_sound("ui_tick")

    def _choose(self) -> None:
        key = CHOICES[self.index]
        self.chosen = key
        if self.save_data is not None:
            self.save_data.weapon = key
        if self.player is not None:
            self.player.equip_weapon(key)
        self.game.play_sound("ui_confirm")
        if self.on_chosen:
            self.on_chosen(key)
        self.scenes.pop()

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        self.frames += 1

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        self._draw_backdrop(surface)
        text.draw(surface, t("weapon.choose_title"), INTERNAL_WIDTH // 2,
                  HEADER_Y, palette.color("bone"), align="center",
                  outline=True)
        text.draw(surface, t("weapon.choose_hint"), INTERNAL_WIDTH // 2,
                  HEADER_Y + ROW_STEP, palette.color("stone_light"),
                  align="center")
        for slot, key in enumerate(CHOICES):
            self._draw_panel(surface, slot, key)

    def _draw_backdrop(self, surface: pygame.Surface) -> None:
        """Alttaki sahne bulanik - arena duruyor ama one cikmiyor."""
        if self._blurred is None:
            self._blurred = widgets.blur(surface, 4)
        surface.blit(self._blurred, (0, 0))
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT),
                              pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 165))
        surface.blit(veil, (0, 0))

    def _panel_rect(self, slot: int) -> pygame.Rect:
        total = PANEL_WIDTH * 2 + PANEL_GAP
        left = (INTERNAL_WIDTH - total) // 2 + slot * (PANEL_WIDTH + PANEL_GAP)
        return pygame.Rect(left, PANEL_TOP, PANEL_WIDTH, PANEL_HEIGHT)

    def _draw_panel(self, surface: pygame.Surface, slot: int,
                    key: str) -> None:
        rect = self._panel_rect(slot)
        active = slot == self.index
        widgets.panel(surface, rect, alpha=225 if active else 170)

        # Secili panel UC kanaldan belli oluyor (renk korlugu, CLAUDE.md 10):
        # daha parlak cerceve, nabiz, ve bir isaretci ucgen. Yalnizca renk
        # olsaydi renk gormeyen oyuncu hangisinde oldugunu bilemezdi.
        if active:
            pulse = abs(((self.frames % PULSE_PERIOD) / PULSE_PERIOD) - 0.5) * 2
            edge = palette.color("gold" if pulse > 0.5 else "ember_light")
            pygame.draw.rect(surface, edge, rect, 1)
            self._draw_marker(surface, rect)
        else:
            pygame.draw.rect(surface, palette.color("stone_dark"), rect, 1)

        y = rect.top + 6
        text.draw(surface, t(LABEL_KEYS[key]), rect.centerx, y,
                  palette.color("bone" if active else "stone_light"),
                  align="center")
        y += ROW_STEP + 2

        preview = self._previews.get(key)
        if preview is not None:
            surface.blit(preview,
                         (rect.centerx - preview.get_width() // 2, y - 4))
            y += preview.get_height() - 6

        text.draw(surface, t(NOTE_KEYS[key]), rect.centerx, y,
                  palette.color("echo" if active else "stone"),
                  align="center")
        y += ROW_STEP + 3

        for label, value in _chain_summary(key):
            text.draw(surface, label, rect.left + 10, y,
                      palette.color("stone_light"))
            text.draw(surface, value, rect.right - 10, y,
                      palette.color("bone" if active else "stone"),
                      align="right")
            y += ROW_STEP

    def _draw_marker(self, surface: pygame.Surface,
                     rect: pygame.Rect) -> None:
        """Secili panelin ustunde asagi bakan ucgen - sekil kanali."""
        tip_x = rect.centerx
        top = rect.top - 6
        colour = palette.color("gold")
        for row in range(4):
            width = 7 - row * 2
            surface.fill(colour, (tip_x - width // 2, top + row, width, 1))
