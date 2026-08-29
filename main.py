#!/usr/bin/env python3
"""Legend of Rey (LORE) — Ardeko Studios

Calistirmak icin:
    python main.py

Hata ayiklama tuslari:
    F3   hata ayiklama katmani (FPS, sahne yigini, sahneye ozel bilgi)
    F4   siluet modu - her sey duz kutuya doner, dovus hissi boyle test edilir
    F11  tam ekran
    F12  ekran goruntusu
"""
from __future__ import annotations

import sys
from pathlib import Path

# Depo kokunu import yoluna ekle: oyun her dizinden calistirilabilsin.
sys.path.insert(0, str(Path(__file__).resolve().parent))


SCENES = {
    # Varsayilan akis: intro -> menunun kurulmasi -> menu. Uculu tek bir
    # kesintisiz kamera hareketi (docs/menu-ui.md 0).
    "intro": ("src.scenes.intro", "IntroScene"),
    "menu": ("src.ui.menu", "MainMenuScene"),
    # Acilis prologu - Rey'in Yankisini anlatan kisa film.
    "prolog": ("src.scenes.prologue", "ReyPrologue"),
    "prolog-ardo": ("src.scenes.prologue", "ArdoPrologue"),
    "bolum1": ("src.scenes.chapter01", "Chapter01Scene"),
    "bolum2": ("src.scenes.chapter02", "Chapter02Scene"),
    # Bolum 1 -> 2 gecisi (yariktan dusus). Ayrica dogrudan
    # acilabilsin: ara sahneyi tek basina ayarlamak icin.
    "inis": ("src.scenes.chapter02_cinematics", "DescentCinematic"),
    "bolum3": ("src.scenes.chapter03", "Chapter03Scene"),
    # Bolum 4 - "Kayit Odasi". ★nefes: dovus yok (docs/yapi.md B4).
    "bolum6": ("src.scenes.chapter06", "Chapter06Scene"),
    "bolum5": ("src.scenes.chapter05", "Chapter05Scene"),
    "bolum4": ("src.scenes.chapter04", "Chapter04Scene"),
    "dovus": ("src.scenes.combat_room", "CombatRoomScene"),
    "temel": ("src.scenes.foundation_check", "FoundationCheckScene"),
}
DEFAULT_SCENE = "intro"


def main() -> int:
    import importlib

    name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SCENE
    if name not in SCENES:
        print(f"bilinmeyen sahne: {name}")
        print(f"secenekler: {', '.join(SCENES)}")
        return 1

    from src.core.game import Game

    module_name, class_name = SCENES[name]
    scene_cls = getattr(importlib.import_module(module_name), class_name)

    game = Game()
    game.run(scene_cls)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
