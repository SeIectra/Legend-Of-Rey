"""Menunun kurulmasi - kameranin vardigi yer.

`docs/menu-ui.md` 0.2. Intro karardiktan sonra ekran **dogrudan menuye
kesmez**. Kamera mor alevin cok yakininda baslar ve yavasca geri cekilir:

    1 ekrani kaplayan mor alev (intro'nun devami gibi)
    2 kamera geri cekilir -> kaide gorunur
    3 geri cekilmeye devam -> mahzen, zincirler, karakterler
    4 kamera durur -> butonlar tek tek belirir

**Menu acilan bir ekran degil, kameranin vardigi bir yer olur.**

## Nasil yapiliyor

Menu sahnesi (`MenuBackdrop`) zaten tam olarak ciziliyor. Kamera hareketi
o goruntuyu **buyutup kaydirarak** elde ediliyor: basta alevin etrafindan
kucuk bir kare, sonunda tam kare. Ayri bir "yakin plan" sahnesi cizmeye
gerek yok.

Olcekleme `transform.scale` ile - `smoothscale` YASAK (CLAUDE.md 12).
Yakinlasma sirasinda tam sayi olcek tutturulamaz; bu **kabul edilebilir**
cunku hareket suruyor ve kare sabit degil. Kamera durdugu anda olcek tam
1.0 oluyor ve piksel izgarasi geri geliyor.
"""
from __future__ import annotations

import pygame

from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.cinematic import CinematicScene
from src.ui.menu_scene import FLAME_BASE, MenuBackdrop, stage_for

TOTAL = int(3.0 * FPS)
START_ZOOM = 4.2          # Alevin cok yakini
FADE_IN_FRAMES = int(0.5 * FPS)


class MenuRevealScene(CinematicScene):
    duration_frames = TOTAL

    def on_enter(self, **kwargs: object) -> None:
        super().on_enter(**kwargs)
        from src.systems.save import read_save
        self.save_data, _ = read_save()
        self.backdrop = MenuBackdrop(stage_for(self.save_data))
        self._buffer = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))

    def update_cinematic(self) -> None:
        self.backdrop.update()

    def draw_cinematic(self, surface: pygame.Surface, progress: float) -> None:
        self.backdrop.draw(self._buffer)

        zoom = START_ZOOM + (1.0 - START_ZOOM) * progress
        if zoom <= 1.001:
            surface.blit(self._buffer, (0, 0))
            return

        # Alevin etrafindan kucuk bir pencere al, ekrani kaplayacak sekilde
        # buyut. Pencere buyudukce kamera geri cekilmis olur.
        view_w = max(8, int(INTERNAL_WIDTH / zoom))
        view_h = max(8, int(INTERNAL_HEIGHT / zoom))
        # Odak alevden ekran merkezine kayar: basta aleve kilitli, sonda
        # sahnenin tamami.
        focus_x = FLAME_BASE[0] + (INTERNAL_WIDTH // 2 - FLAME_BASE[0]) * progress
        focus_y = FLAME_BASE[1] + (INTERNAL_HEIGHT // 2 - FLAME_BASE[1]) * progress

        left = int(round(focus_x - view_w / 2))
        top = int(round(focus_y - view_h / 2))
        left = max(0, min(INTERNAL_WIDTH - view_w, left))
        top = max(0, min(INTERNAL_HEIGHT - view_h, top))

        window = self._buffer.subsurface(pygame.Rect(left, top, view_w, view_h))
        surface.blit(pygame.transform.scale(
            window, (INTERNAL_WIDTH, INTERNAL_HEIGHT)), (0, 0))

        # Intro siyaha kararak bitiyor; buraya parlak bir yakin planla
        # baslamak kesme gibi okunuyordu. Ilk yarim saniye karanliktan
        # cikiyoruz - kamera zaten oradaymis, isik yeni geliyormus gibi.
        if self.elapsed < FADE_IN_FRAMES:
            veil = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
            veil.set_alpha(int(255 * (1.0 - self.elapsed / FADE_IN_FRAMES)))
            surface.blit(veil, (0, 0))

    def on_finished(self) -> None:
        # Menuye **gecis efekti olmadan** varilir: kamera zaten oraya geldi,
        # ustune bir de kararma koymak hareketi bolerdi.
        from src.ui.menu import MainMenuScene
        self.scenes.replace(MainMenuScene, transition=False,
                            reveal_buttons=True)
