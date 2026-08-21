"""Siluet testi - her sprite'i tek renk siyaha cevirip yan yana dizer.

**Test:** Sprite tek renge indirildiginde hala ne oldugu anlasiliyorsa iyi
tasarim. Anlasilmiyorsa yeniden ciz. On saniye suren bu test kaliteyi devasa
artirir (docs/asset-plani.md 4).

Dusman siluetlerinin bir karede taninmasi ozellikle kritik - oyuncu karanlik
bir zindanda tehdidi renkten degil sekilden okur.

Kullanim:
    python tools/silhouette.py assets/sprites/
    python tools/silhouette.py assets/sprites/ --yanyana   # siluet + orijinal
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pygame

# Depo kokunu import yoluna ekle - arac dogrudan calistirilabilsin.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from tools.imagelib import (
    ensure_display, from_arrays, iter_images, load, save, solid_mask, to_arrays,
)

from src.art import palette
from src.ui import text

CELL_PAD = 6
LABEL_HEIGHT = 13
DEFAULT_COLUMNS = 10
DEFAULT_SCALE = 3


def to_silhouette(surface: pygame.Surface,
                  colour_name: str = "ink") -> pygame.Surface:
    """Yuzeyi tek renge indirger, alfayi korur."""
    rgb, alpha = to_arrays(surface)
    solid = solid_mask(alpha)
    flat = np.zeros_like(rgb)
    flat[solid] = np.array(palette.color(colour_name), dtype=np.int16)
    return from_arrays(flat, np.where(solid, 255, 0).astype(np.int16))


def build_sheet(images: list[Path], scale: int = DEFAULT_SCALE,
                columns: int = DEFAULT_COLUMNS,
                side_by_side: bool = False) -> pygame.Surface:
    ensure_display()
    entries = [(path, load(path)) for path in images]
    if not entries:
        raise ValueError("gorsel yok")

    sprite_w = max(s.get_width() for _, s in entries) * scale
    sprite_h = max(s.get_height() for _, s in entries) * scale
    cell_w = sprite_w * (2 if side_by_side else 1) + CELL_PAD * 2
    cell_h = sprite_h + CELL_PAD * 2 + LABEL_HEIGHT
    rows = (len(entries) + columns - 1) // columns

    sheet = pygame.Surface((cell_w * min(columns, len(entries)),
                            cell_h * rows + LABEL_HEIGHT + CELL_PAD))
    # Acik zemin: siyah siluet uzerinde en net okunur.
    sheet.fill(palette.color("stone_light"))
    text.draw(sheet, f"Siluet testi · {len(entries)} asset", CELL_PAD, CELL_PAD,
              color=palette.color("ink"))

    top = LABEL_HEIGHT + CELL_PAD
    for index, (path, surface) in enumerate(entries):
        x = (index % columns) * cell_w + CELL_PAD
        y = top + (index // columns) * cell_h + CELL_PAD

        shadow = to_silhouette(surface)
        sheet.blit(pygame.transform.scale(
            shadow, (surface.get_width() * scale, surface.get_height() * scale)),
            (x, y))
        if side_by_side:
            sheet.blit(pygame.transform.scale(
                surface, (surface.get_width() * scale,
                          surface.get_height() * scale)),
                (x + sprite_w, y))

        text.draw(sheet, path.stem[:cell_w // 6], x,
                  y + sprite_h + CELL_PAD // 2, color=palette.color("ink_soft"))
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser(description="Siluet testi kontak sayfasi")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--out", type=Path,
                        default=Path("build/testshots/silhouette.png"))
    parser.add_argument("--olcek", type=int, default=DEFAULT_SCALE)
    parser.add_argument("--sutun", type=int, default=DEFAULT_COLUMNS)
    parser.add_argument("--yanyana", action="store_true",
                        help="siluetin yaninda orijinali de goster")
    args = parser.parse_args()

    images = iter_images(args.paths)
    if not images:
        print("gorsel bulunamadi")
        return 1

    sheet = build_sheet(images, args.olcek, args.sutun, args.yanyana)
    save(sheet, args.out)
    print(f"{args.out}  ({sheet.get_width()}x{sheet.get_height()}, "
          f"{len(images)} asset)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
