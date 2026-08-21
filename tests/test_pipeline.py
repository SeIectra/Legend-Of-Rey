"""Asset boru hattinin ucundan ucuna calistigini kanitlar.

Palet disi renklerle bir test gorseli uretir, sonra:
    quantize -> outline -> shade -> preview -> silhouette
zincirinden gecirir ve her adimin sozunu tuttugunu dogrular.

Calistir:
    python tests/test_pipeline.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from tools.imagelib import ensure_display, from_arrays, load, save, solid_mask, to_arrays  # noqa: E402
from tools import outline as outline_tool  # noqa: E402
from tools import preview as preview_tool  # noqa: E402
from tools import quantize as quantize_tool  # noqa: E402
from tools import shade as shade_tool  # noqa: E402
from tools import silhouette as silhouette_tool  # noqa: E402

from src.art import palette  # noqa: E402

WORK = ROOT / "build" / "pipeline_test"
failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def make_test_image(path: Path) -> None:
    """Palet disi renklerle 16x16 bir figur uretir."""
    ensure_display()
    rgb = np.zeros((16, 16, 3), dtype=np.int16)
    alpha = np.zeros((16, 16), dtype=np.int16)
    # Bilerek palette olmayan renkler
    rgb[4:12, 5:11] = (200, 30, 140)      # macenta govde
    alpha[4:12, 5:11] = 255
    rgb[2:5, 6:10] = (40, 220, 90)        # yesil kafa
    alpha[2:5, 6:10] = 255
    alpha[6, 7] = 120                     # yari saydam piksel - esik testi
    save(from_arrays(rgb, alpha), path)


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    source = WORK / "test_sprite.png"
    make_test_image(source)

    # --- quantize -----------------------------------------------------------
    print("--- quantize ---")
    rgb, alpha = to_arrays(load(source))
    off_palette = {tuple(int(c) for c in px)
                   for px in rgb[solid_mask(alpha)].reshape(-1, 3)}
    check(any(c not in palette.COLORS.values() for c in off_palette),
          "test gorseli palet disi renk iceriyor", f"{len(off_palette)} renk")

    quantized = WORK / "quantized.png"
    quantize_tool.quantize_file(source, quantized, report=True)

    q_rgb, q_alpha = to_arrays(load(quantized))
    q_solid = solid_mask(q_alpha)
    used = {tuple(int(c) for c in px) for px in q_rgb[q_solid].reshape(-1, 3)}
    palette_values = set(palette.COLORS.values())
    check(used <= palette_values, "quantize sonrasi her renk palette",
          f"{len(used)} renk kullanildi")

    unique_alpha = set(int(a) for a in np.unique(q_alpha))
    check(unique_alpha <= {0, 255}, "alfa 0/255'e yuvarlandi", str(sorted(unique_alpha)))

    # --- outline ------------------------------------------------------------
    print("\n--- outline ---")
    outlined = WORK / "outlined.png"
    outline_tool.outline_file(quantized, outlined)
    o_surface = load(outlined)
    check(o_surface.get_size() == (18, 18), "tuval kontur icin buyudu",
          str(o_surface.get_size()))

    o_rgb, o_alpha = to_arrays(o_surface)
    outline_colour = palette.outline()
    has_outline = np.any(np.all(o_rgb == np.array(outline_colour), axis=2)
                         & solid_mask(o_alpha))
    check(bool(has_outline), "kontur rengi uygulandi", str(outline_colour))
    check(outline_colour != (0, 0, 0), "kontur siyah degil")

    darkest = palette.darkest_names(2)
    check(palette.OUTLINE_NAME == darkest[1], "kontur en koyu 2. renk",
          f"{darkest}")

    # --- shade --------------------------------------------------------------
    print("\n--- shade ---")
    shaded = WORK / "shaded.png"
    shade_tool.shade_file(outlined, shaded)
    s_rgb, s_alpha = to_arrays(load(shaded))
    s_used = {tuple(int(c) for c in px)
              for px in s_rgb[solid_mask(s_alpha)].reshape(-1, 3)}
    check(s_used <= palette_values, "golgeleme paletten cikmadi",
          f"{len(s_used)} renk")
    check(not np.array_equal(s_rgb, o_rgb), "golgeleme gercekten bir sey degistirdi")

    # --- preview + silhouette -----------------------------------------------
    print("\n--- kontak sayfalari ---")
    images = [source, quantized, outlined, shaded]
    sheet = preview_tool.build_sheet(images, scale=4, columns=4)
    preview_path = WORK / "preview.png"
    save(sheet, preview_path)
    check(preview_path.exists() and sheet.get_width() > 0, "preview uretildi",
          f"{sheet.get_size()}")

    sil = silhouette_tool.build_sheet(images, scale=4, columns=4, side_by_side=True)
    sil_path = WORK / "silhouette.png"
    save(sil, sil_path)
    check(sil_path.exists() and sil.get_width() > 0, "siluet sayfasi uretildi",
          f"{sil.get_size()}")

    flat = silhouette_tool.to_silhouette(load(quantized))
    f_rgb, f_alpha = to_arrays(flat)
    flat_colours = {tuple(int(c) for c in px)
                    for px in f_rgb[solid_mask(f_alpha)].reshape(-1, 3)}
    check(len(flat_colours) == 1, "siluet tek renge indi", str(flat_colours))

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print(f"Boru hatti calisiyor. Ciktilar: {WORK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
