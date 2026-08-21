"""Aseprite kopruleri - **opsiyonel hizlandirici, zorunlu bagimlilik degil.**

Kural: hicbir kod Aseprite'in varligini varsaymaz. Kuruluysa bazi isleri
devralir; degilse her sey Pillow/NumPy yoluyla calismaya devam eder.

Aseprite'in en degerli katkisi **kare etiketli atlas**: `--data atlas.json`
ciktisinda animasyon adlari (idle, run, attack) yer alir, yani isimlendirme
elle takip edilmez. Ikinci degeri elle rotus - prosedurel uretimin
yapamadigi %15 (Rey'in yuz ifadesi, boss'un imza pozu).

Aseprite'tan cikan **her PNG yine `tools/quantize.py`'den gecer**. Istisna yok.

Kullanim:
    python tools/aseprite.py --kontrol
    python tools/aseprite.py --atlas assets/source/rey.aseprite
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

# Depo kokunu import yoluna ekle - arac dogrudan calistirilabilsin.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

# Yaygin kurulum adlari. Windows'ta Steam surumu farkli yere kurulabilir.
CANDIDATE_NAMES = ("aseprite", "Aseprite")
SOURCE_DIR = Path("assets/source")
ATLAS_DIR = Path("assets/sprites")


def find_aseprite() -> str | None:
    """Aseprite calistirilabilir mi? Yoksa None - cagiran taraf geri duser."""
    for name in CANDIDATE_NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def is_available() -> bool:
    return find_aseprite() is not None


def version() -> str | None:
    executable = find_aseprite()
    if executable is None:
        return None
    try:
        result = subprocess.run([executable, "--version"], capture_output=True,
                                text=True, timeout=10, check=False)
        return result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def export_atlas(source: Path, out_png: Path | None = None,
                 out_json: Path | None = None) -> tuple[Path, Path] | None:
    """`.aseprite` dosyasindan etiketli atlas uretir.

    Aseprite yoksa None doner - cagiran taraf prosedurel uretime devam eder.
    Uretilen PNG'yi **quantize.py'den gecirmek cagiranin sorumlulugudur.**
    """
    executable = find_aseprite()
    if executable is None:
        return None

    out_png = out_png or ATLAS_DIR / f"{source.stem}.png"
    out_json = out_json or ATLAS_DIR / f"{source.stem}.json"
    out_png.parent.mkdir(parents=True, exist_ok=True)

    command = [
        executable, "-b", str(source),
        "--sheet", str(out_png),
        "--data", str(out_json),
        "--format", "json-array",
        "--list-tags",           # Animasyon etiketleri JSON'a girsin
        "--sheet-pack",
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[aseprite] atlas uretilemedi: {exc}")
        return None
    return out_png, out_json


def read_tags(atlas_json: Path) -> dict[str, tuple[int, int]]:
    """Atlas JSON'undan animasyon etiketlerini okur: ad -> (ilk, son kare)."""
    try:
        data = json.loads(atlas_json.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"[aseprite] atlas verisi okunamadi: {exc}")
        return {}
    tags = data.get("meta", {}).get("frameTags", [])
    return {tag["name"]: (int(tag["from"]), int(tag["to"])) for tag in tags}


def apply_palette(image: Path, gpl: Path, out: Path | None = None) -> Path | None:
    """Bir gorsele Aseprite ile palet uygular.

    Ana yol yine `tools/quantize.py`'dir; bu yalnizca toplu is icin kisayol.
    """
    executable = find_aseprite()
    if executable is None:
        return None
    out = out or image
    try:
        subprocess.run([executable, "-b", str(image), "--palette", str(gpl),
                        "--save-as", str(out)],
                       check=True, capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[aseprite] palet uygulanamadi: {exc}")
        return None
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Aseprite koprusu (opsiyonel)")
    parser.add_argument("--kontrol", action="store_true",
                        help="kurulu mu, hangi surum")
    parser.add_argument("--atlas", type=Path, default=None,
                        help=".aseprite dosyasindan etiketli atlas uret")
    args = parser.parse_args()

    if args.kontrol or args.atlas is None:
        executable = find_aseprite()
        if executable is None:
            print("Aseprite kurulu DEGIL.")
            print("Sorun yok - boru hatti Pillow/NumPy yoluyla calisiyor.")
            print("Prosedurel uretim isin ~%85'ini zaten hallediyor;")
            print("Aseprite kalan elle rotus icin, ihtiyac dogunca kurulur.")
            return 0
        print(f"Aseprite bulundu: {executable}")
        print(f"surum: {version() or 'okunamadi'}")
        return 0

    result = export_atlas(args.atlas)
    if result is None:
        print("atlas uretilemedi (Aseprite yok ya da hata)")
        return 1
    png, data = result
    tags = read_tags(data)
    print(f"{png}")
    print(f"{data}  etiketler: {', '.join(tags) or 'yok'}")
    print("UNUTMA: uretilen PNG'yi tools/quantize.py'den gecir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
