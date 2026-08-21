"""Sprite'a otomatik kontur ekler.

Kontur rengi paletin **en koyu 2. rengi** - siyah degil (CLAUDE.md 6). Saf
siyah kontur piksel artta sert ve ucuz durur; bir tik aydinlik kontur silueti
ayni netlikte verir ama sahneye oturur.

Yontem: alfa maskesini genislet (dilate), orijinali cikar, kalan halka kontur.

Kullanim:
    python tools/outline.py assets/sprites/rey.png
    python tools/outline.py assets/sprites/ --capraz     # 8 yone
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

# Depo kokunu import yoluna ekle - arac dogrudan calistirilabilsin.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from tools.imagelib import (
    from_arrays, iter_images, load, save, solid_mask, to_arrays,
)

from src.art import palette

# Kontur sprite'in disina tasar; tuval bu kadar buyutulur.
PAD = 1


def dilate(mask: np.ndarray, diagonal: bool = False) -> np.ndarray:
    """Maskeyi bir piksel genislet."""
    grown = np.zeros_like(mask)
    grown[1:, :] |= mask[:-1, :]
    grown[:-1, :] |= mask[1:, :]
    grown[:, 1:] |= mask[:, :-1]
    grown[:, :-1] |= mask[:, 1:]
    if diagonal:
        grown[1:, 1:] |= mask[:-1, :-1]
        grown[:-1, :-1] |= mask[1:, 1:]
        grown[1:, :-1] |= mask[:-1, 1:]
        grown[:-1, 1:] |= mask[1:, :-1]
    return grown | mask


def add_outline(rgb: np.ndarray, alpha: np.ndarray, diagonal: bool = False,
                pad: int = PAD) -> tuple[np.ndarray, np.ndarray]:
    """Cevresine kontur eklenmis yeni diziler doner (tuval `pad` kadar buyur)."""
    height, width = alpha.shape
    big_rgb = np.zeros((height + pad * 2, width + pad * 2, 3), dtype=np.int16)
    big_alpha = np.zeros((height + pad * 2, width + pad * 2), dtype=np.int16)
    big_rgb[pad:pad + height, pad:pad + width] = rgb
    big_alpha[pad:pad + height, pad:pad + width] = alpha

    solid = solid_mask(big_alpha)
    ring = dilate(solid, diagonal) & ~solid

    outline_colour = np.array(palette.outline(), dtype=np.int16)
    big_rgb[ring] = outline_colour
    big_alpha[ring] = 255
    return big_rgb, big_alpha


def outline_file(path: Path, out: Path | None = None,
                 diagonal: bool = False) -> Path:
    rgb, alpha = to_arrays(load(path))
    new_rgb, new_alpha = add_outline(rgb, alpha, diagonal)
    target = out or path
    save(from_arrays(new_rgb, new_alpha), target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprite'a kontur ekler")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--capraz", action="store_true",
                        help="8 yone kontur (kose bosluklarini da kapatir)")
    args = parser.parse_args()

    images = iter_images(args.paths)
    if not images:
        print("islenecek gorsel yok")
        return 1
    if args.out and len(images) > 1:
        print("--out yalnizca tek dosyayla kullanilir")
        return 1

    print(f"{len(images)} gorsel · kontur rengi: {palette.OUTLINE_NAME} "
          f"{palette.outline()}")
    for image in images:
        result = outline_file(image, args.out, args.capraz)
        print(f"  {result.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
