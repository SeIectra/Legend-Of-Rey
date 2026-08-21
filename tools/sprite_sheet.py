"""Karakter animasyonlarini kontak sayfasi olarak basar.

Her uretim turundan sonra calistirilir: tutarsizligi ancak yan yana gorunce
fark edersin (docs/asset-boru-hatti.md 2.5).

Kullanim:
    python tools/sprite_sheet.py
    python tools/sprite_sheet.py --karakter rey --durum idle,run,attack1
    python tools/sprite_sheet.py --olcek 6 --siluet
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pygame

# Depo kokunu import yoluna ekle - arac dogrudan calistirilabilsin.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from tools.imagelib import ensure_display, save

from src.art import palette
from src.art.animation import ANIMATIONS, CHARACTERS, build_animation
from src.art.forge import silhouette
from src.ui import text

PAD = 4
LABEL_WIDTH = 78
LABEL_HEIGHT = 13


def build_sheet(characters: list[str], states: list[str], scale: int,
                as_silhouette: bool) -> pygame.Surface:
    ensure_display()
    rows: list[tuple[str, str, list[pygame.Surface]]] = []
    for name in characters:
        spec = CHARACTERS[name]
        for state in states:
            rows.append((name, state, build_animation(spec, state)))

    cell_w = max(s.get_width() for _, _, f in rows for s in f) * scale
    cell_h = max(s.get_height() for _, _, f in rows for s in f) * scale
    max_frames = max(len(f) for _, _, f in rows)

    width = LABEL_WIDTH + max_frames * (cell_w + PAD) + PAD
    height = PAD + len(rows) * (cell_h + PAD)
    sheet = pygame.Surface((width, height))
    sheet.fill(palette.color("stone_light" if as_silhouette else "abyss_dark"))

    y = PAD
    for name, state, frames in rows:
        label_colour = (palette.color("ink") if as_silhouette
                        else palette.role("ui_text_bright"))
        dim_colour = (palette.color("ink_soft") if as_silhouette
                      else palette.role("ui_text_dim"))
        text.draw(sheet, name, 3, y + 3, color=label_colour)
        text.draw(sheet, state, 3, y + 3 + LABEL_HEIGHT, color=dim_colour)

        x = LABEL_WIDTH
        for frame in frames:
            shown = silhouette(frame, palette.color("ink")) if as_silhouette else frame
            big = pygame.transform.scale(
                shown, (shown.get_width() * scale, shown.get_height() * scale))
            if not as_silhouette:
                pygame.draw.rect(sheet, palette.color("ink"),
                                 (x, y, big.get_width(), big.get_height()))
            sheet.blit(big, (x, y))
            x += big.get_width() + PAD
        y += cell_h + PAD
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser(description="Karakter kontak sayfasi")
    parser.add_argument("--karakter", default=",".join(CHARACTERS))
    parser.add_argument("--durum", default="idle,run,jump,fall,attack1,"
                                           "attack2,attack3,dodge,hurt,death")
    parser.add_argument("--olcek", type=int, default=4)
    parser.add_argument("--siluet", action="store_true",
                        help="siluet testi - hepsini tek renge cevir")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    characters = [c for c in args.karakter.split(",") if c in CHARACTERS]
    states = [s for s in args.durum.split(",") if s in ANIMATIONS]
    if not characters or not states:
        print("gecerli karakter ya da durum yok")
        print(f"karakterler: {', '.join(CHARACTERS)}")
        print(f"durumlar: {', '.join(ANIMATIONS)}")
        return 1

    sheet = build_sheet(characters, states, args.olcek, args.siluet)
    default = ("build/testshots/sprites_siluet.png" if args.siluet
               else "build/testshots/sprites.png")
    out = args.out or Path(default)
    save(sheet, out)
    print(f"{out}  ({sheet.get_width()}x{sheet.get_height()}, "
          f"{len(characters)} karakter x {len(states)} durum)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
