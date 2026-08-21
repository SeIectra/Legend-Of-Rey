"""Herhangi bir gorseli 32 renklik palete indirger.

**Boru hattinin altin kurali:** Kaynagi ne olursa olsun - kod, elle cizim,
harici arac - her gorsel buradan gecer. Bu tek kural projenin en buyuk riskini
(tutarsizlik) yapisal olarak cozer (docs/asset-boru-hatti.md 7).

  * Dithering KAPALI - piksel artta genelde kirletir
  * Alfa esige gore 0 veya 255'e yuvarlanir - yari saydam kenar birakmaz
  * En yakin renk oklid mesafesiyle bulunur, sonuc onbelleklenir

Kullanim:
    python tools/quantize.py assets/sprites/rey.png
    python tools/quantize.py assets/sprites/           # klasordeki tum PNG'ler
    python tools/quantize.py girdi.png --out cikti.png --rapor
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


def quantize_arrays(rgb: np.ndarray, alpha: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    """Diziyi palete indirger. (rgb, alfa, degisen_piksel_sayisi) doner."""
    solid = solid_mask(alpha)
    out_rgb = rgb.copy()
    changed = 0

    # Benzersiz renkler uzerinde calis: 32x32 sprite'ta binlerce piksel var
    # ama genelde 20-30 benzersiz renk. Onbellek isi bitiriyor.
    if solid.any():
        pixels = rgb[solid]
        unique, inverse = np.unique(pixels.reshape(-1, 3), axis=0,
                                    return_inverse=True)
        mapped = np.array(
            [palette.nearest(tuple(int(c) for c in colour)) for colour in unique],
            dtype=np.int16)
        result = mapped[inverse]
        changed = int(np.count_nonzero((pixels != result).any(axis=1)))
        out_rgb[solid] = result

    out_alpha = np.where(solid, 255, 0).astype(np.int16)
    return out_rgb, out_alpha, changed


def quantize_file(path: Path, out: Path | None = None,
                  report: bool = False) -> Path:
    surface = load(path)
    rgb, alpha = to_arrays(surface)
    new_rgb, new_alpha, changed = quantize_arrays(rgb, alpha)
    target = out or path
    save(from_arrays(new_rgb, new_alpha), target)
    if report:
        total = int(np.count_nonzero(solid_mask(alpha)))
        percent = (changed / total * 100.0) if total else 0.0
        print(f"  {path.name}: {changed}/{total} piksel degisti (%{percent:.1f})")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Gorseli palete indirger")
    parser.add_argument("paths", nargs="+", help="PNG dosyasi ya da klasor")
    parser.add_argument("--out", type=Path, default=None,
                        help="tek dosya icin cikti yolu (yoksa uzerine yazar)")
    parser.add_argument("--rapor", action="store_true",
                        help="kac pikselin degistigini yazdir")
    args = parser.parse_args()

    images = iter_images(args.paths)
    if not images:
        print("islenecek gorsel yok")
        return 1
    if args.out and len(images) > 1:
        print("--out yalnizca tek dosyayla kullanilir")
        return 1

    print(f"{len(images)} gorsel · palet {len(palette.COLORS)} renk")
    for image in images:
        quantize_file(image, args.out, report=args.rapor)
    print("tamam")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
