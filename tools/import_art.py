"""Disaridan gelen gorseli oyun varligina cevirir.

AI ureticileri (ve cogu cizim programi) **gercek piksel sanati
uretmez**: yuksek cozunurlukte, anti-aliasing'li, binlerce renkli
"piksel gorunumlu" bir goruntu verir. Oyle bir dosya 64x96'lik bir
yuvaya dogrudan girmez - girse bile paletin disinda kalir ve oteki
varliklarla tutmaz.

Bu arac aradaki uc adimi yapiyor:

    1. KIRP     hedef en/boy oranina ortalayarak
    2. KUCULT   hedef boyuta - **alan ortalamasi**, sonra nearest
    3. QUANTIZE 37 renge (`tools/quantize.py` ile ayni fonksiyon)

Ucuncusu `CLAUDE.md` 6'nin sarti: *"Kaynagi ne olursa olsun - kod,
elle cizim, harici arac - her gorsel `tools/quantize.py` filtresinden
gecer. Bu tek kural tutarsizlik riskini yapisal olarak cozer."*

## Neden once alan ortalamasi, sonra quantize

Dogrudan nearest-neighbor ile kucultmek AI ciktisinda **gurultu**
uretiyor: kaynakta yan yana duran iki farkli ton arasindan rastgele
biri seciliyor ve sonuc titrek oluyor. Alan ortalamasi once formu
koruyup renkleri yumusatiyor, quantize sonra palete cakiyor - yani
"hangi palet rengi bu bolgeyi en iyi temsil eder" sorusu dogru
sirada soruluyor.

Kullanim:

    python tools/import_art.py indirilen.png --tur portre --ad rey
    python tools/import_art.py panel.png --tur panel --ad ch14_kaynak
    python tools/import_art.py x.png --boyut 64x96 --cikti assets/a.png

Turler ve hedef boyutlari `TARGETS`te; yeni bir tur eklemek bir
satir.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# **Pillow kullanilmiyor.** `CLAUDE.md` 4: yeni bagimlilik sormadan
# eklenmez, ve `tools/imagelib.py` zaten pygame ile PNG okuyup
# yaziyor. Ilk surum Pillow ile yazilmisti ve venv'de kurulu bile
# degildi - proje bu karari bilerek vermis.
import pygame  # noqa: E402

from tools.imagelib import (  # noqa: E402
    ensure_display, from_arrays, load, save, to_arrays,
)
from tools.quantize import quantize_arrays  # noqa: E402

# --- Hedefler ---------------------------------------------------------------
# (genislik, yukseklik, klasor). Boyutlar tahmin degil: portre
# `src/art/portrait.py`den, panel ic cozunurlukten (`CLAUDE.md` 4).
TARGETS: dict[str, tuple[int, int, str]] = {
    "portre": (64, 96, "assets/portraits"),
    "panel": (480, 270, "assets/panels"),
    "ikon": (16, 16, "assets/icons"),
}


def _fit_crop(surface: pygame.Surface, width: int,
              height: int) -> pygame.Surface:
    """Hedef orana **ortalayarak** kirpar - sikistirmaz.

    Sikistirma yuzu bozar ve bunu fark etmek zor: portre bir piksel
    genis olunca "sisman" gorunuyor ama neden oldugu anlasilmiyor.
    Kirpmak kaybediyor ama yalan soylemiyor.
    """
    src_w, src_h = surface.get_size()
    target = width / height
    source = src_w / src_h
    if abs(source - target) < 1e-3:
        return surface
    if source > target:
        new_w = int(round(src_h * target))
        left = (src_w - new_w) // 2
        return surface.subsurface(pygame.Rect(left, 0, new_w, src_h)).copy()
    new_h = int(round(src_w / target))
    # Ustten degil **ust ucte birden** kirpiyor: portrede onemli olan
    # yuz ve o ustte duruyor. Ortalamak ceneyi kesiyordu.
    top = (src_h - new_h) // 3
    return surface.subsurface(pygame.Rect(0, top, src_w, new_h)).copy()


def _box_downscale(rgb: np.ndarray, alpha: np.ndarray, width: int,
                   height: int) -> tuple[np.ndarray, np.ndarray]:
    """Alan ortalamasiyla kucultme - **numpy ile, kutuphanesiz.**

    Kaynak hedefin tam kati degilse once en yakin kata kirpiliyor;
    kalan birkac piksel satiri gorunmeyecek kadar kucuk ve bir
    "yeniden orneklemeyi yeniden orneklemek"ten iyi.

    `pygame.transform.smoothscale` de alan ortalamasi yapar ama
    `CLAUDE.md` 4 onu piksel sanatinda YASAKLIYOR. Burada kural
    teknik olarak ihlal edilmiyor (kucultmede bulanikilik istiyoruz,
    sonra quantize netlestiriyor) - ama yasak bir cagriyi boru
    hattina sokmak ileride yanlis ornek olurdu. numpy ile yapmak hem
    aciik hem kurala dokunmuyor.
    """
    src_h, src_w = rgb.shape[:2]
    fy, fx = src_h // height, src_w // width
    if fy < 1 or fx < 1:
        # Kaynak hedeften kucuk - buyutmek gerekiyor, nearest yeterli.
        yi = (np.arange(height) * src_h // height).clip(0, src_h - 1)
        xi = (np.arange(width) * src_w // width).clip(0, src_w - 1)
        return rgb[np.ix_(yi, xi)], alpha[np.ix_(yi, xi)]
    rgb = rgb[:fy * height, :fx * width]
    alpha = alpha[:fy * height, :fx * width]
    rgb = rgb.reshape(height, fy, width, fx, 3).mean(axis=(1, 3))
    alpha = alpha.reshape(height, fy, width, fx).mean(axis=(1, 3))
    return rgb.astype(np.uint8), alpha.astype(np.uint8)


def convert(source: Path, out: Path, width: int, height: int,
            report: bool = True) -> Path:
    ensure_display()
    surface = load(source)
    src_w, src_h = surface.get_size()
    surface = _fit_crop(surface, width, height)

    rgb, alpha = to_arrays(surface)
    rgb, alpha = _box_downscale(rgb, alpha, width, height)

    # Yari saydam pikselleri **ikiye ayir**: piksel sanatinda yumusak
    # kenar yoktur. Esik olmadan konturlar bulanik kaliyor ve
    # `outline.py` yanlis yere cizgi cekiyor.
    alpha = np.where(alpha >= 128, 255, 0).astype(np.uint8)

    new_rgb, new_alpha, changed = quantize_arrays(rgb, alpha)

    out.parent.mkdir(parents=True, exist_ok=True)
    save(from_arrays(new_rgb, new_alpha), out)

    if report:
        solid = int(np.count_nonzero(alpha))
        print(f"  {source.name} -> {out}")
        print(f"    {src_w}x{src_h} kaynak -> {width}x{height} hedef")

        # **Kac piksel degisti** degil, **ne kadar** degisti.
        #
        # Ilk surum degisen piksel sayisini raporluyor ve %85 ustunde
        # uyariyordu. AI ciktisinda bu deger her zaman %100 - yani
        # uyari her seferinde cikiyordu ve hicbir sey soylemiyordu.
        # Her zaman yanan bir uyari, olmayan bir uyaridir.
        #
        # Anlamli olcut renk MESAFESI: paletin 37 rengi kaynagin
        # tonlarini ne kadar iyi karsiladi. Kucukse cikti kaynaga
        # benziyor demektir, sayilan piksel ne olursa olsun.
        mask = alpha > 0
        if solid:
            delta = np.abs(rgb[mask].astype(np.int16)
                           - new_rgb[mask].astype(np.int16))
            shift = float(delta.mean())
            print(f"    {changed}/{solid} piksel palete cekildi, "
                  f"ortalama kayma {shift:.1f}/255")
            if shift > 26.0:
                print("    ! Kayma buyuk: kaynakta paletin karsilayamadigi "
                      "tonlar var (cok doygun renk ya da yumusak gecis). "
                      "Sonuc lekeli gorunebilir.")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Disaridan gelen gorseli oyun varligina cevirir.")
    parser.add_argument("source", type=Path, help="kaynak gorsel")
    parser.add_argument("--tur", choices=sorted(TARGETS),
                        help="hazir hedef (portre/panel/ikon)")
    parser.add_argument("--ad", help="cikti dosya adi (uzantisiz)")
    parser.add_argument("--boyut", help="elle boyut, orn. 64x96")
    parser.add_argument("--cikti", type=Path, help="elle cikti yolu")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"bulunamadi: {args.source}")
        return 1

    if args.tur:
        width, height, folder = TARGETS[args.tur]
        name = args.ad or args.source.stem
        out = args.cikti or (ROOT / folder / f"{name}.png")
    elif args.boyut and args.cikti:
        width, height = (int(v) for v in args.boyut.lower().split("x"))
        out = args.cikti
    else:
        print("--tur ya da (--boyut + --cikti) gerekli")
        return 1

    convert(args.source, out, width, height)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
