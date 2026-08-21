"""Faz 0 dogrulama testleri.

Calistir:
    python tests/test_foundation.py

Uc sey kanitlanir:
  1. Palet tam olarak 32 renk ve kontur en koyu 2. renk
  2. Turkce'nin tamami fontta var
  3. tr_upper/tr_lower Python'un yanlis yaptigi yerlerde dogru
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame  # noqa: E402

from src.art import palette  # noqa: E402
from src.config import FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    mark = "OK " if condition else "!! "
    print(f"{mark}{label}" + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


# --- 1. Palet ---------------------------------------------------------------
print("--- palet ---")
check(len(palette.COLORS) == 32, "palet 32 renk", f"{len(palette.COLORS)}")

darkest = palette.darkest_names(2)
check(palette.OUTLINE_NAME == darkest[1],
      "kontur = en koyu 2. renk",
      f"kontur={palette.OUTLINE_NAME}, en koyu ikili={darkest}")
check(palette.outline() != (0, 0, 0), "kontur siyah degil",
      str(palette.outline()))

# Her rampa ve rol gercek renklere isaret etmeli.
for ramp_name in palette.RAMPS:
    for step_name in palette.ramp(ramp_name):
        if step_name not in palette.COLORS:
            failures.append(f"rampa {ramp_name} -> bilinmeyen renk {step_name}")
for role_name, colour_name in palette.ROLES.items():
    if colour_name not in palette.COLORS:
        failures.append(f"rol {role_name} -> bilinmeyen renk {colour_name}")
check(not any(f.startswith(("rampa", "rol")) for f in failures),
      "tum rampa ve roller palet icinde")

# Parcacik yollari - derinlestirme.md 1.3
for path_name in palette.PARTICLE_PATHS:
    palette.particle_path(path_name)
check(len(palette.PARTICLE_PATHS) >= 4, "parcacik renk yollari tanimli",
      f"{len(palette.PARTICLE_PATHS)} yol")

# Yol basi parlak, sonu koyu olmali
blood_start = palette.path_color("blood", 1.0)
blood_end = palette.path_color("blood", 0.0)
check(palette.luminance(blood_start) > palette.luminance(blood_end),
      "parcacik yolu parlaktan koyuya gidiyor")

check(palette.nearest_name((250, 250, 250)) in ("white_flash", "bone"),
      "quantize en yakin rengi buluyor",
      palette.nearest_name((250, 250, 250)))

# Golge zincirleri **monoton parlaklasmali**: 0 en koyu golge, son basamak en
# parlak isik. Ters donen bir zincir isiklandirmayi tersine cevirir ve sprite
# hatali degil, sadece "yanlis" gorunur - goz bunu kolay kolay yakalamaz.
# hair_dark bir kez bu hataya dustu, bu yuzden test var.
for chain_name in palette.SHADE_CHAINS:
    steps = palette.chain(chain_name)
    lums = [palette.luminance(palette.color(n)) for n in steps]
    rising = all(b > a for a, b in zip(lums, lums[1:]))
    check(rising, f"zincir monoton parlaklasiyor: {chain_name}",
          " -> ".join(f"{n}({l:.2f})" for n, l in zip(steps, lums)))

# Basamaklar birbirine cok yakinsa tonlama duz gorunur - golge okunmaz.
# 0.03 parlaklik ~ 8-bit'te 8 seviye: 480x270'te ayri ton olarak okunmanin
# alt siniri. Mevcut zincirlerin en dari 0.038 (shadow ve hair_dark).
MIN_STEP_GAP = 0.03
for chain_name in palette.SHADE_CHAINS:
    steps = palette.chain(chain_name)
    lums = [palette.luminance(palette.color(n)) for n in steps]
    gaps = [b - a for a, b in zip(lums, lums[1:])]
    check(min(gaps) >= MIN_STEP_GAP,
          f"zincir basamaklari ayirt edilebilir: {chain_name}",
          f"en dar aralik {min(gaps):.3f}")

# --- 2. Font ----------------------------------------------------------------
print("\n--- font ---")
pygame.init()
pygame.display.set_mode((64, 64))
from src.ui import text  # noqa: E402

TURKISH = "ğĞüÜşŞıIiİöÖçÇ"
font = text.font()
missing = [c for c in TURKISH if not font.has(text.nfc(c))]
check(not missing, "Turkce glifler tam", f"eksik: {missing or 'yok'}")

ascii_missing = [c for c in
                 "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
                 if not font.has(c)]
check(not ascii_missing, "ASCII glifler tam", f"eksik: {ascii_missing or 'yok'}")

surface = font.render("Ağır kılıç", palette.color("bone"))
check(surface.get_width() > 0 and surface.get_height() > 0,
      "metin yuzeye ciziliyor", f"{surface.get_size()}")

# --- 3. Turkce buyuk/kucuk harf ---------------------------------------------
print("\n--- tr_upper / tr_lower ---")
UPPER_CASES = [("ışık", "IŞIK"), ("İstanbul", "İSTANBUL"), ("Iğdır", "IĞDIR"),
               ("çilek", "ÇİLEK"), ("gemi", "GEMİ")]
for source, expected in UPPER_CASES:
    produced = text.tr_upper(source)
    check(produced == expected, f"tr_upper({source!r})",
          f"{produced!r} beklenen {expected!r}")

LOWER_CASES = [("IŞIK", "ışık"), ("İSTANBUL", "istanbul"), ("GEMİ", "gemi")]
for source, expected in LOWER_CASES:
    produced = text.tr_lower(source)
    check(produced == expected, f"tr_lower({source!r})",
          f"{produced!r} beklenen {expected!r}")

# Python'un yanlis yaptigini gostererek farkin gercek oldugunu kanitla.
check("ışık".upper() != "IŞIK" or "IŞIK".lower() != "ışık",
      "Python'un str.upper/lower'i Turkce'de gercekten yanlis",
      f"upper={'ışık'.upper()!r} lower={'IŞIK'.lower()!r}")

# --- 4. Yapilandirma --------------------------------------------------------
print("\n--- yapilandirma ---")
check(FPS == 60, "sabit 60 kare")
check((INTERNAL_WIDTH, INTERNAL_HEIGHT) == (480, 270), "ic cozunurluk 480x270")

from src.config import CHAIN, CHAIN_WINDOW_FRAMES, DODGE_IFRAMES  # noqa: E402

check(len(CHAIN) == 3, "3'lu zincir tanimli")
check([h.windup for h in CHAIN] == [4, 5, 8], "zincir windup kareleri",
      str([h.windup for h in CHAIN]))
check([h.active for h in CHAIN] == [3, 3, 5], "zincir aktif kareleri")
check([h.recovery for h in CHAIN] == [8, 9, 16], "zincir recovery kareleri")
check([h.damage for h in CHAIN] == [10, 12, 25], "zincir hasarlari")
check(CHAIN[2].cancelable is False, "bitirici iptal edilemez")
check(CHAIN_WINDOW_FRAMES == 12, "zincir penceresi 12 kare")
check(DODGE_IFRAMES == 6, "kacinma 6 kare dokunulmazlik")

# --- Sonuc ------------------------------------------------------------------
print("\n=== SONUC ===")
if failures:
    print(f"{len(failures)} BASARISIZ:")
    for item in failures:
        print(f"  - {item}")
    sys.exit(1)
print("Faz 0 temeli dogrulandi.")
