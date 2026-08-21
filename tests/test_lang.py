"""Coklu dil dogrulamasi.

Ceviri hatalari sessizdir: yanlis bir dize cokme uretmez, sadece yanlis
gorunur - ve genelde o dili konusmayan biri fark etmez. Bu yuzden makinenin
yakalayabilecegi ne varsa burada yakalanir:

  * Anahtar paritesi     - yarim cevrilmis menu surume giremesin
  * Yer tutucu paritesi  - {chapter} bir dilde varken digerinde kaybolmasin
  * Font kapsami         - cevirinin her karakteri cizilebilsin
  * Genislik             - uzun ceviri paneli tasirmasin (bu projede iki kez
                           panel tasmasi yasandi, ucuncusu olmasin)
  * Harf donusumu        - Turkce kurali Ingilizce'yi bozmasin

Calistir:
    python tests/test_lang.py
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

from src.config import INTERNAL_WIDTH  # noqa: E402
from src.ui import i18n, text  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


PLACEHOLDER = re.compile(r"\{(\w+)\}")

# Panel genisligi degil, ekran genisligi: en uzun tek satirlik metin bile
# 480 piksele sigmali. Panele ozel siniralar asagida ayrica olculuyor.
MAX_LINE_WIDTH = INTERNAL_WIDTH - 8

# Bu anahtarlar bir panelin icinde ciziliyor - siniralari daha dar.
PANEL_LIMITS: dict[str, int] = {
    "menu.overwrite_warning": 180,
    "pause.quit_question": 180,
    "pause.quit_saved": 180,
    "character.recommend": 220,
    "settings.controls": 300,
    "character.controls": 300,
    "combat.controls": 460,
}


def main() -> int:
    codes = i18n.available()
    print(f"--- diller: {', '.join(codes)} ---")
    check(i18n.SOURCE_LANGUAGE in codes, "kaynak dil mevcut", i18n.SOURCE_LANGUAGE)
    check(len(codes) >= 2, "en az iki dil var", str(len(codes)))

    source = i18n.table(i18n.SOURCE_LANGUAGE)
    check(len(source) > 60, "kaynak tablo dolu", f"{len(source)} anahtar")

    # --- 1. Anahtar paritesi ------------------------------------------------
    print("\n--- anahtar paritesi ---")
    for code in codes:
        if code == i18n.SOURCE_LANGUAGE:
            continue
        other = i18n.table(code)
        eksik = sorted(set(source) - set(other))
        fazla = sorted(set(other) - set(source))
        check(not eksik, f"{code}: eksik anahtar yok",
              ", ".join(eksik[:5]) + (" ..." if len(eksik) > 5 else ""))
        check(not fazla, f"{code}: fazladan anahtar yok",
              ", ".join(fazla[:5]) + (" ..." if len(fazla) > 5 else ""))

    # --- 2. Yer tutucu paritesi ---------------------------------------------
    # "{chapter}" bir dilde kaybolursa t() bicimlendirmede sessizce ham metin
    # dondurur ve oyuncu "BOLUM" yazip sayisi olmayan bir kart gorur.
    print("\n--- yer tutucular ---")
    bozuk: list[str] = []
    for key, value in source.items():
        want = set(PLACEHOLDER.findall(value))
        for code in codes:
            if code == i18n.SOURCE_LANGUAGE:
                continue
            got = set(PLACEHOLDER.findall(i18n.table(code).get(key, "")))
            if got != want:
                bozuk.append(f"{code}:{key} {sorted(want)} != {sorted(got)}")
    check(not bozuk, "yer tutucular her dilde ayni",
          "; ".join(bozuk[:3]) + (" ..." if len(bozuk) > 3 else ""))

    # --- 3. Font kapsami ----------------------------------------------------
    print("\n--- font kapsami ---")
    # Uyeligi elle sorgulamak yanlis sonuc verir: font kaynaginda bazi glifler
    # ayrisik (NFD) yazili ve ALIASES uzerinden cozuluyor. Font'un kendi
    # cozumleyicisini kullan - cizim ani da ayni yoldan geciyor.
    glyphs = text.font()
    for code in codes:
        eksik_glif: set[str] = set()
        for value in i18n.table(code).values():
            for char in PLACEHOLDER.sub("", value):   # {chapter} cizilmez
                if char in ("\n", " "):
                    continue
                if not glyphs.has(char):
                    eksik_glif.add(char)
        check(not eksik_glif, f"{code}: tum karakterler cizilebilir",
              " ".join(f"U+{ord(c):04X}" for c in sorted(eksik_glif)))

    # --- 4. Genislik --------------------------------------------------------
    print("\n--- genislik ---")
    for code in codes:
        i18n.set_language(code)
        tasan: list[str] = []
        for key, value in i18n.table(code).items():
            ornek = PLACEHOLDER.sub("00", value)     # yer tutuculari doldur
            width = text.text_width(ornek)
            limit = PANEL_LIMITS.get(key, MAX_LINE_WIDTH)
            if width > limit:
                tasan.append(f"{key} {width}>{limit}")
        check(not tasan, f"{code}: metinler sigiyor",
              "; ".join(tasan[:3]) + (" ..." if len(tasan) > 3 else ""))

    # --- 4b. Kod ile tablo ortusuyor mu -------------------------------------
    # Tablolarin birbiriyle tutarli olmasi yetmez: kodun **istedigi** anahtar
    # tabloda yoksa oyuncu ekranda "[settings.percent]" gorur. Bu tam olarak
    # bir kez oldu - anahtar yanlis ad alanina yazilmisti ve parite testi
    # bunu goremedi, cunku iki dosyada da ayni yanlis yerdeydi.
    print("\n--- kod / tablo ortusmesi ---")
    namespaces = sorted({k.split(".")[0] for k in source})
    key_like = re.compile(
        r"[\"'](" + "|".join(namespaces) + r")\.([a-z0-9_]+)[\"']")
    # "save.json" gibi dosya adlari anahtar gibi gorunur; uzantiyla ele.
    FILE_SUFFIXES = {"json", "tmp", "bak", "py", "png", "wav", "ogg", "txt"}

    used: set[str] = set()
    unknown: list[str] = []
    for path in sorted(ROOT.joinpath("src").rglob("*.py")):
        for match in key_like.finditer(path.read_text(encoding="utf-8")):
            namespace, leaf = match.group(1), match.group(2)
            if leaf in FILE_SUFFIXES:
                continue
            key = f"{namespace}.{leaf}"
            used.add(key)
            if key not in source:
                unknown.append(f"{path.name}:{key}")

    check(not unknown, "kodun kullandigi her anahtar tabloda var",
          ", ".join(unknown[:5]) + (" ..." if len(unknown) > 5 else ""))
    check(len(used) > 50, "tarama anlamli sayida anahtar buldu", str(len(used)))

    # Kullanilmayan anahtar cevirmenin bosuna emek harcamasi demek.
    unused = sorted(set(source) - used)
    check(not unused, "tabloda olu anahtar yok",
          ", ".join(unused[:5]) + (" ..." if len(unused) > 5 else ""))

    # --- 5. Dile duyarli harf donusumu --------------------------------------
    # Ayni fonksiyonu iki dile uygulamak birini mutlaka bozar:
    # Turkce'de i -> I, Ingilizce'de i -> I.
    print("\n--- harf donusumu ---")
    i18n.set_language("tr")
    check(i18n.upper("ışık") == "IŞIK", "tr: ışık -> IŞIK", i18n.upper("ışık"))
    check(i18n.upper("iyi") == "İYİ", "tr: iyi -> İYİ", i18n.upper("iyi"))
    if "en" in codes:
        i18n.set_language("en")
        check(i18n.upper("Continue") == "CONTINUE",
              "en: Continue -> CONTINUE (noktali I degil)", i18n.upper("Continue"))
        check(i18n.upper("Settings") == "SETTINGS",
              "en: Settings -> SETTINGS", i18n.upper("Settings"))
    i18n.set_language(i18n.DEFAULT_LANGUAGE)

    # --- 6. Cozulemeyen anahtar kalmadi -------------------------------------
    print("\n--- cozum ---")
    for code in codes:
        i18n.set_language(code)
        # "[" ile baslayan mesru dizeler var ("[Enter] onayla"), bu yuzden
        # tam esitlik aranir - i18n.t() cozemedigi anahtari "[anahtar]" doner.
        kirik = [k for k in source if i18n.t(k) == f"[{k}]"]
        check(not kirik, f"{code}: her anahtar cozuluyor", ", ".join(kirik[:5]))
    i18n.set_language(i18n.DEFAULT_LANGUAGE)

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("Dil tablolari tutarli.")
    return 0


raise SystemExit(main())
