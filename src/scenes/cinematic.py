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

## Hizlandirma **sessiz**

`docs/menu-ui.md` 0.5 ekranin altinda "Hizlandirmak icin basili tut" ipucu
istiyordu. Arda kaldirdi (22.08.2026) ve hakli: studyo logosunun uzerine
"bunu gecebilirsin" yazmak, oyuncuya daha ilk saniyede izlediginin
atlanacak bir sey oldugunu soyluyor.

Davranis duruyor, yalnizca **yazi** yok. Tusa basan hizlanir, basmayan tam
yasar; kimseye atlamasi soylenmiyor.
"""
from __future__ import annotations

import pygame

from src.core.input import Action
from src.core.scene import Scene

SPEEDUP_FACTOR = 3.0


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

    def on_enter(self, **kwargs: object) -> None:
        self.elapsed = 0.0
        self.frame = 0
        self.finished = False
        self.speeding = False

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
        self.update_cinematic()

        if self.raw_progress >= 1.0 and not self.finished:
            self.finished = True
            self.on_finished()

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_cinematic(surface, self.progress)

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
