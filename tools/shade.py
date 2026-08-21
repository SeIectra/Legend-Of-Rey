"""Sol-ust isik kuralini otomatik uygular.

Stil sozlesmesi der ki: **isik kaynagi her zaman sol usttendir** (CLAUDE.md 6).
Elle cizerken bu kural unutulur ve sprite'lar birbirini tutmaz. Burada
otomatiklestiriyoruz:

  * Sol-ust komsusu bos olan piksel isik alir  -> rampada bir basamak acilir
  * Sag-alt komsusu bos olan piksel golgede kalir -> bir basamak koyulasir

Sonuc **paletten cikmaz**: her renk once ait oldugu rampada bulunur, sonra
komsu basamaga tasinir. Rampada olmayan renklere dokunulmaz.

Kullanim:
    python tools/shade.py assets/sprites/rey.png
    python tools/shade.py assets/sprites/ --guc 2
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

LIGHT_DX, LIGHT_DY = -1, -1     # Sol ust


def _build_step_table() -> dict[tuple[int, int, int], tuple[str, int]]:
    """Renk -> (rampa adi, basamak). Bir renk birden fazla rampadaysa ilki."""
    table: dict[tuple[int, int, int], tuple[str, int]] = {}
    for ramp_name, steps in palette.RAMPS.items():
        for index, colour_name in enumerate(steps):
            colour = palette.color(colour_name)
            table.setdefault(colour, (ramp_name, index))
    return table


_STEP_TABLE = _build_step_table()


def shade_arrays(rgb: np.ndarray, alpha: np.ndarray,
                 strength: int = 1) -> np.ndarray:
    """Kenar piksellerini rampada kaydirir, yeni RGB dizisi doner."""
    solid = solid_mask(alpha)
    if not solid.any():
        return rgb

    # Sol-ust komsu bos mu? (kenar = isik)
    lit = np.zeros_like(solid)
    lit[1:, 1:] = solid[1:, 1:] & ~solid[:-1, :-1]
    lit[0, :] |= solid[0, :]
    lit[:, 0] |= solid[:, 0]

    # Sag-alt komsu bos mu? (kenar = golge)
    dark = np.zeros_like(solid)
    dark[:-1, :-1] = solid[:-1, :-1] & ~solid[1:, 1:]
    dark[-1, :] |= solid[-1, :]
    dark[:, -1] |= solid[:, -1]

    # Hem isik hem golge kenarinda olan ince piksel degismez.
    lighten = lit & ~dark
    darken = dark & ~lit

    out = rgb.copy()
    for mask, delta in ((lighten, strength), (darken, -strength)):
        if not mask.any():
            continue
        coords = np.argwhere(mask)
        for y, x in coords:
            key = (int(rgb[y, x, 0]), int(rgb[y, x, 1]), int(rgb[y, x, 2]))
            entry = _STEP_TABLE.get(key)
            if entry is None:
                continue        # Rampada olmayan renge dokunma
            ramp_name, step = entry
            out[y, x] = palette.ramp_color(ramp_name, step + delta)
    return out


def shade_file(path: Path, out: Path | None = None, strength: int = 1) -> Path:
    rgb, alpha = to_arrays(load(path))
    new_rgb = shade_arrays(rgb, alpha, strength)
    target = out or path
    save(from_arrays(new_rgb, alpha), target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Sol-ust isik golgelemesi")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--guc", type=int, default=1,
                        help="rampada kac basamak kaydirilacak")
    args = parser.parse_args()

    images = iter_images(args.paths)
    if not images:
        print("islenecek gorsel yok")
        return 1

    print(f"{len(images)} gorsel · isik sol ust · guc {args.guc}")
    for image in images:
        print(f"  {shade_file(image, args.out, args.guc).name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
