"""Bolum 3'un dort ara sahnesi. `docs/bolum-03.md` panel panel yazili.

`CinematicScene`'den tureyen iki tanesi burada tam ekran ele aliyor
(Inis, Mor - ikisi de kamera/karanlik odakli, `intro.py`'nin kare-esigi
dallanma deseniyle). Diger ikisi (Duvardakiler, Ucuncu Isaret) daha kisa
anlatim vuruslari - `Chapter03Scene` icinde kendi kare sayaciyla,
chapter02'nin `_update_hush`/`_update_claw_marks` desenini takip ediyor.
"""
from __future__ import annotations

import math

import pygame

from src.art import palette
from src.art.glow import radial_glow
from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.scenes.cinematic import CinematicScene

# --- Ara Sahne 1: "Inis" (bolum acilisi, ~8 saniye) --------------------------
PAN_END = int(3.0 * FPS)
GLOW_END = int(6.0 * FPS)
DESCENT_TOTAL = int(8.0 * FPS)


class DescentCinematic(CinematicScene):
    """Kamera asagi pan yapar, isik yaricapi sifira duser.

    *"Kelime yok. Sadece isigin kucuklugu ve karanligin buyuklugu."*
    """

    duration_frames = DESCENT_TOTAL

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        super().on_enter(**kwargs)
        self.character = character

    def draw_cinematic(self, surface: pygame.Surface, progress: float) -> None:
        surface.fill(palette.color("void"))
        elapsed = self.elapsed

        # Panel A: kamera asagi pan - ekran kararir (hicbir sey yok).
        if elapsed < PAN_END:
            return

        # Panel B: mesale isigi - sadece 3 tile'lik bir daire.
        radius = 20.0
        if elapsed < GLOW_END:
            shrink = (elapsed - PAN_END) / max(1, GLOW_END - PAN_END)
            radius = 20.0 * max(0.0, 1.0 - shrink * 0.3)
        else:
            fade = (elapsed - GLOW_END) / max(1, DESCENT_TOTAL - GLOW_END)
            radius = 20.0 * max(0.0, 1.0 - fade)

        if radius > 0.5:
            glow = radial_glow(int(radius * 1.6), palette.color("ember"), peak=0.5)
            cx, cy = INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2 + 20
            surface.blit(glow, (cx - glow.get_width() // 2, cy - glow.get_height() // 2),
                         special_flags=pygame.BLEND_RGB_ADD)

    def on_finished(self) -> None:
        from src.scenes.chapter03 import Chapter03Scene
        self.scenes.replace(Chapter03Scene, transition=False,
                            character=self.character)


# --- Ara Sahne 3: "Mor" (~10 saniye) - bolumun kalbi --------------------------
FLICKER_END = int(1.0 * FPS)
BLACKOUT_END = FLICKER_END + int(2.0 * FPS)          # 2 sn tam karanlik+sessizlik
GLOW_APPEAR = BLACKOUT_END + int(1.5 * FPS)
APPROACH_END = GLOW_APPEAR + int(3.0 * FPS)
ROAR_END = APPROACH_END + int(2.5 * FPS)
PURPLE_TOTAL = ROAR_END


class PurpleCinematic(CinematicScene):
    """Mesale soner, 2 saniye tam karanlik, sonra Mor Alev belirir.

    **Hizlandirilamaz** (`skippable=False`, `cinematic.py:56`'daki yorumun
    isaret ettigi tam bu an): 2 saniyelik karanlik zamanlamaya bagli,
    hizlanirsa etkisi olur - oyuncu "oyun mu dondu?" diye dusunmeli.
    """

    duration_frames = PURPLE_TOTAL
    skippable = False

    def draw_cinematic(self, surface: pygame.Surface, progress: float) -> None:
        surface.fill(palette.color("void"))
        elapsed = self.elapsed

        if elapsed < FLICKER_END:
            # Panel A: mesale titreşir, soner.
            flicker = 1.0 - elapsed / FLICKER_END
            radius = int(18 * flicker)
            if radius > 0:
                glow = radial_glow(radius, palette.color("ember"), peak=0.4 * flicker)
                cx, cy = INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2
                surface.blit(glow, (cx - radius, cy - radius),
                             special_flags=pygame.BLEND_RGB_ADD)
            return

        if elapsed < BLACKOUT_END:
            return                          # Panel B: tam karanlik, tam sessizlik

        if elapsed < GLOW_APPEAR:
            return                          # Uzakta bir isik henuz yok

        # Panel C/D: uzakta beliren, buyuyen mor isik.
        t_value = min(1.0, (elapsed - GLOW_APPEAR) / max(1, APPROACH_END - GLOW_APPEAR))
        radius = int(6 + 46 * t_value)
        glow = radial_glow(radius, palette.color("violet"), peak=0.5 * max(0.2, t_value))
        cx, cy = INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2
        surface.blit(glow, (cx - radius, cy - radius), special_flags=pygame.BLEND_RGB_ADD)

        if elapsed >= APPROACH_END:
            # Panel F: Yanki bagirir - ekran sarsilir (yonlu degil, radyal).
            shake_t = (elapsed - APPROACH_END) / max(1, ROAR_END - APPROACH_END)
            amount = int(3 * max(0.0, 1.0 - shake_t))
            if amount > 0:
                ox = int(math.sin(elapsed * 1.7) * amount)
                oy = int(math.cos(elapsed * 2.1) * amount)
                surface.scroll(ox, oy)

    def on_finished(self) -> None:
        # `push` ile acildi (Chapter03Scene altta durur, dondurulmus
        # halde) - `pop` onu kaldigi yerden aynen surdurur. Ayri bir
        # "resume_room" mekanizmasi gerekmiyor.
        self.scenes.pop()
