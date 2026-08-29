"""Ekipman ekrani - sahip olunan silahi kusanmak.

## Neden var

Duraklatma menusundeki EKIPMAN girdisi kapaliydi ve ipucu olarak
**"Bolum 2'de acilir"** yaziyordu. Bolum 2'de bir sey acilmiyordu.

Arda, canli oynanis (29.08.2026): *"Bolum 2'ye gectigimde balta'm veya
hancerime gecemedim."*

Iki ayri sorun ic ice geciyordu:

  1. Arayuz **tutamayacagi bir soz** veriyordu. Bu, olum yazisinin
     "R ile sifirla" deyip R'nin hicbir yerde dinlenmemesiyle ayni sinif
     hata - bir kez daha.
  2. `SaveData` yalnizca **kusanilan** silahi tutuyordu (`weapon`).
     Bolum 2'de Hancer secen oyuncu kilica bir daha donemiyordu; secim
     geri alinamaz bir kayipti, oysa `weapon_choice.py` acikca *"kilic
     kaybolmuyor"* diyordu.

## Sahiplik nereden geliyor

`SaveData.owned_weapons` artik var, ama **eski kayitlarda bos**. O yuzden
`owned()` bos listeden makul bir varsayilan turetiyor: yumruk her zaman,
kilic yetenek kazanildiysa, ve kusanilan silah ne ise o. Boylece bu
degisiklikten once kaydedilmis bir oyun ekrani actiginda elinde ne varsa
onu goruyor - kimse ilerlemesini kaybetmiyor.

## Sayilar UYDURULMUYOR

`weapon_choice.py` ile ayni kural: hasar/kare/itis degerleri `config.py`'nin
zincir tablolarindan **okunuyor**. Iki ekran ayni sayiyi iki yerde
yazsaydi biri denge gecisinde geride kalirdi.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.combat import weapons
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.ui import text, widgets
from src.ui.font_data import GLYPH_HEIGHT
from src.ui.i18n import t

# Panel genisligi sayi satirina gore: 5px font + tracking ~= 6px/karakter,
# yani 304px ~= 50 karakter. Ilk surum 236'ydi ve satir panelden tasip
# ekranin disina cikiyordu.
PANEL_WIDTH = 304
ROW_HEIGHT = 34
HEADER_Y = 22
LIST_TOP = 58
ROW_STEP = GLYPH_HEIGHT + 3

# Silah adlarinin dil anahtarlari **duz dize**. f-string ile kurulani
# `tests/test_lang.py` goremiyor - bu tuzaga proje bes kereden fazla dustu.
LABEL_KEYS = {
    weapons.FISTS: "weapon.fists",
    weapons.SWORD: "weapon.sword",
    weapons.DAGGER: "weapon.dagger",
    weapons.AXE: "weapon.axe",
}
# Gosterim sirasi - zincir uzunluguna gore degil, kazanma sirasina gore.
ORDER = (weapons.FISTS, weapons.SWORD, weapons.DAGGER, weapons.AXE)


def owned(save_data) -> list[str]:
    """Oyuncunun sahip oldugu silahlar.

    `SaveData.owned_weapons` bos ise (bu alandan onceki kayitlar) kayittan
    turetiliyor - eski bir kayit ekrani actiginda elini bos bulmamali.
    """
    if save_data is None:
        return [weapons.FISTS]

    listed = [key for key in ORDER
              if key in getattr(save_data, "owned_weapons", ())]
    if listed:
        return listed

    # Turetim: yumruk her zaman var; kilic yetenegi varsa kilic; ve
    # kusanilan silah her halukarda listede olmali (yoksa oyuncu onu
    # cikarip bir daha takamaz).
    from src.systems import abilities
    derived = [weapons.FISTS]
    if abilities.SWORD in getattr(save_data, "abilities", ()):
        derived.append(weapons.SWORD)
    current = getattr(save_data, "weapon", "")
    if current in ORDER and current not in derived:
        derived.append(current)
    return [key for key in ORDER if key in derived]


def grant(save_data, key: str) -> None:
    """Bir silahi sahiplik listesine ekler. Cift eklemez."""
    if save_data is None:
        return
    current = list(getattr(save_data, "owned_weapons", []) or [])
    if key not in current:
        current.append(key)
    # Kusanilan silah her zaman listede olmali.
    equipped = getattr(save_data, "weapon", "")
    if equipped in ORDER and equipped not in current:
        current.append(equipped)
    save_data.owned_weapons = current


def _stats(key: str) -> str:
    """Tek satirlik ozet - hepsi zincir tablosundan okunuyor.

    `weapon_choice.py` ayni sayilari **alt alta** gosteriyor cunku orada
    bir KARAR veriliyor ve karsilastirma yavas okunmali. Burada karar
    zaten verilmis; ekranin isi hatirlatmak, o yuzden tek satir ve kisa
    etiketler.
    """
    chain = weapons.get(key).chain
    last = chain[-1]
    budget = last.windup + last.active + last.recovery
    return t("equipment.stat_line", hits=len(chain), damage=last.damage,
             frames=budget, knockback=f"{last.knockback:.1f}")


class EquipmentScene(Scene):
    """Silah degistirme bindirmesi. Duraklatma menusunden aciliyor."""

    blocks_update = True
    blocks_draw = False

    def on_enter(self, save_data=None, player=None, **kwargs: object) -> None:
        self.save_data = save_data
        self.player = player
        self.items = owned(save_data)
        equipped = getattr(save_data, "weapon", weapons.FISTS)
        self.index = (self.items.index(equipped)
                      if equipped in self.items else 0)
        self.frames = 0
        self._blurred: pygame.Surface | None = None

    # --- Girdi --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        inp = self.game.input
        if inp.pressed(Action.CANCEL) or inp.pressed(Action.PAUSE):
            self.game.play_sound("ui_back")
            self.scenes.pop()
        elif inp.pressed(Action.UP):
            self._move(-1)
        elif inp.pressed(Action.DOWN):
            self._move(1)
        elif inp.pressed(Action.CONFIRM):
            self._equip()

    def _move(self, direction: int) -> None:
        if len(self.items) < 2:
            return
        self.index = (self.index + direction) % len(self.items)
        self.game.play_sound("ui_tick")

    def _equip(self) -> None:
        """Secili silahi kusandirir.

        Zaten kusanilmissa **sessizce gecmiyor**: reddedilen bir giris
        oyuncuya "tus mu calismadi" dedirtir (ayni gerekce
        `skill_tree.py`'de de yazili).
        """
        key = self.items[self.index]
        if getattr(self.save_data, "weapon", "") == key:
            self.game.play_sound("ui_deny")
            return
        if self.save_data is not None:
            self.save_data.weapon = key
        if self.player is not None:
            self.player.equip_weapon(key)
        self.game.play_sound("ui_confirm")

    def update(self) -> None:
        self.frames += 1

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        if self._blurred is None:
            self._blurred = widgets.blur(surface, 4)
        surface.blit(self._blurred, (0, 0))
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT),
                              pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 170))
        surface.blit(veil, (0, 0))

        text.draw(surface, t("equipment.heading"), INTERNAL_WIDTH // 2,
                  HEADER_Y, palette.color("bone"), align="center",
                  outline=True, tracking=2)

        left = INTERNAL_WIDTH // 2 - PANEL_WIDTH // 2
        equipped = getattr(self.save_data, "weapon", "")

        for row, key in enumerate(self.items):
            y = LIST_TOP + row * ROW_HEIGHT
            # Yukseklik iki satiri da ICINE almali: ad (y+4) + sayilar
            # (y+17) + glif 11 = 28. Ilk surumde 28'di ve cerceve tam
            # sayi satirinin ortasindan geciyordu.
            rect = pygame.Rect(left, y - 4, PANEL_WIDTH, ROW_HEIGHT - 2)
            selected = row == self.index
            is_on = key == equipped

            widgets.panel(surface, rect, alpha=215 if selected else 150)
            if selected:
                pygame.draw.rect(surface, palette.color("gold"), rect, 1)

            # Kusanili olan UC kanaldan belli oluyor: yazi, isaret ve
            # renk (`CLAUDE.md` 10 - yalnizca renk yeterli degil).
            name = t(LABEL_KEYS.get(key, "weapon.fists"))
            colour = palette.color("gold" if is_on else
                                   ("bone" if selected else "stone_light"))
            text.draw(surface, name, rect.x + 10, rect.y + 4, colour)
            if is_on:
                text.draw(surface, t("equipment.equipped"),
                          rect.right - 10, rect.y + 4,
                          palette.color("gold"), align="right")

            # Sayilar tek satirda, kucuk - hatirlatma, karsilastirma degil.
            text.draw(surface, _stats(key), rect.x + 10,
                      rect.y + 17, palette.color("stone"))

        hint_y = LIST_TOP + len(self.items) * ROW_HEIGHT + 10
        text.draw(surface, t("equipment.hint"), INTERNAL_WIDTH // 2, hint_y,
                  palette.color("stone_light"), align="center")
