"""Her bolum GERCEKTEN cizilebiliyor mu.

## Neden var

31.08.2026, paketlenen surum tester'a verilmeden once denendi ve
**Bolum 9 acilir acilmaz cokuyordu**:

    AttributeError: 'Companion' object has no attribute 'draw_extra'

Sebep o sabah eklenen bir satirdi: `enemy_render.draw_enemy` artik
`enemy.draw_extra()` cagiriyordu ve `Companion` `Actor`den turuyor,
`Enemy`den degil.

Otuz alti test paketi yesildi. Hicbiri yakalayamadi cunku **hicbiri
bolum cizmiyordu**: bolum testleri oda gecislerini, dusman
davranisini, kayit alanlarini olcuyor ama `scene.draw()`u hic
cagirmiyordu.

Ayni sinif hata ayni gun ikinci kez cikti (`draw_extra` hic
cagrilmiyordu, alti dusmanin `silhouette_scale`i float'la
gölgelenmisti). Ders acik: **davranis yesil olabilir, goruntu cokuk.**

## Ne yapiyor

Her bolumu kuruyor, her odasina/katina ugruyor ve **her karede
ciziyor**. Yavas ama ucuz: paketlenmis surumu tester'a verip
"acilmiyor" cevabini almaktan cok daha ucuz.

Calistir:
    python tests/test_render.py
"""
from __future__ import annotations

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

from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH, TILE_SIZE  # noqa: E402
from src.core.game import Game  # noqa: E402
from src.systems.save import SaveData, write_save  # noqa: E402

failures: list[str] = []

# (sahne adi, modul, sinif, karakter). Ikisi de denenmeli: Rey'de Yanki,
# Ardo'da Iz Surme cizim yolu **ayri**.
CHAPTERS = [
    ("bolum1", "src.scenes.chapter01", "Chapter01Scene"),
    ("bolum2", "src.scenes.chapter02", "Chapter02Scene"),
    ("bolum3", "src.scenes.chapter03", "Chapter03Scene"),
    ("bolum4", "src.scenes.chapter04", "Chapter04Scene"),
    ("bolum5", "src.scenes.chapter05", "Chapter05Scene"),
    ("bolum6", "src.scenes.chapter06", "Chapter06Scene"),
    ("bolum7", "src.scenes.chapter07", "Chapter07Scene"),
    ("bolum8", "src.scenes.chapter08", "Chapter08Scene"),
    ("bolum9", "src.scenes.chapter09", "Chapter09Scene"),
    ("bolum10", "src.scenes.chapter10", "Chapter10Scene"),
    ("bolum11", "src.scenes.chapter11", "Chapter11Scene"),
    ("bolum12", "src.scenes.chapter12", "Chapter12Scene"),
    ("bolum13", "src.scenes.chapter13", "Chapter13Scene"),
    ("bolum14", "src.scenes.chapter14", "Chapter14Scene"),
]

FULL_KIT = ["sword", "dodge", "echo_sight", "echo_ask"]


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def sweep(scene, surface, steps: int = 60) -> None:
    """Bolumu bastan sona tarayip **her adimda ciziyor**.

    Yalnizca dogum noktasinda cizmek yetmiyordu: Bolum 9'un yoldasi
    ilk saniyelerde ekranda degil, ve tam o yuzden hata bir sonraki
    katta cikiyordu. Oyuncu haritanin bir ucundan otekine
    isinlaniyor, arada her sey ciziliyor.
    """
    width = scene.tilemap.width * TILE_SIZE
    height = scene.tilemap.height * TILE_SIZE
    body = scene.player.body
    for step in range(steps):
        t = step / max(1, steps - 1)
        # Yatay bolumlerde x, dikey olanlarda y taranıyor.
        if width >= height:
            body.set_feet(t * (width - TILE_SIZE * 2) + TILE_SIZE,
                          body.feet[1])
        else:
            body.set_feet(body.center_x,
                          t * (height - TILE_SIZE * 3) + TILE_SIZE * 2)
        scene.update()
        scene.draw(surface)


def run_chapter(game, surface, name: str, module: str, cls_name: str,
                character: str) -> None:
    import importlib
    scene_cls = getattr(importlib.import_module(module), cls_name)
    write_save(SaveData(chapter=1, character=character,
                        abilities=list(FULL_KIT)))
    game.scenes.set_root(scene_cls, transition=False, character=character)
    game.scenes._flush()
    scene = game.scenes.current
    sweep(scene, surface)
    check(True, f"{name} ({character}) tarandi ve cizildi")


def test_chapters() -> None:
    print("\n--- bolumler ---")
    game = Game()
    surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
    try:
        for name, module, cls_name in CHAPTERS:
            for character in ("rey", "ardo"):
                try:
                    run_chapter(game, surface, name, module, cls_name,
                                character)
                except Exception as exc:  # noqa: BLE001
                    import traceback
                    check(False, f"{name} ({character}) cizilirken COKTU",
                          f"{type(exc).__name__}: {exc}")
                    traceback.print_exc()
    finally:
        game.quit()


def test_companion_draws() -> None:
    """Yoldas **acikca** ciziliyor - Bolum 9'u cokuten seyin testi.

    Yoldas `Actor`den turuyor ama `enemy_render.draw_enemy` ile
    ciziliyor: iki hiyerarsi tek bir cizicide bulusuyor ve
    sozlesmelerinin ayrisması sessiz bir cokme uretiyor.
    """
    print("\n--- yoldas ---")
    from src.entities.actor import Actor
    from src.entities.companion import Companion
    from src.entities.enemy import Enemy

    check(hasattr(Actor, "draw_extra"),
          "kanca ORTAK atada (Actor) - iki hiyerarsi de aliyor")
    check(hasattr(Companion, "draw_extra"), "Companion kancayi aliyor")
    check(hasattr(Enemy, "draw_extra"), "Enemy kancayi aliyor")

    game = Game()
    surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
    try:
        import importlib
        scene_cls = getattr(importlib.import_module("src.scenes.chapter09"),
                            "Chapter09Scene")
        write_save(SaveData(chapter=9, character="rey",
                            abilities=list(FULL_KIT)))
        game.scenes.set_root(scene_cls, transition=False, character="rey")
        game.scenes._flush()
        scene = game.scenes.current
        check(scene.companion is not None, "Bolum 9'da yoldas var")
        # Yoldasi oyuncunun yanina getirip **gorunur** kil.
        scene.companion.body.set_feet(scene.player.body.center_x + 20,
                                      scene.player.body.feet[1])
        for _ in range(30):
            scene.update()
            scene.draw(surface)
        check(True, "yoldas ekrandayken 30 kare cizildi")
    finally:
        game.quit()


def main() -> int:
    test_companion_draws()
    test_chapters()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("On dort bolumun ikisi de (Rey/Ardo) bastan sona cizilebiliyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
