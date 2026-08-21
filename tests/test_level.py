"""Bolum tasarimi dogrulamasi - her platforma cikilabiliyor mu?

Prototipte bir bolumun cikis kapisina ulasilamiyordu ve bu ancak elle
oynayinca fark edildi. Bir odada 50+ basilabilir nokta varsa hepsinin
erisilebilir oldugunu gozle dogrulamak mumkun degil - bu yuzden makine
dogruluyor.

Zarf `tools/measure_jump.py` ile **olculmus** degerlerden geliyor, tahminden
degil. `PLAYER_JUMP_SPEED` degisirse once o arac, sonra `config.py`, sonra
bu test.

Calistir:
    python tests/test_level.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from src.config import (  # noqa: E402
    MAX_JUMP_GAP_TILES, MAX_JUMP_HEIGHT_TILES,
)
from reachability import _known_rooms, standing_spots, validate, Grid  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def main() -> int:
    print(f"ziplama zarfi: {MAX_JUMP_GAP_TILES} tile bosluk, "
          f"{MAX_JUMP_HEIGHT_TILES} tile yukseklik\n")

    rooms = _known_rooms()
    check(bool(rooms), "dogrulanacak oda var", f"{len(rooms)} oda")

    for name, rows, spawn in rooms:
        report = validate(rows, spawn, name)
        check(report.spawn in report.spots,
              f"{name}: dogum noktasi basilabilir", str(spawn))
        check(not report.unreachable, f"{name}: her nokta ulasilabilir",
              (f"{len(report.unreachable)} ulasilamaz nokta, orn. "
               f"{sorted(report.unreachable)[:4]}") if report.unreachable else
              f"{len(report.spots)} nokta")

    # Dogrulayicinin kendisi calisiyor mu? Bilerek bozuk bir oda vermezsek
    # "her sey yolunda" demesi hicbir sey kanitlamaz.
    print("\n--- dogrulayici gercekten yakaliyor mu ---")
    broken = [
        "##########",
        "##......##",
        "##......##",
        "##.####.##",     # Erisilemez ada: zeminden 6 tile yukarida
        "##......##",
        "##......##",
        "##......##",
        "##......##",
        "##......##",
        "##########",
    ]
    report = validate(broken, (3, 9), "kasitli bozuk oda")
    check(bool(report.unreachable),
          "erisilemez ada yakalandi",
          f"{len(report.unreachable)} nokta")

    # Ulasilabilir bir oda temiz gecmeli - yoksa arac her seye "bozuk" der.
    fine = [
        "##########",
        "##......##",
        "##......##",
        "##......##",
        "##......##",
        "##.####.##",     # Zeminden 3 tile: zarf icinde
        "##......##",
        "##......##",
        "##########",
    ]
    report = validate(fine, (3, 8), "saglam oda")
    check(not report.unreachable, "zarf icindeki platform temiz geciyor",
          f"{len(report.unreachable)} ulasilamaz")

    # Bosluk kontrolu: oyuncu boyu kadar tavan yoksa orada durulamaz.
    print("\n--- tavan bosluğu ---")
    tight = [
        "##########",
        "##.####.##",     # Platformun hemen ustunde tavan
        "##.####.##",
        "##......##",
        "##########",
    ]
    spots = standing_spots(Grid(tight))
    check(all(spot[1] != 2 for spot in spots),
          "tavanin dibindeki platform basilabilir sayilmiyor",
          str(sorted(spots)))

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Bolum tasarimi ziplama zarfina uyuyor.")
    return 0


raise SystemExit(main())
