"""Olum ekrani - "oldun, simdi ne olacak" sorusunun cevabi.

## Neden var

Arda, 29.08.2026, canli oynanis: *"Boss fight'ta olunce kaldik oyle.
Hicbir sey yapilmiyor."*

Hata `restart()`'ta degildi - R **calisiyordu**. Hata soyleyende: olum
bir **toast** ile bildiriliyordu ve toast 72 karede (~1.2 saniye)
sonuyordu. O andan sonra oyuncu, olu bir karakterin durdugu hareketsiz
bir ekrana bakiyor ve ekranda hicbir yonerge yok.

Gecici bir bildirim kalici bir durumu anlatamaz. Olum bir olay degil bir
**hal**; hal, hal gibi gosterilmeli - o yuzden bu bir bindirme sahne,
kapanana kadar duruyor.

## Arka plan gorunur kaliyor

`PauseScene` ile ayni desen (`blocks_update=True`, `blocks_draw=False`):
oyuncu **nerede oldugunu** goruyor. Tam siyah bir ekran bilgiyi siler;
oyuncunun "ha, o patlamada" diyebilmesi gerekiyor.

## Varsayilan secim TEKRAR DENE

`docs/menu-ui.md` / `CLAUDE.md` 9: *"Yikici eylemlerde varsayilan secim
daima IPTAL."* Buradaki yikici eylem ana menuye donmek - bolumun geri
kalanini birakmak demek. O yuzden imlec tekrar denemede basliyor ve ana
menu asagida, ayri bir bosluktan sonra.

Ayrica ana menuye donerken **kaydedildigi acikca yaziliyor** - ayni
belgenin "kaydedilmemis ilerleme belirsizligi asla olusmasin" kurali.

## Nereden devam edecegi YAZIYOR

`PlayScene.restart()` bolumun degil **odanin** basindan devam ettiriyor
(29.08.2026 kontrol noktasi). Oyuncu bunu bilmiyorsa "bastan mi
basliyorum" korkusuyla cikabilir - o yuzden oda adi ekranda.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.scene import Scene
from src.systems.save import write_save
from src.ui import text
from src.ui.i18n import t
from src.ui.widgets import Menu, MenuItem, blur, panel

PANEL_WIDTH = 190
PANEL_HEIGHT = 92
BLUR_FACTOR = 4
# Baslik panelin ustunde, biraz ayri - "OLDUN" bir menu ogesi degil.
TITLE_Y = INTERNAL_HEIGHT // 2 - 62
# Yazinin belirmesi: ani degil. Olum ani zaten sarsintili; ekranin da
# aninda gelmesi ust uste binerdi.
FADE_IN_FRAMES = 26


class DeathScene(Scene):
    """Oyuncu oldu. Bindirme - altaki sahne gorunur ama donmus."""

    blocks_update = True
    blocks_draw = False

    def on_enter(self, save_data=None, room_label: str = "",
                 on_retry=None, **kwargs: object) -> None:
        self.save_data = save_data
        self.room_label = room_label
        self.on_retry = on_retry
        self.frames = 0
        self.saved_notice = 0
        self._blurred: pygame.Surface | None = None

        self.menu = Menu([
            MenuItem("death.retry", self._retry),
            MenuItem("death.main_menu", self._quit, gap_before=True),
        ], INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 - 8, width=140,
            centered=True, on_sound=self.game.play_sound)

    # --- Eylemler -----------------------------------------------------------
    def _retry(self) -> None:
        self.game.play_sound("ui_confirm")
        self.scenes.pop()
        if self.on_retry:
            self.on_retry()

    def _quit(self) -> None:
        """Ana menuye don - **kaydederek**.

        Kayit sessizce yapilmiyor, yazisi ekranda beliriyor: oyuncu neyi
        kaybettigini/koruduguni bilmeden cikmamali.
        """
        if self.save_data is not None:
            write_save(self.save_data)
        self.saved_notice = 90
        self.game.play_sound("ui_back")
        from src.ui.menu import MainMenuScene
        self.scenes.set_root(MainMenuScene)

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        self.frames += 1
        self.saved_notice = max(0, self.saved_notice - 1)
        # `Menu.update` gezinme + onaylamanin tamamini yapiyor (`game`
        # aliyor, `input` degil - `PauseScene` ile ayni cagri).
        self.menu.update(self.game)

    def handle_event(self, event: pygame.event.Event) -> None:
        # `R` de calisiyor: eski olum yazisi R'yi ogretmisti ve oyuncunun
        # kas hafizasi oyle kuruldu. Menuyu okumadan refleksle basana da
        # ayni sey olmali - yeni ekran eski aliskanligi kirmamali.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self._retry()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.menu.click(self.game)

    # --- Cizim --------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        if self._blurred is None:
            self._blurred = blur(surface, BLUR_FACTOR)
        surface.blit(self._blurred, (0, 0))

        veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT),
                              pygame.SRCALPHA)
        fade = min(1.0, self.frames / FADE_IN_FRAMES)
        veil.fill((*palette.color("void"), int(190 * fade)))
        surface.blit(veil, (0, 0))
        if fade < 0.35:
            return                      # yazi henuz gelmedi

        text.draw(surface, t("death.title"), INTERNAL_WIDTH // 2, TITLE_Y,
                  palette.color("blood_bright"), align="center",
                  outline=True, tracking=3)

        rect = pygame.Rect(0, 0, PANEL_WIDTH, PANEL_HEIGHT)
        rect.center = (INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 + 4)
        panel(surface, rect)

        # Nereden devam edilecegi - "bastan mi basliyorum" korkusunu
        # ekranda kesiyoruz.
        if self.room_label:
            text.draw(surface, t("death.resume_at", room=self.room_label),
                      INTERNAL_WIDTH // 2, rect.top + 8,
                      palette.color("stone_light"), align="center")

        self.menu.draw(surface)

        if self.saved_notice:
            text.draw(surface, t("death.saved"), INTERNAL_WIDTH // 2,
                      rect.bottom + 6, palette.color("moss_light"),
                      align="center")
