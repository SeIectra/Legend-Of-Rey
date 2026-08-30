"""Portreler - Arda'nin yuz sartnamesi gercekten karsilaniyor mu.

Arda (29.08.2026), oncelik sirasiyla: yuz ve kafa, vucut oranlari, siluet,
sac, gozler, isik/golge, kiyafet.

    "Gozleri sadece iki piksel nokta olarak birakma. Gozlerde goz kapagi,
    iris/pupil hissi ve kucuk highlight kullan. Kaslar gozlerle uyumlu
    olsun. Burun icin kucuk ama gercekci bir pixel cluster kullan. Agiz
    tek bir yatay cizgi gibi gorunmesin. Saci tek renk buyuk bir blok
    halinde cizme. Rey icin daha acik, zarif ve canli gozler; Ardo icin
    daha dar, ciddi ve golgeli."

Bunlarin cogu **sayilabilir**: kac ton kullanildigi, gozde kac katman
oldugu, iki karakterin ayni olcude farkli olup olmadigi. Test bunlari
olcuyor - "guzel mi" sorusunu degil (o goze bakar,
`build/testshots/portreler.png`), "istenen yapi KURULMUS mu" sorusunu.

Calistir:
    python tests/test_portrait.py
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

# `pygame.init()` DEGIL. O, joystick alt sistemini de acar ve bu
# makinede 40 SANIYE surer (olculdu 30.08.2026 - bir surucu sorunu,
# kodla ilgisi yok). 21 test paketi bunu ayri ayri odedigi icin butun
# paket 14 dakikayi asiyordu.
#
# `src/core/game.py` de tam olarak bu yolu izliyor; test oyunla ayni
# sekilde acilsin. Ses gerekirse `synth.init_mixer()` cagrilir.
pygame.display.init()
pygame.font.init()
pygame.display.set_mode((64, 64))

from src.art import portrait as pt  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def tones(surface: pygame.Surface, rect: pygame.Rect) -> Counter:
    """Bir bolgedeki gorunur renklerin sayimi."""
    counts: Counter = Counter()
    for y in range(rect.top, rect.bottom):
        for x in range(rect.left, rect.right):
            r, g, b, a = surface.get_at((x, y))
            if a > 0:
                counts[(r, g, b)] += 1
    return counts


def main() -> int:
    print("--- uc portre de uretiliyor ---")
    for name in ("rey", "ardo", "cemo"):
        surface = pt.portrait(name)
        check(surface is not None, f"{name} portresi var")
        if surface is None:
            continue
        check(surface.get_size() == (pt.WIDTH, pt.HEIGHT),
              f"{name} 64x96", str(surface.get_size()))

    rey = pt.portrait("rey")
    ardo = pt.portrait("ardo")

    # --- 1. Yuz semasi ------------------------------------------------------
    # Klasik cizim semasi: goz cizgisi kafanin dikey ORTASINDA. Ilk surumde
    # kafa 29x46 (oran 0.63) ve gozler semanin disindaydi - "uzun surat"
    # gibi okunuyordu.
    print("\n--- yuz semasi ---")
    middle = (pt.CROWN + pt.CHIN) / 2
    check(abs(pt.EYE - middle) <= 1.0,
          "goz cizgisi kafanin dikey ortasinda",
          f"goz {pt.EYE}, orta {middle:.1f}")
    head_h = pt.CHIN - pt.CROWN
    ratio = pt.REY_PORTRAIT.skull_width / head_h
    check(0.66 <= ratio <= 0.80,
          "kafa genislik/yukseklik orani semada (~0.72)",
          f"{ratio:.2f}")
    check(pt.MOUTH - pt.NOSE_BASE < pt.CHIN - pt.MOUTH,
          "agiz burun tabani ile cene arasinin UST kisminda")

    # --- 2. Goz: bes katman -------------------------------------------------
    # "Iki piksel nokta" olmadigini kanitlamanin olculebilir yolu: goz
    # bolgesinde kac AYRI ton var. Kapak + sklera + iris + pupil +
    # highlight = en az bes.
    print("\n--- goz: iki piksel nokta DEGIL ---")
    for name, surface in (("rey", rey), ("ardo", ardo)):
        spec = pt.PORTRAITS[name]
        box = pygame.Rect(int(pt.FACE_CX) - 16, pt.EYE - 3, 32, 8)
        found = tones(surface, box)
        check(len(found) >= 5,
              f"{name} goz bolgesinde en az bes ton var",
              f"{len(found)} ton")

    # --- 3. Kaslar gozlerle uyumlu ve ZIT ----------------------------------
    print("\n--- kas: Rey acik, Ardo catik ---")
    check(pt.REY_PORTRAIT.brow_angle > 0 > pt.ARDO_PORTRAIT.brow_angle,
          "kas egimleri zit isaretli",
          f"rey {pt.REY_PORTRAIT.brow_angle:+d} / "
          f"ardo {pt.ARDO_PORTRAIT.brow_angle:+d}")
    check(pt.ARDO_PORTRAIT.brow_thickness > pt.REY_PORTRAIT.brow_thickness,
          "Ardo'nun kasi daha kalin")
    check(pt.ARDO_PORTRAIT.lid_weight > pt.REY_PORTRAIT.lid_weight,
          "Ardo'nun kapagi daha agir - 'dar, ciddi, golgeli'")
    check(pt.REY_PORTRAIT.eye_height > pt.ARDO_PORTRAIT.eye_height,
          "Rey'in gozu daha acik - 'acik, zarif, canli'")

    # --- 4. Sac tek renk blok DEGIL ----------------------------------------
    print("\n--- sac: tek renk blok degil ---")
    for name, surface in (("rey", rey), ("ardo", ardo)):
        spec = pt.PORTRAITS[name]
        top = pt.CROWN - spec.hair_volume
        box = pygame.Rect(int(pt.FACE_CX) - 16, top, 32,
                          pt.HAIRLINE - top + 2)
        found = tones(surface, box)
        check(len(found) >= 3,
              f"{name} sacinda en az uc ton (golge + ana + isik)",
              f"{len(found)} ton")

    # --- 5. Isik/golge: kontrollu, 3-5 seviye ------------------------------
    print("\n--- yuzde kontrollu golge ---")
    for name, surface in (("rey", rey), ("ardo", ardo)):
        box = pygame.Rect(int(pt.FACE_CX) - 12, pt.BROW, 24,
                          pt.CHIN - pt.BROW)
        found = tones(surface, box)
        check(3 <= len(found) <= 12,
              f"{name} yuzunde kontrollu ton sayisi (3-12)",
              f"{len(found)} ton")

    # --- 6. Ardo'nun yuzunun bir kismi golgede -----------------------------
    print("\n--- Ardo: yuzun bir kismi golgede ---")
    check(pt.ARDO_PORTRAIT.face_shadow > 0,
          "Ardo'da yuz golgesi acik", str(pt.ARDO_PORTRAIT.face_shadow))
    check(pt.REY_PORTRAIT.face_shadow == 0,
          "Rey'de yok - iki karakter ayni isik altinda degil")
    left = pygame.Rect(int(pt.FACE_CX) - 10, pt.CHEEK, 8, 8)
    right = pygame.Rect(int(pt.FACE_CX) + 3, pt.CHEEK, 8, 8)
    left_lum = sum(sum(c) * n for c, n in tones(ardo, left).items())
    right_lum = sum(sum(c) * n for c, n in tones(ardo, right).items())
    check(left_lum > right_lum,
          "Ardo'nun SOL yanagi sag yanagindan aydinlik - isik sol-ustten",
          f"{left_lum} > {right_lum}")

    # --- 7. Anatomi: Rey zarif, Ardo agir ----------------------------------
    print("\n--- anatomi ---")
    check(pt.ARDO_PORTRAIT.jaw_width > pt.REY_PORTRAIT.jaw_width,
          "Ardo'nun cene hatti daha guclu",
          f"{pt.ARDO_PORTRAIT.jaw_width} > {pt.REY_PORTRAIT.jaw_width}")
    check(pt.ARDO_PORTRAIT.shoulder_span > pt.REY_PORTRAIT.shoulder_span,
          "Ardo daha genis omuzlu",
          f"{pt.ARDO_PORTRAIT.shoulder_span} > "
          f"{pt.REY_PORTRAIT.shoulder_span}")
    check(pt.REY_PORTRAIT.hair_length > pt.ARDO_PORTRAIT.hair_length,
          "Rey'in saci uzun (kanon), Ardo'nunki kisa")

    # --- 8. Palet disina cikilmadi -----------------------------------------
    # `forge.Canvas` yalnizca zincir indeksiyle cizdigi icin bu yapisal
    # olarak imkansiz; yine de dogruluyoruz - `CLAUDE.md` 6'nin en sert
    # kurali ve bir gun biri `Surface`e dogrudan cizmeye kalkabilir.
    print("\n--- palet disi renk yok ---")
    from src.art import palette
    allowed = {palette.color(n) for n in palette.COLORS}
    for name, surface in (("rey", rey), ("ardo", ardo)):
        used = set(tones(surface, surface.get_rect()))
        stray = used - allowed
        check(not stray, f"{name} palet icinde", str(list(stray)[:3]))

    # --- 9. Yanki'nin portresi YOK -----------------------------------------
    # Kafanin icindeki sesin yuzu olmaz - ayni gerekce onun diyalog
    # kutusunu da kaldirmisti (`src/ui/dialogue.py`).
    print("\n--- Yanki'nin yuzu yok ---")
    check(pt.portrait("echo") is None, "echo portresi bilerek yok")

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Portreler: sema dogru, goz bes katmanli, karakterler ayrisiyor.")
    return 0


raise SystemExit(main())
