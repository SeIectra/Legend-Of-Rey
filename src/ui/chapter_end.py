"""Bolum sonu ekrani.

`docs/bolum-02.md`: *"Bolum sonu ekrani onemli: '0/1 gizli alan' goren
oyuncu bir daha gizli alan arar."* Ekranin isi ozetlemek degil, **bir
sonraki oynayisi sekillendirmek**.

## Bulunmayan gizli alan vurgulanir, bulunan sessiz gecer

1/1 goren oyuncuya soylenecek bir sey yok - zaten yapmis. 0/1 goren
oyuncuya bir sey kacirdigi soylenmeli. O yuzden eksik satir tehlike
renginde ve digerlerinden bir tik daha gec aciliyor: goz en son oraya
takiliyor.

## Satirlar sirayla aciliyor

Hepsi ayni anda gelseydi ekran bir tablo olurdu ve okunmadan gecilirdi.
Sirayla acilinca her satir kendi anini aliyor. Toplam ~40 kare - menu
gecisi degil bu, bir **kapanis**; 12 kare kurali (CLAUDE.md 9) menu
gecisleri icin, kapanis anlari icin degil.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

from src.art import palette
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.ui import text
from src.ui.i18n import t
from src.ui.widgets import blur, panel

PANEL_WIDTH = 196
PANEL_HEIGHT = 112
ROW_STEP = 13                    # Satirlar arasi dikey mesafe
BLUR_FACTOR = 4

FADE_FRAMES = 26                 # Karartma
ROW_DELAY = 9                    # Satirlar arasi
ROW_START = 20                   # Ilk satir bu kareden sonra
# Onaydan once bu kadar kare gecmeli: kapanis anini yanlislikla atlamak
# butun ozeti gorunmez yapardi.
INPUT_LOCK_FRAMES = 36


@dataclass(frozen=True)
class ChapterResult:
    """Bir bolumun ozeti. Sahne bunu doldurup ekrani aciyor."""

    chapter_key: str             # Dil anahtari - kayit dilden bagimsiz
    frames: int                  # Bolumde gecen kare
    best_combo: int
    gold: int
    secrets_found: int
    secrets_total: int
    # Bolum 3'un karari. `None` = bu bolumde hic sorulmadi (Bolum 1/2),
    # satir hic gorunmez - onceki bolumlerin ozet ekranini degistirmez.
    purple_flame_taken: bool | None = None

    @property
    def missed_secret(self) -> bool:
        return self.secrets_total > 0 and self.secrets_found < self.secrets_total


def format_time(frames: int) -> str:
    """Kare -> dd:ss. Zaman birimi karede tutulur, saniyede degil."""
    seconds = max(0, frames) // 60
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class ChapterEndScene(Scene):
    """Bolum ozeti. Altaki sahne donar ama gorunur kalir."""

    blocks_update = True
    blocks_draw = False
    transparent_bg = True

    def on_enter(self, result: ChapterResult | None = None,
                 on_continue: Callable[[], None] | None = None,
                 **kwargs: object) -> None:
        self.result = result
        self.on_continue = on_continue
        self.frames = 0
        self._blurred: pygame.Surface | None = None

    # --- Dongu --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if self.frames < INPUT_LOCK_FRAMES:
            return
        if (self.game.input.pressed(Action.CONFIRM)
                or self.game.input.pressed(Action.PAUSE)):
            self._continue()

    def update(self) -> None:
        self.frames += 1

    def _continue(self) -> None:
        if self.on_continue is not None:
            self.on_continue()
            return
        from src.ui.menu import MainMenuScene
        self.scenes.set_root(MainMenuScene)

    # --- Cizim --------------------------------------------------------------
    def _rows(self) -> list[tuple[str, str, str]]:
        """(etiket anahtari, deger, renk rolu) uclulerinden olusan satirlar."""
        data = self.result
        if data is None:
            return []
        rows = [
            ("chapter_end.time", format_time(data.frames), "ui_text"),
            ("chapter_end.combo", str(data.best_combo), "ui_text"),
            ("chapter_end.gold", str(data.gold), "ui_text"),
        ]
        # Gizli alani olmayan bolumde satir **hic** gorunmuyor. "0/0" bu
        # ekranin isini tersine cevirirdi: satirin butun anlami "bir sey
        # kacirdin" demek, ve kacirilacak bir sey yokken oyuncuya yanlis
        # bir eksiklik duygusu verirdi (Bolum 4 bir ★nefes bolumu).
        # Varsayilan davranis degismedi: Bolum 2 ve 3 birer gizli alan
        # bildiriyor ve satirlarini aynen goruyor (DEVIR.md 6/18 -
        # paylasilan sinifa eklenen davranis eskisini korumali).
        if data.secrets_total > 0:
            rows.append(("chapter_end.secrets",
                         f"{data.secrets_found}/{data.secrets_total}",
                         "danger" if data.missed_secret else "ui_text"))
        if data.purple_flame_taken is not None:
            value_key = ("chapter_end.taken" if data.purple_flame_taken
                        else "chapter_end.left")
            rows.append(("chapter_end.purple_flame", t(value_key), "ui_text"))
        return rows

    def visible_rows(self) -> int:
        """Kac satir acildi. Test bunu okuyor."""
        if self.frames < ROW_START:
            return 0
        return min(len(self._rows()),
                   1 + (self.frames - ROW_START) // ROW_DELAY)

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_backdrop(surface)
        if self.result is None:
            return

        # Satir sayisi bolume gore degisir (Bolum 3'un Mor Alev satiri gibi)
        # - panel yuksekligi buna gore buyur, aksi halde son satir cerceveyi
        # keser (DEVIR.md 9 - bu hata iki panelde daha once yasandi).
        panel_height = max(PANEL_HEIGHT, 43 + len(self._rows()) * ROW_STEP + 20)
        rect = pygame.Rect(INTERNAL_WIDTH // 2 - PANEL_WIDTH // 2,
                           INTERNAL_HEIGHT // 2 - panel_height // 2,
                           PANEL_WIDTH, panel_height)
        panel(surface, rect)

        text.draw(surface, t("chapter_end.heading"), INTERNAL_WIDTH // 2,
                  rect.y + 9, color=palette.role("ui_text_dim"),
                  align="center", tracking=2)
        text.draw(surface, t(self.result.chapter_key), INTERNAL_WIDTH // 2,
                  rect.y + 21, color=palette.color("violet_bright"),
                  align="center", outline=True)
        surface.fill(palette.role("ui_border"),
                     (rect.x + 14, rect.y + 34, rect.width - 28, 1))

        shown = self.visible_rows()
        y = rect.y + 43
        for index, (label, value, role) in enumerate(self._rows()):
            if index >= shown:
                break
            colour = (palette.color("danger_bright") if role == "danger"
                      else palette.role("ui_text_dim"))
            text.draw(surface, t(label), rect.x + 18, y,
                      color=palette.role("ui_text_dim"))
            text.draw(surface, value, rect.right - 18, y,
                      color=colour, align="right")
            y += ROW_STEP

        if shown >= len(self._rows()) and self.frames >= INPUT_LOCK_FRAMES:
            self._draw_prompt(surface, rect)

    def _draw_prompt(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            return
        text.draw(surface, t("chapter_end.continue"), INTERNAL_WIDTH // 2,
                  rect.bottom - 13, color=palette.role("ui_text_dim"),
                  align="center")

    def _draw_backdrop(self, surface: pygame.Surface) -> None:
        """Altaki sahne bulaniklasip karariyor - bolum geride kaliyor."""
        if self._blurred is None:
            self._blurred = blur(surface, BLUR_FACTOR)
        surface.blit(self._blurred, (0, 0))

        alpha = int(190 * min(1.0, self.frames / FADE_FRAMES))
        shade = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        shade.fill(palette.color("void"))
        shade.set_alpha(alpha)
        surface.blit(shade, (0, 0))
