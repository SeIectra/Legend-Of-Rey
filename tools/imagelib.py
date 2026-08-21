"""Boru hatti araclarinin ortak yardimcilari.

**Pillow gerekmiyor.** pygame zaten PNG okuyup yazabiliyor ve numpy dizi
islemlerini yapiyor; ucuncu bir bagimlilik eklemenin karsiligi yok
(CLAUDE.md 4: yeni bagimlilik sormadan eklenmez).

Diziler numpy'de (satir, sutun) sirali, pygame'de (genislik, yukseklik).
Aradaki eksen cevrimi tek yerde toplanmis olsun diye bu modul var.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

ALPHA_THRESHOLD = 128       # Yari saydam pikseller buna gore 0 veya 255 olur


def ensure_display() -> None:
    """convert_alpha() bir ekran bicimi ister; basssiz da olsa acilmali."""
    if not pygame.display.get_init():
        pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((64, 64))


def load(path: Path | str) -> pygame.Surface:
    ensure_display()
    return pygame.image.load(str(path)).convert_alpha()


def save(surface: pygame.Surface, path: Path | str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(path))


def to_arrays(surface: pygame.Surface) -> tuple[np.ndarray, np.ndarray]:
    """(yukseklik, genislik, 3) RGB ve (yukseklik, genislik) alfa dizileri."""
    rgb = np.transpose(pygame.surfarray.array3d(surface), (1, 0, 2))
    alpha = np.transpose(pygame.surfarray.array_alpha(surface), (1, 0))
    return rgb.astype(np.int16), alpha.astype(np.int16)


def from_arrays(rgb: np.ndarray, alpha: np.ndarray) -> pygame.Surface:
    ensure_display()
    height, width = alpha.shape
    surface = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
    pygame.surfarray.pixels3d(surface)[:] = np.transpose(
        np.clip(rgb, 0, 255).astype(np.uint8), (1, 0, 2))
    pygame.surfarray.pixels_alpha(surface)[:] = np.transpose(
        np.clip(alpha, 0, 255).astype(np.uint8), (1, 0))
    return surface


def solid_mask(alpha: np.ndarray) -> np.ndarray:
    """Dolu piksel maskesi - yari saydamlar esige gore yuvarlanir."""
    return alpha >= ALPHA_THRESHOLD


def iter_images(paths: list[str]) -> list[Path]:
    """Dosya ve klasor karisik girdiden PNG listesi cikarir."""
    found: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            found.extend(sorted(path.rglob("*.png")))
        elif path.is_file():
            found.append(path)
        else:
            print(f"[imagelib] bulunamadi: {path}")
    return found
