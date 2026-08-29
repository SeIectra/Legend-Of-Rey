"""Ekran ayari degisimi - onbellekler bayat kalmiyor mu.

Arda, canli oynanis (29.08.2026): *"Oyunun tam ekran / pencereli ayarini
degistirdiginde oyun donuyor."*

Iki ayri sebep vardi:

  1. **Bayat yuzey bicimi.** Bu projede uretilen her yuzey `convert()`
     goruyor (`CLAUDE.md` 4) ve donusum O ANKI ekranin piksel bicimine
     gore yapiliyor. `set_mode` ekrani yeniden kurunca onbellekteki her
     sprite/karo/portre/vinyet yanlis bicimde kaliyor; pygame bunu hata
     olarak bildirmiyor, sessizce her blit'te tek tek donusturuyor.
     Karede yuzlerce blit -> "donma".
  2. **Ozel (exclusive) tam ekran.** `pygame.FULLSCREEN` gercek bir ekran
     modu degisimi yapiyor ve Windows'ta surucuye gore kilitlenebiliyor.
     Yerine masaustu boyutunda kenarliksiz pencere kullaniliyor.

Bu testin asil isi **birinciyi kalici kilmak**: yeni bir onbellek
eklendiginde `src/art/caches.py`'ye eklenmezse test kirilsin. Guvence
bir yorumda degil, burada.

Calistir:
    python tests/test_display.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((64, 64))

from src.art import caches  # noqa: E402
from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH  # noqa: E402
from src.core.game import viewport_for  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def main() -> int:
    # --- 1. Her onbellek listede mi -----------------------------------------
    # `caches.invalidate_all()` elle tutulan bir liste. Kaynagi tarayip
    # onbellek tanimlayan her modulun orada gectigini dogruluyoruz -
    # boylece yeni bir onbellek eklenip unutulursa test kiriliyor.
    print("--- her onbellek tek listede ---")
    source = (ROOT / "src" / "art" / "caches.py").read_text(encoding="utf-8")

    # Onbellek isareti: modul seviyesinde `clear_cache` tanimlayan dosya.
    owners = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        if path.name == "caches.py":
            continue
        body = path.read_text(encoding="utf-8")
        if re.search(r"^def clear_cache\(", body, re.M):
            owners.append(path.stem)

    check(bool(owners), "onbellek tanimlayan modul bulundu", str(owners))
    missing = [name for name in owners if name not in source]
    check(not missing,
          "clear_cache tanimlayan her modul caches.py'de geciyor",
          f"eksik: {missing}" if missing else "")

    # --- 2. Temizlik gercekten calisiyor ------------------------------------
    print("\n--- temizlik calisiyor ---")
    from src.art import animator, portrait, postfx, tileset
    from src.ui import echo_view, text

    # Onbellekleri doldur.
    a = animator.Animator("rey")
    a.play("idle")
    a.update()
    portrait.portrait("rey")
    text.font().render("LORE", (255, 255, 255))
    filled = [
        ("animator", animator._cache if hasattr(animator, "_cache") else None),
        ("portrait", portrait._cache),
        ("text", text.font()._cache),
        ("echo_view", echo_view._vignette_cache),
    ]
    any_filled = any(c for _, c in filled if c is not None and len(c) > 0)
    check(any_filled, "onbellekler doldu", str([(n, len(c)) for n, c in filled
                                                if c is not None]))

    caches.invalidate_all()
    still = [(n, len(c)) for n, c in filled if c is not None and len(c) > 0]
    check(not still, "invalidate_all hepsini bosaltti", str(still))

    # --- 3. Ekran ayari degisince temizlik CAGRILIYOR -----------------------
    # Asil hata buydu: `_create_window` onbellege hic dokunmuyordu.
    print("\n--- ayar degisimi temizligi tetikliyor ---")
    from src.core.game import Game
    game = Game()
    portrait.portrait("rey")
    check(len(portrait._cache) > 0, "portre onbellegi dolu")
    game.settings.set("fullscreen", not game.settings.get("fullscreen", False))
    check(len(portrait._cache) == 0,
          "tam ekran ayari degisince onbellek BOSALDI",
          f"{len(portrait._cache)} kalinti")
    game.settings.set("fullscreen", False)

    # --- 4. Tam ekran ozel kip DEGIL ----------------------------------------
    # `pygame.FULLSCREEN` gercek bir ekran modu degisimi yapiyor ve
    # Windows'ta kilitlenebiliyor. Kenarliksiz pencere ayni gorunuyu
    # veriyor, mod degisimi yok.
    print("\n--- tam ekran kenarliksiz pencere ---")
    game_source = (ROOT / "src" / "core" / "game.py").read_text(
        encoding="utf-8")
    window_body = game_source.split("def _create_window")[1].split(
        "def _recompute_viewport")[0]
    check("flags = pygame.NOFRAME" in window_body,
          "kenarliksiz pencere kullaniliyor")
    # **Atamaya** bakiyoruz, metne degil: fonksiyonun aciklamasi zaten
    # `pygame.FULLSCREEN`'den neden kacinildigini anlatiyor ve ilk surum
    # kendi yorumunu hata sanip kirmisti.
    check("flags = pygame.FULLSCREEN" not in window_body,
          "ozel (exclusive) tam ekran kipi KULLANILMIYOR")

    # --- 4b. Tekrarli gecis pencereyi KUCULTMUYOR ---------------------------
    # `pygame.display.Info()` bir pencere acildiktan sonra masaustunu degil
    # O ANKI KIPI doner. Olcek ondan hesaplaninca her gecis pencereyi bir
    # kat kuculuyordu: 1920 -> 1440 -> 960 -> ... Arda bunu canli
    # oynanista buldu; arayuz pencereden buyuk cizilip kirpiliyordu.
    print("\n--- tekrarli gecis pencereyi kucultmuyor ---")
    from src.core.game import desktop_size
    check(desktop_size()[0] > 0, "masaustu boyutu okunuyor",
          str(desktop_size()))

    game.settings.set("fullscreen", False)
    first = game.screen.get_size()
    for _ in range(4):
        game.settings.set("fullscreen", True)
        game.settings.set("fullscreen", False)
    check(game.screen.get_size() == first,
          "dort tur gidip gelince pencere AYNI boyutta",
          f"{first} -> {game.screen.get_size()}")

    # Gorunum her zaman pencerenin icinde kalmali. Disina tastigi anda
    # her karede pencereden buyuk bir yuzey olcekleniyor - ekran kirpilir
    # ve oyun "donar" (ses devam ettigi icin tam olarak oyle gorunur).
    width, height = game.screen.get_size()
    check(game.viewport.width <= width and game.viewport.height <= height,
          "gorunum pencereye SIGIYOR",
          f"{game.viewport.size} <= {(width, height)}")

    # --- 4c. vsync yalnizca ilk pencerede -----------------------------------
    # Tekrarli `set_mode(..., vsync=1)` pygame-ce 2.5.8'de SEGFAULT
    # veriyor (saf pygame ile de ureniyor). Yakalanabilir bir hata degil,
    # o yuzden tek korunma istememek.
    print("\n--- vsync yalnizca ilk pencerede ---")
    window_body2 = (ROOT / "src" / "core" / "game.py").read_text(
        encoding="utf-8").split("def _create_window")[1].split(
        "def _recompute_viewport")[0]
    check("first_window" in window_body2,
          "vsync yalnizca ilk pencerede isteniyor")

    # --- 5. Olcek matematigi bozulmadi --------------------------------------
    # Tam ekran artik masaustu boyutunda bir pencere; olcek hesabi ayni
    # yoldan geciyor ve **daima tam sayi** olmali (piksel art titremesin).
    print("\n--- olcek daima tam sayi ---")
    for width, height in ((1920, 1080), (2560, 1440), (1366, 768),
                          (3840, 2160), (1280, 720)):
        scale, view = viewport_for(width, height)
        check(scale == int(scale) and scale >= 1,
              f"{width}x{height} -> tam sayi olcek",
              f"{scale}x")
        check(view.width == INTERNAL_WIDTH * scale
              and view.height == INTERNAL_HEIGHT * scale,
              f"{width}x{height} -> gorunum tam katinda",
              f"{view.width}x{view.height}")
        check(view.x >= 0 and view.y >= 0,
              f"{width}x{height} -> gorunum ekranin icinde")

    game.shutdown()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Ekran ayari degisimi onbellek birakmiyor, tam ekran mod "
          "degistirmiyor.")
    return 0


raise SystemExit(main())
