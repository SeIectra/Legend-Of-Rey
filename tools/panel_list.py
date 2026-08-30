"""Sinematik panellerinin tam listesi - hangi dosya adi nereye ait.

Elle cizilmis (ya da AI ile uretilmis) bir panel `assets/panels/`
altina **tam dogru adla** konmali; ad yanlissa sessizce yok sayilir ve
prosedurel arka plan cizilir. Sessiz basarisizlik bu projede uc kez
pahaliya patladi (dil anahtarlari, ses adlari, `draw_extra`), o yuzden
listeyi tahmin etmek yerine koddan uretiyoruz.

Kullanim:

    python tools/panel_list.py              # hepsi
    python tools/panel_list.py --eksik      # yalnizca dosyasi OLMAYANLAR
    python tools/panel_list.py --bolum 14
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.scenes.staging import PANEL_DIR, StagedScene, panel_prefix  # noqa: E402


def collect() -> list[tuple[str, str, str, bool]]:
    """(bolum, dosya_adi, sahne_sinifi, yakin_cekim_mi)."""
    rows: list[tuple[str, str, str, bool]] = []
    for path in sorted((ROOT / "src" / "scenes").glob("*_cinematics.py")):
        module = importlib.import_module(f"src.scenes.{path.stem}")
        for name, obj in vars(module).items():
            if not inspect.isclass(obj) or name.startswith("_"):
                continue
            if not issubclass(obj, StagedScene) or obj is StagedScene:
                continue
            # Yalnizca **bu modulde tanimlananlar** - import edilmis
            # sinifi ikinci kez saymak listeyi sisirirdi.
            if obj.__module__ != module.__name__:
                continue
            chapter = path.stem.replace("_cinematics", "")
            for panel in getattr(obj, "PANELS", ()):
                rows.append((chapter,
                             f"{panel_prefix(obj)}_{panel.name}.png",
                             name, bool(panel.closeup)))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eksik", action="store_true",
                        help="yalnizca dosyasi olmayanlari yaz")
    parser.add_argument("--bolum", help="orn. 14")
    args = parser.parse_args()

    rows = collect()
    if args.bolum:
        rows = [r for r in rows if args.bolum in r[0]]

    shown = 0
    current = ""
    for chapter, filename, scene, closeup in rows:
        exists = (PANEL_DIR / filename).exists()
        if args.eksik and exists:
            continue
        if chapter != current:
            current = chapter
            print(f"\n--- {chapter} ---")
        mark = "VAR " if exists else "    "
        note = "  (yakin cekim - PORTRE kullaniyor, panel gerekmez)" \
            if closeup else ""
        print(f"  {mark}assets/panels/{filename}{note}")
        shown += 1

    backgrounds = [r for r in rows if not r[3]]
    have = sum(1 for r in backgrounds if (PANEL_DIR / r[1]).exists())
    print(f"\n{shown} satir yazildi.")
    print(f"Arka plan paneli: {have}/{len(backgrounds)} hazir.")
    print(f"Yakin cekim: {len(rows) - len(backgrounds)} "
          f"(bunlar `assets/portraits/` kullaniyor).")
    print(f"\nUretim yolu: python tools/import_art.py <dosya> "
          f"--tur panel --ad <ad_uzantisiz>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
