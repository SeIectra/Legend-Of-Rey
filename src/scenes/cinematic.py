"""Sinematik sahne temeli - intro, dikey yolculuk, ara sahneler.

## Bir kural, tek yerde

**Hicbir gecis tusla ANIDEN kesilmez** (CLAUDE.md 9, docs/menu-ui.md 0.5).
Sert kesme ucuz gorunur ve mekan hissini bozar. Bunun yerine tusa **basili
tutunca gecis 3 kat hizlanir** ve akici bicimde varir:

  * kesik yok, ekran kaymiyor, sadece daha cabuk iniyorsun
  * ilk kez oynayan tam yasar
  * 20. kez acan bekletilmez

Kural burada bir kez yaziliyor; her sinematik bundan tureyerek dogru
davranisi bedavaya aliyor. Ayri ayri yazilsaydi biri mutlaka "tusa
basinca atla" derdi.

## Zaman

Sinematikler **kare** sayar, saniye degil (CLAUDE.md 4). Hizlandirma
ilerlemeyi hizlandirir, kare hizini degil - fizik sabit adimda kalir.

## Hizlandirma ipucu

Iki saniye sonra ekranin altinda beliriyor. Hemen gosterilse sinematigi
bastan "atlanacak bir sey" gibi cerceveler; hic gosterilmese 20. acilista
oyuncu beklemek zorunda kalir.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH
from src.core.input import Action
from src.core.scene import Scene
from src.ui import text
from src.ui.i18n import t

SPEEDUP_FACTOR = 3.0
HINT_DELAY_FRAMES = FPS * 2          # 2 saniye
HINT_FADE_FRAMES = 20


def smoothstep(t_value: float) -> float:
    """Hizlanma -> sabit -> yavaslama. Dogrusal hareket makine gibi okunur."""
    t_value = max(0.0, min(1.0, t_value))
    return t_value * t_value * (3.0 - 2.0 * t_value)


class CinematicScene(Scene):
    """Sureli, hizlandirilabilir sahne.

    Alt sinif `duration_frames` verir ve `draw_cinematic(surface, progress)`
    yazar. `progress` 0..1 arasi **yumusatilmis** ilerleme.
    """

    duration_frames: int = 120
    skippable: bool = True          # Bolum 3'teki "Mor" sahnesi False olacak
    show_hint: bool = True

    def on_enter(self, **kwargs: object) -> None:
        self.elapsed = 0.0
        self.frame = 0
        self.finished = False
        self.speeding = False
        self._hint_alpha = 0

    # --- Ilerleme -----------------------------------------------------------
    @property
    def raw_progress(self) -> float:
        return min(1.0, self.elapsed / max(1, self.duration_frames))

    @property
    def progress(self) -> float:
        return smoothstep(self.raw_progress)

    def _advance(self) -> None:
        held = self.game.input.held(Action.CONFIRM) or \
            self.game.input.held(Action.JUMP) or \
            self.game.input.held(Action.ATTACK)
        self.speeding = bool(held) and self.skippable
        # Hizlandirma **ilerlemeyi** hizlandirir, kare hizini degil.
        self.elapsed += SPEEDUP_FACTOR if self.speeding else 1.0

    # --- Dongu --------------------------------------------------------------
    def update(self) -> None:
        self.frame += 1
        self._advance()

        if self.show_hint and self.skippable and self.frame > HINT_DELAY_FRAMES:
            self._hint_alpha = min(180, self._hint_alpha + 180 // HINT_FADE_FRAMES)

        self.update_cinematic()

        if self.raw_progress >= 1.0 and not self.finished:
            self.finished = True
            self.on_finished()

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_cinematic(surface, self.progress)
        if self._hint_alpha > 0:
            self._draw_hint(surface)

    def _draw_hint(self, surface: pygame.Surface) -> None:
        label = t("cinematic.hold_to_speed")
        width = text.text_width(label)
        strip = pygame.Surface((width + 8, 13), pygame.SRCALPHA)
        strip.fill((*palette.color("void"), min(140, self._hint_alpha)))
        surface.blit(strip, (INTERNAL_WIDTH // 2 - width // 2 - 4,
                             INTERNAL_HEIGHT - 20))
        text.draw(surface, label, INTERNAL_WIDTH // 2, INTERNAL_HEIGHT - 18,
                  color=palette.role("ui_text_dim"), align="center",
                  alpha=self._hint_alpha)

    # --- Alt sinif kancalari ------------------------------------------------
    def update_cinematic(self) -> None:
        """Her karede cagrilir. Alt sinif kendi durumunu burada surer."""

    def draw_cinematic(self, surface: pygame.Surface,
                       progress: float) -> None:
        raise NotImplementedError

    def on_finished(self) -> None:
        """Sure doldu. Alt sinif sonraki sahneye gecer."""

    def debug_lines(self) -> list[str]:
        return [f"sinematik {self.raw_progress * 100:5.1f}%"
                f"{'  HIZLI' if self.speeding else ''}"]
