"""Renk korlugu paleti uretici - 3 varyant (protanopi/doteranopi/tritanopi).

CLAUDE.md 10: "Renk korlugu modu: 3 palet varyanti... Palet tek kaynak
oldugu icin bunlarin cogu neredeyse bedava." Bu arac o bedavaligi
gerceklestiriyor: `tools/palette.json`'daki 32 rengi okur, her biri icin
3 "daltonize edilmis" (renk korlugune gore duzeltilmis) karsilik uretir
ve sonucu ayni dosyaya `colorblind_variants` anahtari olarak yazar.

## Simulasyon degil, duzeltme (daltonization)

Iki farkli sey karistirilmasin:
  * **Simulasyon** - "bu renk bir renk koru kisiye nasil gorunur" (gelistirici
    onizlemesi icin).
  * **Duzeltme (daltonization)** - "bu rengi, renk koru kisi ayirt
    edebilsin diye nasil degistirmeliyim" (oyuncunun GERCEKTEN goreceği
    renk).

Ayarlar menusundeki secenek ikincisi - oyuncu paleti degistiriyor, simulasyon
izlemiyor. Once simulasyon uygulanir (kaybolan bilgi olculur), sonra o
kayip bilgi ayirt edilebilir kanallara (mavi/sari eksende) geri eklenir.
Bu, yaygin kullanilan "Daltonize" algoritmasinin (Fidaner/Lin/Ozguven,
2005 - acik kaynak Ruminski uygulamasi) standart bir uygulamasi.

## Simulasyon matrisleri

Machado, Oliveira & Fair - "A Physiologically-based Model for Simulation
of Color Vision Deficiency" (IEEE TVCG, 2009) - tam dikromazi (severity=1.0),
doGrusal (linear) RGB uzerinde calisir. Bu sabitler yaygin kullanilan
renk korlugu simulasyon araclarinin (Coblis, Sim Daltonism, vb.) dayandigi
degerlerdir.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "tools" / "palette.json"

# --- Machado 2009 tam-dikromazi simulasyon matrisleri (linear RGB) ------------
_SIM_MATRICES: dict[str, np.ndarray] = {
    "protanopia": np.array([
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [-0.003882, -0.048116, 1.051998],
    ]),
    "deuteranopia": np.array([
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ]),
    "tritanopia": np.array([
        [1.255528, -0.076749, -0.178779],
        [-0.078411, 0.930809, 0.147602],
        [0.004733, 0.691367, 0.303900],
    ]),
}

# Kayip bilgiyi mavi/sari eksenine dagitan hata-duzeltme matrisi - Daltonize
# algoritmasinin standart sabiti (Fidaner/Lin/Ozguven 2005).
_ERROR_MATRIX = np.array([
    [0.0, 0.0, 0.0],
    [0.7, 1.0, 0.0],
    [0.7, 0.0, 1.0],
])

MODES = ("protanopia", "deuteranopia", "tritanopia")


def _srgb_to_linear(c: np.ndarray) -> np.ndarray:
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _linear_to_srgb(c: np.ndarray) -> np.ndarray:
    c = np.clip(c, 0.0, 1.0)
    out = np.where(c <= 0.0031308, c * 12.92, 1.055 * (c ** (1 / 2.4)) - 0.055)
    return np.clip(out * 255.0, 0, 255)


def daltonize(rgb: tuple[int, int, int], mode: str) -> tuple[int, int, int]:
    """Bir rengi verilen renk korlugu turune gore duzeltir.

    1. Dogrusal RGB'ye cevir, dikromazi matrisiyle **simule et** (bu kisi
       bu rengi nasil gorur).
    2. Kaybolan bilgiyi (orijinal - simule) hesapla.
    3. Kaybi ayirt edilebilir kanallara (mavi/yesil agirlikli) geri ekle.
    4. sRGB'ye geri cevir.
    """
    linear = _srgb_to_linear(np.array(rgb, dtype=np.float64))
    simulated = _SIM_MATRICES[mode] @ linear
    error = linear - simulated
    correction = _ERROR_MATRIX @ error
    corrected = linear + correction
    result = _linear_to_srgb(corrected)
    return (int(round(result[0])), int(round(result[1])), int(round(result[2])))


def build_variants(colors: dict[str, list[int]]) -> dict[str, dict[str, list[int]]]:
    variants: dict[str, dict[str, list[int]]] = {}
    for mode in MODES:
        variants[mode] = {
            name: list(daltonize(tuple(rgb), mode))
            for name, rgb in colors.items()
        }
    return variants


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true",
                        help="Kontak sayfasi da uret (build/testshots/)")
    parser.add_argument("--check", action="store_true",
                        help="Yazmadan sadece hesapla, ozet bas")
    args = parser.parse_args()

    data = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    colors = data["colors"]
    variants = build_variants(colors)

    if args.check:
        for mode in MODES:
            print(f"{mode}: {len(variants[mode])} renk hesaplandi")
        return 0

    data["_renk_korlugu_aciklama"] = (
        "Otomatik uretildi: tools/colorblind.py. Elle duzenleme - bir "
        "sonraki calistirmada uzerine yazilir. Daltonize (duzeltme), "
        "simulasyon degil - oyuncunun GERCEKTEN gorecegi renkler."
    )
    data["colorblind_variants"] = variants
    PALETTE_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{PALETTE_PATH} guncellendi - {len(MODES)} varyant x "
          f"{len(colors)} renk.")

    if args.preview:
        _write_preview(colors, variants)
    return 0


def _write_preview(colors: dict[str, list[int]],
                   variants: dict[str, dict[str, list[int]]]) -> None:
    """Karsilastirma kontak sayfasi - orijinal + 3 varyant, satir satir."""
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    pygame.init()
    pygame.display.set_mode((64, 64))

    names = list(colors.keys())
    swatch = 24
    cols = 1 + len(MODES)
    width = cols * swatch
    height = len(names) * swatch
    sheet = pygame.Surface((width, height))
    sheet.fill((30, 30, 30))

    for row, name in enumerate(names):
        y = row * swatch
        sheet.fill(tuple(colors[name]), (0, y, swatch, swatch))
        for col, mode in enumerate(MODES, start=1):
            sheet.fill(tuple(variants[mode][name]),
                      (col * swatch, y, swatch, swatch))

    out = ROOT / "build" / "testshots" / "colorblind_preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(sheet, str(out))
    print(f"onizleme: {out}  (sutunlar: orijinal, {', '.join(MODES)})")


if __name__ == "__main__":
    sys.exit(main())
