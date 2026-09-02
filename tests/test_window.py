"""Pencere ve tam ekran olcekleme dogrulamasi.

Tam ekran hatalari elle fark edilmesi zor cinsten: oyun calisir, ekran
dolar, ama pikseller kesirli olcekte titrer. Bu yuzden olcek matematigi
`viewport_for()` icinde saf fonksiyon olarak duruyor ve burada pencere
acmadan sinaniyor.

**Neden `pygame.SCALED` kullanilmiyor:** o bayrakla pygame kendi olceklemesini
yapar ve olcek tam sayi olmak zorunda degildir. 1920x1080 ekranda mantiksal
1440x810 yuzey 1.333x gerilir - piksel art bozulur (CLAUDE.md 4, 12). Ustelik
`screen.get_size()` fiziksel degil mantiksal boyutu doner, yani viewport
hesabi gercek ekrani hic gormez.

Calistir:
    python tests/test_window.py
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from src.config import INTERNAL_HEIGHT, INTERNAL_WIDTH  # noqa: E402
from src.core.game import (  # noqa: E402
    MIN_SCALE, viewport_for, window_origin,
)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


# Gercek dunyada karsilasilacak ekranlar. 1920x1080 onemli: 480x270'in tam
# 4 kati, yani tam ekranda hic bant kalmamali.
SCREENS: tuple[tuple[int, int, str], ...] = (
    (1920, 1080, "1080p - tam 4x, bant yok"),
    (2560, 1440, "1440p"),
    (3840, 2160, "4K"),
    (1366, 768, "yaygin dizustu"),
    (1280, 1024, "5:4 - bant kacinilmaz"),
    (1440, 810, "3x pencere"),
    (800, 600, "kucuk"),
    (400, 200, "ic cozunurlukten kucuk"),
)


def test_window_is_placed() -> None:
    """Pencere **konumu** da hesaplaniyor - `set_mode` tasimiyor.

    Arda 02.09.2026: *"tam ekran pencereli ekran ayari duzgun
    calismiyor."* Sebep: `set_mode` var olan bir pencereyi yalnizca
    yeniden boyutlandiriyor, tasimiyor. Tam ekrana gecince
    2560x1440'lik kenarliksiz pencere eski konumunda (560, 315)
    kaliyordu:

        solda 560, ustte 315 piksel masaustu goruluyor
        sag alt kose ekran DISINDA kaliyor

    Olculdu ve duzeltildi. Bu kontrol tekrar bozulmasin diye.
    """
    print("\n--- pencere konumu ---")
    for width, height, note in SCREENS:
        scale, rect = viewport_for(width, height)

        # Tam ekran: pencere ekranin sol ust kosesinde.
        origin = window_origin((width, height), fullscreen=True)
        check(origin == (0, 0),
              f"{note}: tam ekran ekranin BASINDA", str(origin))

        # Ve goruntu ekranin tam ortasinda kaliyor.
        left = origin[0] + rect.x
        top = origin[1] + rect.y
        # **Ic cozunurlukten kucuk ekran haric.** Orada `MIN_SCALE = 1`
        # en az bir kat zorluyor ve 480x270'lik goruntu ekrani tasiyor -
        # bu bilincli bir denge (hic cizmemektense kirpmak) ve bu
        # duzeltmeden once de boyleydi. 480x270'ten kucuk bir masaustu
        # pratikte yok.
        if width >= INTERNAL_WIDTH and height >= INTERNAL_HEIGHT:
            check(left >= 0 and top >= 0
                  and left + rect.width <= width
                  and top + rect.height <= height,
                  f"{note}: goruntu ekran ICINDE",
                  f"({left},{top}) {rect.width}x{rect.height}")
        check(left * 2 + rect.width == width
              and top * 2 + rect.height == height,
              f"{note}: goruntu ORTALANMIS")


def test_windowed_is_centred() -> None:
    """Pencereli kip ortalaniyor - tam ekrandan cikinca (0,0)'da kalmasin."""
    print("\n--- pencereli kip ortalaniyor ---")
    from src.core.game import desktop_size
    screen_w, screen_h = desktop_size()
    for scale in (2, 3, 4):
        size = (INTERNAL_WIDTH * scale, INTERNAL_HEIGHT * scale)
        if size[0] > screen_w or size[1] > screen_h:
            continue
        origin = window_origin(size, fullscreen=False)
        check(origin[0] * 2 + size[0] in (screen_w, screen_w - 1),
              f"{scale}x pencere yatayda ortali", str(origin))
        check(origin[1] * 2 + size[1] in (screen_h, screen_h - 1),
              f"{scale}x pencere dikeyde ortali", str(origin))
    big = (INTERNAL_WIDTH * 99, INTERNAL_HEIGHT * 99)
    check(window_origin(big, fullscreen=False) == (0, 0),
          "ekrandan buyuk pencere negatif konuma KACMIYOR")


def main() -> int:
    print(f"ic cozunurluk {INTERNAL_WIDTH}x{INTERNAL_HEIGHT}\n")
    print("--- olcek daima tam sayi, viewport ekrani asmiyor ---")
    for width, height, note in SCREENS:
        scale, rect = viewport_for(width, height)

        integer = (rect.width == INTERNAL_WIDTH * scale
                   and rect.height == INTERNAL_HEIGHT * scale)
        check(integer, f"{width}x{height}: tam sayi olcek", f"{scale}x  {note}")

        check(scale >= MIN_SCALE, f"{width}x{height}: olcek en az {MIN_SCALE}",
              str(scale))

        # Ic cozunurlukten kucuk ekranlarda tasma kabul (MIN_SCALE korumasi),
        # ama sigan her ekranda viewport ekranin icinde kalmali.
        if width >= INTERNAL_WIDTH and height >= INTERNAL_HEIGHT:
            fits = (rect.width <= width and rect.height <= height
                    and rect.x >= 0 and rect.y >= 0)
            check(fits, f"{width}x{height}: viewport ekrana siğiyor",
                  f"{rect.width}x{rect.height} @ {rect.x},{rect.y}")

            # Ortalanmis: iki yandaki bant esit (tek piksel fark kabul).
            margin_x = width - rect.width
            margin_y = height - rect.height
            centred = (abs(rect.x - margin_x // 2) <= 1
                       and abs(rect.y - margin_y // 2) <= 1)
            check(centred, f"{width}x{height}: ortalanmis",
                  f"bant {margin_x}x{margin_y}")

    print("\n--- 1080p tam ekran: bant birakmamali ---")
    scale, rect = viewport_for(1920, 1080)
    check(scale == 4, "1080p olcek 4x", str(scale))
    check(rect.size == (1920, 1080), "1080p'de viewport tam ekran",
          f"{rect.width}x{rect.height}")
    check(rect.topleft == (0, 0), "1080p'de bant yok", str(rect.topleft))

    print("\n--- olcek monoton: buyuk ekran kucuk olcek vermez ---")
    previous = 0
    for width in (480, 960, 1440, 1920, 2400, 2880, 3840):
        scale, _ = viewport_for(width, width * INTERNAL_HEIGHT // INTERNAL_WIDTH)
        check(scale >= previous, f"{width}px genislikte olcek dusmedi",
              f"{previous} -> {scale}")
        previous = scale

    print("\n--- SCALED bayragi kullanilmiyor ---")
    # Bayrak geri gelirse tam ekran sessizce kesirli olceklemeye doner.
    # Metin araması yapmiyoruz: bu dosyanin ve game.py'nin **aciklamalari**
    # bayragin adini gecirdigi icin duz arama kendi yorumumuzu yakaliyordu.
    # AST gercek kod kullanimina bakar, duzyazi onu ilgilendirmez.
    source = (ROOT / "src" / "core" / "game.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    used = [node.lineno for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr == "SCALED"]
    check(not used, "game.py pygame.SCALED kullanmiyor",
          "satir " + ", ".join(str(n) for n in used[:3]))

    test_window_is_placed()
    test_windowed_is_centred()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Pencere olceklemesi her ekranda tam sayi.")
    return 0


# `pygame.init()` DEGIL. O, joystick alt sistemini de acar ve bu
# makinede 40 SANIYE surer (olculdu 30.08.2026 - bir surucu sorunu,
# kodla ilgisi yok). 21 test paketi bunu ayri ayri odedigi icin butun
# paket 14 dakikayi asiyordu.
#
# `src/core/game.py` de tam olarak bu yolu izliyor; test oyunla ayni
# sekilde acilsin. Ses gerekirse `synth.init_mixer()` cagrilir.
pygame.display.init()
pygame.font.init()
raise SystemExit(main())
