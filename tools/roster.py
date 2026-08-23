"""Dusman kadro sayfasi - 18 bolumun tum dusmanlari tek gorselde.

Uc katmani (`animation.TIERS`) satir satir dizer, her dusmani hem NORMAL
hem SILUET halinde gosterir. Yan yana bakinca iki soru cevaplanir:

  * Ayni katmanin uyeleri birbirinden ayirt ediliyor mu?
  * Farkli katmanlar birbirinden AYRI BIR TUR gibi mi duruyor?

Siluet sutunu `docs/asset-plani.md` 4'un zorunlu testi: sprite tek renge
indirildiginde ne oldugu hala anlasilmali. Silahin/boynuzun/kalkanin
siluetten disari tasmasi tam olarak bunun icin.

Calistir:
    python tools/roster.py
    python tools/roster.py --zoom 8 --durum attack1
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from src.art import palette  # noqa: E402
from src.art.animation import CHARACTERS, TIERS, build_animation  # noqa: E402
from src.ui import text  # noqa: E402

# Katmanin adi + gdd.md 7'deki ogretme sorusu. Sayfanin isi yalnizca
# "guzel mi" degil, "hangi soruyu soruyor" - ikisi birlikte okunmali.
TIER_LABELS: dict[str, tuple[str, str]] = {
    "curuyenler": ("KATMAN 1 - CURUYENLER", "combo kurmayi ogren"),
    "muhafizlar": ("KATMAN 2 - LANETLI MUHAFIZLAR", "combo'yu KIRMAYI ogren"),
    "yanki": ("KATMAN 3 - YANKI'NIN COCUKLARI", "yardimcinin ihaneti"),
}

PAD = 10
LABEL_H = 13
HEADER_H = 22


def silhouette(surface: pygame.Surface) -> pygame.Surface:
    """Sprite'i tek renge indirir - siluet testi.

    Renk **acik** olmali: siluet koyu arka plan uzerine koyu cizilirse
    hicbir sey gorunmez (ilk surumde "ink" kullandim ve serit bombostu -
    tam da testin yakalamasi gereken seyin testin kendisinde olmasi).
    """
    out = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    tone = palette.color("bone")
    width, height = surface.get_size()
    for x in range(width):
        for y in range(height):
            if surface.get_at((x, y)).a > 40:
                out.set_at((x, y), tone)
    return out


def render(zoom: int, state: str, bg: tuple[int, int, int]) -> pygame.Surface:
    rows: list[tuple[str, str, list[tuple[str, pygame.Surface]]]] = []
    for tier, names in TIERS.items():
        title, question = TIER_LABELS[tier]
        entries = [(n, build_animation(CHARACTERS[n], state)[0]) for n in names]
        rows.append((title, question, entries))

    # Hucreyi her sprite'in KENDI boyuna gore degil, en buyugune gore
    # olcuyoruz - boyut hiyerarsisi ancak ortak bir zeminde gorulur.
    cell_w = max(s.get_width() for _, _, e in rows for _, s in e) * zoom + PAD
    cell_h = max(s.get_height() for _, _, e in rows for _, s in e) * zoom + 4
    # Her katman iki serit: normal + siluet.
    row_h = HEADER_H + (cell_h + LABEL_H) * 2 + PAD
    cols = max(len(e) for _, _, e in rows)

    width = cell_w * cols + PAD * 2
    height = row_h * len(rows) + PAD
    surface = pygame.Surface((width, height))
    surface.fill(bg)

    y = PAD
    for title, question, entries in rows:
        text.draw(surface, title, PAD, y, color=palette.color("gold"))
        text.draw(surface, question, PAD + 210, y,
                  color=palette.color("stone_light"))
        y += HEADER_H

        for band, transform in (("", None), ("SILUET", silhouette)):
            for i, (name, sprite) in enumerate(entries):
                image = transform(sprite) if transform else sprite
                big = pygame.transform.scale(
                    image, (image.get_width() * zoom, image.get_height() * zoom))
                x = PAD + i * cell_w + (cell_w - big.get_width()) // 2
                # Taban hizali: hucrenin ALTINA otursunlar, yoksa boy
                # farki (kadronun asil bilgisi) gorulmez.
                surface.blit(big, (x, y + cell_h - big.get_height()))
            y += cell_h
            for i, (name, _) in enumerate(entries):
                label = name.upper() + ("  (siluet)" if band else "")
                x = PAD + i * cell_w + (cell_w - text.text_width(label)) // 2
                text.draw(surface, label, x, y,
                          color=palette.color("bone") if not band
                          else palette.color("stone"))
            y += LABEL_H
        y += PAD
    return surface


def main() -> int:
    parser = argparse.ArgumentParser(description="Dusman kadro sayfasi")
    parser.add_argument("--zoom", type=int, default=5)
    parser.add_argument("--durum", default="idle",
                        help="idle, run, attack1, hurt, death ...")
    parser.add_argument("--out", default="build/testshots/kadro.png")
    args = parser.parse_args()

    pygame.init()
    pygame.display.set_mode((64, 64))

    surface = render(args.zoom, args.durum, palette.color("ink"))
    dest = ROOT / args.out
    dest.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(dest))
    print(f"{dest}  {surface.get_size()}  ({args.durum}, {args.zoom}x)")

    total = sum(len(v) for v in TIERS.values())
    print(f"{len(TIERS)} katman, {total} dusman tipi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
