"""Ana menu.

Kurallar (docs/menu-ui.md 3, CLAUDE.md 9):
  * DEVAM ET en ustte ve **onceden secili** - oyuncu dusunmeden devam etsin
  * Kayit yoksa DEVAM ET **gorunmez** (gri degil) - gri buton "bir seyi
    kacirdim" hissi verir
  * CIKIS bir boslukla ayrilmis - yanlislikla basma riski azalir
  * YENI OYUN uzerine yazacaksa onay sorulur, **varsayilan secim IPTAL**
  * Hicbir gecis 12 kareyi asmaz

Sahne cilasi (mor alev, sarkan zincirler, dikey yolculuk) Gorev 7'de.
Burada islevsellik onceliklidir: cirkin ama hizli bir menu, guzel ama
kullanilamayan bir menuden iyidir.
"""
from __future__ import annotations


import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.systems.save import has_save, read_save
from src.ui import text
from src.ui.i18n import t, t_or_raw
from src.ui.menu_scene import MenuBackdrop, stage_for
from src.ui.font_data import GLYPH_HEIGHT, GLYPH_WIDTH
from src.ui.widgets import Menu, MenuItem, panel

TITLE_Y = 46
MENU_X = 46
MENU_Y = 116
CARD_X = 250
CARD_Y = 104
CARD_WIDTH = 178
# Baslik + bolum adi + ayrac + dort satir. Kisa tutunca son satir ("Gizli")
# cerceveyi kesiyordu.
CARD_HEIGHT = 96


class MainMenuScene(Scene):
    def on_enter(self, reveal_buttons: bool = False,
                 **kwargs: object) -> None:
        # Ana menu muzigi (Azula). `MusicDirector.play` ayni baglamda
        # hicbir sey yapmiyor, yani menuye her donuste parca bastan
        # baslamıyor - kesintisiz kaliyor.
        self.game.music.play("menu")
        self.frame = 0
        self.save_data, self.save_status = read_save()
        self.confirm_overwrite: Menu | None = None
        self.notice = ""
        self.notice_frames = 0

        if self.save_status == "backup":
            self.notice = "menu.restored_from_backup"
            self.notice_frames = 300

        self.menu = self._build_menu()
        # Sahne kayittaki ilerlemeye gore kurulur (5 asama).
        self.backdrop = MenuBackdrop(stage_for(self.save_data))
        if reveal_buttons:
            # Kamera menuye yeni vardi: butonlar tek tek belirsin.
            self.menu.start_reveal()

    def _build_menu(self) -> Menu:
        save_exists = has_save()
        return Menu([
            # Kayit yoksa gorunmez - gri degil, YOK.
            MenuItem("menu.continue", self._continue, visible=save_exists,
                     hint="menu.continue_hint"),
            MenuItem("menu.new_game", self._new_game,
                     hint="menu.new_game_hint"),
            MenuItem("menu.settings", self._open_settings,
                     hint="menu.settings_hint"),
            MenuItem("menu.extras", None, enabled=False,
                     hint="menu.extras_hint"),
            MenuItem("menu.quit", self.game.quit, gap_before=True),
        ], MENU_X, MENU_Y, width=140,
            on_sound=self.game.play_sound)

    # --- Eylemler -----------------------------------------------------------
    def _continue(self) -> None:
        if self.save_data is None:
            return
        # Kamera alevden **asagi** iner, kaldigin bolume kadar. Ne kadar
        # ilerlediysen o kadar uzun dusersin (docs/menu-ui.md 0.4).
        from src.scenes.vertical_journey import VerticalJourneyScene
        self.scenes.replace(VerticalJourneyScene, transition=False,
                            direction="down",
                            chapter=self.save_data.chapter,
                            character=self.save_data.character)

    def _new_game(self) -> None:
        if has_save():
            self._ask_overwrite()
            return
        self._go_character_select()

    def _ask_overwrite(self) -> None:
        # Yikici eylem: varsayilan secim daima IPTAL.
        self.confirm_overwrite = Menu([
            MenuItem("common.cancel", self._cancel_overwrite),
            MenuItem("menu.overwrite_confirm", self._go_character_select,
                     danger=True),
        ], INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 + 14, width=150,
            centered=True, on_sound=self.game.play_sound)

    def _cancel_overwrite(self) -> None:
        self.confirm_overwrite = None

    def _go_character_select(self) -> None:
        self.confirm_overwrite = None
        from src.ui.character_select import CharacterSelectScene
        self.scenes.push(CharacterSelectScene)

    def _open_settings(self) -> None:
        from src.ui.settings_scene import SettingsScene
        self.scenes.push(SettingsScene)

    # --- Dongu --------------------------------------------------------------
    def on_resume(self) -> None:
        # Karakter seciminden ya da ayarlardan donunce kayit degismis olabilir.
        self.save_data, self.save_status = read_save()
        self.menu = self._build_menu()
        self.backdrop.stage = stage_for(self.save_data)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            active = self.confirm_overwrite or self.menu
            active.click(self.game)
        elif event.type == pygame.KEYDOWN and self.confirm_overwrite:
            if self.game.input.pressed(Action.CANCEL):
                self._cancel_overwrite()

    def update(self) -> None:
        self.frame += 1
        self.backdrop.update()
        self.notice_frames = max(0, self.notice_frames - 1)
        active = self.confirm_overwrite or self.menu
        active.update(self.game)

    def draw(self, surface: pygame.Surface) -> None:
        self.backdrop.draw(surface)
        self._draw_title(surface)

        self.menu.draw(surface)
        self.menu.draw_hint(surface, INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 26)

        if self.save_data is not None and self.menu.index == 0:
            self._draw_save_card(surface)

        if self.confirm_overwrite:
            self._draw_overwrite_dialog(surface)

        self._draw_footer(surface)
        active = self.confirm_overwrite or self.menu
        active.draw_cursor(surface, self.game)

    # --- Cizim yardimcilari -------------------------------------------------
    def _draw_title(self, surface: pygame.Surface) -> None:
        """Baslik + kisaltma.

        Isim her iki dilde de kelimelerin bas harflerinden anlamli bir sozcuk
        cikaracak sekilde secildi:
            LEGEND OF REY: ECHOES  -> LORE
            REY EFSANESI: YANKILAR -> REY
        Bas harfleri vurgulayarak ciziyoruz ki bu tesadüf gibi degil, tasarim
        gibi okunsun - kisaltma basligin kendi icinden cikiyor.
        """
        self._draw_initial_caps(surface, t("title.full"), MENU_X, TITLE_Y)
        text.draw(surface, t("title.acronym"), MENU_X, TITLE_Y + 14,
                  color=palette.role("ui_text_bright"), outline=True,
                  tracking=6)
        pygame.draw.line(surface, palette.color("violet"),
                         (MENU_X, TITLE_Y + 32), (MENU_X + 96, TITLE_Y + 32))

    def _draw_initial_caps(self, surface: pygame.Surface, value: str,
                           x: int, y: int) -> None:
        """Her kelimenin ilk harfini vurgulu, gerisini soluk cizer."""
        bright = palette.role("ui_text")
        dim = palette.role("ui_text_dim")
        tracking = 1
        advance = GLYPH_WIDTH + tracking
        for word in value.split(" "):
            if not word:
                x += advance
                continue
            text.draw(surface, word[0], x, y, color=bright, tracking=tracking)
            if len(word) > 1:
                text.draw(surface, word[1:], x + advance, y, color=dim,
                          tracking=tracking)
            # Kelime + tek bosluk kadar ilerle.
            x += (len(word) + 1) * advance

    def _draw_save_card(self, surface: pygame.Surface) -> None:
        """DEVAM ET kartı: uc hafta sonra donen oyuncu nerede kaldigini
        hatirlamiyor. Bu kart hatirlatir."""
        data = self.save_data
        rect = pygame.Rect(CARD_X, CARD_Y, CARD_WIDTH, CARD_HEIGHT)
        panel(surface, rect)

        line_y = rect.y + 6
        text.draw(surface, t("save.chapter", chapter=data.chapter),
                  rect.x + 8, line_y,
                  color=palette.role("ui_text_bright"))
        line_y += GLYPH_HEIGHT + 2
        text.draw(surface, f"\"{t_or_raw(data.chapter_name)}\"", rect.x + 8, line_y,
                  color=palette.role("ui_text"))
        line_y += GLYPH_HEIGHT + 4
        pygame.draw.line(surface, palette.color("stone_dark"),
                         (rect.x + 8, line_y), (rect.right - 8, line_y))
        line_y += 4

        rows = (
            (t("save.playtime"), data.playtime_text),
            (t("save.gold"), str(data.gold)),
            (t("save.echo"),
             "●" * (data.echo_tier + 1) + "○" * (2 - data.echo_tier)),
            (t("save.secrets"),
             f"{data.secrets_found}/{max(1, data.secrets_total)}"),
        )
        for label, value in rows:
            text.draw(surface, label, rect.x + 8, line_y,
                      color=palette.role("ui_text_dim"))
            text.draw(surface, value, rect.right - 8, line_y,
                      color=palette.role("ui_text"), align="right")
            line_y += GLYPH_HEIGHT + 1

    def _draw_overwrite_dialog(self, surface: pygame.Surface) -> None:
        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        veil.fill((*palette.color("void"), 190))
        surface.blit(veil, (0, 0))

        rect = pygame.Rect(INTERNAL_WIDTH // 2 - 108,
                           INTERNAL_HEIGHT // 2 - 46, 216, 92)
        panel(surface, rect)
        text.draw(surface, t("menu.overwrite_warning"), INTERNAL_WIDTH // 2,
                  rect.y + 10, color=palette.role("ui_text"), align="center")
        if self.save_data:
            detail = (t("save.chapter", chapter=self.save_data.chapter) + " · "
                      f"{self.save_data.playtime_text}")
            text.draw(surface, detail, INTERNAL_WIDTH // 2, rect.y + 24,
                      color=palette.role("ui_text_dim"), align="center")
        self.confirm_overwrite.draw(surface)

    def _draw_footer(self, surface: pygame.Surface) -> None:
        if self.notice_frames > 0:
            text.draw(surface, t(self.notice), INTERNAL_WIDTH // 2,
                      INTERNAL_HEIGHT - 40, color=palette.color("danger_bright"),
                      align="center")
        text.draw(surface, "Ardeko Studios", 6, INTERNAL_HEIGHT - 12,
                  color=palette.color("stone_dark"))

    def debug_lines(self) -> list[str]:
        return [f"kayıt: {self.save_status}  "
                f"seçili: {self.menu.selected.label}"]
