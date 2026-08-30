"""Paketlenmis surum calisir mi - **calistirmadan** once.

## Neden var

`Legend of Rey.spec` bir kez sessizce bozuldu: yalnizca `assets`
klasorunu paketliyordu, ama oyun iki yerden daha diskten okuyor ve
ikisi de `assets` altinda degil:

    tools/palette.json     37 rengin tek kaynagi
    src/ui/lang/*.json     Turkce/Ingilizce metinler

Paketlenen oyun **acilir acilmaz cokerdi** ve bu ancak exe
calistirilinca gorulurdu - yani tester'in elinde. Kaynak tarafta
hicbir sey yanlis gorunmuyordu.

Ayni sinif hata bu projede uc kez yasandi (dil anahtarlari, ses
adlari, `draw_extra`): **sessizce basarisiz olan sey testle
yakalanir**, dikkatle degil.

Bu test iki sey soruyor:

  1. Kaynakta diskten okunan her klasor spec'te bildirilmis mi?
  2. `importlib` ile ada gore yuklenen her modul `hiddenimports`ta mi?

Ikincisi de gercek: bolumler ve dusmanlar dize yollarla yukleniyor
(`main.py` SCENES, `ENEMY_CLASSES`), PyInstaller statik analizle
bunlari goremiyor.

Calistir:
    python tests/test_build.py
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

SPEC = ROOT / "Legend of Rey.spec"

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def spec_text() -> str:
    return SPEC.read_text(encoding="utf-8")


# --- 1. Diskten okunan yollar spec'te mi -------------------------------------
def test_data_paths() -> None:
    """`Path(__file__)...` ile kurulan her veri yolu paketlenmeli.

    Desen: `parents[N] / "klasor" / ...`. Kaynak agacinin disina cikan
    her yol bir veri dosyasidir ve donmus surumde `sys._MEIPASS`
    altinda **ayni goreli konumda** bulunmali.
    """
    print("\n--- diskten okunan yollar ---")
    spec = spec_text()
    pattern = re.compile(
        r'Path\(__file__\)\.resolve\(\)\.parents?\[?\d*\]?'
        r'((?:\s*/\s*"[^"]+")+)')
    found: dict[str, str] = {}
    for path in (ROOT / "src").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for match in pattern.finditer(source):
            parts = re.findall(r'"([^"]+)"', match.group(1))
            if not parts:
                continue
            found.setdefault(parts[0], str(path.relative_to(ROOT)))

    # `parent / "lang"` gibi **kardes** klasorler de veri: modulun
    # yanindaki json PyInstaller'a otomatik girmiyor.
    sibling = re.compile(r'Path\(__file__\)\.resolve\(\)\.parent\s*/\s*"([^"]+)"')
    for path in (ROOT / "src").rglob("*.py"):
        for match in sibling.finditer(path.read_text(encoding="utf-8")):
            rel = path.relative_to(ROOT).parent / match.group(1)
            found.setdefault(str(rel).replace("\\", "/"),
                             str(path.relative_to(ROOT)))

    check(bool(found), "kaynakta veri yolu bulundu", f"{len(found)} tane")
    for folder, owner in sorted(found.items()):
        needle = folder.replace("\\", "/")
        check(needle in spec.replace("\\", "/"),
              f"'{needle}' spec'te bildirilmis", f"kullanan: {owner}")


# --- 2. Ada gore yuklenen moduller hiddenimports'ta mi ----------------------
def test_dynamic_imports() -> None:
    """`"modul:Sinif"` ve `("modul", "Sinif")` ile yuklenen her sey.

    PyInstaller bunlari **goremiyor**: statik analiz `importlib` ile
    calisan bir dize yolunu takip etmiyor. Bildirilmezse paketlenen
    oyun o bolume girildiginde coker - yani ilk uc bolum calisir,
    dorduncusu patlar.
    """
    print("\n--- dinamik import'lar ---")
    spec = spec_text()
    modules: set[str] = set()

    colon = re.compile(r'"(src\.[\w.]+):(\w+)"')
    tuple_form = re.compile(r'\(\s*"(src\.[\w.]+)"\s*,\s*"(\w+)"\s*\)')
    for path in list((ROOT / "src").rglob("*.py")) + [ROOT / "main.py"]:
        source = path.read_text(encoding="utf-8")
        for match in colon.finditer(source):
            modules.add(match.group(1))
        for match in tuple_form.finditer(source):
            modules.add(match.group(1))

    check(bool(modules), "dinamik yuklenen modul bulundu",
          f"{len(modules)} tane")
    missing = sorted(m for m in modules if f"'{m}'" not in spec)
    check(not missing, "hepsi hiddenimports'ta",
          ", ".join(missing) if missing else f"{len(modules)} modul")


# --- 3. Paketlenmemesi gerekenler --------------------------------------------
def test_excluded() -> None:
    """Yuksek cozunurluklu asillar ve belgeler pakete girmemeli."""
    print("\n--- disarida kalmasi gerekenler ---")
    # **Yalnizca DATAS listesine bak.** Modul basligindaki aciklama
    # `assets/portraits/kaynak` klasorunden bahsediyor ve ilk surum onu
    # "paketlenmis" sandi. Bir yorumda gecmek paketlenmek degildir.
    raw = spec_text()
    start = raw.find("DATAS = [")
    spec = raw[start:raw.find("]", start)].replace("\\", "/")
    check("assets/portraits/kaynak" not in spec,
          "yuksek cozunurluklu asillar paketlenmiyor (5.7 MB)")
    check("('assets', 'assets')" not in spec,
          "assets TOPTAN paketlenmiyor - kaynak klasoru de girerdi")


# --- 4. Spec'in kendisi tutarli mi -------------------------------------------
def test_spec_sane() -> None:
    print("\n--- spec ---")
    check(SPEC.exists(), "spec dosyasi var")
    spec = spec_text()
    check("console=True" in spec,
          "tester surumunde konsol ACIK - cokme gorunur olmali")
    check((ROOT / "icon.ico").exists(), "icon.ico yerinde")
    check((ROOT / "tools" / "palette.json").exists(), "palette.json yerinde")
    check((ROOT / "src" / "ui" / "lang" / "tr.json").exists(),
          "dil dosyalari yerinde")


def main() -> int:
    test_spec_sane()
    test_data_paths()
    test_dynamic_imports()
    test_excluded()

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for name in failures:
            print(f"  - {name}")
        print("\nPaketlenen surum calismayabilir. Spec'i duzelt.")
        return 1
    print("Paket tanimi tutarli - her veri yolu ve dinamik modul bildirilmis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
