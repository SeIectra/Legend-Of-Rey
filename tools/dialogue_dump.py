"""Oyundaki butun diyaloglari duzenlenebilir bir dosyaya doker.

Arda (30.08.2026): *"Butun diyaloglari at guncelliyim."*

Ciktinin isi tek: metin yazari **anahtar aramadan** okuyup duzeltebilsin.
Bu yuzden JSON degil duz metin, ve konusmaci adlari cozulmus halde.

    python tools/dialogue_dump.py            # docs/diyaloglar.md yazar
    python tools/dialogue_dump.py --geri     # duzenlenmis dosyayi geri okur

## Neden geri okuma da var

Elle JSON duzenlemek iki dosyayi (tr/en) senkron tutmayi gerektiriyor ve
bir virgul hatasi butun oyunu aciyor. Doker-duzenle-geri oku dongusu o
riski aradan cikariyor: yazar yalnizca **metni** goruyor, anahtarlar ve
JSON bicimi arac tarafinda kaliyor.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANG = ROOT / "src" / "ui" / "lang"
TARGET = ROOT / "docs" / "diyaloglar.md"

# Konusmaci anahtarlari (`ui/dialogue.py` SPEAKER_KEYS ile ayni sozluk).
SPEAKERS = {"rey": "REY", "ardo": "ARDO", "cemo": "CEMO", "echo": "YANKI"}

# Anahtar onekine gore gruplama. Sira = oyundaki sira.
GROUPS = (
    ("prologue_", "PROLOG - acilis (src/scenes/prologue.py)"),
    ("ch01_", "BOLUM 1 - Koy"),
    ("ch02_", "BOLUM 2 - Ilk Inis"),
    ("ch03_", "BOLUM 3 - Mesale Mahzeni"),
    ("ch04_", "BOLUM 4 - Kayit Odasi"),
    ("ch05_", "BOLUM 5 - Sular"),
    ("ch06_", "BOLUM 6 - ARDO"),
)

HEADER = """# DİYALOGLAR

Bu dosya `tools/dialogue_dump.py` ile üretildi. **Elle düzenlenebilir** —
sadece tırnak içindeki metni değiştir, sonra:

    python tools/dialogue_dump.py --geri

komutuyla dile geri yazılır. Anahtarlara (`ch01_echo_wake` gibi) dokunma;
onlar kodun içinde geçiyor.

Konuşmacı adı satırın başında: **YANKI** kafanın içindeki ses (mor,
çerçevesiz), diğerleri odada konuşan kişiler.

"""


def _speaker_of(key: str) -> str:
    """Anahtardan konusmaciyi tahmin eder.

    Anahtarlar `ch05_echo_valve` / `prologue_rey_3` gibi konusmaciyi
    ICINDE tasiyor - ayri bir tablo tutmaya gerek yok ve tutulsaydi
    ikisi bir gun ayrisirdi.
    """
    for token, label in SPEAKERS.items():
        if re.search(rf"(^|_){token}(_|\d|$)", key):
            return label
    return "?"


def dump() -> str:
    tr = json.loads((LANG / "tr.json").read_text(encoding="utf-8"))["line"]
    en = json.loads((LANG / "en.json").read_text(encoding="utf-8"))["line"]

    used: set[str] = set()
    parts = [HEADER]
    for prefix, title in GROUPS:
        keys = sorted(k for k in tr if k.startswith(prefix))
        if not keys:
            continue
        used.update(keys)
        parts.append(f"\n## {title}\n")
        for key in keys:
            parts.append(f"\n### {key}\n")
            parts.append(f"**{_speaker_of(key)}**\n")
            parts.append(f'- tr: "{tr[key]}"\n')
            parts.append(f'- en: "{en.get(key, "")}"\n')

    rest = sorted(k for k in tr if k not in used)
    if rest:
        parts.append("\n## DIGER\n")
        for key in rest:
            parts.append(f"\n### {key}\n")
            parts.append(f"**{_speaker_of(key)}**\n")
            parts.append(f'- tr: "{tr[key]}"\n')
            parts.append(f'- en: "{en.get(key, "")}"\n')
    return "".join(parts)


def restore() -> int:
    """Duzenlenmis dosyayi dil tablolarina geri yazar."""
    if not TARGET.is_file():
        print(f"!! {TARGET} yok - once dokum al")
        return 1
    body = TARGET.read_text(encoding="utf-8")

    current_key = ""
    updates: dict[str, dict[str, str]] = {"tr": {}, "en": {}}
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("### "):
            current_key = line[4:].strip()
            continue
        match = re.match(r'^-\s*(tr|en)\s*:\s*"(.*)"\s*$', line)
        if match and current_key:
            updates[match.group(1)][current_key] = match.group(2)

    changed = 0
    for lang in ("tr", "en"):
        path = LANG / f"{lang}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for key, value in updates[lang].items():
            if key in data["line"] and data["line"][key] != value:
                data["line"][key] = value
                changed += 1
            elif key not in data["line"]:
                # **Yeni anahtar EKLENMIYOR.** Kodda kullanilmayan bir
                # anahtar `tests/test_lang.py`'de "olu anahtar" olarak
                # kirilir; yeni replik once kodda yerini bulmali.
                print(f"   atlandi (kodda yok): {lang}/{key}")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"{changed} replik guncellendi")
    return 0


def main() -> int:
    if "--geri" in sys.argv:
        return restore()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(dump(), encoding="utf-8", newline="\n")
    count = dump().count("\n### ")
    print(f"yazildi: {TARGET}  ({count} replik)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
