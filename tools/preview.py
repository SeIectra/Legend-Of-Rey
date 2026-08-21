"""Kontak sayfasi - tum asset'leri yan yana dizer.

**Boru hattinin en kullanisli araci.** Tutarsizligi ancak yan yana gorunce
fark edersin: biri fazla parlak, biri farkli konturlu, biri baska oranda.
Her uretim turundan sonra bu sayfayi ac ve bak.

Kullanim:
    python tools/preview.py assets/sprites/
    python tools/preview.py assets/sprites/ --olcek 4 --sutun 8
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pygame

# Depo kokunu import yoluna ekle - arac dogrudan calistirilabilsin.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from tools.imagelib import ensure_display, iter_images, load, save

from src.art import palette
from src.ui import text

CELL_PAD = 6
LABEL_HEIGHT = 13
DEFAULT_COLUMNS = 10
DEFAULT_SCALE = 3


def build_sheet(images: list[Path], scale: int = DEFAULT_SCALE,
                columns: int = DEFAULT_COLUMNS,
                background: str = "abyss_dark") -> pygame.Surface:
    ensure_display()
    surfaces = [(path, load(path)) for path in images]
    if not surfaces:
        raise ValueError("gorsel yok")

    cell_w = max(s.get_width() for _, s in surfaces) * scale + CELL_PAD * 2
    cell_h = (max(s.get_height() for _, s in surfaces) * scale
              + CELL_PAD * 2 + LABEL_HEIGHT)
    rows = (len(surfaces) + columns - 1) // columns

    sheet = pygame.Surface((cell_w * min(columns, len(surfaces)),
                            cell_h * rows + LABEL_HEIGHT + CELL_PAD))
    sheet.fill(palette.color(background))

    text.draw(sheet, f"{len(surfaces)} asset · palet {len(palette.COLORS)} renk",
              CELL_PAD, CELL_PAD, color=palette.role("ui_text_bright"))

    top = LABEL_HEIGHT + CELL_PAD
    for index, (path, surface) in enumerate(surfaces):
        column = index % columns
        row = index // columns
        x = column * cell_w
        y = top + row * cell_h

        # Dama zemin: saydam bolgeler ve acik pikseller ayirt edilsin.
        _draw_checker(sheet, pygame.Rect(x + CELL_PAD, y + CELL_PAD,
                                         surface.get_width() * scale,
                                         surface.get_height() * scale))
        scaled = pygame.transform.scale(
            surface, (surface.get_width() * scale, surface.get_height() * scale))
        sheet.blit(scaled, (x + CELL_PAD, y + CELL_PAD))

        label = path.stem[:cell_w // 6]
        text.draw(sheet, label, x + CELL_PAD, y + cell_h - LABEL_HEIGHT,
                  color=palette.role("ui_text_dim"))
    return sheet


def _draw_checker(sheet: pygame.Surface, rect: pygame.Rect,
                  square: int = 6) -> None:
    light = palette.color("stone_darkest")
    dark = palette.color("ink_soft")
    for y in range(rect.top, rect.bottom, square):
        for x in range(rect.left, rect.right, square):
            shade = light if ((x // square) + (y // square)) % 2 else dark
            cell = pygame.Rect(x, y, square, square).clip(rect)
            if cell.width and cell.height:
                sheet.fill(shade, cell)


def main() -> int:
    parser = argparse.ArgumentParser(description="Asset kontak sayfasi")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--out", type=Path,
                        default=Path("build/testshots/preview.png"))
    parser.add_argument("--olcek", type=int, default=DEFAULT_SCALE)
    parser.add_argument("--sutun", type=int, default=DEFAULT_COLUMNS)
    args = parser.parse_args()

    images = iter_images(args.paths)
    if not images:
        print("gorsel bulunamadi")
        return 1

    sheet = build_sheet(images, args.olcek, args.sutun)
    save(sheet, args.out)
    print(f"{args.out}  ({sheet.get_width()}x{sheet.get_height()}, "
          f"{len(images)} asset)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
