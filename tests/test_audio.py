"""Ses adlari - **kodda cagrilan her ses gercekten var mi?**

`test_lang.py` dil anahtarlari icin ne yapiyorsa bu ses adlari icin
onu yapiyor. Sebep somut: 30.08.2026'da uc ara sahne yazdim ve ucunde
de olmayan ses adlari uydurdum - `torch_out`, `wall_break`, `pickup`.

Ucu de **sessizce** basarisiz oluyordu: `AudioMixer.play` bilinmeyen
adi gormezden geliyor, hata vermiyor. Yani sahne oynuyordu, sesi
yoktu, ve kimse fark etmiyordu. Ancak elle "acaba bu ses var mi" diye
bakinca ortaya cikti.

Iki yonlu kontrol:

  * kodda cagrilan her ad kayitli olmali (uydurma yok)
  * kayitli her ad bir yerden cagrilmali (olu ses yok)

Ikinci kontrol daha yumusak: bazi sesler yalnizca ileri bolumlerde
kullanilacak. Onlar `PLANNED` listesinde - **acikca** yazilmis olmalari
"unutuldu mu yoksa bekliyor mu" sorusunu ortadan kaldiriyor.

Calistir:
    python tests/test_audio.py
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

# Sesleri okumak icin oyunu acmaya gerek yok - kaynak taraniyor.
SFX_FILES = ("sfx.py", "sfx_combat.py", "sfx_enemies.py", "sfx_ui.py",
             "sfx_world.py")

# Kayitli ama henuz cagrilmayan sesler - **bilerek** bekliyorlar.
# Ses paketi bolumlerden once yazildi (`assets/audio/SES-LISTESI.md`),
# yani bunlarin cogu sirasi gelmemis bolumlere ait:
#
#   amb_*        oda atmosferleri - `Ambience` su an parcacik ureten
#                bir katman, sesli degil
#   journey_*    dikey yolculuk sahnesi kendi muziginden besleniyor
#   step_gravel  Bolum 9+ zeminleri (su an tas ve toprak var)
#   echo_loop    Yanki acikken surekli calacak katman
#
# Liste kisaliyor: `echo_reveal` Bolum 10'da (Yanki'nin yalani)
# kullanildi ve listeden dustu - testin ucuncu kontrolu bunu
# yakaladi. `step_water` Bolum 15'te dustu: damla odasinin su
# damlasi (`chapter15.py`) onu caliyor - ayak sesi olarak degil,
# **metronom** olarak. Ses zaten dogru sesti, bekledigi kullanim
# baskaymis.
#   *_idle       dusman bosta sesleri - `Enemy` bunlari hic calmiyor
#
# Bu liste bir "yapilacaklar"; kisaldikca ses tasarimi tamamlaniyor.
PLANNED: frozenset[str] = frozenset({
    "amb_cellar", "amb_deep", "amb_torch", "amb_village_night",
    "amb_water", "bloated_idle", "climber_cling",
    "echo_silent", "echo_sonar", "enemy_stagger",
    "intro_hum", "journey_cellar", "journey_night", "journey_wind",
    "shambler_attack",
    "shambler_idle", "step_gravel",
})
# `necklace_warm` ve `necklace_conflict` 30.08.2026'da listeden CIKTI:
# Bolum 13'un ara sahneleri ikisini de caliyor (kafes goruldugunde
# kolye isiniyor, bos kapida catisiyor). Aylardir bekleyen iki ses
# nihayet ait olduklari ana kavustu. `ledge_grab` de 31.08.2026'da
# cikti: Bolum 12'de kafese binerken caliyor. `echo_loop` de -
# Bolum 14'un arena girisinde, Kaynak karanliktan cikmadan once.

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    print(("OK " if condition else "!! ") + label
          + (f"  ({detail})" if detail else ""))
    if not condition:
        failures.append(label)


def registered() -> set[str]:
    names: set[str] = set()
    for name in SFX_FILES:
        source = (ROOT / "src" / "audio" / name).read_text(encoding="utf-8")
        names |= set(re.findall(r'@_register\("([a-z0-9_]+)"\)', source))
    return names


def called() -> dict[str, set[str]]:
    """Cagri bicimlerinde gecen ses adlari -> hangi dosyada.

    Yalnizca **cagri** bicimleri: `play_sound("ad")` ve sahneleme
    katmaninin `Cue(..., sound="ad")` alani. Uydurma ad kontrolu bunu
    kullaniyor - dar olmasi iyi, cunku bir yazim hatasini burada
    yakalamak istiyoruz.
    """
    found: dict[str, set[str]] = {}
    # `\w*sound\s*=` bilerek genis: `sound="x"` (Cue alani),
    # `tell_sound = "x"` ve `death_sound = "x"` (dusman sinif alanlari)
    # hepsi ayni desene giriyor. Ilk surum yalnizca `sound="` ariyordu
    # ve **esitligin etrafindaki bosluklar yuzunden** sinif alanlarini
    # hic gormuyordu - Zindanci'nin uydurma `shield_clang`'i tam bu
    # delikten gecti (30.08.2026).
    patterns = (re.compile(r'play_sound\(\s*"([a-z0-9_]+)"'),
                re.compile(r'\w*sound\s*=\s*"([a-z0-9_]+)"'))
    for path in (ROOT / "src").rglob("*.py"):
        if path.parent.name == "audio":
            continue            # tanimin kendisi, cagri degil
        source = path.read_text(encoding="utf-8")
        for pattern in patterns:
            for name in pattern.findall(source):
                found.setdefault(name, set()).add(
                    str(path.relative_to(ROOT)))
    return found


def mentioned() -> set[str]:
    """Kodda **herhangi bir yerde** duz dize olarak gecen ses adlari.

    Olu ses kontrolu bunu kullaniyor, `called()`i degil: bazi sesler
    bir fonksiyondan donuyor (`PlayScene._hit_sound` -> "hit_light")
    ve cagri bicimine hic uymuyor. Ilk surumde `hit_light`/`hit_heavy`
    "olu" diye raporlandi ve yanlisti.

    Genis tarama burada dogru: amac "hic kullanilmiyor mu" sorusu,
    "dogru mu yazilmis" sorusu degil.
    """
    seen: set[str] = set()
    for path in (ROOT / "src").rglob("*.py"):
        if path.parent.name == "audio":
            continue
        source = path.read_text(encoding="utf-8")
        seen |= set(re.findall(r'"([a-z0-9_]{4,})"', source))
    return seen


def main() -> int:
    print("=== ses adlari ===")
    known = registered()
    used = called()
    check(len(known) > 40, "ses bankasi dolu", f"{len(known)} ses")

    # --- 1. Uydurma ad var mi? ---
    invented = {name: files for name, files in used.items()
                if name not in known}
    if invented:
        for name, files in sorted(invented.items()):
            print(f"   -> {name}: {', '.join(sorted(files))}")
    check(not invented,
          "kodda cagrilan her ses KAYITLI",
          f"{len(invented)} uydurma ad" if invented else "")

    # --- 2. Olu ses var mi? ---
    unused = known - mentioned() - PLANNED
    if unused:
        print(f"   -> {', '.join(sorted(unused))}")
    check(not unused,
          "kayitli her ses bir yerden cagriliyor",
          f"{len(unused)} olu ses (ya kullan ya PLANNED'a ekle)"
          if unused else "")

    # --- 3. PLANNED listesi guncel mi? ---
    # Planli sayilan bir ses artik kullaniliyorsa listeden dusmeli;
    # yoksa liste zamanla anlamsizlasir ve gercek olu sesleri gizler.
    stale = PLANNED & mentioned()
    if stale:
        print(f"   -> {', '.join(sorted(stale))}")
    check(not stale,
          "PLANNED listesi guncel",
          f"{len(stale)} ses artik kullaniliyor, listeden cikarilmali"
          if stale else "")

    # --- 4. PLANNED'da olmayan bir ad yok ---
    ghost = PLANNED - known
    check(not ghost, "PLANNED'daki her ad gercekten kayitli",
          ", ".join(sorted(ghost)) if ghost else "")

    print("\n=== SONUC ===")
    if failures:
        print(f"{len(failures)} BASARISIZ:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("Ses adlari tutarli - uydurma yok, olu yok.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
