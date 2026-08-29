"""Karakter secim ekrani.

Gorsel dil (docs/menu-ui.md 4): secili karakter **buyuk, aydinlik,
animasyonlu**; digeri kucuk, karanlik, hareketsiz. Bu, "secmedigin kisi
hikayede olacak" fikrini gorsel olarak kurar.

Ilk oynayista kucuk bir not: "Ilk kez oynuyorsan Rey onerilir." Zorlamaz,
yonlendirir.

Not: bir ara Rey seciliyken arkada dongulu bir fisilti sesi vardi
(`echo_loop`) - Arda'nin canli oynanis geri bildirimi "cizirti gibi,
rahatsiz edici, kaldiralim" oldu (22.08.2026). Kaldirildi; sentezlenmis
donguler (`echo_loop` dahil) genel olarak guvenilir bulunmadi, bkz.
`src/scenes/play.py` ayni tarihli not.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art import portrait as portrait_art
from src.art.animator import Animator
from src.config import (
    ARDO_CHAIN_WINDOW, ARDO_DODGE_CHARGES, ARDO_MAX_HEALTH,
    ARDO_MOVE_MULTIPLIER, INTERNAL_HEIGHT, INTERNAL_WIDTH,
    REY_CHAIN_WINDOW, REY_DODGE_CHARGES, REY_MAX_HEALTH,
    REY_MOVE_MULTIPLIER,
)
from src.core.input import Action
from src.core.scene import Scene
from src.systems.save import SaveData, write_save
from src.ui import text
from src.ui.i18n import t
from src.ui.font_data import GLYPH_HEIGHT
from src.ui.widgets import panel, value_bar

SELECTED_SCALE = 2
UNSELECTED_SCALE = 1
# Portrenin bas+omuz kadraji (satir). Tam bust 96; bu ekranda
# portrelere ayrilan bant baslik ile `PORTRAIT_BOTTOM` arasi 86.
HEAD_CROP = 62

# 270 piksel dar; dikey butce bastan hesaplandi. Ilk denemede baslik
# portrelerin, sutun basliklari tanitim yazisinin uzerine biniyordu ve
# Yanki panelinin son iki satiri cerceveden tasiyordu.
#   6   baslik
#   22  portreler (52)
#   76  adlar
#   88  tanitim yazisi
#   100 dort istatistik satiri (44)
#   148 ozet satiri
#   162 Yanki paneli (90)
#   256 kontroller
HEADING_Y = 4
PORTRAIT_BOTTOM = 90       # Portrelerin ayak hizasi
NAME_Y = 92
TAGLINE_Y = 104
STATS_Y = 118
NOTE_Y = 164
ECHO_PANEL = pygame.Rect(16, 176, INTERNAL_WIDTH - 32, 78)
PANEL_STEP = 10            # Panel ici satir araligi - 78 piksele sigsin

LEFT_X = INTERNAL_WIDTH // 2 - 96
RIGHT_X = INTERNAL_WIDTH // 2 + 96
# Etiketler ortada, cubuklar iki yanda. Ilk denemede etiket sag hizaliydi
# ve "Combo penceresi" gibi uzun olanlar sol cubugun uzerine tasiyordu.
STAT_LABEL_X = INTERNAL_WIDTH // 2
BAR_COL_X = (INTERNAL_WIDTH // 2 - 104, INTERNAL_WIDTH // 2 + 104)
BAR_WIDTH = 54
BAR_HEIGHT = 5
ROW_STEP = 11

# Yanki panelinin metinleri. Anahtarlar **acikca** yaziliyor, f-string ile
# kurulmuyor: tests/test_lang.py kaynagi tarayip kodun kullandigi her
# anahtarin tabloda oldugunu dogruluyor ve f-string icindeki anahtari
# goremiyor. Once dinamik kurmustum, test hepsini "olu anahtar" sandi -
# hakliydi, cunku tarayici acisindan gercekten kullanilmiyorlardi.
ECHO_TEXT = {
    "rey": {
        "title": "character.echo_title_rey",
        "bullets": ("character.echo_rey_1", "character.echo_rey_2",
                    "character.echo_rey_3"),
        "cost": "character.echo_rey_cost",
        "loss": "character.echo_rey_loss",
    },
    "ardo": {
        "title": "character.echo_title_ardo",
        "bullets": ("character.echo_ardo_1", "character.echo_ardo_2",
                    "character.echo_ardo_3"),
        "cost": "character.echo_ardo_cost",
        "loss": "character.echo_ardo_loss",
    },
}


class CharacterInfo:
    """Karakter kartinin verisi.

    `name` cevrilmiyor - ozel isim. Tanitim yazisi ve ozellikler dil anahtari
    tutar. Yanki bir **boolean**: eskiden "VAR"/"YOK" dizesiydi ve rengi de o
    dizeyle secilirdi; ceviri gelince o karsilastirma sessizce yanlis renk
    verirdi. Gorunen metin artik durumdan turetiliyor, tersi degil.
    """

    def __init__(self, key: str, name: str, tagline_key: str,
                 trait_keys: tuple[str, ...], has_echo: bool,
                 health: int) -> None:
        self.key = key
        self.name = name
        self.tagline_key = tagline_key
        self.trait_keys = trait_keys
        self.has_echo = has_echo
        self.health = health

    @property
    def tagline(self) -> str:
        return t(self.tagline_key)

    @property
    def traits(self) -> tuple[str, ...]:
        return tuple(t(k) for k in self.trait_keys)


CHARACTERS = (
    CharacterInfo("rey", "REY", "character.rey_quote",
                  ("character.rey_trait_1", "character.rey_trait_2"),
                  True, 80),
    CharacterInfo("ardo", "ARDO", "character.ardo_quote",
                  ("character.ardo_trait_1", "character.ardo_trait_2"),
                  False, 120),
)


class CharacterSelectScene(Scene):
    def on_enter(self, **kwargs: object) -> None:
        self.index = 0
        self.frame = 0
        self.animators = {info.key: Animator(info.key) for info in CHARACTERS}
        for animator in self.animators.values():
            animator.play("idle")

    # --- Girdi --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._click()

    def _click(self) -> None:
        mx, my = pygame.mouse.get_pos()
        view = self.game.viewport
        if not view.collidepoint(mx, my) or self.game.scale <= 0:
            return
        vx = (mx - view.x) / self.game.scale
        chosen = 0 if vx < INTERNAL_WIDTH // 2 else 1
        if chosen == self.index:
            self._confirm()
        else:
            self._select(chosen)

    def _select(self, index: int) -> None:
        if index == self.index:
            return
        self.index = index
        self.game.play_sound("ui_tick")

    def update(self) -> None:
        self.frame += 1
        inp = self.game.input

        if inp.pressed(Action.LEFT):
            self._select(0)
        elif inp.pressed(Action.RIGHT):
            self._select(1)
        if inp.pressed(Action.CONFIRM):
            self._confirm()
        elif inp.pressed(Action.CANCEL):
            self.game.play_sound("ui_back")
            self.scenes.pop()

        # Yalnizca secili karakter animasyonlu - digeri durgun.
        self.animators[CHARACTERS[self.index].key].update()

    def _confirm(self) -> None:
        info = CHARACTERS[self.index]
        self.game.play_sound("ui_confirm")

        data = SaveData(character=info.key,
                        max_health=info.health, health=info.health)
        write_save(data)

        # **Prolog once.** Arda'nin istegi (29.08.2026): oyunun basinda
        # Rey'i ve Yankisini anlatan bir kisa film. Karakter seciminden
        # SONRA oynatiliyor cunku iki karakterin acilisi farkli - Rey'in
        # laneti anlatiliyor, Ardo'nunki (Yankisi olmayan) baska bir sey
        # (`src/scenes/prologue.py`).
        #
        # Prolog bitince kamera mor alevden **yukari** cikip koye varir.
        # Menu gidecegin yer, oyun geldigin yer (docs/menu-ui.md 0.3).
        from src.scenes.prologue import ArdoPrologue, ReyPrologue
        prologue = ArdoPrologue if info.key == "ardo" else ReyPrologue
        self.scenes.set_root(prologue, transition=False, character=info.key)

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("abyss_dark"))
        text.draw(surface, t("character.heading"),
                  INTERNAL_WIDTH // 2, HEADING_Y,
                  color=palette.role("ui_text"), align="center", tracking=2)

        for index, info in enumerate(CHARACTERS):
            self._draw_character(surface, index, info)

        self._draw_details(surface, CHARACTERS[self.index])
        self._draw_comparison(surface)
        self._draw_echo_panel(surface, CHARACTERS[self.index])
        self._draw_footer(surface)

    def _draw_character(self, surface: pygame.Surface, index: int,
                        info: CharacterInfo) -> None:
        selected = index == self.index
        centre_x = LEFT_X if index == 0 else RIGHT_X
        scale = SELECTED_SCALE if selected else UNSELECTED_SCALE

        # **Portre varsa portre.** Bu ekran karakteri TANITIYOR; oyun ici
        # sprite'i 2x buyutmek 7 piksellik bir kafayi 14 piksellik bloklara
        # cevirip "basit pixel bloklari" hissini tam da tanisma aninda
        # veriyordu (Arda'nin 29.08.2026 sikayeti). Portrede kafa 40
        # piksel ve yuz gercekten okunuyor - `src/art/portrait.py`.
        bust = portrait_art.portrait(info.key)
        if bust is not None:
            # **Bas + omuz kadraji.** Tam bust 96 piksel; bu ekranda
            # portrelere ayrilan bant 86 piksel (`PORTRAIT_BOTTOM` ile
            # baslik arasi) ve 2x buyutunce kafa ekranin ustunden tasip
            # kesiliyordu - ilk denemede tam oyle oldu. Kadraj yuze
            # odaklaniyor, ki bu ekranin isi zaten o.
            image = bust.subsurface(
                pygame.Rect(0, 0, bust.get_width(), HEAD_CROP)).copy()
            if not selected:
                # Secili olmayan karanlikta kalir - siluete yakin.
                shade = pygame.Surface(image.get_size(), pygame.SRCALPHA)
                shade.fill((*palette.color("abyss_dark"), 170))
                image.blit(shade, (0, 0))
            # Portre cozunurlugunde **buyutme gerekmiyor**: `docs/menu-ui.md`
            # 4'un "secili buyuk" dili parlaklik + cerceve ile zaten
            # tasiniyor, ve 2x bant disina tasardi.
            scale = 1
        else:
            image = self.animators[info.key].render(
                1 if index == 0 else -1,
                tint_colour=(None if selected
                             else palette.color("stone_darkest")),
            )
        if image is None:
            return
        # Hucre karakterden buyuk (silahin savrulmasina yer birakiyor).
        # Kirpmadan olceklersek portre ekranin ustunden tasiyor ve basligin
        # arkasina giriyordu.
        bounds = image.get_bounding_rect()
        if bounds.width and bounds.height:
            image = image.subsurface(bounds).copy()
        big = pygame.transform.scale(
            image, (image.get_width() * scale, image.get_height() * scale))
        if not selected:
            big = big.copy()
            big.set_alpha(150)

        rect = big.get_rect()
        rect.midbottom = (centre_x, PORTRAIT_BOTTOM)

        if selected:
            frame = rect.inflate(10, 8)
            panel(surface, frame, alpha=140)
        surface.blit(big, rect.topleft)

        colour = (palette.role("ui_text_bright") if selected
                  else palette.color("stone_dark"))
        text.draw(surface, info.name, centre_x, NAME_Y,
                  color=colour, align="center", tracking=2,
                  outline=selected)

    def _draw_details(self, surface: pygame.Surface,
                      info: CharacterInfo) -> None:
        text.draw(surface, info.tagline, INTERNAL_WIDTH // 2, TAGLINE_Y,
                  color=palette.role("ui_text"), align="center")

    # --- Sayilarla karsilastirma -------------------------------------------
    def _draw_comparison(self, surface: pygame.Surface) -> None:
        """Iki karakter yan yana, gercek degerlerle.

        Sifat degil sayi: "hizli" gorecelidir, iki cubuk yan yana degildir.
        Oyuncu neyi sectigini **bakarak** anlamali.
        """
        rows = self._stat_rows()
        # Cubuklar portrelerin **altina** hizali: portre altindaki ad zaten
        # sutun basligi. Ayrica basliğı yazmak ikinci bir REY/ARDO satiri
        # uretiyor ve tanitim yazisiyla cakisiyordu.
        label_x = STAT_LABEL_X
        col_x = BAR_COL_X

        y = STATS_Y
        for key, values, best_is_high in rows:
            text.draw(surface, t(key), label_x, y,
                      color=palette.role("ui_text_dim"), align="center")
            for index in range(2):
                ratio = values[index] / max(values) if max(values) else 0.0
                selected = index == self.index
                colour = (palette.color("echo") if selected
                          else palette.color("stone_darkest"))
                rect = pygame.Rect(col_x[index] - BAR_WIDTH // 2, y + 2,
                                   BAR_WIDTH, BAR_HEIGHT)
                value_bar(surface, rect, ratio, colour)
            y += ROW_STEP

        # Kimin neyle kazandigi - tek satirlik ozet.
        note = t("character.stat_note_rey" if self.index == 0
                 else "character.stat_note_ardo")
        if self.index == 0:
            # Ilk oynayis onerisi buraya kaynadi: ayri satir olarak
            # cizilince Yanki paneliyle cakisiyordu.
            note += "  ·  " + t("character.recommend")
        text.draw(surface, note, INTERNAL_WIDTH // 2, NOTE_Y,
                  color=palette.color("stone_light"), align="center")

    def _stat_rows(self):
        """(dil anahtari, (rey, ardo), yuksek olan mi iyi)"""
        return (
            ("character.stat_health",
             (REY_MAX_HEALTH, ARDO_MAX_HEALTH), True),
            ("character.stat_speed",
             (REY_MOVE_MULTIPLIER, ARDO_MOVE_MULTIPLIER), True),
            ("character.stat_chain",
             (REY_CHAIN_WINDOW, ARDO_CHAIN_WINDOW), True),
            ("character.stat_dodge",
             (REY_DODGE_CHARGES, ARDO_DODGE_CHARGES), True),
        )

    # --- Yanki nedir --------------------------------------------------------
    def _draw_echo_panel(self, surface: pygame.Surface,
                         info: CharacterInfo) -> None:
        """Oyunun ana mekanigi burada anlatiliyor.

        Yanki yalnizca bir istatistik degil, oynanisin tamami; oyuncu
        secmeden once ne oldugunu bilmeli. Bir cumlelik "Yanki: VAR"
        hicbir sey anlatmiyordu.
        """
        panel(surface, ECHO_PANEL)
        keys = ECHO_TEXT["rey" if info.has_echo else "ardo"]
        # **MOR** - oyuncunun Yanki'yi ILK OKUDUGU yer burasi. Bolum
        # 1'de mor bir ses fisildamaya baslamadan once beklenti burada
        # kuruluyor; camgobegi birakmak o baglantiyi bir ekran once
        # koparirdi (Arda: "mor konusan seyin senin yankin oldugunu
        # anlamasi lazim").
        accent = (palette.color("violet_bright") if info.has_echo
                  else palette.color("stone_light"))

        x = ECHO_PANEL.x + 8
        y = ECHO_PANEL.y + 7
        text.draw(surface, t(keys["title"]), x, y, color=accent)
        y += GLYPH_HEIGHT + 4
        pygame.draw.line(surface, palette.role("ui_border"),
                         (x, y - 3), (ECHO_PANEL.right - 8, y - 3))

        for key in keys["bullets"]:
            text.draw(surface, "·", x + 2, y, color=accent)
            text.draw(surface, t(key), x + 10, y,
                      color=palette.role("ui_text"))
            y += PANEL_STEP

        y += 2
        text.draw(surface, t(keys["cost"]), x, y,
                  color=palette.color("stone_light"))
        y += PANEL_STEP
        text.draw(surface, t(keys["loss"]), x, y,
                  color=palette.role("ui_text_dim"))

    def _draw_footer(self, surface: pygame.Surface) -> None:
        text.draw(surface, t("character.controls"),
                  INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 13,
                  color=palette.role("ui_text_dim"), align="center")

    def debug_lines(self) -> list[str]:
        return [f"seçili: {CHARACTERS[self.index].name}"]
