#!/usr/bin/env python3
"""LORE - Legend of Rey: Echoes

Baslatmak icin:
    python run.py

Hata ayiklama:
    F3   hata ayiklama katmani (carpisma kutulari, AI durumlari, FPS)
    F11  tam ekran
    F12  ekran goruntusu
"""
from __future__ import annotations

import sys
from pathlib import Path

# Depo kokunu import yoluna ekle: oyun her dizinden calistirilabilsin.
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> int:
    from lore.core.app import App
    from lore.scenes.boot import BootScene

    app = App()
    app.run(BootScene)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
