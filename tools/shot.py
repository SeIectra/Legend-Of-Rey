"""Oyunu basssiz calistirip ekran goruntusu alir.

Gorunur pencere acmadan belirli sayida kare surer ve ic yuzeyi PNG olarak
kaydeder. Degisiklikleri gozle dogrulamanin en hizli yolu - "calisiyor"
demek yerine goruntuyu gostermek icin.

Kullanim:
    python tools/shot.py                       # varsayilan sahne
    python tools/shot.py --frames 120 --out build/testshots/menu.png
    python tools/shot.py --scene src.scenes.foundation_check:FoundationCheckScene
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

DEFAULT_SCENE = "src.scenes.foundation_check:FoundationCheckScene"
DEFAULT_OUT = ROOT / "build" / "testshots" / "shot.png"


def load_scene(spec: str) -> type:
    module_name, _, class_name = spec.partition(":")
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Basssiz ekran goruntusu")
    parser.add_argument("--scene", default=DEFAULT_SCENE,
                        help="modul:Sinif biciminde sahne")
    parser.add_argument("--frames", type=int, default=60,
                        help="goruntuden once surulecek kare sayisi")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--scale", type=int, default=2,
                        help="cikti buyutme kati (tam sayi)")
    args = parser.parse_args()

    from src.core.game import Game

    game = Game()
    scene_cls = load_scene(args.scene)
    game.scenes.set_root(scene_cls, transition=False)

    for _ in range(max(1, args.frames)):
        game.input.begin_frame()
        game.input.end_frame()
        game.scenes.update()
        game.frame += 1

    game.canvas.fill((0, 0, 0, 255))
    game.scenes.draw(game.canvas)

    surface = game.canvas
    if args.scale > 1:
        surface = pygame.transform.scale(
            surface, (surface.get_width() * args.scale,
                      surface.get_height() * args.scale))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(args.out))
    print(f"{args.out}  ({surface.get_width()}x{surface.get_height()}, "
          f"{args.frames} kare)")

    game.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
