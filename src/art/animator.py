"""Animasyon oynatici ve sprite onbellegi.

Iki oynatma kipi var, ikisi de gerekli:

  * **Zamanla surulen** (bosta, kosu, dusme): her sanat karesi sabit sayida
    oyun karesi durur - 8 FPS hissi.
  * **Ilerlemeyle surulen** (saldirilar): kare, saldirinin kendi kare
    butcesindeki (`4/3/8`) ilerleme oranindan secilir. Animasyon dovus
    zamanlamasini asla kaydiramaz - kare hassasiyeti dovusun kalbidir.

Sprite'lar **bir kez** uretilir ve onbellege alinir; her karede yeniden
uretmek kare butcesini yer (CLAUDE.md 4).
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.animation import ANIMATIONS, CHARACTERS, build_sprite_set
from src.art.forge import flip_h, silhouette, squash_surface
from src.art.spritegen import CharSpec

# Bosta/kosu gibi donguselerde her sanat karesi kac oyun karesi durur.
DEFAULT_HOLD_FRAMES = 7
HOLD_OVERRIDES: dict[str, int] = {
    "run": 5,          # Kosu biraz daha hizli okunmali
    "fall": 6,
    "idle": 9,         # Nefes yavas
    "death": 8,
}

_sprite_cache: dict[str, dict[str, list[pygame.Surface]]] = {}
_flipped_cache: dict[int, pygame.Surface] = {}
_silhouette_cache: dict[int, pygame.Surface] = {}


def sprite_set(name: str) -> dict[str, list[pygame.Surface]]:
    """Karakterin tum animasyonlari - ilk cagirmada uretilir, sonra onbellek."""
    cached = _sprite_cache.get(name)
    if cached is None:
        spec: CharSpec = CHARACTERS[name]
        cached = build_sprite_set(spec)
        _sprite_cache[name] = cached
    return cached


def clear_cache() -> None:
    """Palet ya da rig degistiginde cagrilir."""
    _sprite_cache.clear()
    _flipped_cache.clear()
    _silhouette_cache.clear()


def _flipped(surface: pygame.Surface) -> pygame.Surface:
    key = id(surface)
    cached = _flipped_cache.get(key)
    if cached is None:
        cached = flip_h(surface)
        _flipped_cache[key] = cached
    return cached


def _silhouetted(surface: pygame.Surface,
                 colour: palette.RGB) -> pygame.Surface:
    key = (id(surface), colour)
    cached = _silhouette_cache.get(key)
    if cached is None:
        cached = silhouette(surface, colour)
        if len(_silhouette_cache) > 512:
            _silhouette_cache.clear()
        _silhouette_cache[key] = cached
    return cached


class Animator:
    """Bir karakterin animasyon durumunu surer."""

    def __init__(self, character: str) -> None:
        self.character = character
        self.frames = sprite_set(character)
        self.state = "idle"
        self.index = 0
        self.hold = 0
        self.finished = False

    def play(self, state: str, restart: bool = False) -> None:
        if state not in self.frames:
            return
        if state == self.state and not restart:
            return
        self.state = state
        self.index = 0
        self.hold = 0
        self.finished = False

    def update(self) -> None:
        """Zamanla surulen kip - bir oyun karesi ilerlet."""
        sequence = self.frames.get(self.state)
        if not sequence:
            return
        _, _, looping = ANIMATIONS.get(self.state, (None, 1, True))
        if self.finished and not looping:
            return

        self.hold += 1
        if self.hold < HOLD_OVERRIDES.get(self.state, DEFAULT_HOLD_FRAMES):
            return
        self.hold = 0
        self.index += 1
        if self.index >= len(sequence):
            if looping:
                self.index = 0
            else:
                self.index = len(sequence) - 1
                self.finished = True

    def set_progress(self, ratio: float) -> None:
        """Ilerlemeyle surulen kip - saldirilar icin.

        `ratio` saldirinin kendi kare butcesindeki konumu (0..1).
        """
        sequence = self.frames.get(self.state)
        if not sequence:
            return
        ratio = max(0.0, min(1.0, ratio))
        self.index = min(len(sequence) - 1, int(ratio * len(sequence)))
        self.hold = 0

    @property
    def image(self) -> pygame.Surface | None:
        sequence = self.frames.get(self.state)
        if not sequence:
            return None
        return sequence[min(self.index, len(sequence) - 1)]

    def render(self, facing: int, *, flash: bool = False,
               squash: tuple[float, float] = (1.0, 1.0),
               silhouette_mode: bool = False,
               tint_colour: palette.RGB | None = None,
               alpha: int = 255) -> pygame.Surface | None:
        """Cizime hazir yuzey: yon, flas, deformasyon ve siluet uygulanmis."""
        image = self.image
        if image is None:
            return None
        if facing < 0:
            image = _flipped(image)

        if silhouette_mode:
            image = _silhouetted(image, palette.color("stone_light"))
        elif flash:
            image = _silhouetted(image, palette.role("hit_flash"))
        elif tint_colour is not None:
            image = _silhouetted(image, tint_colour)

        image = squash_surface(image, squash)

        if alpha < 255:
            image = image.copy()
            image.set_alpha(alpha)
        return image
