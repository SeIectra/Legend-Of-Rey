"""palette.json -> GIMP/Aseprite palet dosyasi (.gpl).

`tools/palette.json` **tek gercek kaynak** olmaya devam eder. Aseprite paleti
elle yazilmaz, buradan uretilir. Palet degisirse bu script tekrar calistirilir
ve iki taraf ayni renkleri gorur.

Kullanim:
    python tools/palette_to_gpl.py
    python tools/palette_to_gpl.py --out assets/source/lore.gpl
"""
from __future__ import annotations

import argparse
from pathlib import Path

# Depo kokunu import yoluna ekle - arac dogrudan calistirilabilsin.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from src.art import palette

DEFAULT_OUT = Path("assets/source/lore.gpl")


def build_gpl() -> str:
    lines = [
        "GIMP Palette",
        "Name: LORE",
        "Columns: 8",
        "# Legend of Rey - 32 renk ana palet",
        "# KAYNAK: tools/palette.json - bu dosyayi elle duzenleme,",
        "# python tools/palette_to_gpl.py ile yeniden uret.",
        "#",
    ]
    for name in palette.ORDERED_NAMES:
        r, g, b = palette.color(name)
        lines.append(f"{r:3d} {g:3d} {b:3d}\t{name}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Paletten .gpl uretir")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_gpl(), encoding="utf-8")
    print(f"{args.out}  ({len(palette.COLORS)} renk)")
    print("Aseprite: Palette > Load Palette > bu dosyayi sec")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
