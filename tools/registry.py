"""assets/REGISTRY.md dosyasini koddan uretir.

`CLAUDE.md` 6 uretilen her asset'in kaydedilmesini istiyor. Elle tutulan bir
liste kaciniLmaz olarak eskir - kimse spec degistirdiginde belgeyi
guncellemeyi hatirlamaz. Bu yuzden tablo koddan turetiliyor.

Kullanim:
    python tools/registry.py            # yazar
    python tools/registry.py --kontrol  # guncel mi diye bakar, yazmaz
                                        # (guncel degilse 1 doner)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "assets" / "REGISTRY.md"

ROLES = {
    "rey": "Oynanabilir - Yankisoyleyen",
    "ardo": "Oynanabilir - yabanci",
    "shambler": "Katman 1 - Suruklenen",
    "climber": "Katman 1 - Tirmanan",
    "bloated": "Katman 1 - Sismek",
}


def build() -> str:
    pygame.init()
    pygame.display.set_mode((64, 64))
    from src.art.animation import ANIMATIONS, CHARACTERS
    from src.art import palette

    total_frames = sum(count for _, count, _ in ANIMATIONS.values())
    anims = " · ".join(f"{k} ({c})"
                       for k, (_, c, _) in sorted(ANIMATIONS.items()))

    lines = [
        "# ASSET KAYDI",
        "",
        "`CLAUDE.md` 6: uretilen her asset buraya kaydedilir.",
        "",
        "**Bu projede sprite'lar PNG degil.** Hepsi `src/art/spritegen.py`",
        "icindeki `draw_humanoid()` ile **calisma zamaninda** uretiliyor;",
        "disk uzerinde sprite dosyasi yok. Bu yuzden kayit \"hangi dosya\"",
        "degil, **hangi spec** sorusunu cevapliyor.",
        "",
        "> Bu dosya `tools/registry.py` tarafindan uretilir. **Elle",
        "> duzenleme** - spec degisince araci yeniden calistir.",
        "",
        "## Karakterler",
        "",
        "Uretici: `src/art/spritegen.py :: draw_humanoid(spec, pose)`  ",
        "Spec'ler: `src/art/animation.py :: CHARACTERS`",
        "",
        "| Ad | Hucre | Taban (foot_y) | Kare | Rol |",
        "|---|---|---|---|---|",
    ]
    for name, spec in CHARACTERS.items():
        lines.append(
            f"| `{name}` | {spec.cell_width}x{spec.cell_height} | "
            f"{spec.foot_y} | {total_frames} | {ROLES.get(name, '-')} |")

    lines += [
        "",
        f"**Animasyon durumlari (kare sayisi):** {anims}",
        "",
        "Her karakter bu durumlarin tamamini uretir; toplam kare sayisi bu",
        "yuzden kadroda ayni.",
        "",
        "## Palet",
        "",
        f"Tek kaynak: `tools/palette.json` - **{len(palette.COLORS)} renk**, ",
        "degistirilemez. `src/art/palette.py` okur ve palet disi her rengi ",
        "`PaletteError` ile reddeder. Golge zincirleri "
        f"({len(palette.SHADE_CHAINS)} adet) rampalar arasi gecerek renk ",
        "sinirini asmadan tonlama saglar.",
        "",
        "## Font",
        "",
        "`src/ui/font_data.py` - 5x11 bitmap, tam Turkce seti. Eksik glif ",
        "sessizce dusmez, konsola rapor edilir.",
        "",
        "## Dil",
        "",
        "`src/ui/lang/tr.json` (kanonik) ve `en.json`. Anahtar paritesi ",
        "`tests/test_lang.py` ile korunuyor.",
        "",
        "## Ses",
        "",
        "Henuz yok. Gorev 10.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    content = build()
    check_only = "--kontrol" in sys.argv

    current = TARGET.read_text(encoding="utf-8") if TARGET.is_file() else ""
    if current == content:
        print("REGISTRY.md guncel.")
        return 0

    if check_only:
        print("!! REGISTRY.md guncel degil - `python tools/registry.py` calistir.")
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(content, encoding="utf-8", newline="\n")
    print(f"yazildi: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
